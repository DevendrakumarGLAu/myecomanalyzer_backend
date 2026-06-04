from datetime import datetime
import json
import re
import time

from api.analytics_service import AnalyticsService
from api.chat_history_service import ChatHistoryService
from api.local_chat_service import LocalChatService
from api.schemas.ai_schema import AIChatResponse
from django.contrib.auth.models import User


class AIController:

    # --------------------------
    # Keyword Mapping
    # --------------------------
    METRICS_KEYWORDS = {
        "dispatch": ["dispatch", "shipped", "shipment", "sent out", "deliveries"],
        "cancel": ["cancel", "cancelled", "cancellation", "refunded"],
        "orders": ["order", "orders", "purchases"],
        "revenue": ["revenue", "sales", "earnings", "total sales"],
        "profit": ["profit", "margin", "net income", "net profit"],
        "returns": ["return", "returned", "refund", "rto"],
    }

    # --------------------------
    # Intent detection
    # --------------------------
    @staticmethod
    def detect_intent_from_keywords(user_message: str) -> str:
        msg = user_message.lower()
        for metric, keywords in AIController.METRICS_KEYWORDS.items():
            if any(k in msg for k in keywords):
                return metric
        return "general"

    # --------------------------
    # date_range parser (simple version)
    # --------------------------
    @staticmethod
    def extract_date_range(user_message: str):
        msg = user_message.lower()

        if "today" in msg:
            return "today"
        elif "yesterday" in msg:
            return "yesterday"
        elif "last 7" in msg or "week" in msg:
            return "last_7_days"

        return None

    # --------------------------
    #  MAIN CHAT
    # --------------------------
    @staticmethod
    def process_chat(user: User, user_message: str, platform_code: str | None = None) -> AIChatResponse:

        # 1. Intent
        intent = AIController.detect_intent_from_keywords(user_message)

        # 2. Date range (IMPORTANT FIX)
        date_range = AIController.extract_date_range(user_message)

        # 3. Analytics fetch (FIXED - no month/year)
        analytics = AnalyticsService.fetch_analytics(
            current_user=user,
            platform_code=platform_code,
            date_range=date_range
        )

        analytics = json.loads(json.dumps(analytics, default=str))

        summary = analytics["summary"]

        # --------------------------
        # Metric-specific overrides
        # --------------------------
        if intent == "dispatch":
            summary["dispatch_count"] = AnalyticsService.get_dispatch_count(
                current_user=user,
                platform_code=platform_code,
                date_range=date_range
            )

        elif intent == "cancel":
            summary["cancelled_orders"] = AnalyticsService.get_cancelled_orders(
                current_user=user,
                platform_code=platform_code,
                date_range=date_range
            )

        elif intent == "orders":
            summary["total_orders_filtered"] = AnalyticsService.get_total_orders(
                current_user=user,
                platform_code=platform_code,
                date_range=date_range
            )

        # --------------------------
        # AI response
        # --------------------------
        ai_reply = LocalChatService.generate_reply(
            intent=intent,
            analytics_summary=summary,
            user_message=user_message,
        )

        # save history
        ChatHistoryService.save_chat_history(
            user=user,
            platform_code=platform_code,
            intent=intent,
            user_message=user_message,
            assistant_reply=ai_reply,
            analytics_summary=summary,
        )

        return AIChatResponse(
            success=True,
            reply=ai_reply,
            intent=intent,
            analytics_used=summary,
        )

    # --------------------------
    # STREAMING CHAT
    # --------------------------
    @staticmethod
    def process_chat_stream(user: User, user_message: str, platform_code: str | None = None):

        intent = AIController.detect_intent_from_keywords(user_message)
        date_range = AIController.extract_date_range(user_message)

        analytics = AnalyticsService.fetch_analytics(
            current_user=user,
            platform_code=platform_code,
            date_range=date_range
        )

        analytics = json.loads(json.dumps(analytics, default=str))
        summary = analytics["summary"]

        full_reply = LocalChatService.generate_reply(
            intent=intent,
            analytics_summary=summary,
            user_message=user_message,
        )

        words = re.split(r"(\s+)", full_reply)
        for chunk in words:
            if chunk:
                yield f"data: {chunk}\n\n"
                time.sleep(0.01)

        ChatHistoryService.save_chat_history(
            user=user,
            platform_code=platform_code,
            intent=intent,
            user_message=user_message,
            assistant_reply=full_reply,
            analytics_summary=summary,
        )

    # --------------------------
    # history
    # --------------------------
    @staticmethod
    def fetch_history(user: User, limit: int = 20):
        return ChatHistoryService.get_history(user=user, limit=limit)