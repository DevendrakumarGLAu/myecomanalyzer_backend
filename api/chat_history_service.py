from ai.models import ChatHistory
from django.contrib.auth.models import User


class ChatHistoryService:
    @staticmethod
    def save_chat_history(
        user: User,
        platform_code: str | None,
        intent: str,
        user_message: str,
        assistant_reply: str,
        analytics_summary: dict,
    ) -> ChatHistory:
        return ChatHistory.objects.create(
            user=user,
            platform=(platform_code or "ALL").upper(),
            intent=intent,
            user_message=user_message,
            assistant_reply=assistant_reply,
            analytics_summary=analytics_summary,
            created_by=user,
            updated_by=user,
        )

    @staticmethod
    def get_history(user: User, limit: int = 20):
        return [
            {
                "id": chat.id,
                "platform": chat.platform,
                "intent": chat.intent,
                "user_message": chat.user_message,
                "assistant_reply": chat.assistant_reply,
                "created_at": chat.created_at.isoformat(),
            }
            for chat in ChatHistory.objects.filter(user=user).order_by("-created_at")[:limit]
        ]
