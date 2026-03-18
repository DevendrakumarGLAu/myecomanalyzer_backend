from pydantic import BaseModel
from typing import List, Optional


class ProductVariantRequest(BaseModel):
    sku: str
    size: Optional[str] = None
    color: Optional[str] = None
    cost_price: float
    selling_price: float
    stock: int
    rto_cost: Optional[float] = None
    shipping_cost: Optional[float] = None


class ProductVariantResponse(ProductVariantRequest):
    id: int

    class Config:
        from_attributes = True
        
class ProductRequest(BaseModel):
    catalog_id: int
    name: str
    category_id: int
    platform_code: Optional[str] = None
    gst_percent: float = 0.0
    commission_percent: float = 0.0
    shipping_cost: float = 0.0
    rto_cost: float = 0.0
    is_active: Optional[bool] = True

    variants: List[ProductVariantRequest]
    
class ProductResponse(BaseModel):
    id: int
    catalog_id: str
    name: str
    category_id: int
    category_name: str
    platform_code: Optional[str] = None
    gst_percent: float = 0.0
    commission_percent: float = 0.0
    is_active: bool
    variants: List[ProductVariantResponse]

    class Config:
        from_attributes = True

        
class PaginatedProductResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    
class ProductUpdateRequest(BaseModel):
    catalog_id: Optional[str] = None
    name: Optional[str] = None
    category_id: Optional[int] = None
    platform_code: Optional[str] = None
    gst_percent: Optional[float] = None
    commission_percent: Optional[float] = None
    shipping_cost: Optional[float] = None
    rto_cost: Optional[float] = None
    is_active: Optional[bool] = None
    variants: Optional[List[ProductVariantRequest]] = None