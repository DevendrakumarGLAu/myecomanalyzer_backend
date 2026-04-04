from fastapi import HTTPException
import bcrypt

from api.auth import create_access_token
from marriage_user_auth.models import MarriageUser


class MarriageAuthController:
    @staticmethod
    def signup_user(payload):
        try:
            if MarriageUser.objects.filter(email=payload.email).exists():
                raise HTTPException(status_code=400, detail="Email already exists")

            # Check password match
            if payload.password != payload.confirmPassword:
                raise HTTPException(status_code=400, detail="Passwords do not match")

            # Hash password
            hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()

            # Full name
            full_name = f"{payload.firstName} {payload.middleName or ''} {payload.lastName}".strip()

            # Create user
            user = MarriageUser.objects.create(
                firstName=payload.firstName,
                middleName=payload.middleName,
                lastName=payload.lastName,
                email=payload.email,
                mobile=payload.mobile,
                name=full_name,
                password=hashed,
                is_active=True
            )

            return {
                "message": "MarriageUser created",
                "user_id": user.id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def login_user(payload):
        try:
            user = MarriageUser.objects.get(email=payload.username)
        except MarriageUser.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            if not bcrypt.checkpw(payload.password.encode(), user.password.encode()):
                raise HTTPException(status_code=401, detail="Invalid password")

            access_token = create_access_token({"sub": user.email})
            return {
                "message": "Login success",
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        