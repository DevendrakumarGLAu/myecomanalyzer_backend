from datetime import datetime, timedelta

from django.db.models import Sum, Count, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone

from payments.models import OrderSettlement
from profit.models import OrderProfit

RANGE_PRESETS = {
    "7d": 6,
    "1m": 29,
    "1y": 364,
}

SKU_PROFIT_SORT_FIELDS = {
    "profit_desc": "-total_profit",
    "profit_asc": "total_profit",
    "revenue_desc": "-total_revenue",
}


class PaymentController:

    @staticmethod
    def _resolve_date_range(range_type, date_from, date_to):
        """Turn a range preset (or explicit custom dates) into (start_date, end_date).

        Returns (None, None) when range_type is falsy, so callers for whom a date
        range is optional (e.g. all-time SKU profit) can skip filtering entirely.
        """
        if not range_type:
            return None, None

        range_type = range_type.lower()
        today = timezone.now().date()

        if range_type == "custom":
            if not date_from or not date_to:
                raise ValueError("date_from and date_to are required for range=custom")
            try:
                start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("date_from/date_to must be in YYYY-MM-DD format")
        elif range_type in RANGE_PRESETS:
            end_date = today
            start_date = today - timedelta(days=RANGE_PRESETS[range_type])
        else:
            raise ValueError(f"Invalid range '{range_type}'. Use one of: 7d, 1m, 1y, custom")

        if start_date > end_date:
            raise ValueError("date_from must not be after date_to")

        return start_date, end_date

    @staticmethod
    def get_payment_trend(
        current_user,
        range_type="7d",
        date_from=None,
        date_to=None,
        platform_code=None,
    ):
        if current_user is None:
            raise ValueError("current_user must be provided")

        range_type = (range_type or "7d").lower()
        start_date, end_date = PaymentController._resolve_date_range(range_type, date_from, date_to)

        # A year of daily points is too dense for a line chart, so that range is
        # bucketed by month; everything else (7 days / 1 month / a short custom
        # range) is bucketed by day.
        group_by_month = range_type == "1y"

        settlements = OrderSettlement.objects.filter(
            created_by=current_user,
            payment_date__gte=start_date,
            payment_date__lte=end_date,
        )

        if platform_code:
            settlements = settlements.filter(platform__code__iexact=platform_code)

        if group_by_month:
            trend = PaymentController._monthly_trend(settlements, start_date, end_date)
        else:
            trend = PaymentController._daily_trend(settlements, start_date, end_date)

        total_amount = sum(point["amount"] for point in trend)
        total_payments = sum(point["count"] for point in trend)

        return {
            "success": True,
            "message": "Payment trend fetched successfully",
            "data": {
                "range": range_type,
                "group_by": "month" if group_by_month else "day",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_amount": round(total_amount, 2),
                "total_payments": total_payments,
                "trend": trend,
            },
        }

    @staticmethod
    def get_sku_wise_profit(
        current_user,
        range_type=None,
        date_from=None,
        date_to=None,
        platform_code=None,
        sort="profit_desc",
        limit=20,
    ):
        if current_user is None:
            raise ValueError("current_user must be provided")

        sort_field = SKU_PROFIT_SORT_FIELDS.get(sort)
        if not sort_field:
            raise ValueError(f"Invalid sort '{sort}'. Use one of: {', '.join(SKU_PROFIT_SORT_FIELDS)}")

        limit = max(1, min(limit or 20, 100))

        # range is optional here (unlike /trend) — with none given this is an
        # all-time leaderboard, which is the common case for "which SKUs make
        # the most/least money".
        start_date, end_date = PaymentController._resolve_date_range(range_type, date_from, date_to)

        # Sourced from the precomputed OrderProfit snapshot (written once per
        # order at settlement-upload time) instead of recomputing the profit
        # formula live — this is a single indexed GROUP BY, not N+1 calculation.
        profits = OrderProfit.objects.filter(created_by=current_user)

        if start_date and end_date:
            profits = profits.filter(
                settlement__payment_date__gte=start_date,
                settlement__payment_date__lte=end_date,
            )

        if platform_code:
            profits = profits.filter(settlement__platform__code__iexact=platform_code)

        rows = (
            profits
            .values("sku")
            .annotate(
                product_name=Max("product_name"),
                total_quantity=Sum("quantity"),
                total_revenue=Sum("gross_revenue"),
                total_cost=Sum("total_cost"),
                total_deductions=Sum("total_deductions"),
                total_profit=Sum("net_profit"),
                order_count=Count("id"),
            )
            .order_by(sort_field)[:limit]
        )

        skus = []
        for row in rows:
            revenue = float(row["total_revenue"] or 0)
            profit = float(row["total_profit"] or 0)
            margin = round((profit / revenue) * 100, 2) if revenue else 0.0

            skus.append({
                "sku": row["sku"],
                "product_name": row["product_name"] or "",
                "quantity": row["total_quantity"] or 0,
                "revenue": round(revenue, 2),
                "cost": round(float(row["total_cost"] or 0), 2),
                "deductions": round(float(row["total_deductions"] or 0), 2),
                "profit": round(profit, 2),
                "margin_percent": margin,
                "orders": row["order_count"],
            })

        return {
            "success": True,
            "message": "SKU-wise profit fetched successfully",
            "data": {
                "range": range_type,
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
                "sort": sort,
                "limit": limit,
                "skus": skus,
            },
        }

    @staticmethod
    def _daily_trend(settlements, start_date, end_date):
        rows = (
            settlements
            .values("payment_date")
            .annotate(amount=Sum("final_settlement_amount"), count=Count("id"))
        )
        by_day = {row["payment_date"]: row for row in rows}

        trend = []
        cursor = start_date
        while cursor <= end_date:
            row = by_day.get(cursor)
            trend.append({
                "date": cursor.strftime("%Y-%m-%d"),
                "amount": round(row["amount"], 2) if row else 0.0,
                "count": row["count"] if row else 0,
            })
            cursor += timedelta(days=1)

        return trend

    @staticmethod
    def _monthly_trend(settlements, start_date, end_date):
        rows = (
            settlements
            .annotate(period=TruncMonth("payment_date"))
            .values("period")
            .annotate(amount=Sum("final_settlement_amount"), count=Count("id"))
        )

        by_month = {}
        for row in rows:
            period = row["period"]
            key = period.date() if hasattr(period, "date") else period
            by_month[key.replace(day=1)] = row

        trend = []
        cursor = start_date.replace(day=1)
        last = end_date.replace(day=1)
        while cursor <= last:
            row = by_month.get(cursor)
            trend.append({
                "date": cursor.strftime("%Y-%m"),
                "amount": round(row["amount"], 2) if row else 0.0,
                "count": row["count"] if row else 0,
            })
            cursor = (cursor.replace(year=cursor.year + 1, month=1)
                      if cursor.month == 12
                      else cursor.replace(month=cursor.month + 1))

        return trend
