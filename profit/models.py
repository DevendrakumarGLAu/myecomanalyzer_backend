# profit/models.py
from django.db import models
from api.base import BaseModel


class OrderProfit(BaseModel):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="profit")
    settlement = models.ForeignKey("payments.OrderSettlement", on_delete=models.SET_NULL, null=True, blank=True, related_name="profits" )
    # ---------------------------------
    # PRODUCT INFO
    # ---------------------------------
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=120)
    # ---------------------------------
    # SALES
    # ---------------------------------

    quantity = models.IntegerField(default=1)

    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ---------------------------------
    # PRODUCT COSTS
    # ---------------------------------
    product_cost = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    shipping_cost = models.DecimalField( max_digits=12, decimal_places=2, default=0)
    rto_cost = models.DecimalField( max_digits=12, decimal_places=2, default=0 )
    packaging_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0 )
    # ---------------------------------
    # MARKETPLACE FEES
    # ---------------------------------
    commission_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    fixed_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    warehousing_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    return_shipping_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ---------------------------------
    # RETURNS / CLAIMS
    # ---------------------------------

    total_return_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    claim_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ---------------------------------
    # FINAL METRICS
    # ---------------------------------

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    profit_margin_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    roi_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    is_loss = models.BooleanField(default=False)

    class Meta:
        db_table = "order_profit"

        indexes = [
            models.Index(fields=["net_profit"]),
            models.Index(fields=["is_loss"]),
        ]
