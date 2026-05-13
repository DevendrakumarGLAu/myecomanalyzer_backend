from django.conf import settings
from django.db import models
from api.base import BaseModel


class ChatHistory(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_histories",
    )
    platform = models.CharField(max_length=50, blank=True, null=True)
    intent = models.CharField(max_length=80)
    user_message = models.TextField()
    assistant_reply = models.TextField()
    analytics_summary = models.JSONField(default=dict, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = "ai_chat_history"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["created_at"]),
        ]
