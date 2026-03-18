# payments/models.py

from django.db import models
from api.base import BaseModel
from orders.models import Order

class OrderSettlement(BaseModel):
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name="settlement")
    transaction_id = models.CharField(max_length=120)
    payment_date = models.DateField()
    total_sale_amount = models.FloatField(default=0)
    total_return_amount = models.FloatField(default=0)
    final_settlement_amount = models.FloatField(default=0)
    fixed_fee = models.FloatField(default=0)
    warehousing_fee = models.FloatField(default=0)
    return_premium = models.FloatField(default=0)
    return_premium_return = models.FloatField(default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "meesho_order_settlements"