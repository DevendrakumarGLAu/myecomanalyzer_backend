from pydantic import BaseModel
from typing import Optional, List

class CategoryRequest(BaseModel):
    name: str
    description: Optional[str] = None
    
class UpdateCategoryRequest(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str
    # description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class PaginatedCategoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[CategoryResponse]