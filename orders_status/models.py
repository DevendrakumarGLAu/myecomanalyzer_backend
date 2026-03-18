from django.db import models

from api.base import BaseModel

# Create your models here.
class OrderStatus(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)

    class Meta:
        db_table = "order_status"

    def __str__(self):
        return self.label