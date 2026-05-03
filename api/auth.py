"""
JWT Authentication module for FastAPI with secure token management.
Implements access token validation and FastAPI dependencies.
"""
import logging
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Header
from django.contrib.auth.models import User
from django.db import connection

from api.token_manager import TokenManager
from users.auth_models import TokenBlacklist
from asgiref.sync import sync_to_async
logger = logging.getLogger("auth")
security_logger = logging.getLogger("security")

@sync_to_async
def get_user_by_id(user_id: int):
    return User.objects.get(id=user_id)


@sync_to_async
def is_blacklisted(token_hash: str):
    return TokenBlacklist.objects.filter(token_hash=token_hash).exists()
# FastAPI Dependencies for protected routes
async def get_current_user(
    authorization: str = Header(..., description="Bearer <access_token>")
) -> User:
    """
    Extract and validate JWT token from Authorization header.
    Used as FastAPI dependency for protected routes.
    
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )

        token = authorization.split(" ", 1)[1]

        # Verify token signature and claims
        payload = TokenManager.verify_token(token, token_type="access")
        if not payload:
            security_logger.warning("Access token verification failed")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Check if token is blacklisted
        token_hash = TokenManager.hash_token(token)
        # if TokenBlacklist.objects.filter(token_hash=token_hash).exists():
        #     security_logger.warning("Blacklisted token attempted")
        #     raise HTTPException(status_code=401, detail="Token has been revoked")
        blacklisted = await is_blacklisted(token_hash)
        if blacklisted:
            security_logger.warning("Blacklisted token attempted")
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Get user from payload
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token claims")

        try:
            user = await get_user_by_id(int(user_id))
        except User.DoesNotExist:
            security_logger.warning(f"User not found for ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token claims")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        return user

    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_optional(
    authorization: Optional[str] = Header(None, description="Bearer <access_token>")
) -> Optional[User]:
    """
    Optional authentication - returns user if token provided, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if not authorization:
        return None

    try:
        user = await get_current_user(authorization)
        return user
    except HTTPException:
        return None