from pydantic import BaseModel
from typing import List


class DashboardSummary(BaseModel):
    total_orders: int
    total_products: int
    total_sales: float
    total_returns: float
    total_settlement: float
    low_stock_products: int


class StatusData(BaseModel):
    status: str
    total: int


class PlatformData(BaseModel):
    platform: str
    total: int


class SalesTrend(BaseModel):
    date: str
    total_orders: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    orders_by_status: List[StatusData]
    orders_by_platform: List[PlatformData]
    sales_trend: List[SalesTrend]