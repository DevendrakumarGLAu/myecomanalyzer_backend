from fastapi import HTTPException
import bcrypt

# from api.auth import create_access_token
from api.token_manager import TokenManager
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
        generic_error = HTTPException(status_code=401, detail="Invalid email or password")

        try:
            user = MarriageUser.objects.get(email=payload.username)
        except MarriageUser.DoesNotExist:
            # Same error as a wrong password below — a distinct "not found"
            # response here would let a caller enumerate registered emails.
            raise generic_error

        if not bcrypt.checkpw(payload.password.encode(), user.password.encode()):
            raise generic_error

        try:
            # create_access_token(user_id, username, ...) — the previous call
            # passed a single dict as user_id with username missing entirely,
            # which raises TypeError on every login attempt.
            access_token = TokenManager.create_access_token(user.id, user.email)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "message": "Login success",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id
        }
        