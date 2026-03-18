from django.db import models
from django.conf import settings
from django.utils import timezone

class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)    # created timestamp
    updated_at = models.DateTimeField(auto_now=True)        # updated timestamp
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    # Soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted",
    )

    class Meta:
        abstract = True  # Important: no table is created for BaseModel

    def soft_delete(self, user=None):
        """
        Mark the object as deleted instead of removing from DB.
        """
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.is_active = False
        self.save()