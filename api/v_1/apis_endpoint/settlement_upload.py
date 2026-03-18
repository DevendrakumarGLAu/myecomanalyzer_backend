from io import BytesIO
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
import pandas as pd
from datetime import datetime

from api.auth import get_current_user
from api.controllers.settlement_upload_controller import SettlementUploadController
from orders.models import Order
from payments.models import OrderSettlement
from django.contrib.auth.models import User
from api.auth import get_current_user
router = APIRouter()
# prefix="/settlements", tags=["Settlements"]

@router.post("/upload-excel")
def upload_settlement_excel(
    platform_code: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    return SettlementUploadController.upload_settlement_excel(
        file.file,
        current_user,
        platform_code
    )