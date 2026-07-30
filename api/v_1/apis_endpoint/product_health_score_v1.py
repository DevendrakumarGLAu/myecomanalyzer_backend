from typing import Optional

from fastapi import APIRouter, Depends, Query
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.controllers.product_health_score_controller import ProductHealthScoreController
from api.schemas.product_health_score_schema import ProductHealthScoreListResponse

router = APIRouter()


@router.get("/getall", response_model=ProductHealthScoreListResponse)
def get_health_scores(
    current_user: User = Depends(get_current_user),
    platform_code: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365, description="Lookback window for orders-based factors"),
):
    return ProductHealthScoreController.get_health_scores(
        current_user=current_user, platform_code=platform_code, days=days
    )
