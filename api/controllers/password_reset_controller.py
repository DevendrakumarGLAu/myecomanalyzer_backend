import logging
import secrets
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.utils import timezone

from api.auth_utils import PasswordValidator
from api.services.otp_delivery import get_otp_provider
from users.auth_models import PasswordResetOTP
from users.models import UserProfile

security_logger = logging.getLogger("security")

OTP_EXPIRY_MINUTES = settings.OTP_EXPIRY_MINUTES
OTP_MAX_ATTEMPTS = settings.OTP_MAX_ATTEMPTS
OTP_RESET_TOKEN_EXPIRY_MINUTES = settings.OTP_RESET_TOKEN_EXPIRY_MINUTES
OTP_DEBUG_MODE = settings.OTP_DEBUG_MODE
OTP_RESEND_COOLDOWN_SECONDS = settings.OTP_RESEND_COOLDOWN_SECONDS

VALID_CHANNELS = {"email", "sms"}


class PasswordResetController:

    @staticmethod
    def _find_user(channel, identifier):
        if channel == "email":
            return User.objects.filter(email__iexact=identifier).first()

        profile = UserProfile.objects.filter(mobile_number=identifier).select_related("user").first()
        return profile.user if profile else None

    @staticmethod
    def request_otp(channel, identifier):
        channel = (channel or "").lower()
        if channel not in VALID_CHANNELS:
            raise ValueError("channel must be 'email' or 'sms'")

        identifier = (identifier or "").strip()
        if not identifier:
            raise ValueError("identifier is required")

        channel_label = "email address" if channel == "email" else "mobile number"
        # Same response whether or not the account exists — this codebase
        # already avoids leaking account existence elsewhere (see
        # UserEnumerationProtection in auth_utils.py), so forgot-password
        # follows the same rule instead of returning a 404.
        generic_message = f"If an account matches that {channel_label}, an OTP has been sent."

        user = PasswordResetController._find_user(channel, identifier)
        if not user:
            # No account, no message sent — nothing to throttle. A fixed
            # delay narrows (doesn't fully close — the found branch's SMTP/SNS
            # call is unbounded) the timing gap vs. the found branch, which
            # otherwise lets response latency alone reveal account existence
            # despite the identical response body.
            time.sleep(0.2)
            # No account, no message sent — nothing to throttle.
            return {
                "success": True,
                "message": generic_message,
                "expires_in_minutes": OTP_EXPIRY_MINUTES,
                "otp": None,
            }

        # Resend cooldown, keyed off our own OTP rows rather than the login
        # rate limiter (RateLimiter.check_ip_rate_limit only counts rows in
        # LoginAttempt, which nothing in this flow writes to — it would be a
        # silent no-op here). This both stops OTP-spam abuse and caps SMS cost.
        last = (
            PasswordResetOTP.objects
            .filter(user=user, channel=channel)
            .order_by("-created_at")
            .first()
        )
        if last:
            elapsed = (timezone.now() - last.created_at).total_seconds()
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                wait = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise ValueError(f"Please wait {wait} seconds before requesting another OTP.")

        # Only the newest outstanding OTP for this user+channel is ever valid.
        PasswordResetOTP.objects.filter(
            user=user, channel=channel, is_used=False
        ).update(is_used=True)

        otp = f"{secrets.randbelow(1_000_000):06d}"

        PasswordResetOTP.objects.create(
            user=user,
            channel=channel,
            identifier=identifier,
            otp_hash=make_password(otp),
            expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )

        try:
            get_otp_provider(channel).send(identifier, otp)
        except Exception:
            # The OTP is already stored — a transient delivery failure
            # shouldn't turn into a 500; the user can just request a resend.
            security_logger.exception(f"Failed to deliver OTP via {channel} to {identifier}")

        return {
            "success": True,
            "message": generic_message,
            "expires_in_minutes": OTP_EXPIRY_MINUTES,
            "otp": otp if OTP_DEBUG_MODE else None,
        }

    @staticmethod
    def verify_otp(channel, identifier, otp):
        channel = (channel or "").lower()
        identifier = (identifier or "").strip()

        record = (
            PasswordResetOTP.objects
            .filter(channel=channel, identifier=identifier, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not record:
            raise ValueError("No active OTP request found. Please request a new OTP.")

        if record.is_expired():
            record.is_used = True
            record.save(update_fields=["is_used"])
            raise ValueError("OTP has expired. Please request a new one.")

        if record.attempts >= OTP_MAX_ATTEMPTS:
            record.is_used = True
            record.save(update_fields=["is_used"])
            raise ValueError("Too many incorrect attempts. Please request a new OTP.")

        if not check_password(otp, record.otp_hash):
            record.attempts += 1
            record.save(update_fields=["attempts"])
            remaining = OTP_MAX_ATTEMPTS - record.attempts
            raise ValueError(f"Incorrect OTP. {remaining} attempt(s) remaining.")

        # A second, unrelated secret — the OTP itself is never accepted again
        # after this point, even if the reset that follows never happens.
        reset_token = secrets.token_urlsafe(32)

        record.is_verified = True
        record.reset_token_hash = make_password(reset_token)
        record.reset_token_expires_at = timezone.now() + timedelta(minutes=OTP_RESET_TOKEN_EXPIRY_MINUTES)
        record.save(update_fields=["is_verified", "reset_token_hash", "reset_token_expires_at"])

        return {
            "success": True,
            "message": "OTP verified successfully",
            "reset_token": reset_token,
            "expires_in_minutes": OTP_RESET_TOKEN_EXPIRY_MINUTES,
        }

    @staticmethod
    def reset_password(channel, identifier, reset_token, new_password):
        channel = (channel or "").lower()
        identifier = (identifier or "").strip()

        record = (
            PasswordResetOTP.objects
            .filter(channel=channel, identifier=identifier, is_verified=True, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not record:
            raise ValueError("Please verify the OTP before resetting your password.")

        if record.is_reset_token_expired():
            record.is_used = True
            record.save(update_fields=["is_used"])
            raise ValueError("Reset session expired. Please request a new OTP.")

        if not record.reset_token_hash or not check_password(reset_token, record.reset_token_hash):
            raise ValueError("Invalid reset token.")

        valid, error = PasswordValidator.validate(new_password)
        if not valid:
            raise ValueError(error)

        user = record.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Dead the instant the password is changed — can't be replayed.
        record.is_used = True
        record.save(update_fields=["is_used"])

        return {"success": True, "message": "Password reset successfully"}
