from fastapi import APIRouter, Depends, HTTPException
from django.contrib.auth.models import User
from api.auth import get_current_user
from api.schemas.user_profile_schema import (
    UserProfileUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateResponse
)
from api.controllers.user_profile_controller import UserProfileController

router = APIRouter()

@router.get("/get", response_model=UserProfileResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    result = UserProfileController.get_profile(current_user)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result["data"]

@router.put("/update", response_model=UserProfileUpdateResponse)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    result = UserProfileController.update_profile(current_user, payload)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result



