
# Create your models here.
from django.db import models
# F:\project\ecomm-profit\backend\api\base.py

from api.base import BaseModel

class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.name