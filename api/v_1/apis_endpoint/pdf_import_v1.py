from fastapi import APIRouter, UploadFile, File, Query, HTTPException,Depends
import shutil
import os

from api.controllers.pdf_import_controlller import InvoiceExtractController
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from api.auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "media/invoices/"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-invoice/")
async def upload_invoice(
    platform_code: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "message": "Only PDF files are allowed",
            "data": None
        }

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = await sync_to_async(
            InvoiceExtractController.save_invoice_to_db
        )(file_path, platform_code, current_user)

        # Propagate error if controller returns success: False
        if isinstance(result, dict) and result.get("success") is False:
            return {
                "success": False,
                "message": result.get("message", "Invoice processed with errors"),
                "error": result.get("error"),
                "data": result.get("data")
            }

        return {
            "success": True,
            "message": "Invoice processed successfully",
            "data": result
        }

    except Exception as e:
        # ⚠️ STILL RETURN 200
        return {
            "success": False,
            "message": "Invoice processed with errors",
            "error": str(e),
            "data": None
        }