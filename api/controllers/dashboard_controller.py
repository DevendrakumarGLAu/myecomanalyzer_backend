from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone

from orders.models import Order
from products.models import Product, ProductVariant
from payments.models import OrderSettlement
from marketplace.models import MarketplaceOrder
from platforms.models import Platform
from django.db.models import Count, Q

class DashboardController:

    @staticmethod
    def get_dashboard(platform_code: str = None, current_user=None):
        try:
            # Make sure current_user is required
            if current_user is None:
                raise ValueError("current_user must be provided")

            # Get platform_id from platform_code
            platform_id = None
            if platform_code:
                try:
                    platform = Platform.objects.get(code=platform_code)
                    platform_id = platform.id
                except Platform.DoesNotExist:
                    # Platform not found, return empty dashboard
                    return {
                        "summary": {
                            "total_orders": 0,
                            "total_products": 0,
                            "total_sales": 0,
                            "total_returns": 0,
                            "total_settlement": 0,
                            "low_stock_products": 0
                        },
                        "orders_by_status": [],
                        "orders_by_platform": [],
                        "sales_trend": [],
                        "delivery_partner_stats": []
                    }

            # Filter orders for logged-in user
            order_filter = {
                "product__owner": current_user  # only user's products
            }

            if platform_id:
                order_filter["marketplace_order__platform_id"] = platform_id

            # Total Orders
            total_orders = Order.objects.filter(**order_filter).count()

            # Total Products
            product_filter = {"owner": current_user}
            if platform_id:
                product_filter["platform_id"] = platform_id
            total_products = Product.objects.filter(**product_filter).count()

            # Settlements
            settlements = OrderSettlement.objects.filter(order__product__owner=current_user)
            if platform_id:
                settlements = settlements.filter(order__marketplace_order__platform_id=platform_id)

            total_sales = settlements.aggregate(total=Sum("total_sale_amount"))["total"] or 0
            total_returns = settlements.aggregate(total=Sum("total_return_amount"))["total"] or 0
            total_settlement = settlements.aggregate(total=Sum("final_settlement_amount"))["total"] or 0

            # Low stock products
            low_stock_products = ProductVariant.objects.filter(
                product__owner=current_user,
                stock__lt=10
            )
            if platform_id:
                low_stock_products = low_stock_products.filter(product__platform_id=platform_id)
            low_stock_products = low_stock_products.count()

            # Orders by Status
            orders_by_status = list(
                Order.objects.filter(**order_filter)
                .values("status__label")
                .annotate(total=Count("id"))
            )

            # Orders by Platform
            orders_by_platform = list(
    MarketplaceOrder.objects.filter(sub_orders__product__owner=current_user)
    .values("platform__name")
    .annotate(total=Count("sub_orders"))
)

            # Last 7 days sales trend
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
            delivery_partner_stats = list(
                    Order.objects.filter(**order_filter)
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

            return {
                "summary": {
                    "total_orders": total_orders,
                    "total_products": total_products,
                    "total_sales": total_sales,
                    "total_returns": total_returns,
                    "total_settlement": total_settlement,
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
                    "low_stock_products": 0
                },
                "orders_by_status": [],
                "orders_by_platform": [],
                "sales_trend": [],
                "delivery_partner_stats": []
            }