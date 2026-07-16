from datetime import date

from pydantic import BaseModel
from typing import List


class ManifestItemResponse(BaseModel):
    product_name: str
    sku: str
    size: str
    color: str
    quantity: int


class DeliveryPartnerManifestResponse(BaseModel):
    delivery_partner: str
    total_quantity: int
    total_products: int
    items: List[ManifestItemResponse]


class SkuManifestItemResponse(BaseModel):
    sku: str
    product_name: str
    size: str
    color: str
    quantity: int
    delivery_partner_count: int


class ManifestResponse(BaseModel):
    manifest_date: date
    total_quantity: int
    delivery_partner_count: int
    data: List[DeliveryPartnerManifestResponse]
    sku_wise: List[SkuManifestItemResponse]