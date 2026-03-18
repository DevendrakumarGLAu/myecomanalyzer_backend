from fastapi import APIRouter
from api import signup
from api import login
from api import auth


# F:\project\ecomm-profit\backend\api\v_1\apis_endpoint\product_v1.py

# Central router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(auth.router)     # /api/v1/auth/test
router.include_router(signup.router)   # /api/v1/auth/signup
router.include_router(login.router)    # /api/v1/auth/login

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