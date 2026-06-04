from datetime import datetime, timedelta
from django.utils import timezone


def resolve_date_range(date_range: str | None):
    """
    Returns (start_date, end_date)
    """

    today = timezone.now().date()

    if not date_range:
        return None, None

    date_range = date_range.lower()

    # -------------------------
    # TODAY
    # -------------------------
    if date_range == "today":
        return today, today

    # -------------------------
    # YESTERDAY
    # -------------------------
    if date_range == "yesterday":
        yday = today - timedelta(days=1)
        return yday, yday

    # -------------------------
    # LAST 7 DAYS
    # -------------------------
    if date_range == "last_7_days":
        start = today - timedelta(days=7)
        return start, today

    # -------------------------
    # DEFAULT (no filter)
    # -------------------------
    return None, None