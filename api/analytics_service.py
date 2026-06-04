from datetime import datetime, timedelta
from django.db.models import Sum, Count, F, Q, Max
from django.utils import timezone
from orders.models import Order
from payments.models import OrderSettlement
from products.models import ProductVariant
from platforms.models import Platform
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from datetime import timedelta
from django.db.models import Sum, Count, F, Q, Max
from django.utils import timezone

from orders.models import Order
from payments.models import OrderSettlement
from products.models import ProductVariant
from platforms.models import Platform


class AnalyticsService:

    @classmethod
    def _resolve_platform(cls, platform_code: str | None):
        if not platform_code:
            return None
        return Platform.objects.filter(code__iexact=platform_code).first()

    # -----------------------------
    # DATE RANGE RESOLVER
    # -----------------------------
    @classmethod
    def resolve_date_range(cls, date_range):
        today = timezone.now().date()

        if date_range == "today":
            return today, today

        if date_range == "yesterday":
            return today - timedelta(days=1), today - timedelta(days=1)

        if date_range == "last_7_days":
            return today - timedelta(days=7), today

        return None, None

    # -----------------------------
    # MAIN ANALYTICS FUNCTION
    # -----------------------------
    @classmethod
    def fetch_analytics(cls, current_user, platform_code=None, date_range=None):

        platform = cls._resolve_platform(platform_code)
        start_date, end_date = cls.resolve_date_range(date_range)

        # -----------------------------
        # ORDERS QUERYSET
        # -----------------------------
        order_filter = Q(product__owner=current_user)

        if platform:
            order_filter &= Q(marketplace_order__platform=platform)

        orders_qs = Order.objects.filter(order_filter)

        if start_date and end_date:
            orders_qs = orders_qs.filter(
                marketplace_order__order_date__range=(start_date, end_date)
            )

        total_orders = orders_qs.count()

        # -----------------------------
        # DISPATCH COUNT
        # -----------------------------
        dispatch_count = orders_qs.filter(
            status__code__in=["READY_TO_SHIP", "SHIPPED"]
        ).count()

        # -----------------------------
        # SETTLEMENTS QUERYSET
        # -----------------------------
        settlement_filter = Q(order__product__owner=current_user)

        settlements = OrderSettlement.objects.filter(settlement_filter)

        if platform:
            settlements = settlements.filter(platform=platform)

        if start_date and end_date:
            settlements = settlements.filter(
                payment_date__range=(start_date, end_date)
            )

        # -----------------------------
        # AGGREGATES
        # -----------------------------
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

        # -----------------------------
        # PROFIT
        # -----------------------------
        profit_aggregate = settlements.annotate(
            cost=F("order__variant__cost_price") * F("order__quantity"),
            profit=F("final_settlement_amount") - F("cost"),
        ).aggregate(total_profit=Sum("profit"))

        total_profit = float(profit_aggregate.get("total_profit") or 0)

        profit_margin = float((total_profit / total_sales) * 100 if total_sales else 0)
        return_rate = float((total_returns_count / total_orders) * 100 if total_orders else 0)
        rto_rate = float((total_rtos / total_orders) * 100 if total_orders else 0)

        # -----------------------------
        # INVENTORY
        # -----------------------------
        low_stock_variants = ProductVariant.objects.filter(
            product__owner=current_user,
            stock__lt=10
        )

        if platform:
            low_stock_variants = low_stock_variants.filter(product__platform=platform)

        low_stock_count = low_stock_variants.count()

        dead_stock_threshold = timezone.now().date() - timedelta(days=90)

        dead_inventory_variants = ProductVariant.objects.filter(
            product__owner=current_user,
            stock__gt=0,
        ).annotate(
            last_sold_date=Max("orders__marketplace_order__order_date")
        ).filter(
            Q(last_sold_date__lt=dead_stock_threshold) |
            Q(last_sold_date__isnull=True)
        )

        if platform:
            dead_inventory_variants = dead_inventory_variants.filter(
                product__platform=platform
            )

        dead_inventory_count = dead_inventory_variants.count()

        # -----------------------------
        # TOP PRODUCTS
        # -----------------------------
        top_product_rows = (
            settlements
            .annotate(
                variant_sku=F("order__variant__sku"),
                product_name=F("order__product__name"),
                variant_stock=F("order__variant__stock"),
                order_revenue=F("order__selling_price") * F("order__quantity"),
                order_profit=F("final_settlement_amount")
                             - F("order__variant__cost_price") * F("order__quantity"),
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

        # -----------------------------
        # PLATFORM PERFORMANCE
        # -----------------------------
        platform_rows = (
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
            for row in platform_rows
        ]

        # -----------------------------
        # FINAL RESPONSE
        # -----------------------------
        analytics_summary = {
                "total_sales": total_sales,
                "total_settlement": total_settlement,
                "total_profit": total_profit,
                "profit_margin": profit_margin,
                "total_orders": total_orders,
                "dispatch_count": dispatch_count,
                "return_rate": return_rate,
                "rto_rate": rto_rate,
                "low_stock_count": low_stock_count,
                "dead_inventory_count": dead_inventory_count,
                "top_products": top_products,
                "platform_performance": platform_performance,
                
                # ✅ FIELDS REQUIRED BY AIChatResponse
                "settlement_mismatch_count": 0,  # placeholder, compute if needed
                "cancelled_orders": 0,           # placeholder, compute if needed
                "dead_inventory_examples": [],   # optional list of examples
                "alerts": [],                    # optional alerts list
            }

        return {"summary": analytics_summary}


    @classmethod
    def get_dispatch_count(
        cls,
        current_user,
        platform_code=None,
        date_range=None,
    ):
        platform = cls._resolve_platform(platform_code)

        start_date, end_date = cls.resolve_date_range(date_range)

        query = Order.objects.filter(
            product__owner=current_user,
            status__code__in=["READY_TO_SHIP", "SHIPPED"]
        )

        # -------------------------
        # DATE FILTER (IMPORTANT)
        # -------------------------
        if start_date and end_date:
            query = query.filter(
                marketplace_order__order_date__range=(start_date, end_date)
            )

        if platform:
            query = query.filter(
                marketplace_order__platform=platform
            )

        return query.count()

    @classmethod
    def get_total_orders(cls, current_user, platform_code=None, date_range=None):

        platform = cls._resolve_platform(platform_code)
        start_date, end_date = cls.resolve_date_range(date_range)

        query = Order.objects.filter(product__owner=current_user)

        if start_date and end_date:
            query = query.filter(
                marketplace_order__order_date__range=(start_date, end_date)
            )

        if platform:
            query = query.filter(marketplace_order__platform=platform)

        return query.count()
    @staticmethod
    def extract_month_year(message: str):
        """
        Detect month from user message like:
        'in may', 'for april', 'march orders'
        """

        message = message.lower()

        months = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }

        for name, num in months.items():
            if name in message:
                return num, datetime.now().year

        return None, None

    @staticmethod
    def resolve_date_range(date_range):
        today = timezone.now().date()

        if date_range == "today":
            return today, today

        if date_range == "yesterday":
            return today - timedelta(days=1), today - timedelta(days=1)

        if date_range == "last_7_days":
            return today - timedelta(days=7), today

        return None, None