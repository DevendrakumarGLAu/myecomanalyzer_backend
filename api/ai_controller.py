from api.analytics_service import AnalyticsService
from api.chat_history_service import ChatHistoryService
from api.intent_classifier import IntentClassifier
from api.openai_service import LangChainService
from api.prompt_builder import PromptBuilder
from api.schemas.ai_schema import AIChatResponse
from django.contrib.auth.models import User
import json

class AIController:
    @staticmethod
    def process_chat(user: User, user_message: str, platform_code: str | None = None) -> AIChatResponse:
        intent = IntentClassifier.classify(user_message)
        analytics = AnalyticsService.fetch_analytics(user, platform_code)
        analytics = json.loads(json.dumps(analytics, default=str))
        prompt_messages = PromptBuilder.build_messages(
            user_message=user_message,
            intent=intent,
            analytics_summary=analytics["summary"],
            platform_code=platform_code,
        )

        ai_reply = LangChainService.create_chat_completion(prompt_messages)

        ChatHistoryService.save_chat_history(
            user=user,
            platform_code=platform_code,
            intent=intent,
            user_message=user_message,
            assistant_reply=ai_reply,
            analytics_summary=analytics["summary"],
        )

        return AIChatResponse(
            success=True,
            reply=ai_reply,
            intent=intent,
            analytics_used=analytics["summary"],
        )

    @staticmethod
    def process_chat_stream(user: User, user_message: str, platform_code: str | None = None):
        intent = IntentClassifier.classify(user_message)
        analytics = AnalyticsService.fetch_analytics(user, platform_code)

        analytics = json.loads(json.dumps(analytics, default=str))
        prompt_messages = PromptBuilder.build_messages(
            user_message=user_message,
            intent=intent,
            analytics_summary=analytics["summary"],
            platform_code=platform_code,
        )

        stream = LangChainService.create_chat_completion(prompt_messages, stream=True)

        full_reply = ""
        for chunk in stream:
            if chunk:
                full_reply += chunk
                yield f"data: {chunk}\n\n"

        # Save to history after streaming completes
        ChatHistoryService.save_chat_history(
            user=user,
            platform_code=platform_code,
            intent=intent,
            user_message=user_message,
            assistant_reply=full_reply,
            analytics_summary=analytics["summary"],
        )

    @staticmethod
    def fetch_history(user: User, limit: int = 20):
        return ChatHistoryService.get_history(user=user, limit=limit)
