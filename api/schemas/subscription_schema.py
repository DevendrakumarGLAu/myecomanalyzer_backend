from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# =========================
# GET RESPONSE
# =========================
class SubscriptionResponse(BaseModel):
    username: str
    email: str

    plan: str
    status: str

    trial_start: Optional[datetime]
    trial_end: Optional[datetime]

    subscription_start: Optional[datetime]
    subscription_end: Optional[datetime]

    payment_verified: bool
    is_active: bool

    days_left: int
    is_expired: bool


# =========================
# ADD REQUEST
# =========================
class SubscriptionAddRequest(BaseModel):
    plan: str  # FREE / PRO / ENTERPRISE


# =========================
# ADD RESPONSE
# =========================
class SubscriptionAddResponse(BaseModel):
    success: bool
    message: str
    data: dict