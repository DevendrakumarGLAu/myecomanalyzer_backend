from django.db import models

# Create your models here.
from django.db import models
from api.base import BaseModel
from platforms.models import Platform
from customers.models import Customer


class MarketplaceOrder(BaseModel):
    platform = models.ForeignKey(Platform,on_delete=models.PROTECT, related_name="marketplace_orders")
    marketplace_order_id = models.CharField(max_length=120)
    customer = models.ForeignKey( Customer,on_delete=models.PROTECT,related_name="marketplace_orders")
    order_date = models.DateField()

    class Meta:
        db_table = "marketplace_orders"
        unique_together = ("platform", "marketplace_order_id")
        indexes = [
            models.Index(fields=["platform", "marketplace_order_id"]),
            models.Index(fields=["order_date"]),
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.marketplace_order_id}"