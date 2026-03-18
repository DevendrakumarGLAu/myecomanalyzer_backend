from fastapi import APIRouter, Depends, Query
from typing import Optional
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.controllers.dashboard_controller import DashboardController
from api.schemas.dashboard_schema import DashboardResponse

router = APIRouter()


@router.get("/summary", response_model=DashboardResponse)
def dashboard_summary(
    platform_code: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    result = DashboardController.get_dashboard(platform_code=platform_code, current_user=current_user)

    return result