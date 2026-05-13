from datetime import timedelta
from django.db.models import Sum, Count, F, Q, Max
from django.utils import timezone
from django.contrib.auth.models import User

from orders.models import Order
from payments.models import OrderSettlement
from products.models import ProductVariant
from marketplace.models import MarketplaceOrder
from platforms.models import Platform


class AnalyticsService:
    @classmethod
    def _resolve_platform(cls, platform_code: str | None):
        if not platform_code:
            return None
        return Platform.objects.filter(code__iexact=platform_code).first()

    @classmethod
    def _platform_filter(cls, qs, platform):
        if platform is None:
            return qs
        return qs.filter(order__marketplace_order__platform=platform)

    @classmethod
    def _platform_filter_orders(cls, qs, platform):
        if platform is None:
            return qs
        return qs.filter(marketplace_order__platform=platform)

    @classmethod
    def fetch_analytics(cls, current_user: User, platform_code: str | None = None) -> dict:
        platform = cls._resolve_platform(platform_code)

        order_filter = Q(product__owner=current_user)
        settlement_filter = Q(order__product__owner=current_user)
        marketplace_filter = Q(sub_orders__product__owner=current_user)

        if platform is not None:
            order_filter &= Q(marketplace_order__platform=platform)
            settlement_filter &= Q(order__marketplace_order__platform=platform)
            marketplace_filter &= Q(platform=platform)

        total_orders = Order.objects.filter(order_filter).count()

        settlements = OrderSettlement.objects.filter(settlement_filter).select_related(
            "order__variant",
            "order__product",
            "order__marketplace_order",
        )

        totals = settlements.aggregate(
            total_sales=Sum("total_sale_amount"),
            total_settlement=Sum("final_settlement_amount"),
            total_returns=Sum("total_return_amount"),
            total_rtos=Count("id", filter=Q(is_rto=True)),
            total_returns_count=Count("id", filter=Q(is_return=True)),
        )

        total_sales = float(totals.get("total_sales") or 0)
        total_settlement = float(totals.get("total_settlement") or 0)
        total_returns_amount = float(totals.get("total_returns") or 0)
        total_rtos = totals.get("total_rtos") or 0
        total_returns_count = totals.get("total_returns_count") or 0

        profit_aggregate = settlements.annotate(
            cost=F("order__variant__cost_price") * F("order__quantity"),
            profit=F("final_settlement_amount") - F("cost"),
        ).aggregate(total_profit=Sum("profit"))

        total_profit = float(profit_aggregate.get("total_profit") or 0)
        profit_margin = float((total_profit / total_sales) * 100 if total_sales else 0)
        return_rate = float((total_returns_count / total_orders) * 100 if total_orders else 0)
        rto_rate = float((total_rtos / total_orders) * 100 if total_orders else 0)

        low_stock_variants = ProductVariant.objects.filter(product__owner=current_user, stock__lt=10)
        if platform is not None:
            low_stock_variants = low_stock_variants.filter(product__platform=platform)

        low_stock_count = low_stock_variants.count()

        dead_stock_threshold = timezone.now().date() - timedelta(days=90)
        dead_inventory_variants = ProductVariant.objects.filter(
            product__owner=current_user,
            stock__gt=0,
        ).annotate(
            last_sold_date=Max("orders__marketplace_order__order_date")
        ).filter(
            Q(last_sold_date__lt=dead_stock_threshold) | Q(last_sold_date__isnull=True)
        )
        if platform is not None:
            dead_inventory_variants = dead_inventory_variants.filter(product__platform=platform)

        dead_inventory_count = dead_inventory_variants.count()
 
        dead_inventory_examples = [
                {
                    key: (value.isoformat() if hasattr(value, "isoformat") else value)
                    for key, value in row.items()
                }
                for row in dead_inventory_variants.values(
                    variant_sku=F("sku"),
                    product_name=F("product__name"),
                    variant_stock=F("stock"),
                    last_sold_date=F("last_sold_date"),
                )[:5]
            ]

        top_product_rows = (
            settlements
            .annotate(
                variant_sku=F("order__variant__sku"),
                product_name=F("order__product__name"),
                variant_stock=F("order__variant__stock"),
                order_revenue=F("order__selling_price") * F("order__quantity"),
                order_profit=F("final_settlement_amount") - F("order__variant__cost_price") * F("order__quantity"),
            )
            .values("variant_sku", "product_name", "variant_stock")
            .annotate(
                total_revenue=Sum("order_revenue"),
                total_profit=Sum("order_profit"),
                order_count=Count("id"),
            )
            .order_by("-total_revenue")[:5]
        )

        top_products = [
            {
                "sku": row["variant_sku"],
                "product_name": row["product_name"],
                "stock": int(row["variant_stock"] or 0),
                "sales": float(row["total_revenue"] or 0),
                "profit": float(row["total_profit"] or 0),
                "order_count": int(row["order_count"]),
            }
            for row in top_product_rows
        ]

        platform_performance_rows = (
            settlements
            .values("order__marketplace_order__platform__name")
            .annotate(
                platform_name=F("order__marketplace_order__platform__name"),
                cost=F("order__variant__cost_price") * F("order__quantity"),
                profit=F("final_settlement_amount") - F("cost"),
            )
            .values("platform_name")
            .annotate(
                order_count=Count("id"),
                revenue=Sum("final_settlement_amount"),
                total_profit=Sum("profit"),
            )
            .order_by("-order_count")
        )

        platform_performance = [
            {
                "platform": row["platform_name"] or "Unknown",
                "sales": float(row["revenue"] or 0),
                "profit": float(row["total_profit"] or 0),
                "orders": int(row["order_count"] or 0),
            }
            for row in platform_performance_rows
        ]

        mismatch_query = settlements.filter(
            Q(total_sale_amount__gt=F("final_settlement_amount") + 1)
            | Q(total_sale_amount__lt=F("final_settlement_amount") - 1)
        )
        settlement_mismatch_count = mismatch_query.count()

        alerts = []
        if low_stock_count:
            alerts.append(f"{low_stock_count} SKU(s) below 10 units")
        if dead_inventory_count:
            alerts.append(f"{dead_inventory_count} dead inventory SKU(s)")
        if return_rate > 5:
            alerts.append(f"Return rate is {return_rate:.1f}%")
        if rto_rate > 3:
            alerts.append(f"RTO rate is {rto_rate:.1f}%")
        if settlement_mismatch_count:
            alerts.append(f"{settlement_mismatch_count} settlement records have a mismatch")

        analytics_summary = {
            "total_sales": total_sales,
            "total_settlement": total_settlement,
            "total_profit": total_profit,
            "profit_margin": profit_margin,
            "total_orders": total_orders,
            "return_rate": return_rate,
            "rto_rate": rto_rate,
            "low_stock_count": low_stock_count,
            "dead_inventory_count": dead_inventory_count,
            "settlement_mismatch_count": settlement_mismatch_count,
            "top_products": top_products,
            "platform_performance": platform_performance,
            "dead_inventory_examples": dead_inventory_examples,
            "alerts": alerts,
        }

        return {"summary": analytics_summary}
