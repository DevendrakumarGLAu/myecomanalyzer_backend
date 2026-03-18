from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from django.contrib.auth import authenticate
from users.models import UserProfile
from api import auth  # JWT helpers

router = APIRouter(prefix="/login", tags=["Login"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    trial_end: str | None = None
    subscription_end: str | None = None
    payment_verified: bool

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """
    Authenticate user by email and return JWT token + profile/subscription info
    """
    # Lookup username from UserProfile by email
    try:
        profile = UserProfile.objects.get(email=credentials.email)
        username = profile.user.username
    except UserProfile.DoesNotExist:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if profile is active
    if not profile.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Authenticate using Django auth
    user = authenticate(username=username, password=credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = auth.create_access_token({"sub": user.username})
    
    # Return token + user_id + subscription/trial info
    return TokenResponse(
        access_token=token,
        user_id=profile.user.id,
        trial_end=profile.trial_end.strftime("%Y-%m-%d %H:%M:%S") if profile.trial_end else None,
        subscription_end=profile.subscription_end.strftime("%Y-%m-%d %H:%M:%S") if profile.subscription_end else None,
        payment_verified=profile.payment_verified
    )