from typing import Optional

from fastapi import APIRouter, Depends, Query
from django.contrib.auth.models import User

from api.auth import require_staff_user
from api.controllers.platform_fee_slab_controller import PlatformFeeSlabController
from api.schemas.platform_fee_slab_schema import (
    PlatformFeeSlabCreateResponse,
    PlatformFeeSlabListResponse,
    PlatformFeeSlabRequest,
)

router = APIRouter(dependencies=[Depends(require_staff_user)])


@router.get("/getall", response_model=PlatformFeeSlabListResponse)
def list_fee_slabs(
    platform_code: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
):
    return PlatformFeeSlabController.list_slabs(platform_code=platform_code, include_inactive=include_inactive)


@router.post("/add", response_model=PlatformFeeSlabCreateResponse)
def create_fee_slab(
    payload: PlatformFeeSlabRequest,
    current_user: User = Depends(require_staff_user),
):
    return PlatformFeeSlabController.create_slab(payload, current_user)


@router.put("/update/{slab_id}", response_model=PlatformFeeSlabCreateResponse)
def update_fee_slab(
    slab_id: int,
    payload: PlatformFeeSlabRequest,
    current_user: User = Depends(require_staff_user),
):
    return PlatformFeeSlabController.update_slab(slab_id, payload, current_user)


@router.post("/toggle_active/{slab_id}", response_model=PlatformFeeSlabCreateResponse)
def toggle_fee_slab_active(
    slab_id: int,
    current_user: User = Depends(require_staff_user),
):
    return PlatformFeeSlabController.toggle_active(slab_id, current_user)


@router.delete("/delete/{slab_id}")
def delete_fee_slab(
    slab_id: int,
    current_user: User = Depends(require_staff_user),
):
    return PlatformFeeSlabController.delete_slab(slab_id, current_user)
