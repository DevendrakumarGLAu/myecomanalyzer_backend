from fastapi import APIRouter, HTTPException
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from api.schemas.schemas import SignupRequest
from users.models import UserProfile

router = APIRouter(prefix="/signup", tags=["Signup"])

@router.post("/", response_model=dict)
def signup(user: SignupRequest):
    """
    Register a new Django user with profile info.
    Explicitly create UserProfile (no signals needed).
    Handles free trial or paid subscription.
    """
    # Validate username/email
    if User.objects.filter(username=user.username).exists():
        raise HTTPException(status_code=400, detail="Username already exists")
    if User.objects.filter(email=user.email).exists():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate passwords
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Create Django User
    new_user = User.objects.create_user(
        username=user.username,
        email=user.email,
        password=user.password
    )
    
    # Create UserProfile with extra fields
    profile = UserProfile.objects.create(
        user=new_user,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=user.mobile_number,
        is_active=True,
        created_at=timezone.now()
    )
    
    # Set trial or subscription
    if hasattr(user, "use_trial") and user.use_trial:
        profile.trial_start = timezone.now()
        profile.trial_end = timezone.now() + timedelta(days=7)
        profile.payment_verified = False
    else:
        profile.payment_verified = True
        profile.subscription_start = timezone.now()
        profile.subscription_end = timezone.now() + timedelta(days=30)
        profile.trial_start = None
        profile.trial_end = None
    
    profile.save()
    
    return {
        "message": "User created successfully ✅",
        "username": new_user.username,
        "email": new_user.email,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "mobile_number": profile.mobile_number,
        "trial_end": profile.trial_end.strftime("%Y-%m-%d %H:%M:%S") if profile.trial_end else None,
        "subscription_end": profile.subscription_end.strftime("%Y-%m-%d %H:%M:%S") if profile.subscription_end else None,
        "payment_verified": profile.payment_verified
    }