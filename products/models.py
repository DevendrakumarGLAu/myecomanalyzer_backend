from django.db import models
from django.contrib.auth.models import User
# F:\project\ecomm-profit\backend\api\base.py

from api.base import BaseModel
from categories.models import Category
from platforms.models import Platform

class Product(BaseModel):
    catalog_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform,on_delete=models.CASCADE, related_name="products" )
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "products"

    def __str__(self):
        return self.name
    
    
class ProductVariant(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    sku = models.CharField(max_length=50)

    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    cost_price = models.FloatField()
    selling_price = models.FloatField()
    stock = models.IntegerField(default=0)

    shipping_cost = models.FloatField(default=0)
    rto_cost = models.FloatField(default=0)

    class Meta:
        db_table = "product_variants"
        unique_together = ('product', 'sku', 'size', 'color')
        indexes = [
        models.Index(fields=["sku", "size", "color"]),
    ]


class CostPriceUpdateHistory(BaseModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cost_price_updates")
    old_cost_price = models.FloatField()
    new_cost_price = models.FloatField()
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "cost_price_update_history"
        ordering = ['-created_at']