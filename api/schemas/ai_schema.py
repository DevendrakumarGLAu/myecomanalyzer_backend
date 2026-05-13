from pydantic import BaseModel, Field
from typing import Optional


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt for the ecommerce analyst chatbot")
    platform: Optional[str] = Field(None, description="Marketplace platform code, e.g. MEESHO, AMAZON")


class AIAnalyticsSummary(BaseModel):
    total_sales: float
    total_settlement: float
    total_profit: float
    profit_margin: float
    total_orders: int
    return_rate: float
    rto_rate: float
    low_stock_count: int
    dead_inventory_count: int
    settlement_mismatch_count: int
    top_products: list[dict]
    platform_performance: list[dict]
    alerts: list[str]


class AIChatResponse(BaseModel):
    success: bool
    reply: str
    intent: str
    analytics_used: dict


class AIChatHistoryItem(BaseModel):
    id: int
    platform: str
    intent: str
    user_message: str
    assistant_reply: str
    created_at: str


class AIChatHistoryResponse(BaseModel):
    success: bool
    history: list[AIChatHistoryItem]
