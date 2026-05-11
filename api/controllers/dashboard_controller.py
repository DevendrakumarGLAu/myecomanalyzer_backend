from django.db.models import Sum, Count, Q, F
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
                            "total_profit": 0,
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
            # PROFIT CALCULATION
            # ----------------------------
            profit_query = OrderSettlement.objects.filter(
                order__product__owner=current_user
            ).select_related('order__variant')

            # Apply the same filters as settlements_query
            if date_from_obj:
                profit_query = profit_query.filter(
                    order__marketplace_order__order_date__gte=date_from_obj
                )
            
            if date_to_obj:
                profit_query = profit_query.filter(
                    order__marketplace_order__order_date__lte=date_to_obj
                )
            
            if platform_id:
                profit_query = profit_query.filter(
                    order__marketplace_order__platform_id=platform_id
                )

            if order_status:
                profit_query = profit_query.filter(
                    order__status__code__iexact=order_status
                )

            if delivery_partner:
                profit_query = profit_query.filter(
                    order__delivery_partner__name__icontains=delivery_partner
                )

            if min_order_amount is not None:
                profit_query = profit_query.filter(
                    order__selling_price__gte=min_order_amount / 100
                )
            
            if max_order_amount is not None:
                profit_query = profit_query.filter(
                    order__selling_price__lte=max_order_amount / 100
                )

            # Calculate total profit: sum(final_settlement_amount - cost_price * quantity)
            profit_totals = profit_query.aggregate(
                total_settlement_sum=Sum("final_settlement_amount"),
                total_cost_sum=Sum("order__variant__cost_price") * Sum("order__quantity")  # This won't work directly
            )

            # Actually, need to calculate per order: final_settlement - (cost_price * quantity)
            # Since final_settlement is per settlement, and cost_price * quantity per order
            # But settlements are per order, so we can do:
            profit_orders = profit_query.annotate(
                profit_per_order=F("final_settlement_amount") - F("order__variant__cost_price") * F("order__quantity")
            ).aggregate(
                total_profit=Sum("profit_per_order")
            )

            total_profit = profit_orders["total_profit"] or 0

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
                    "total_profit": total_profit,
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
                    "total_profit": 0,
                    "low_stock_products": 0
                },
                "orders_by_status": [],
                "orders_by_platform": [],
                "sales_trend": [],
                "delivery_partner_stats": []
            }

    @staticmethod
    def get_notifications(current_user=None, platform_code: str = None):
        try:
            if current_user is None:
                raise ValueError("current_user must be provided")

            # Platform filter
            platform_filter = {}
            if platform_code:
                try:
                    platform = Platform.objects.get(code__iexact=platform_code)
                    platform_filter["platform_id"] = platform.id
                except Platform.DoesNotExist:
                    return {"notifications": []}

            notifications = []

            # 1. Low stock products (stock < 10)
            low_stock_variants = ProductVariant.objects.filter(
                product__owner=current_user,
                stock__lt=10,
                stock__gt=0
            ).select_related('product').order_by('stock')[:5]

            for variant in low_stock_variants:
                notifications.append({
                    "type": "warning",
                    "title": "Low Stock Alert",
                    "message": f"Product '{variant.product.name}' (SKU: {variant.sku}) has only {variant.stock} units left",
                    "product_id": variant.product.id,
                    "variant_id": variant.id,
                    "priority": "high"
                })

            # 2. Out of stock products
            out_of_stock_variants = ProductVariant.objects.filter(
                product__owner=current_user,
                stock=0
            ).select_related('product')[:5]

            for variant in out_of_stock_variants:
                notifications.append({
                    "type": "error",
                    "title": "Out of Stock",
                    "message": f"Product '{variant.product.name}' (SKU: {variant.sku}) is out of stock",
                    "product_id": variant.product.id,
                    "variant_id": variant.id,
                    "priority": "high"
                })

            # 3. Most sold products (by quantity in last 30 days)
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            most_sold_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago
            ).values('product__name', 'product__id').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:3]

            for product in most_sold_products:
                notifications.append({
                    "type": "info",
                    "title": "Top Selling Product",
                    "message": f"'{product['product__name']}' sold {product['total_quantity']} units in the last 30 days",
                    "product_id": product['product__id'],
                    "priority": "medium"
                })

            # 4. Most profitable products (revenue - cost in last 30 days)
            profitable_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago
            ).values(
                'product__name', 
                'product__id'
            ).annotate(
                total_revenue=Sum('selling_price') * Sum('quantity'),
                total_cost=Sum('variant__cost_price') * Sum('quantity'),
                profit=Sum('selling_price') * Sum('quantity') - Sum('variant__cost_price') * Sum('quantity')
            ).order_by('-profit')[:3]

            for product in profitable_products:
                if product['profit'] > 0:
                    notifications.append({
                        "type": "success",
                        "title": "High Profit Product",
                        "message": f"'{product['product__name']}' generated ₹{product['profit']:.2f} profit in the last 30 days",
                        "product_id": product['product__id'],
                        "priority": "medium"
                    })

            # 5. Products with losses (negative profit)
            loss_products = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago
            ).values(
                'product__name', 
                'product__id'
            ).annotate(
                total_revenue=Sum('selling_price') * Sum('quantity'),
                total_cost=Sum('variant__cost_price') * Sum('quantity'),
                profit=Sum('selling_price') * Sum('quantity') - Sum('variant__cost_price') * Sum('quantity')
            ).filter(profit__lt=0).order_by('profit')[:3]

            for product in loss_products:
                notifications.append({
                    "type": "error",
                    "title": "Loss Making Product",
                    "message": f"'{product['product__name']}' incurred ₹{abs(product['profit']):.2f} loss in the last 30 days",
                    "product_id": product['product__id'],
                    "priority": "high"
                })

            # 6. Recent high-value orders
            recent_high_value_orders = Order.objects.filter(
                product__owner=current_user,
                marketplace_order__order_date__gte=thirty_days_ago,
                selling_price__gte=1000  # Orders worth more than ₹1000
            ).select_related('product', 'marketplace_order').order_by('-marketplace_order__order_date')[:3]

            for order in recent_high_value_orders:
                notifications.append({
                    "type": "info",
                    "title": "High Value Order",
                    "message": f"Order for '{order.product.name}' worth ₹{order.selling_price:.2f} placed on {order.marketplace_order.order_date}",
                    "product_id": order.product.id,
                    "order_id": order.id,
                    "priority": "low"
                })

            # Sort notifications by priority (high -> medium -> low)
            priority_order = {"high": 0, "medium": 1, "low": 2}
            notifications.sort(key=lambda x: priority_order.get(x["priority"], 3))

            return {"notifications": notifications[:10]}  # Return top 10 notifications

        except Exception as e:
            print(f"Error in DashboardController.get_notifications: {str(e)}")
            return {"notifications": []}