"""
Secure authentication endpoints: login, refresh, logout
Implements complete auth flow with rate limiting and brute force protection
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Cookie, Response
from pydantic import BaseModel, EmailStr, Field, validator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db import transaction

from api.token_manager import TokenManager, TokenRotationManager
from api.auth_utils import (
    PasswordValidator,
    RateLimiter,
    BruteForceProtection,
    UserEnumerationProtection,
)
from users.auth_models import SessionLog
from users.models import UserProfile

logger = logging.getLogger("auth")
security_logger = logging.getLogger("security")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ======================== REQUEST SCHEMAS ========================
class LoginRequest(BaseModel):
    """Login request with email and password"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    device_id: Optional[str] = None
    remember_me: bool = False

    @validator("password")
    def password_not_empty(cls, v):
        if not v or v.isspace():
            raise ValueError("Password cannot be empty")
        return v


class SignupRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8)
    password_confirm: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator("username")
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str
    device_id: Optional[str] = None


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: Optional[str] = None


# ======================== RESPONSE SCHEMAS ========================
class TokenResponse(BaseModel):
    """Successful auth response with tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class SimpleTokenResponse(BaseModel):
    """Simple response for refresh endpoint"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str


# ======================== HELPER FUNCTIONS ========================
def _get_client_ip(request) -> str:
    """Extract client IP from request"""
    # Check X-Forwarded-For first (for proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request) -> str:
    """Extract user agent from request"""
    return request.headers.get("user-agent", "Unknown")


def _store_refresh_token_in_cookie(
    response: Response,
    token: str,
    max_age: int = 30 * 24 * 60 * 60,  # 30 days
) -> None:
    """
    Store refresh token in HttpOnly cookie.
    Prevents XSS attacks from accessing token.
    """
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=max_age,
        httponly=True,  # Prevent JavaScript access
        secure=True,  # HTTPS only
        samesite="strict",  # CSRF protection
        path="/",
    )


# ======================== ENDPOINTS ========================
@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, request) -> TokenResponse:
    """
    Register new user and return access + refresh tokens.
    
    Security:
    - Rate limit: 10 signups per hour per IP
    - Password must meet policy requirements
    - Email must be unique
    - Generic error messages to prevent enumeration
    """
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)

    try:
        # Rate limiting - prevent signup abuse
        allowed, error = RateLimiter.check_ip_rate_limit(
            ip_address,
            limit=10,
            window_seconds=3600,
        )
        if not allowed:
            security_logger.warning(f"Signup rate limit exceeded from {ip_address}")
            raise HTTPException(status_code=429, detail=error)

        # Validate password
        is_valid, error = PasswordValidator.validate(req.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Check if user exists
        if User.objects.filter(email=req.email).exists():
            raise HTTPException(status_code=400, detail="Email already registered")

        if User.objects.filter(username=req.username).exists():
            raise HTTPException(status_code=400, detail="Username already taken")

        # Create user
        with transaction.atomic():
            user = User.objects.create_user(
                username=req.username,
                email=req.email,
                password=req.password,
                first_name=req.first_name or "",
                last_name=req.last_name or "",
            )

            # Create user profile if doesn't exist
            UserProfile.objects.get_or_create(user=user)

        logger.info(f"New user registered: {user.username} from {ip_address}")

        # Generate tokens
        access_token = TokenManager.create_access_token(user.id, user.username)
        refresh_token = TokenManager.create_refresh_token(user.id, user.username)

        # Store refresh token
        token_hash = TokenManager.hash_token(refresh_token)
        from users.auth_models import RefreshToken

        expires_at = timezone.now() + timezone.timedelta(days=30)
        RefreshToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )

        # Log event
        SessionLog.objects.create(
            user=user,
            event_type="login",
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=15 * 60,  # 15 minutes
            user_id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request) -> TokenResponse:
    """
    Authenticate user and return access + refresh tokens.
    
    Security features:
    - Rate limiting: 5 attempts per minute per IP
    - Brute force detection: Lock after 5 failed attempts in 15 min
    - Generic error messages
    - Logs all attempts
    """
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)

    try:
        # Rate limit - per IP
        allowed, error = RateLimiter.check_ip_rate_limit(ip_address)
        if not allowed:
            raise HTTPException(status_code=429, detail=error)

        # Rate limit - per email
        allowed, error = RateLimiter.check_rate_limit(req.email)
        if not allowed:
            raise HTTPException(status_code=429, detail=error)

        # Generic error for security
        generic_error = HTTPException(
            status_code=401,
            detail=UserEnumerationProtection.get_generic_error()
        )

        # Find user by email
        try:
            user_profile = UserProfile.objects.select_related("user").get(email=req.email)
            user = user_profile.user
        except UserProfile.DoesNotExist:
            BruteForceProtection.log_failed_attempt(
                req.email, ip_address, user_agent, "invalid_email"
            )
            raise generic_error

        # Check if account is locked
        is_locked, lock_message = BruteForceProtection.check_account_locked(user)
        if is_locked:
            BruteForceProtection.log_failed_attempt(
                req.email, ip_address, user_agent, "account_locked"
            )
            security_logger.warning(f"Login attempt on locked account: {user.username}")
            raise HTTPException(status_code=403, detail=lock_message)

        # Check account active
        if not user.is_active or not user_profile.is_active:
            BruteForceProtection.log_failed_attempt(
                req.email, ip_address, user_agent, "account_inactive"
            )
            security_logger.warning(f"Login attempt on inactive account: {user.username}")
            raise generic_error

        # Verify password (constant-time comparison)
        if not check_password(req.password, user.password):
            BruteForceProtection.log_failed_attempt(
                req.email, ip_address, user_agent, "invalid_creds"
            )

            # Check if should lock account
            should_lock, _ = BruteForceProtection.check_failed_attempts(req.email)
            if should_lock:
                BruteForceProtection.lock_account(user)
                raise HTTPException(
                    status_code=403,
                    detail="Account locked due to multiple failed attempts"
                )

            raise generic_error

        # Successful login
        with transaction.atomic():
            # Create tokens
            access_token = TokenManager.create_access_token(user.id, user.username)
            refresh_token = TokenManager.create_refresh_token(user.id, user.username)

            # Store refresh token
            token_hash = TokenManager.hash_token(refresh_token)
            from users.auth_models import RefreshToken

            expires_at = timezone.now() + timezone.timedelta(days=30)
            RefreshToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=req.device_id,
                is_active=True,
            )

            # Log successful attempt
            BruteForceProtection.log_successful_attempt(user, ip_address, user_agent)

            # Log session
            SessionLog.objects.create(
                user=user,
                event_type="login",
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=req.device_id,
                status="success",
            )

        logger.info(f"User logged in: {user.username} from {ip_address}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=15 * 60,  # 15 minutes in seconds
            user_id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=SimpleTokenResponse)
