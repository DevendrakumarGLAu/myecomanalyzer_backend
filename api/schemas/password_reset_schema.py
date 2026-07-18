from typing import Literal, Optional

from pydantic import BaseModel, Field


class ForgotPasswordRequest(BaseModel):
    channel: Literal["email", "sms"]
    identifier: str = Field(
        ...,
        min_length=3,
        description="Email address (channel=email) or mobile number in E.164 format, e.g. +919876543210 (channel=sms)",
    )


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    expires_in_minutes: int
    otp: Optional[str] = None  # only populated when OTP_DEBUG_MODE=true


class VerifyOtpRequest(BaseModel):
    channel: Literal["email", "sms"]
    identifier: str
    otp: str = Field(..., min_length=6, max_length=6)


class VerifyOtpResponse(BaseModel):
    success: bool
    message: str
    reset_token: str
    expires_in_minutes: int


class ResetPasswordRequest(BaseModel):
    channel: Literal["email", "sms"]
    identifier: str
    reset_token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
