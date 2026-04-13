from fastapi import APIRouter, Depends, HTTPException,Query
from django.contrib.auth.models import User
from typing import List, Optional
from api.auth import get_current_user
from api.schemas.product_schema import APIResponse, PaginatedProductResponse, ProductResponse, ProductRequest
from api.controllers.product_controller import ProductController


router = APIRouter()
controller = ProductController()




@router.get("/getallproduct/", response_model=PaginatedProductResponse)
def get_products(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    search: Optional[str] = None,
    platform: Optional[str] = None,
):
    try:
        return controller.get_all_products(current_user, page, limit, search, platform)
        # return controller.get_all_products(current_user, page=page, limit=limit, search=search)
    except Exception as e:
        # Handle and log the error
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, current_user: User = Depends(get_current_user)):
    return ProductController.get_product_by_id(product_id, current_user)

@router.post("/add/", response_model=APIResponse)
def add_product(payload: ProductRequest, current_user: User = Depends(get_current_user)):
    try:
        product = ProductController.add_product(payload, current_user)

        return APIResponse(
            status=True,
            message="Product added successfully",
            data=product
        )

    except Exception as e:
        return APIResponse(
            status=False,
            message=f"Failed to add product: {str(e)}",
            data=None
        )
        



# @router.put("/update", response_model=ProductResponse)
# def update_product(
#     id: int = Query(..., description="Product ID"),
#     payload: ProductRequest = ...,
#     current_user: User = Depends(get_current_user)
# ):
#     return controller.update_product_logic(id, payload, current_user)

@router.put("/update", response_model=APIResponse)
def update_product(
    id: int = Query(..., description="Product ID"),
    payload: ProductRequest = ...,
    current_user: User = Depends(get_current_user)
):
    try:
        product = ProductController.update_product_logic(id, payload, current_user)

        return APIResponse(
            status=True,
            message="Product updated successfully",
            data=product
        )

    except Exception as e:
        return APIResponse(
            status=False,
            message=f"Failed to update product: {str(e)}",
            data=None
        )


@router.delete("deletebyId/{product_id}")
def delete_product(product_id: int, current_user: User = Depends(get_current_user)):
    return ProductController.delete_product_logic(product_id, current_user)


@router.post("/toggle_active/{product_id}", response_model=ProductResponse)
def toggle_product_active(product_id: int, current_user: User = Depends(get_current_user)):
    return ProductController.toggle_product_active_logic(product_id, current_user)