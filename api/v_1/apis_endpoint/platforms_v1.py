from fastapi import APIRouter, Depends
from django.contrib.auth.models import User

from api.auth import get_current_user, require_staff_user
from api.controllers.platform_controller import PlatformController
from api.schemas.platform_schema import PlatformCreateResponse, PlatformListResponse, PlatformRequest

router = APIRouter()


@router.get("/getall", response_model=PlatformListResponse)
def get_all_platforms(current_user: User = Depends(get_current_user)):
    return PlatformController.list_platforms()


@router.post("/add", response_model=PlatformCreateResponse)
def add_platform(
    payload: PlatformRequest,
    current_user: User = Depends(require_staff_user),
):
    return PlatformController.create_platform(payload, current_user)
