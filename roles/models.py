from django.db import models
from api.base import BaseModel


class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name