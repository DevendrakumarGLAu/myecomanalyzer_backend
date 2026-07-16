"""
Forgot-password endpoints: request an OTP by email or SMS, verify it, then
reset the password with the token issued by verification.
"""
import logging

from fastapi import APIRouter, HTTPException, Request

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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Send an OTP to the given email or mobile number, if an account matches it."""
    try:
        result = PasswordResetController.request_otp(req.channel, req.identifier)
        return ForgotPasswordResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"forgot-password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process forgot-password request")


@router.post("/verify-otp", response_model=VerifyOtpResponse)
def verify_otp(req: VerifyOtpRequest) -> VerifyOtpResponse:
    """Verify an OTP and, on success, issue a short-lived reset_token."""
    try:
        result = PasswordResetController.verify_otp(req.channel, req.identifier, req.otp)
        return VerifyOtpResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"verify-otp error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest) -> ResetPasswordResponse:
    """Reset the password using the reset_token issued by /verify-otp."""
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
