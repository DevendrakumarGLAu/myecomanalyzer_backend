# api/controllers/state_analytics.py
from django.db.models import Count, Q
from orders.models import Order

class StateAnalyticsController:
    @staticmethod
    def get_state_wise_order_analytics(start_date=None, end_date=None, platform_id=None,state=None, current_user=None):

        queryset = Order.objects.select_related(
            "marketplace_order",
            "marketplace_order__customer",
            "status"
        )

        # -----------------------------------
        # DATE FILTER
        # -----------------------------------
        if start_date and end_date:
            queryset = queryset.filter(marketplace_order__order_date__range=[
                    start_date,
                    end_date
                ]
            )

        # -----------------------------------
        # PLATFORM FILTER
        # -----------------------------------

        if platform_id:
            queryset = queryset.filter( marketplace_order__platform_id=platform_id)

        # -----------------------------------
        # STATE FILTER
        # -----------------------------------

        if state:
            queryset = queryset.filter(
                marketplace_order__customer__state__iexact=state
            )
        if current_user:
            queryset = queryset.filter(product__owner=current_user)
        # -----------------------------------
        # AGGREGATION
        # -----------------------------------

        data = (queryset.values("marketplace_order__customer__state").annotate(
                total_orders=Count("id"),
                delivered_orders=Count("id",filter=Q(status__code="DELIVERED")),
                rto_orders=Count("id",filter=Q(status__code__in=[
                            "RTO",
                            "RTO_DELIVERED"
                        ]
                    )
                ),
                customer_returns=Count("id",filter=Q(status__code__in=[
                            "RETURNED",
                            "CUSTOMER_RETURN"
                        ]
                    )
                )
            ).order_by("-total_orders")
        )

        # -----------------------------------
        # RESPONSE
        # -----------------------------------

        return [
            {
                "state": row[
                    "marketplace_order__customer__state"
                ],
                "total_orders": row[
                    "total_orders"
                ],
                "delivered_orders": row[
                    "delivered_orders"
                ],
                "rto_orders": row[
                    "rto_orders"
                ],
                "customer_returns": row[
                    "customer_returns"
                ],
                "rto_percent": round(

                    (
                        row["rto_orders"]
                        / row["total_orders"]
                    ) * 100,

                    2

                ) if row["total_orders"] > 0 else 0,
                "return_percent": round(
                    (
                        row["customer_returns"]
                        / row["total_orders"]
                    ) * 100,
                    2
                ) if row["total_orders"] > 0 else 0,
            }
            for row in data
        ]