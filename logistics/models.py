# logistics/models.py

from django.db import models
from api.base import BaseModel

class DeliveryPartner(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "delivery_partners"