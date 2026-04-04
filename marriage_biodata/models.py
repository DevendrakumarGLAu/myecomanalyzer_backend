from django.db import models

from api.base import BaseModel
from marriage_user_auth.models import MarriageUser
    
class Template(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "marriage", "resume"
    display_name = models.CharField(max_length=150)       # e.g., "Marriage Biodata"
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='templates/thumbnails/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "templates"

    def __str__(self):
        return self.display_name
    
    
class Biodata(models.Model):
    user = models.ForeignKey(MarriageUser, on_delete=models.CASCADE, db_column="marriage_user_id")
    template = models.ForeignKey(Template, on_delete=models.PROTECT, null=True, blank=True)  # Protect to avoid deleting template
    data = models.JSONField()
    photo = models.ImageField(upload_to="biodata/photos/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "biodata"
        unique_together = ('user', 'template')  # optional: prevent duplicate for same user/template

    def __str__(self):
        return f"{self.user.email} - {self.template.name}"