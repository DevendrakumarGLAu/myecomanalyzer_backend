from datetime import date
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Query, HTTPException,Depends
import shutil
import os

from api.controllers.pdf_import_controlller import InvoiceExtractController
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from api.auth import get_current_user
from api.schemas.product_schema import CreateSingleOrderRequest

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
        
@router.get("/dispatch-invoice")
def get_dispatch_data(
    platform_code: str = Query(...),
    page: int = Query(1),
    limit: int = Query(10),

    search: Optional[str] = None,
    status: Optional[str] = None,
    state: Optional[str] = None,
    sku: Optional[str] = None,

    start_date: Optional[date] = None,
    end_date: Optional[date] = None,

    sort_by: Optional[str] = "id",
    order: Optional[str] = "desc",
    current_user: User = Depends(get_current_user)
):
    
    if platform_code.lower() == "meesho":
        return InvoiceExtractController.process_meesho_invoice(current_user,platform_code,page,limit,search,status,state,sku,start_date,end_date,sort_by,order)
    elif platform_code.lower() == "amazon":
        return {
            "message": "Amazon invoice processing not implemented yet",
            "status": "error"
        }
        return InvoiceExtractController.process_amazon_invoice()
    else:
        raise ValueError("Unsupported platform code")
    
@router.post("/order-status")
def upload_order_status(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    try:
        result = InvoiceExtractController.update_order_status_from_csv(
            file.file, current_user
        )

        return {
            "status": "success",
            "message": "Order status updated successfully",
            "data": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "CSV processing failed",
            "error": str(e)
        }
        
@router.post("/dispatch-single-order")
def create_single_order(
    payload: CreateSingleOrderRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        result = InvoiceExtractController.create_single_order(payload.dict(), current_user)

        return result

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }