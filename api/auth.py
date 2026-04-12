from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import APIRouter, Response
from django.db import connection
from django.contrib.auth.models import User
SECRET_KEY = "devendrakumarglau"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
ACCESS_TOKEN_EXPIRE_MINUTES = 0

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter( prefix="/auth",tags=["Auth"])
@router.get("/test")
def test_auth():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        engine = connection.settings_dict.get("ENGINE")
        engine = connection.settings_dict.get("ENGINE")
        host = connection.settings_dict.get("HOST")
        if "mysql" in engine:
            db_name = "MySQL (Local)"
        elif "postgresql" in engine:
            if "supabase" in host:
                db_name = "PostgreSQL (Supabase)"
            elif "render" in host:
                db_name = "PostgreSQL (Render)"
            else:
                db_name = "PostgreSQL (Other)"
        else:
            db_name = "Unknown Database"
        return Response({
            "message": f"{db_name} connected successfully ✅",
            "host": host,
            "result": result
        })
    except Exception as e:
        return {"error": str(e)}
    
def create_access_token(data: dict):
    to_encode = data.copy()
    # expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS, minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException

# Name of header: Authorization
from fastapi import Header, HTTPException

api_key_header = APIKeyHeader(name="accesstoken")
def get_current_user(access_token: str = Header(..., description="Enter JWT token as 'Bearer <token>'")):
    """
    Read JWT token from header per endpoint
    """
    if not access_token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = access_token.split(" ")[1]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    try:
        user = User.objects.get(username=username)
        return user
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")