from pydantic import BaseModel
from typing import List, Optional


class PaymentTrendPoint(BaseModel):
    date: str
    amount: float
    count: int


class PaymentTrendData(BaseModel):
    range: str
    group_by: str
    start_date: str
    end_date: str
    total_amount: float
    total_payments: int
    trend: List[PaymentTrendPoint]


class PaymentTrendResponse(BaseModel):
    success: bool
    message: str
    data: PaymentTrendData


class SkuProfitPoint(BaseModel):
    sku: str
    product_name: str
    quantity: int
    revenue: float
    cost: float
    deductions: float
    profit: float
    margin_percent: float
    orders: int


class SkuProfitData(BaseModel):
    range: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sort: str
    limit: int
    skus: List[SkuProfitPoint]


class SkuProfitResponse(BaseModel):
    success: bool
    message: str
    data: SkuProfitData
