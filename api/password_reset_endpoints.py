"""
Forgot-password endpoints: request an OTP by email or SMS, verify it, then
reset the password with the token issued by verification.
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from api.auth_utils import check_endpoint_rate_limit
from api.controllers.password_reset_controller import PasswordResetController
from api.schemas.password_reset_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

security_logger = logging.getLogger("security")

router = APIRouter(prefix="/auth", tags=["Password Reset"])


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, request: Request) -> ForgotPasswordResponse:
    """Send an OTP to the given email or mobile number, if an account matches it."""
    ip_address = _client_ip(request)
    # Stricter than the others — each allowed request can send a real SMS/email.
    allowed, error = check_endpoint_rate_limit("forgot_password", ip_address, limit=5, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail=error)
    try:
        result = PasswordResetController.request_otp(req.channel, req.identifier)
        return ForgotPasswordResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"forgot-password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process forgot-password request")


@router.post("/verify-otp", response_model=VerifyOtpResponse)
def verify_otp(req: VerifyOtpRequest, request: Request) -> VerifyOtpResponse:
    """Verify an OTP and, on success, issue a short-lived reset_token."""
    ip_address = _client_ip(request)
    allowed, error = check_endpoint_rate_limit("verify_otp", ip_address, limit=15, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail=error)
    try:
        result = PasswordResetController.verify_otp(req.channel, req.identifier, req.otp)
        return VerifyOtpResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"verify-otp error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest, request: Request) -> ResetPasswordResponse:
    """Reset the password using the reset_token issued by /verify-otp."""
    ip_address = _client_ip(request)
    allowed, error = check_endpoint_rate_limit("reset_password", ip_address, limit=10, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail=error)
    try:
        result = PasswordResetController.reset_password(
            req.channel, req.identifier, req.reset_token, req.new_password
        )
        return ResetPasswordResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"reset-password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset password")
