from pydantic import BaseModel
from typing import List

class AdsTrendData(BaseModel):
    month: str
    total_spend: float

class DashboardSummary(BaseModel):
    total_orders: int
    total_products: int
    total_sales: float
    total_returns: float
    total_settlement: float
    low_stock_products: int
    total_claims: float
    total_profit:float
    total_ads_spend: float
    ads_trend: List[AdsTrendData]


class StatusData(BaseModel):
    status: str
    total: int


class PlatformData(BaseModel):
    platform: str
    total: int


class SalesTrend(BaseModel):
    date: str
    total_orders: int


class DeliveryPartnerStat(BaseModel):
    partner: str
    total_orders: int
    delivered: int
    rto: int
    cancelled: int
    customer_return: int
    ready_to_ship: int
    exchange: int
    lost: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    orders_by_status: List[StatusData]
    orders_by_platform: List[PlatformData]
    sales_trend: List[SalesTrend]
    delivery_partner_stats: List[DeliveryPartnerStat]
    state_wise_analytics: List[dict]