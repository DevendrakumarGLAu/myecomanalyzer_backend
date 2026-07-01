from fastapi import APIRouter, Depends, Query
from django.contrib.auth.models import User
from typing import Optional

from api.auth import get_current_user
from api.controllers.manifest_controller import ManifestController
from api.schemas.manifest_schema import ManifestResponse

router = APIRouter()


@router.get("/getall", response_model=ManifestResponse)
def get_manifest(
    current_user: User = Depends(get_current_user),
    date: Optional[str] = Query(None),
    platform_code: str = Query("MEESHO"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1),
):
    return ManifestController.get_manifest(
        current_user=current_user,
        manifest_date=date,
        platform_code=platform_code,
        search=search,
        page=page,
        limit=limit,
    )