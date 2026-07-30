from django.db.models import Count, Max, Q

from customers.models import Customer
from orders.models import Order

RTO_CODES = {"RTO_COMPLETE", "RTO", "RTO_DELIVERED"}
RETURN_CODES = {"CUSTOMER_RETURN"}
BAD_CODES = RTO_CODES | RETURN_CODES

# total_orders < MIN_ORDERS_FOR_VERDICT -> not enough history to judge yet,
# regardless of what that one order's outcome was.
MIN_ORDERS_FOR_VERDICT = 2
HIGH_RISK_RATE = 0.5
MEDIUM_RISK_RATE = 0.25


def _risk_level(total_orders: int, bad_count: int) -> tuple[str, float, str]:
    if total_orders < MIN_ORDERS_FOR_VERDICT:
        return "NEW", 0.0, "Not enough order history yet to judge this customer."

    rate = bad_count / total_orders
    percent = round(rate * 100, 1)

    if rate >= HIGH_RISK_RATE:
        level = "HIGH_RISK"
    elif rate >= MEDIUM_RISK_RATE:
        level = "MEDIUM_RISK"
    else:
        level = "LOW_RISK"

    reason = f"{bad_count} of {total_orders} orders ({percent}%) were returned or RTO'd."
    return level, rate, reason


class CustomerRiskController:

    @staticmethod
    def get_risk_report(current_user, search=None, min_orders=None, risk_level=None, limit=50):
        """
        One customer per row: how many times they've ordered from this
        seller, and how many of those came back as a return/RTO — the
        repeat-RTO pattern is the actual fake/serial-return-order signal,
        not any single order's outcome.
        """
        owner_filter = Q(marketplace_orders__sub_orders__product__owner=current_user)

        customers = (
            Customer.objects.filter(owner_filter)
            .annotate(
                total_orders=Count(
                    "marketplace_orders__sub_orders",
                    filter=Q(marketplace_orders__sub_orders__product__owner=current_user),
                    distinct=True,
                ),
                rto_count=Count(
                    "marketplace_orders__sub_orders",
                    filter=Q(
                        marketplace_orders__sub_orders__product__owner=current_user,
                        marketplace_orders__sub_orders__status__code__in=RTO_CODES,
                    ),
                    distinct=True,
                ),
                return_count=Count(
                    "marketplace_orders__sub_orders",
                    filter=Q(
                        marketplace_orders__sub_orders__product__owner=current_user,
                        marketplace_orders__sub_orders__status__code__in=RETURN_CODES,
                    ),
                    distinct=True,
                ),
                delivered_count=Count(
                    "marketplace_orders__sub_orders",
                    filter=Q(
                        marketplace_orders__sub_orders__product__owner=current_user,
                        marketplace_orders__sub_orders__status__code="DELIVERED",
                    ),
                    distinct=True,
                ),
                last_order_date=Max(
                    "marketplace_orders__order_date",
                    filter=Q(marketplace_orders__sub_orders__product__owner=current_user),
                ),
            )
            .distinct()
        )

        if search:
            customers = customers.filter(
                Q(name__icontains=search) | Q(phone__icontains=search) | Q(pincode__icontains=search)
            )

        results = []
        for c in customers:
            bad_count = c.rto_count + c.return_count
            level, rate, reason = _risk_level(c.total_orders, bad_count)

            if risk_level and level != risk_level.upper():
                continue
            if min_orders and c.total_orders < min_orders:
                continue

            results.append({
                "customer_id": c.id,
                "name": c.name,
                "phone": c.phone,
                "state": c.state,
                "pincode": c.pincode,
                "total_orders": c.total_orders,
                "delivered_count": c.delivered_count,
                "rto_count": c.rto_count,
                "return_count": c.return_count,
                "return_rto_rate_percent": round(rate * 100, 1),
                "risk_level": level,
                "risk_reason": reason,
                "last_order_date": c.last_order_date,
            })

        # Worst offenders first — highest return/RTO rate, then most orders
        # (a serial-RTO customer with many orders is a bigger deal than one
        # with the same rate but only 2 orders).
        results.sort(key=lambda r: (r["return_rto_rate_percent"], r["total_orders"]), reverse=True)

        return {
            "total": len(results),
            "data": results[:limit],
        }

    @staticmethod
    def get_customer_detail(customer_id, current_user):
        customer = Customer.objects.filter(
            id=customer_id,
            marketplace_orders__sub_orders__product__owner=current_user,
        ).distinct().first()

        if not customer:
            return None

        orders = (
            Order.objects.filter(
                marketplace_order__customer_id=customer_id,
                product__owner=current_user,
            )
            .select_related("marketplace_order", "marketplace_order__platform", "product", "variant", "status")
            .order_by("-marketplace_order__order_date", "-created_at")
        )

        order_history = [
            {
                "order_id": o.marketplace_sub_order_id,
                "order_date": o.marketplace_order.order_date,
                "platform": o.marketplace_order.platform.name if o.marketplace_order.platform else None,
                "product_name": o.product.name if o.product else None,
                "sku": o.variant.sku if o.variant else None,
                "status": o.status.code if o.status else None,
                "is_bad_outcome": (o.status.code in BAD_CODES) if o.status else False,
            }
            for o in orders
        ]

        total_orders = len(order_history)
        bad_count = sum(1 for o in order_history if o["is_bad_outcome"])
        level, rate, reason = _risk_level(total_orders, bad_count)

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "address": customer.address,
            "state": customer.state,
            "pincode": customer.pincode,
            "phone": customer.phone,
            "email": customer.email,
            "total_orders": total_orders,
            "return_rto_rate_percent": round(rate * 100, 1),
            "risk_level": level,
            "risk_reason": reason,
            "order_history": order_history,
        }
