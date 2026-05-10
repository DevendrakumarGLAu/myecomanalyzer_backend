from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.controllers.dashboard_controller import DashboardController
from api.controllers.notification_controller import NotificationController
from api.schemas.dashboard_schema import DashboardResponse
from api.schemas.notification_schema import NotificationListResponse, MarkReadResponse

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


@router.get("/notifications", response_model=NotificationListResponse)
def get_notifications(
    platform_code: Optional[str] = Query(None),
    include_read: Optional[bool] = Query(False, description="Include read notifications"),
    current_user: User = Depends(get_current_user)
):
    result = NotificationController.get_notifications(
        current_user=current_user,
        platform_code=platform_code,
        include_read=include_read
    )

    return result


@router.put("/notifications/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    success = NotificationController.mark_as_read(notification_id, current_user)
    
    if success:
        return {"success": True, "message": "Notification marked as read"}
    else:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.put("/notifications/mark-all-read", response_model=MarkReadResponse)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    success = NotificationController.mark_all_as_read(current_user)
    
    if success:
        return {"success": True, "message": "All notifications marked as read"}
    else:
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")