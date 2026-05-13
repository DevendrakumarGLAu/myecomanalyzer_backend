from typing import TypedDict, Optional, Any
from django.contrib.auth.models import User


class EcommerceAgentState(TypedDict):
    """State schema for the ecommerce LangChain graph"""
    user: User
    user_message: str
    intent: str
    analytics: dict
    platform: Optional[str]
    ai_reply: str
