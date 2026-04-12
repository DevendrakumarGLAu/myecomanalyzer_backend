from django.db import models
from api.marriage_base import BaseModel


class Template(BaseModel):
    name = models.CharField(max_length=100, unique=True)  # internal key (e.g. "marriage")
    display_name = models.CharField(max_length=150)       # UI name (e.g. "Marriage Biodata")
    description = models.TextField(blank=True, null=True)

    thumbnail = models.ImageField(
        upload_to='templates/thumbnails/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "templates"

    def __str__(self):
        return self.display_name