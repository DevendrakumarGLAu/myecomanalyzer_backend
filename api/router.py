from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from django.contrib.auth.models import User

from api import signup
from api import login
from api import auth
from api.auth_endpoints import router as secure_auth_router
from api.auth import get_current_user
from api.ai_controller import AIController
from api.schemas.ai_schema import AIChatRequest, AIChatResponse, AIChatHistoryResponse


# F:\project\ecomm-profit\backend\api\v_1\apis_endpoint\product_v1.py

# Central router
router = APIRouter(prefix="/api/v1")

# Include new secure auth endpoints (replaces old auth)
router.include_router(secure_auth_router)  # /api/v1/auth/*

# Include all sub-routers
from api.auth_endpoints import router as auth_router
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# router.include_router(auth.router)     # /api/v1/auth/test
router.include_router(signup.router)   # /api/v1/auth/signup (deprecated, use /auth/signup)
router.include_router(login.router)    # /api/v1/auth/login (deprecated, use /auth/login)

# category
from api.v_1.apis_endpoint.categories_v1 import router as category_router
router.include_router(category_router, prefix="/categories", tags=["Categories"])

# product router
from api.v_1.apis_endpoint.product_v1 import router as product_router
router.include_router(product_router, prefix="/products", tags=["Products V1"])

# orders
from api.v_1.apis_endpoint.pdf_import_v1 import router as invoice_router
router.include_router(invoice_router, prefix="/upload", tags=["Invoice Upload"])

#ordersettlement
from api.v_1.apis_endpoint.settlement_upload import router as settlement_router
router.include_router(settlement_router, prefix="/upload", tags=["Settlements"])

# dashboard
from api.v_1.apis_endpoint.dashboard_v1 import router as dashboard_router
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])


# db dump
from api.v_1.apis_endpoint.db_dump_v1 import router as db_dump_router
router.include_router(db_dump_router, prefix="/db", tags=["Database"])

# db
from api.v_1.apis_endpoint.csv_dump import router as db_csv_router
router.include_router(db_csv_router, prefix="/db", tags=["Database"])

# F:\project\ecomm-profit\backend\api\v_1\apis_endpoint\marriage_biodata_v1.py
# marriage


from api.v_1.apis_endpoint.marriage_auth_v1 import router as marriage_auth_router
router.include_router(marriage_auth_router, prefix="/marriage", tags=["Marriage Auth"])

from api.v_1.apis_endpoint.marriage_biodata_v1 import router as marriage_biodata_router
router.include_router(marriage_biodata_router, prefix="/marriage", tags=["Marriage Biodata"])

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])


@ai_router.post("/chat", response_model=AIChatResponse)
def chat_endpoint(payload: AIChatRequest, current_user: User = Depends(get_current_user)):
    try:
        return AIController.process_chat(
            user=current_user,
            user_message=payload.message,
            platform_code=payload.platform,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@ai_router.post("/chat/stream")
def chat_stream_endpoint(payload: AIChatRequest, current_user: User = Depends(get_current_user)):
    try:
        return StreamingResponse(
            AIController.process_chat_stream(
                user=current_user,
                user_message=payload.message,
                platform_code=payload.platform,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@ai_router.get("/history", response_model=AIChatHistoryResponse)
def chat_history(current_user: User = Depends(get_current_user)):
    history = AIController.fetch_history(current_user)
    return {"success": True, "history": history}
