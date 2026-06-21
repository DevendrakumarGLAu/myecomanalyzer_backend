from fastapi import APIRouter, Depends, HTTPException
from django.contrib.auth.models import User
from api.auth import get_current_user
from api.controllers.subscription_controller import SubscriptionController
from api.schemas.subscription_schema import (
    SubscriptionResponse,
    SubscriptionAddRequest,
    SubscriptionAddResponse
)

router = APIRouter()


# =========================
# GET SUBSCRIPTION
# =========================
@router.get("/get", response_model=SubscriptionResponse)
def get_subscription(
    current_user: User = Depends(get_current_user)
):
    result = SubscriptionController.get_subscription(current_user)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result["data"]


# =========================
# ADD / RENEW SUBSCRIPTION
# =========================
@router.post("/add", response_model=SubscriptionAddResponse)
def add_subscription(
    payload: SubscriptionAddRequest,
    current_user: User = Depends(get_current_user)
):
    result = SubscriptionController.renew_subscription(
        current_user,
        payload.plan
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result