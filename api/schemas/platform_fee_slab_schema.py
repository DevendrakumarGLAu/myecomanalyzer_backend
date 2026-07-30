from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PlatformFeeSlabRequest(BaseModel):
    platform_code: str = Field(..., description="Platform code, e.g. MEESHO, AMAZON, FLIPKART, MYNTRA")
    category: str = Field("ALL", description="Category this slab applies to, or 'ALL' for every category")
    min_selling_price: float = Field(..., ge=0)
    max_selling_price: Optional[float] = Field(None, description="Omit for no upper bound (top-most slab)")
    commission_percent: float = Field(0, ge=0, le=100)
    fixed_fee: float = Field(0, ge=0)
    shipping_fee: float = Field(0, ge=0)
    rto_fee: float = Field(0, ge=0)
    gst_percent: float = Field(18, ge=0, le=100)
    effective_from: date


class PlatformFeeSlabResponse(BaseModel):
    id: int
    platform_code: str
    platform_name: str
    category: str
    min_selling_price: float
    max_selling_price: Optional[float]
    commission_percent: float
    fixed_fee: float
    shipping_fee: float
    rto_fee: float
    gst_percent: float
    effective_from: date
    is_active: bool


class PlatformFeeSlabListResponse(BaseModel):
    total: int
    data: List[PlatformFeeSlabResponse]


class PlatformFeeSlabCreateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PlatformFeeSlabResponse] = None
