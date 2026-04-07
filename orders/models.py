from django.db import models

from api.base import BaseModel
from customers.models import Customer
from marketplace.models import MarketplaceOrder
from orders_status.models import OrderStatus
from platforms.models import Platform
from products.models import Product, ProductVariant
# F:\project\ecomm-profit\backend\customers\models.py
# from products.models import Cu

# Create your models here.
class Order(BaseModel):

    marketplace_order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.CASCADE,
        related_name="sub_orders"
    )

    marketplace_sub_order_id = models.CharField(max_length=120)

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant,on_delete=models.PROTECT,null=False,blank=False,related_name="orders")
    quantity = models.IntegerField(default=1)
    selling_price = models.FloatField()

    status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT)
    status_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orders"
        unique_together = (
            ("marketplace_order", "marketplace_sub_order_id"),
        )
        indexes = [
            models.Index(fields=["marketplace_sub_order_id"]),
            models.Index(fields=["status"]),
        ]