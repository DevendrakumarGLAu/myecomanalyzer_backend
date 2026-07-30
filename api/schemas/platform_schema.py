from typing import List, Optional

from pydantic import BaseModel, Field


class PlatformRequest(BaseModel):
    name: str = Field(..., description="Display name, e.g. Amazon")
    code: str = Field(..., description="Short code used across the app, e.g. AMAZON")


class PlatformResponse(BaseModel):
    id: int
    name: str
    code: str


class PlatformListResponse(BaseModel):
    data: List[PlatformResponse]


class PlatformCreateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PlatformResponse] = None
