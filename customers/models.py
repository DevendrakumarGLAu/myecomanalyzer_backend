from django.db import models

from api.base import BaseModel

# Create your models here.
class Customer(BaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)  # optional
    email = models.EmailField(null=True, blank=True)  # optional

    class Meta:
        db_table = "customers"

    def __str__(self):
        return f"{self.name} - {self.state}"