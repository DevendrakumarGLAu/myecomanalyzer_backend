# main.py

import os
import django

# 1️⃣ Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# 2️⃣ Setup Django
django.setup()

# 3️⃣ Now import FastAPI and routers
from fastapi import Depends, FastAPI
from fastapi import APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.router import router as api_v1_router
from fastapi.middleware.cors import CORSMiddleware
# F:\project\ecomm-profit\backend\api\router.py

# Security scheme for Swagger
security = HTTPBearer()


app = FastAPI(
    title="MyEcomAnalyzer API",
    description="E-commerce Analytics and Management API",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    }
)

@app.get("/test")
def test_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    return {"token": token}
# Configure OpenAPI security scheme
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="MyEcomAnalyzer API",
        version="1.0.0",
        description="E-commerce Analytics and Management API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://marriage-biodata-lufw.onrender.com",
    "https://myecomanalyzer-frontend.onrender.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # frontend origins
    allow_credentials=True,     # allow cookies/headers
    allow_methods=["*"],        # allow all HTTP methods (POST, GET, OPTIONS, etc.)
    allow_headers=["*"],        # allow all headers
)
# 4️⃣ Include router
router = APIRouter()
app.include_router(api_v1_router)
# uvicorn main:app --reload