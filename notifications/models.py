from django.db import models
from django.contrib.auth.models import User
from api.base import BaseModel


class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success')
    ])
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    is_read = models.BooleanField(default=False)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)  # For additional metadata

    class Meta:
        db_table = "notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()