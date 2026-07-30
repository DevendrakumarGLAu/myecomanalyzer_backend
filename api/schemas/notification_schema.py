from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class NotificationData(BaseModel):
    id: int
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    created_at: str
    product_id: Optional[int]
    order_id: Optional[int]
    action_url: Optional[str] = None
    data: Optional[Dict[str, Any]]


class NotificationListResponse(BaseModel):
    unread_count: int = 0
    notifications: List[NotificationData]


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    success: bool
    message: str