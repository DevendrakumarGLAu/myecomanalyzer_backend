from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =========================
# 🔥 REQUEST
# =========================
class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    platform: Optional[str] = Field(
        None,
        description="Marketplace platform code (MEESHO, AMAZON, FLIPKART etc.)"
    )


# =========================
# 📊 ANALYTICS MODELS
# =========================
class TopProduct(BaseModel):
    product_name: str
    sales: float
    profit: float


class PlatformPerformance(BaseModel):
    platform: str
    sales: float
    profit: float
    orders: int


class AlertItem(BaseModel):
    message: str


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

    top_products: List[TopProduct] = []
    platform_performance: List[PlatformPerformance] = []
    alerts: List[str] = []


# =========================
# 🤖 CHAT RESPONSE
# =========================
class AIChatResponse(BaseModel):
    success: bool
    reply: str
    intent: str

    # safer typing (prevents JSON bugs)
    analytics_used: Optional[AIAnalyticsSummary] = None


# =========================
# 🕘 CHAT HISTORY
# =========================
class AIChatHistoryItem(BaseModel):
    id: int
    platform: Optional[str] = None
    intent: Optional[str] = None
    user_message: str
    assistant_reply: str
    created_at: datetime   # ✅ FIXED (no JSON error)


class AIChatHistoryResponse(BaseModel):
    success: bool
    history: List[AIChatHistoryItem]