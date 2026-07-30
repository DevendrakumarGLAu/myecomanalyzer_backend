from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class CustomerRiskRow(BaseModel):
    customer_id: int
    name: str
    phone: Optional[str] = None
    state: str
    pincode: Optional[str] = None
    total_orders: int
    delivered_count: int
    rto_count: int
    return_count: int
    return_rto_rate_percent: float
    risk_level: str
    risk_reason: str
    last_order_date: Optional[date] = None


class CustomerRiskListResponse(BaseModel):
    total: int
    data: List[CustomerRiskRow]


class CustomerOrderHistoryRow(BaseModel):
    order_id: str
    order_date: date
    platform: Optional[str] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    status: Optional[str] = None
    is_bad_outcome: bool


class CustomerRiskDetailResponse(BaseModel):
    customer_id: int
    name: str
    address: str
    state: str
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    total_orders: int
    return_rto_rate_percent: float
    risk_level: str
    risk_reason: str
    order_history: List[CustomerOrderHistoryRow]
