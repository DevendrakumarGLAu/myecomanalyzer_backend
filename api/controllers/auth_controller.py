# api_v1/controllers/auth_controller.py

from fastapi import HTTPException
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

from core.auth import create_access_token


def signup_controller(user_data):
    if User.objects.filter(username=user_data.username).exists():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User.objects.create(
        username=user_data.username,
        email=user_data.email,
        password=make_password(user_data.password),
    )

    token = create_access_token({"user_id": new_user.id})

    return {
        "message": "User created successfully",
        "access_token": token,
        "token_type": "bearer",
    }


def login_controller(user_data):
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