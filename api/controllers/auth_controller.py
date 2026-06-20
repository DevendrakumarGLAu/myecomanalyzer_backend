# api_v1/controllers/auth_controller.py

from datetime import timedelta
from gettext import translation

from fastapi import HTTPException
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezones

from core.auth import create_access_token
from roles.models import Role
from users.models import UserProfile
from rest_framework.exceptions import ValidationError
from django.conf import settings


# def signup_controller(user_data):
#     if User.objects.filter(username=user_data.username).exists():
#         raise HTTPException(status_code=400, detail="Username already exists")

#     new_user = User.objects.create(
#         username=user_data.username,
#         email=user_data.email,
#         password=make_password(user_data.password),
#     )

#     token = create_access_token({"user_id": new_user.id})

#     return {
#         "message": "User created successfully",
#         "access_token": token,
#         "token_type": "bearer",
#     }

@translation.atomic
def signup_controller(user_data):

    # 1. Username check
    if User.objects.filter(username=user_data.username).exists():
        raise ValidationError({"username": "Username already exists"})

    # 2. Email check
    if user_data.email and User.objects.filter(email=user_data.email).exists():
        raise ValidationError({"email": "Email already exists"})

    # 3. Create user (Django handles password hashing)
    user = User.objects.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name or "",
        last_name=user_data.last_name or "",
    )

    # 4. Default role (SAFE)
    role = Role.objects.filter(name="user").first()
    if not role:
        raise ValidationError({"role": "Default role not found"})

    # 5. Subscription (7 days trial)
    now = timezones.now()
    trial_days = settings.TRIAL_DAYS

    subscription_start = now
    subscription_end = now + timedelta(days=trial_days)

    # 6. Create profile
    UserProfile.objects.create(
        user=user,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=getattr(user_data, "mobile_number", None),
        role=role,
        is_active=True,

        # subscription fields
        subscription_start=subscription_start,
        subscription_end=subscription_end,
        payment_verified=False,
    )

    # 7. Token
    token = create_access_token({"user_id": user.id})

    return {
        "message": "User created successfully",
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "subscription_start": subscription_start,
        "subscription_end": subscription_end,
        "access_token": token,
        "token_type": "bearer",
    }


def login_controller(user_data):
    # print(user_data)
    try:
        user = User.objects.get(username=user_data.username)
    except User.DoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not check_password(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
    }