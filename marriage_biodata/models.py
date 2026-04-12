
from api.marriage_base import BaseModel
from django.db import models

from marriage_user_auth.models import MarriageUser

class Biodata(BaseModel):
    user = models.ForeignKey(MarriageUser, on_delete=models.CASCADE, db_column="marriage_user_id")
    template = models.ForeignKey('biodata_templates.Template', on_delete=models.PROTECT, null=True, blank=True)
    data = models.JSONField()
    photo = models.ImageField(upload_to="biodata/photos/", null=True, blank=True)

    class Meta:
        db_table = "biodata"
        unique_together = ('user', 'template')

    def __str__(self):
        return f"{self.user.email}"