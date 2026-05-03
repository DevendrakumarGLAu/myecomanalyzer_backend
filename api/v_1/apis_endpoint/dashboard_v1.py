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
    date_from: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    date_to: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    order_status: Optional[str] = Query(None, description="Filter by order status code (e.g., DELIVERED, CANCELLED)"),
    delivery_partner: Optional[str] = Query(None, description="Filter by delivery partner name"),
    min_order_amount: Optional[float] = Query(None, description="Minimum order amount"),
    max_order_amount: Optional[float] = Query(None, description="Maximum order amount"),
    current_user: User = Depends(get_current_user)
):
    result = DashboardController.get_dashboard(
        platform_code=platform_code,
        date_from=date_from,
        date_to=date_to,
        order_status=order_status,
        delivery_partner=delivery_partner,
        min_order_amount=min_order_amount,
        max_order_amount=max_order_amount,
        current_user=current_user
    )

    return result