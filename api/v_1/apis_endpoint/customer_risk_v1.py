from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.controllers.customer_risk_controller import CustomerRiskController
from api.schemas.customer_risk_schema import CustomerRiskDetailResponse, CustomerRiskListResponse

router = APIRouter()


@router.get("/getall", response_model=CustomerRiskListResponse)
def get_customer_risk_report(
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search by name, phone, or pincode"),
    min_orders: Optional[int] = Query(None, ge=1),
    risk_level: Optional[str] = Query(None, description="Filter: NEW, LOW_RISK, MEDIUM_RISK, HIGH_RISK"),
    limit: int = Query(50, ge=1, le=500),
):
    return CustomerRiskController.get_risk_report(
        current_user=current_user,
        search=search,
        min_orders=min_orders,
        risk_level=risk_level,
        limit=limit,
    )


@router.get("/{customer_id}", response_model=CustomerRiskDetailResponse)
def get_customer_risk_detail(
    customer_id: int,
    current_user: User = Depends(get_current_user),
):
    result = CustomerRiskController.get_customer_detail(customer_id, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return result
