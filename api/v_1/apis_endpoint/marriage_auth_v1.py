

from fastapi import APIRouter

from api.controllers.marriage_auth_controller import MarriageAuthController
from api.schemas.marriage_auth_schema import LoginSchema, SignupSchema


router = APIRouter()
@router.get("/test")
def test_auth():
    return {
        "message": "Marriage auth endpoint is working ✅"
    }
    

@router.post("/signup")
def signup(payload:SignupSchema):
    
    return MarriageAuthController.signup_user(payload)
    
@router.post("/login")
def login(payload:LoginSchema):
    return MarriageAuthController.login_user(payload)