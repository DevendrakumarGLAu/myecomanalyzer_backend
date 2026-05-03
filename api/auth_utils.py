"""
Authentication utilities: password validation, rate limiting, brute force protection.
"""
import logging
import re
import time
from datetime import timedelta
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger("auth")
security_logger = logging.getLogger("security")


class PasswordValidator:
    """Enforce strong password policy"""

    MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
    REQUIRE_UPPERCASE = settings.PASSWORD_REQUIRE_UPPERCASE
    REQUIRE_NUMBERS = settings.PASSWORD_REQUIRE_NUMBERS
    REQUIRE_SPECIAL_CHARS = settings.PASSWORD_REQUIRE_SPECIAL_CHARS

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password against security policy.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Check minimum length
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"

        # Check for uppercase
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        # Check for numbers
        if cls.REQUIRE_NUMBERS and not re.search(r"[0-9]", password):
            return False, "Password must contain at least one number"

        # Check for special characters
        if cls.REQUIRE_SPECIAL_CHARS and not re.search(r"[!@#$%^&*_+-=\[\]{};:,.<>?]", password):
            return False, "Password must contain at least one special character (!@#$%^&*)"

        # Prevent common patterns
        if cls._is_common_pattern(password):
            return False, "Password is too common or predictable"

        return True, None

    @staticmethod
    def _is_common_pattern(password: str) -> bool:
        """Check for common password patterns"""
        common_patterns = [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "letmein",
            "welcome",
            "admin",
            "root",
        ]

        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                return True

        return False


class RateLimiter:
    """Rate limiting for authentication endpoints"""

    @staticmethod
    def check_rate_limit(
        identifier: str,
        limit: int = settings.RATE_LIMIT_LOGIN_PER_MINUTE,
        window_seconds: int = 60,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request exceeds rate limit.
        Uses simple in-memory checking (can be upgraded to Redis).
        
        Args:
            identifier: Unique identifier (IP, email, etc.)
            limit: Max requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Tuple (is_allowed, error_message)
        """
        from users.auth_models import LoginAttempt

        now = timezone.now()
        window_start = now - timedelta(seconds=window_seconds)

        # Count attempts in window
        attempt_count = LoginAttempt.objects.filter(
            email=identifier,
            created_at__gte=window_start,
        ).count()

        if attempt_count >= limit:
            remaining_seconds = int(
                (window_start + timedelta(seconds=window_seconds) - now).total_seconds()
            )
            message = f"Too many attempts. Try again in {remaining_seconds} seconds"
            security_logger.warning(f"Rate limit exceeded for {identifier}")
            return False, message

        return True, None

    @staticmethod
    def check_ip_rate_limit(
        ip_address: str,
        limit: int = settings.RATE_LIMIT_LOGIN_PER_MINUTE,
        window_seconds: int = 60,
    ) -> Tuple[bool, Optional[str]]:
        """Check rate limit per IP address"""
        from users.auth_models import LoginAttempt

        now = timezone.now()
        window_start = now - timedelta(seconds=window_seconds)

        attempt_count = LoginAttempt.objects.filter(
            ip_address=ip_address,
            created_at__gte=window_start,
        ).count()

        if attempt_count >= limit:
            remaining_seconds = int(
                (window_start + timedelta(seconds=window_seconds) - now).total_seconds()
            )
            message = f"Too many requests from this IP. Try again in {remaining_seconds} seconds"
            security_logger.warning(f"IP rate limit exceeded: {ip_address}")
            return False, message

        return True, None


class BruteForceProtection:
    """Brute force attack detection and prevention"""

    FAILED_ATTEMPTS_LIMIT = settings.FAILED_LOGIN_ATTEMPTS_LIMIT
    FAILED_ATTEMPTS_WINDOW_MINUTES = settings.FAILED_LOGIN_WINDOW_MINUTES
    ACCOUNT_LOCK_DURATION_MINUTES = settings.ACCOUNT_LOCK_DURATION_MINUTES

    @staticmethod
    def log_failed_attempt(
        email: str,
        ip_address: str,
        user_agent: str = None,
        reason: str = "invalid_creds",
    ) -> None:
        """Log a failed login attempt"""
        from users.auth_models import LoginAttempt

        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            reason=reason,
        )

        logger.warning(f"Failed login attempt: {email} from {ip_address}")

    @staticmethod
    def log_successful_attempt(
        user: User,
        ip_address: str,
        user_agent: str = None,
    ) -> None:
        """Log a successful login"""
        from users.auth_models import LoginAttempt

        LoginAttempt.objects.create(
            user=user,
            email=user.email if user.email else "unknown",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            reason="success",
        )

        logger.info(f"Successful login: {user.username} from {ip_address}")

    @staticmethod
    def check_account_locked(user: User) -> Tuple[bool, Optional[str]]:
        """Check if account is temporarily locked"""
        from users.auth_models import AccountLock

        try:
            lock = AccountLock.objects.get(user=user)
            if lock.is_active():
                remaining_minutes = int(
                    (lock.locked_until - timezone.now()).total_seconds() / 60
                )
                message = f"Account locked. Try again in {remaining_minutes} minutes"
                security_logger.warning(f"Account locked for user: {user.username}")
                return True, message
            else:
                lock.unlock()
        except AccountLock.DoesNotExist:
            pass

        return False, None

    @staticmethod
    def check_failed_attempts(email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if email/account should be locked based on failed attempts.
        
        Returns:
            Tuple (should_lock_account, error_message)
        """
        from users.auth_models import LoginAttempt

        now = timezone.now()
        window_start = now - timedelta(minutes=BruteForceProtection.FAILED_ATTEMPTS_WINDOW_MINUTES)

        failed_attempts = LoginAttempt.objects.filter(
            email=email,
            success=False,
            created_at__gte=window_start,
        ).count()

        if failed_attempts >= BruteForceProtection.FAILED_ATTEMPTS_LIMIT:
            message = f"Too many failed attempts. Account locked temporarily."
            return True, message

        return False, None

    @staticmethod
    def lock_account(user: User, reason: str = "brute_force") -> None:
        """Temporarily lock account after multiple failed attempts"""
        from users.auth_models import AccountLock

        locked_until = timezone.now() + timedelta(
            minutes=BruteForceProtection.ACCOUNT_LOCK_DURATION_MINUTES
        )

        AccountLock.objects.update_or_create(
            user=user,
            defaults={
                "locked_until": locked_until,
                "reason": reason,
            },
        )

        security_logger.critical(
            f"Account locked for {user.username}: {reason}"
        )

    @staticmethod
    def unlock_account(user: User) -> None:
        """Manually unlock account (admin action)"""
        from users.auth_models import AccountLock

        try:
            lock = AccountLock.objects.get(user=user)
            lock.unlock()
            logger.info(f"Account unlocked for {user.username}")
        except AccountLock.DoesNotExist:
            pass


class UserEnumerationProtection:
    """Prevent user enumeration attacks"""

    GENERIC_ERROR = "Invalid credentials"

    @staticmethod
    def get_generic_error() -> str:
        """Always return generic error to prevent enumeration"""
        return UserEnumerationProtection.GENERIC_ERROR
