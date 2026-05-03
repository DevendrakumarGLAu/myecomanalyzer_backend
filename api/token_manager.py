"""
JWT Token utilities for secure token generation, validation, and rotation.
Implements access + refresh token flow with proper claims and expiration.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os

from jose import JWTError, jwt
from django.contrib.auth.models import User
from django.utils import timezone as django_timezone
from django.conf import settings

logger = logging.getLogger("auth")
security_logger = logging.getLogger("security")


class TokenManager:
    """Manage JWT token creation, validation, and rotation"""

    SECRET_KEY = settings.JWT_SECRET_KEY
    ALGORITHM = settings.JWT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash token using SHA256 for safe storage in database.
        Prevents token compromise if DB is breached.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_access_token(
        cls,
        user_id: int,
        username: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create short-lived access token with standard JWT claims.
        
        Args:
            user_id: Django user ID
            username: Django username
            additional_claims: Extra claims to include (e.g., permissions)
        
        Returns:
            Signed JWT access token
        """
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),  # subject (user ID)
            "username": username,
            "type": "access",
            "iat": int(now.timestamp()),        # ✅ FIX HERE
            "exp": int(expiry.timestamp()),
            "iss": "ecomm-profit",  # issuer
            "aud": "ecomm-profit-api",  # audience
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        logger.debug(f"Access token created for user {username}")
        return token

    @classmethod
    def create_refresh_token(
        cls,
        user_id: int,
        username: str,
    ) -> str:
        """
        Create long-lived refresh token with minimal claims.
        Used only for token rotation, not API access.
        
        Args:
            user_id: Django user ID
            username: Django username
        
        Returns:
            Signed JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "username": username,
            "type": "refresh",
            "iat": int(now.timestamp()),        # ✅ FIX HERE
            "exp": int(expiry.timestamp()),     # ✅ FIX HERE
            "iss": "ecomm-profit",
            "aud": "ecomm-profit-api",
        }

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        logger.debug(f"Refresh token created for user {username}")
        return token

    @classmethod
    def verify_token(
        cls,
        token: str,
        token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and extract payload.
        Performs complete validation including signature, expiry, and type.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
        
        Returns:
            Decoded payload if valid, None otherwise
        """
        
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM],
                options={"verify_exp": True},
                 audience="ecomm-profit-api",   # ✅ ADD THIS
                issuer="ecomm-profit"  
            )

            # Verify token type
            if payload.get("type") != token_type:
                security_logger.warning(
                    f"Token type mismatch: expected {token_type}, got {payload.get('type')}"
                )
                return None

            return payload

        except JWTError as e:
            security_logger.warning(f"JWT verification failed: {str(e)}")
            return None
        except Exception as e:
            security_logger.error(f"Unexpected error verifying token: {str(e)}")
            return None

    @classmethod
    def decode_token_unverified(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token WITHOUT verification (use with caution).
        Used for extracting info from potentially compromised tokens.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload if valid JWT format, None otherwise
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception:
            return None

    @classmethod
    def extract_user_id(cls, token: str) -> Optional[int]:
        """Extract user ID from token payload"""
        payload = cls.decode_token_unverified(token)
        if payload and "sub" in payload:
            try:
                return int(payload["sub"])
            except (ValueError, TypeError):
                pass
        return None

    @classmethod
    def is_token_expired(cls, payload: Dict[str, Any]) -> bool:
        """Check if token is expired"""
        if "exp" not in payload:
            return True

        exp_timestamp = payload["exp"]
        current_timestamp = datetime.now(timezone.utc).timestamp()
        return current_timestamp > exp_timestamp

    @classmethod
    def get_token_expiry_seconds(cls, payload: Dict[str, Any]) -> int:
        """Get remaining seconds until token expiry"""
        if "exp" not in payload:
            return 0

        exp_timestamp = payload["exp"]
        current_timestamp = datetime.now(timezone.utc).timestamp()
        remaining = int(exp_timestamp - current_timestamp)
        return max(0, remaining)


class TokenRotationManager:
    """Manage refresh token rotation and revocation"""

    @staticmethod
    def rotate_refresh_token(
        old_token: str,
        user: User,
        ip_address: str = None,
        user_agent: str = None,
        device_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Rotate refresh token by revoking old and issuing new.
        Returns both access and refresh tokens.
        
        Args:
            old_token: Previous refresh token
            user: Django User object
            ip_address: Client IP (for tracking)
            user_agent: Client user agent
            device_id: Device identifier
        
        Returns:
            Dict with new access and refresh tokens, or None if rotation failed
        """
        from users.auth_models import RefreshToken, SessionLog

        logger.info(f"Rotating refresh token for user {user.username}")

        # Verify old token
        payload = TokenManager.verify_token(old_token, token_type="refresh")
        if not payload:
            security_logger.warning(
                f"Refresh token rotation failed for {user.username}: invalid token"
            )
            return None

        try:
            # Create new tokens
            access_token = TokenManager.create_access_token(user.id, user.username)
            refresh_token = TokenManager.create_refresh_token(user.id, user.username)

            # Store new refresh token
            token_hash = TokenManager.hash_token(refresh_token)
            expires_at = django_timezone.now() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )

            RefreshToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id,
                is_active=True,
            )

            # Log rotation
            SessionLog.objects.create(
                user=user,
                event_type="token_refresh",
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                device_id=device_id,
                status="success",
                details={"device_id": device_id},
            )

            logger.info(f"Refresh token rotated successfully for {user.username}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        except Exception as e:
            security_logger.error(f"Error rotating refresh token: {str(e)}")
            return None

    @staticmethod
    def revoke_refresh_token(token: str, reason: str = "logout") -> bool:
        """
        Revoke (invalidate) a refresh token.
        Used on logout and compromise scenarios.
        
        Args:
            token: Refresh token to revoke
            reason: Reason for revocation
        
        Returns:
            True if revocation successful, False otherwise
        """
        from users.auth_models import RefreshToken, TokenBlacklist

        try:
            token_hash = TokenManager.hash_token(token)

            # Soft delete refresh token
            refresh_token = RefreshToken.objects.filter(token_hash=token_hash).first()
            if refresh_token:
                refresh_token.revoke()
                logger.info(f"Refresh token revoked for {refresh_token.user.username}")

            # Add to blacklist for extra security
            payload = TokenManager.decode_token_unverified(token)
            if payload and "sub" in payload:
                user_id = int(payload["sub"])
                user = User.objects.get(id=user_id)
                expires_at = django_timezone.now() + timedelta(
                    days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
                )

                TokenBlacklist.objects.create(
                    token_hash=token_hash,
                    user=user,
                    reason=reason,
                    expires_at=expires_at,
                )

            return True

        except Exception as e:
            security_logger.error(f"Error revoking refresh token: {str(e)}")
            return False

    @staticmethod
    def detect_token_reuse(token: str) -> bool:
        """
        Detect if a refresh token is being reused (possible compromise).
        
        Args:
            token: Refresh token to check
        
        Returns:
            True if token reuse detected, False otherwise
        """
        from users.auth_models import TokenBlacklist

        token_hash = TokenManager.hash_token(token)

        # Check if token is in blacklist
        is_blacklisted = TokenBlacklist.objects.filter(token_hash=token_hash).exists()

        if is_blacklisted:
            security_logger.critical(
                f"POSSIBLE TOKEN COMPROMISE DETECTED: Token reuse attempt"
            )
            return True

        return False

    @staticmethod
    def invalidate_user_tokens(user: User, reason: str = "admin_revoke") -> int:
        """
        Invalidate all active refresh tokens for a user.
        Used when password changes or account compromise detected.
        
        Args:
            user: Django User to invalidate tokens for
            reason: Reason for invalidation
        
        Returns:
            Number of tokens invalidated
        """
        from users.auth_models import RefreshToken, TokenBlacklist

        active_tokens = RefreshToken.objects.filter(user=user, is_active=True)
        count = 0

        for token_obj in active_tokens:
            token_obj.revoke()
            count += 1

            # Add to blacklist
            TokenBlacklist.objects.create(
                token_hash=token_obj.token_hash,
                user=user,
                reason=reason,
                expires_at=token_obj.expires_at,
            )

        logger.info(f"Invalidated {count} tokens for user {user.username}")
        return count


class TokenCleanupManager:
    """Cleanup expired and revoked tokens from database"""

    @staticmethod
    def cleanup_expired_tokens(batch_size: int = 1000) -> Dict[str, int]:
        """
        Remove expired tokens from database.
        Should be run periodically (celery task recommended).
        
        Args:
            batch_size: Number of tokens to delete per batch
        
        Returns:
            Statistics of cleanup operation
        """
        from users.auth_models import RefreshToken, TokenBlacklist
        import time

        stats = {"refresh_tokens_deleted": 0, "blacklisted_tokens_deleted": 0}
        now = django_timezone.now()

        try:
            # Clean expired refresh tokens
            expired_refresh = RefreshToken.objects.filter(expires_at__lt=now)
            for batch_start in range(0, expired_refresh.count(), batch_size):
                expired_refresh[batch_start : batch_start + batch_size].delete()
                stats["refresh_tokens_deleted"] += batch_size
                time.sleep(0.1)  # Prevent DB overload

            # Clean expired blacklisted tokens
            expired_blacklist = TokenBlacklist.objects.filter(expires_at__lt=now)
            for batch_start in range(0, expired_blacklist.count(), batch_size):
                expired_blacklist[batch_start : batch_start + batch_size].delete()
                stats["blacklisted_tokens_deleted"] += batch_size
                time.sleep(0.1)

            logger.info(f"Token cleanup completed: {stats}")
            return stats

        except Exception as e:
            security_logger.error(f"Error during token cleanup: {str(e)}")
            return stats
