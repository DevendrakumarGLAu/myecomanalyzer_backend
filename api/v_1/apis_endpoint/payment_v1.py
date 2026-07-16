from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.controllers.payment_controller import PaymentController
from api.schemas.payment_schema import PaymentTrendResponse, SkuProfitResponse

router = APIRouter()


@router.get("/trend", response_model=PaymentTrendResponse)
def payment_trend(
    range: str = Query("7d", description="One of: 7d, 1m, 1y, custom"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), required when range=custom"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD), required when range=custom"),
    platform_code: Optional[str] = Query(None, description="Filter by platform code"),
    current_user: User = Depends(get_current_user),
):
    try:
        return PaymentController.get_payment_trend(
            current_user=current_user,
            range_type=range,
            date_from=date_from,
            date_to=date_to,
            platform_code=platform_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/sku-profit", response_model=SkuProfitResponse)
def sku_profit(
    range: Optional[str] = Query(None, description="Optional: 7d, 1m, 1y, or custom. Omit for all-time."),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), required when range=custom"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD), required when range=custom"),
    platform_code: Optional[str] = Query(None, description="Filter by platform code"),
    sort: str = Query("profit_desc", description="One of: profit_desc, profit_asc, revenue_desc"),
    limit: int = Query(20, ge=1, le=100, description="Max number of SKUs to return"),
    current_user: User = Depends(get_current_user),
):
    try:
        return PaymentController.get_sku_wise_profit(
            current_user=current_user,
            range_type=range,
            date_from=date_from,
            date_to=date_to,
            platform_code=platform_code,
            sort=sort,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
