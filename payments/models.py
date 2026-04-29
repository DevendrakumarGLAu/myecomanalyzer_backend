# payments/models.py

from django.db import models
from api.base import BaseModel
from orders.models import Order

class OrderSettlement(BaseModel):

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="settlements"
    )

    platform = models.ForeignKey(
        "platforms.Platform",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    transaction_id = models.CharField(max_length=120, db_index=True)
    payment_date = models.DateField()

    # -------------------------------
    # 💰 CORE AMOUNTS
    # -------------------------------
    total_sale_amount = models.FloatField(default=0)   # what customer paid
    final_settlement_amount = models.FloatField(default=0)  # what you received

    # -------------------------------
    # 🔻 DEDUCTIONS
    # -------------------------------
    commission_fee = models.FloatField(default=0)
    fixed_fee = models.FloatField(default=0)
    shipping_fee = models.FloatField(default=0)
    return_shipping_charge = models.FloatField(default=0)  # 👈 YOUR COLUMN
    warehousing_fee = models.FloatField(default=0)

    # -------------------------------
    # 🔁 RETURNS / RTO
    # -------------------------------
    total_return_amount = models.FloatField(default=0)
    return_premium = models.FloatField(default=0)
    return_premium_return = models.FloatField(default=0)

    # -------------------------------
    # 🧾 CLAIMS (IMPORTANT)
    # -------------------------------
    claim_amount = models.FloatField(default=0)   # 👈 ADD THIS

    # -------------------------------
    # FLAGS
    # -------------------------------
    is_return = models.BooleanField(default=False)
    is_rto = models.BooleanField(default=False)
    is_claim = models.BooleanField(default=False)

    # -------------------------------
    # TAX
    # -------------------------------
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # -------------------------------
    # EXTRA RAW DATA
    # -------------------------------
    extra_data = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = "order_settlements"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["payment_date"]),
        ]