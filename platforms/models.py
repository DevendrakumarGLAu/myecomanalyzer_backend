from django.db import models
from api.base import BaseModel

class Platform(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "platforms"

    def __str__(self):
        return self.name