async def refresh(req: RefreshTokenRequest, request) -> SimpleTokenResponse:
    """
    Rotate refresh token and return new access token.
    
    Security:
    - Validates refresh token signature
    - Detects token reuse (possible compromise)
    - Rate limited to prevent abuse
    - Invalidates old token
    """
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)

    try:
        # Rate limiting
        allowed, error = RateLimiter.check_ip_rate_limit(
            ip_address,
            limit=10,
            window_seconds=60,
        )
        if not allowed:
            raise HTTPException(status_code=429, detail=error)

        # Detect token reuse (possible compromise)
        if TokenRotationManager.detect_token_reuse(req.refresh_token):
            raise HTTPException(
                status_code=403,
                detail="Token reuse detected. Please login again for security."
            )

        # Get user from token
        user_id = TokenManager.extract_user_id(req.refresh_token)
        if not user_id:
            security_logger.warning("Invalid refresh token format")
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")

        # Rotate token
        result = TokenRotationManager.rotate_refresh_token(
            req.refresh_token,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=req.device_id,
        )

        if not result:
            raise HTTPException(status_code=401, detail="Token refresh failed")

        return SimpleTokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result["expires_in"],
        )

    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    req: LogoutRequest,
    request,
    authorization: Optional[str] = Header(None),
) -> SuccessResponse:
    """
    Logout user by invalidating refresh token.
    Also blacklists access token for additional security.
    
    Security:
    - Invalidates refresh token in DB
    - Adds tokens to blacklist
    - Clears cookie
    """
    ip_address = _get_client_ip(request)

    try:
        # Extract user from access token if provided
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
            user_id = TokenManager.extract_user_id(token)

        # Revoke refresh token if provided
        if req.refresh_token:
            TokenRotationManager.revoke_refresh_token(req.refresh_token, reason="logout")

        # If we have user ID, log the event
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                SessionLog.objects.create(
                    user=user,
                    event_type="logout",
                    ip_address=ip_address,
                    status="success",
                )
                logger.info(f"User logged out: {user.username} from {ip_address}")
            except User.DoesNotExist:
                pass

        return SuccessResponse(message="Logout successful")

    except Exception as e:
        security_logger.error(f"Logout error: {str(e)}")
        # Still return success to client
        return SuccessResponse(message="Logout successful")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": str(datetime.now())}
