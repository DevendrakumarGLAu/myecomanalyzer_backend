from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    created_at: Optional[datetime] = None
    
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    payment_verified: Optional[bool] = None

    class Config:
        from_attributes = True

class UserProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

class UserProfileUpdateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[UserProfileResponse] = None
