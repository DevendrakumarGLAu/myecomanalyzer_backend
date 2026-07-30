from typing import List

from pydantic import BaseModel


class HealthScoreFactor(BaseModel):
    score: float
    weight_percent: int
    detail: str


class HealthScoreBreakdown(BaseModel):
    profit_margin: HealthScoreFactor
    sales_volume: HealthScoreFactor
    return_rate: HealthScoreFactor
    inventory_availability: HealthScoreFactor


class ProductHealthScoreResponse(BaseModel):
    product_id: int
    product_name: str
    health_score: float
    grade: str
    breakdown: HealthScoreBreakdown


class ProductHealthScoreListResponse(BaseModel):
    data: List[ProductHealthScoreResponse]
