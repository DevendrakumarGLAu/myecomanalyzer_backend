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
    data: Optional[Dict[str, Any]]


class NotificationListResponse(BaseModel):
    notifications: List[NotificationData]


class MarkReadResponse(BaseModel):
    success: bool
    message: str