from django.db.models import Sum, Count, Q
from datetime import timedelta, datetime
from django.utils import timezone

from orders.models import Order
from products.models import Product, ProductVariant
from payments.models import OrderSettlement
from marketplace.models import MarketplaceOrder
from platforms.models import Platform


class DashboardController:

    @staticmethod
    def get_dashboard(
        platform_code: str = None,
        date_from: str = None,
        date_to: str = None,
        order_status: str = None,
        delivery_partner: str = None,
        min_order_amount: float = None,
        max_order_amount: float = None,
        current_user=None
    ):
        try:
            if current_user is None:
                raise ValueError("current_user must be provided")

            # ----------------------------
            # PLATFORM FILTER
            # ----------------------------
            platform_id = None
            if platform_code:
                try:
                    platform = Platform.objects.get(code__iexact=platform_code)
                    platform_id = platform.id
                except Platform.DoesNotExist:
                    return {
                        "summary": {
                            "total_orders": 0,
                            "total_products": 0,
                            "total_sales": 0,
                            "total_returns": 0,
                            "total_settlement": 0,
                            "total_claims": 0,
                            "low_stock_products": 0
                        },
                        "orders_by_status": [],
                        "orders_by_platform": [],
                        "sales_trend": [],
                        "delivery_partner_stats": []
                    }

            # ----------------------------
            # DATE FILTERS
            # ----------------------------
            date_from_obj = None
            date_to_obj = None
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                except ValueError:
                    date_from_obj = None
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                except ValueError:
                    date_to_obj = None

            # ----------------------------
            # ORDER FILTER
            # ----------------------------
            order_filter = {"product__owner": current_user}
            marketplace_filter = {"sub_orders__product__owner": current_user}

            if platform_id:
                order_filter["marketplace_order__platform_id"] = platform_id
                marketplace_filter["platform_id"] = platform_id

            # Apply date filters
            if date_from_obj:
                marketplace_filter["order_date__gte"] = date_from_obj
            
            if date_to_obj:
                marketplace_filter["order_date__lte"] = date_to_obj

            # Apply order status filter
            if order_status:
                order_filter["status__code__iexact"] = order_status

            # Apply delivery partner filter
            if delivery_partner:
                order_filter["delivery_partner__name__icontains"] = delivery_partner

            # ----------------------------
            # TOTAL ORDERS (FAST)
            # ----------------------------
            total_orders_query = Order.objects.filter(**order_filter)
            
            # Apply amount filters if provided
            if min_order_amount is not None or max_order_amount is not None:
                # Filter by selling_price (unit price) * quantity for order amount
                if min_order_amount is not None:
                    total_orders_query = total_orders_query.filter(
                        Q(selling_price__gte=min_order_amount / 100)  # Approximate filter
                    )
                if max_order_amount is not None:
                    total_orders_query = total_orders_query.filter(
                        Q(selling_price__lte=max_order_amount / 100)  # Approximate filter
                    )
            
            total_orders = total_orders_query.count()

            # ----------------------------
            # TOTAL PRODUCTS
            # ----------------------------
            product_filter = {"owner": current_user}
            if platform_id:
                product_filter["platform_id"] = platform_id

            total_products = Product.objects.filter(**product_filter).count()

            # ----------------------------
            # SETTLEMENTS (OPTIMIZED - SINGLE QUERY)
            # ----------------------------
            settlements_query = OrderSettlement.objects.filter(
                order__product__owner=current_user
            )

            # Apply marketplace filters (date, platform)
            if date_from_obj:
                settlements_query = settlements_query.filter(
                    order__marketplace_order__order_date__gte=date_from_obj
                )
            
            if date_to_obj:
                settlements_query = settlements_query.filter(
                    order__marketplace_order__order_date__lte=date_to_obj
                )
            
            if platform_id:
                settlements_query = settlements_query.filter(
                    order__marketplace_order__platform_id=platform_id
                )

            # Apply order status filter
            if order_status:
                settlements_query = settlements_query.filter(
                    order__status__code__iexact=order_status
                )

            # Apply delivery partner filter
            if delivery_partner:
                settlements_query = settlements_query.filter(
                    order__delivery_partner__name__icontains=delivery_partner
                )

            # Apply amount filters
            if min_order_amount is not None:
                settlements_query = settlements_query.filter(
                    order__selling_price__gte=min_order_amount / 100
                )
            
            if max_order_amount is not None:
                settlements_query = settlements_query.filter(
                    order__selling_price__lte=max_order_amount / 100
                )

            settlements = settlements_query

            totals = settlements.aggregate(
                total_sales=Sum("total_sale_amount"),

                total_returns=Sum(
                    "final_settlement_amount",
                    filter=Q(final_settlement_amount__lt=0)
                ),

                total_settlement=Sum(
                    "final_settlement_amount",
                    filter=Q(final_settlement_amount__gt=0)
                ),

                total_claims=Sum("claim_amount"),
            )

            total_sales = totals["total_sales"] or 0
            total_returns = totals["total_returns"] or 0
            total_settlement = totals["total_settlement"] or 0
            total_claims = totals["total_claims"] or 0

            # ----------------------------
            # LOW STOCK PRODUCTS
            # ----------------------------
            low_stock_products = ProductVariant.objects.filter(
                product__owner=current_user,
                stock__lt=10
            )

            if platform_id:
                low_stock_products = low_stock_products.filter(
                    product__platform_id=platform_id
                )

            low_stock_products = low_stock_products.count()

            # ----------------------------
            # ORDERS BY STATUS
            # ----------------------------
            orders_by_status_query = Order.objects.filter(**order_filter)
            
            # Apply marketplace filters
            if date_from_obj or date_to_obj:
                date_filters = {}
                if date_from_obj:
                    date_filters["marketplace_order__order_date__gte"] = date_from_obj
                if date_to_obj:
                    date_filters["marketplace_order__order_date__lte"] = date_to_obj
                orders_by_status_query = orders_by_status_query.filter(**date_filters)
            
            orders_by_status = list(
                orders_by_status_query
                .values("status__label")
                .annotate(total=Count("id"))
            )

            # ----------------------------
            # ORDERS BY PLATFORM
            # ----------------------------
            orders_by_platform_query = MarketplaceOrder.objects.filter(**marketplace_filter)
            
            orders_by_platform = list(
                orders_by_platform_query
                .values("platform__name")
                .annotate(total=Count("sub_orders"))
            )

            # ----------------------------
            # SALES TREND (LAST 7 DAYS OR DATE RANGE)
            # ----------------------------
            if date_from_obj and date_to_obj:
                # Use the provided date range
                sales_trend_query = MarketplaceOrder.objects.filter(
                    order_date__gte=date_from_obj,
                    order_date__lte=date_to_obj,
                    sub_orders__product__owner=current_user
                )
            else:
                # Default to last 7 days
                last_7_days = timezone.now().date() - timedelta(days=7)
                sales_trend_query = MarketplaceOrder.objects.filter(
                    order_date__gte=last_7_days,
                    sub_orders__product__owner=current_user
                )

            if platform_id:
                sales_trend_query = sales_trend_query.filter(platform_id=platform_id)

            sales_trend = list(
                sales_trend_query
                .values("order_date")
                .annotate(total_orders=Count("sub_orders"))
                .order_by("order_date")
            )

            # ----------------------------
            # DELIVERY PARTNER STATS (OPTIMIZED)
            # ----------------------------
            delivery_partner_stats_query = Order.objects.filter(**order_filter)
            
            # Apply marketplace filters
            if date_from_obj or date_to_obj:
                date_filters = {}
                if date_from_obj:
                    date_filters["marketplace_order__order_date__gte"] = date_from_obj
                if date_to_obj:
                    date_filters["marketplace_order__order_date__lte"] = date_to_obj
                delivery_partner_stats_query = delivery_partner_stats_query.filter(**date_filters)
            
            delivery_partner_stats = list(
                delivery_partner_stats_query
                .select_related("delivery_partner", "status")
                .values("delivery_partner__name")
                .annotate(
                    total_orders=Count("id"),
                    delivered=Count("id", filter=Q(status__code="DELIVERED")),
                    rto=Count("id", filter=Q(status__code="RTO_COMPLETE")),
                    cancelled=Count("id", filter=Q(status__code="CANCELLED")),
                    customer_return=Count("id", filter=Q(status__code="DOOR_STEP_EXCHANGED")),
                    ready_to_ship=Count("id", filter=Q(status__code="READY_TO_SHIP")),
                )
            )

            # ----------------------------
            # RESPONSE
            # ----------------------------
            return {
                "summary": {
                    "total_orders": total_orders,
                    "total_products": total_products,
                    "total_sales": total_sales,
                    "total_returns": total_returns,
                    "total_settlement": total_settlement,
                    "total_claims": total_claims,
                    "low_stock_products": low_stock_products
                },
                "orders_by_status": [
                    {"status": x["status__label"], "total": x["total"]}
                    for x in orders_by_status
                ],
                "orders_by_platform": [
                    {"platform": x["platform__name"], "total": x["total"]}
                    for x in orders_by_platform
                ],
                "sales_trend": [
                    {"date": str(x["order_date"]), "total_orders": x["total_orders"]}
                    for x in sales_trend
                ],
                "delivery_partner_stats": [
                    {
                        "partner": x.get("delivery_partner__name") or "Unknown",
                        "total_orders": x["total_orders"],
                        "delivered": x["delivered"],
                        "rto": x["rto"],
                        "cancelled": x["cancelled"],
                        "customer_return": x["customer_return"],
                        "ready_to_ship": x["ready_to_ship"],
                    }
                    for x in delivery_partner_stats
                ]
            }

        except Exception as e:
            print(f"Error in DashboardController.get_dashboard: {str(e)}")

            return {
                "summary": {
                    "total_orders": 0,
                    "total_products": 0,
                    "total_sales": 0,
                    "total_returns": 0,
                    "total_settlement": 0,
                    "total_claims": 0,
                    "low_stock_products": 0
                },
                "orders_by_status": [],
                "orders_by_platform": [],
                "sales_trend": [],
                "delivery_partner_stats": []
            }