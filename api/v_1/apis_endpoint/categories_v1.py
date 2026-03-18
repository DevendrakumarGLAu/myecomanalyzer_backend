from fastapi import APIRouter, Depends, HTTPException, Query
from django.contrib.auth.models import User
from typing import Optional, List
from api.auth import get_current_user
from api.schemas.category_schema import (
    CategoryRequest,
    CategoryResponse,
    PaginatedCategoryResponse,
    UpdateCategoryRequest
)
from api.controllers.categories_controller import CategoryController


router = APIRouter()
# controller = CategoryController()

@router.get("/getall", response_model=PaginatedCategoryResponse)
def get_all_categories(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    search: Optional[str] = Query(None, description="Search category by name")
):
    result = CategoryController.get_all_category(current_user=current_user,page=page, limit=limit, search=search)

    # if not result["success"]:
    #     raise HTTPException(status_code=400, detail=result["message"])

    return result

@router.post("/add", response_model=CategoryResponse)
def add_category(
    payload: CategoryRequest,
    current_user: User = Depends(get_current_user)
):
    result = CategoryController.add_category(payload, current_user)

    # if not result["success"]:
    #     raise HTTPException(status_code=400, detail=result["message"])

    return result

@router.put("/update", response_model=CategoryResponse)
def update_category(
    payload: UpdateCategoryRequest,
    category_id: int = Query(..., description="ID of the category to update"),
    current_user: User = Depends(get_current_user)
):
    result = CategoryController.update_category(category_id, payload, current_user)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.patch("/deactivate")
def deactivate_category(
    category_id: int = Query(..., description="ID of the category to deactivate"),
    current_user: User = Depends(get_current_user)
):
    result = CategoryController.deactivate_category(category_id, current_user)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return {"message": result["message"]}
