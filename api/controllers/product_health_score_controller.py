from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from orders.models import Order
from products.models import Product, ProductVariant

# Dispatch Delay (10% in the original 5-factor design) has no tracked data
# anywhere in this codebase today — Order has no dispatched/shipped
# timestamp, and status_updated_at is overwritten on every transition, so a
# true placed->dispatched delta can't be computed. Its weight is
# redistributed proportionally across the other 4 factors instead of being
# guessed at with an unreliable proxy:
#   30/25/20/15 (sums to 90) -> scaled to sum to 100
WEIGHTS = {
    "profit_margin": 33,
    "sales_volume": 28,
    "return_rate": 22,
    "inventory_availability": 17,
}

RETURN_STATUS_CODES = {"CUSTOMER_RETURN", "RTO_COMPLETE", "RTO", "RTO_DELIVERED"}

GRADE_BANDS = [
    (85, "A"),
    (70, "B"),
    (55, "C"),
    (40, "D"),
]


def _grade_for(score: float) -> str:
    for threshold, grade in GRADE_BANDS:
        if score >= threshold:
            return grade
    return "F"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class ProductHealthScoreController:

    @staticmethod
    def get_health_scores(current_user, platform_code=None, days=90):
        """
        Computes a 0-100 health score for every product owned by current_user,
        in one batch (not per-product queries) so this is cheap enough to
        back a product-table column rather than just a single-product detail
        view.
        """
        cutoff = timezone.now() - timedelta(days=days)

        products = Product.objects.filter(owner=current_user)
        if platform_code:
            products = products.filter(platform__code__iexact=platform_code)
        products = list(products.values("id", "name"))
        product_ids = [p["id"] for p in products]

        if not product_ids:
            return {"data": []}

        # ---- Orders in the window: quantity, profit, returns ----
        order_stats = {
            row["product_id"]: row
            for row in (
                Order.objects.filter(product_id__in=product_ids, created_at__gte=cutoff)
                .values("product_id")
                .annotate(
                    total_quantity=Sum("quantity"),
                    total_orders=Count("id"),
                    returned_orders=Count("id", filter=Q(status__code__in=RETURN_STATUS_CODES)),
                    total_net_profit=Sum("profit__net_profit"),
                    total_gross_revenue=Sum("profit__gross_revenue"),
                )
            )
        }

        # ---- Inventory availability: active variants in stock vs total ----
        inventory_stats = {
            row["product_id"]: row
            for row in (
                ProductVariant.objects.filter(product_id__in=product_ids, is_active=True)
                .values("product_id")
                .annotate(
                    total_variants=Count("id"),
                    in_stock_variants=Count("id", filter=Q(stock__gt=0)),
                )
            )
        }

        # Sales-volume score is a percentile rank of this product's order
        # quantity among the same seller's other products in the window —
        # self-normalizing, no arbitrary absolute "good" volume threshold.
        volumes = sorted(
            (order_stats.get(pid, {}).get("total_quantity") or 0) for pid in product_ids
        )

        def volume_percentile(qty: int) -> float:
            if len(volumes) <= 1:
                return 100.0 if qty > 0 else 0.0
            rank = sum(1 for v in volumes if v <= qty)
            return (rank - 1) / (len(volumes) - 1) * 100

        results = []
        for p in products:
            pid = p["id"]
            o = order_stats.get(pid)
            inv = inventory_stats.get(pid)

            breakdown = ProductHealthScoreController._score_breakdown(o, inv, volume_percentile)
            health_score = round(
                sum(b["score"] * WEIGHTS[key] / 100 for key, b in breakdown.items()), 1
            )

            results.append({
                "product_id": pid,
                "product_name": p["name"],
                "health_score": health_score,
                "grade": _grade_for(health_score),
                "breakdown": breakdown,
            })

        results.sort(key=lambda r: r["health_score"], reverse=True)
        return {"data": results}

    @staticmethod
    def _score_breakdown(order_row, inventory_row, volume_percentile_fn):
        total_orders = (order_row or {}).get("total_orders") or 0
        total_quantity = (order_row or {}).get("total_quantity") or 0
        returned_orders = (order_row or {}).get("returned_orders") or 0
        total_net_profit = (order_row or {}).get("total_net_profit")
        total_gross_revenue = (order_row or {}).get("total_gross_revenue")

        # Profit margin: blended margin (sum of profit / sum of revenue),
        # not an average of per-order percentages — avoids a handful of
        # tiny orders skewing the number. No sales yet -> neutral (50),
        # not 0 — a brand-new product hasn't earned a bad score yet.
        if total_gross_revenue:
            margin_percent = (total_net_profit or 0) / total_gross_revenue * 100
            # profit_score = _clamp(margin_percent, 0, 50) / 50 * 100
            profit_score = float(_clamp(margin_percent, 0, 50)) / 50.0 * 100.0
            profit_raw = f"{margin_percent:.1f}% blended margin"
        else:
            profit_score = 50.0
            profit_raw = "No sales in this period"

        # Sales volume: percentile rank among the seller's own products.
        volume_score = volume_percentile_fn(total_quantity)
        volume_raw = f"{total_quantity} units sold"

        # Return rate: lower is better.
        if total_orders:
            return_rate = returned_orders / total_orders
            return_score = _clamp(1 - return_rate, 0, 1) * 100
            return_raw = f"{return_rate * 100:.1f}% return/RTO rate ({returned_orders}/{total_orders} orders)"
        else:
            return_score = 50.0
            return_raw = "No orders in this period"

        # Inventory availability: fraction of active variants currently
        # in stock — scale-invariant, no arbitrary "good stock level".
        total_variants = (inventory_row or {}).get("total_variants") or 0
        in_stock_variants = (inventory_row or {}).get("in_stock_variants") or 0
        if total_variants:
            inventory_score = in_stock_variants / total_variants * 100
            inventory_raw = f"{in_stock_variants}/{total_variants} variants in stock"
        else:
            inventory_score = 0.0
            inventory_raw = "No active variants"

        return {
            "profit_margin": {"score": round(profit_score, 1), "weight_percent": WEIGHTS["profit_margin"], "detail": profit_raw},
            "sales_volume": {"score": round(volume_score, 1), "weight_percent": WEIGHTS["sales_volume"], "detail": volume_raw},
            "return_rate": {"score": round(return_score, 1), "weight_percent": WEIGHTS["return_rate"], "detail": return_raw},
            "inventory_availability": {"score": round(inventory_score, 1), "weight_percent": WEIGHTS["inventory_availability"], "detail": inventory_raw},
        }
