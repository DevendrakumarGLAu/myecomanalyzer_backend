# main.py

import os
import django

# 1️⃣ Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# 2️⃣ Setup Django
django.setup()

# 3️⃣ Now import FastAPI and routers
from fastapi import Depends, FastAPI, Request
from fastapi import APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.router import router as api_v1_router, ai_router
from api.security_middleware import setup_security_middleware
from django.conf import settings
from django.db import close_old_connections
# F:\project\ecomm-profit\backend\api\router.py

# Security scheme for Swagger
security = HTTPBearer()

# Swagger/Redoc/OpenAPI docs will now require a Bearer token for authentication. You can provide the token in the "Authorize" button in Swagger UI or Redoc.
# you are only need to use locally (DEBUG=True) and in production (DEBUG=False) you can use the token in the header of the request.
docs_url = "/docs" if os.environ.get("DEBUG", "True") == "True" else None
redoc_url = "/redoc" if os.environ.get("DEBUG", "True") == "True" else None
openapi_url = "/openapi.json" if os.environ.get("DEBUG", "True") == "True" else None
print("ENV DEBUG:", os.environ.get("DEBUG"))

app = FastAPI(
    title="MyEcomAnalyzer API",
    description="E-commerce Analytics and Management API",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    }
)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    close_old_connections()
    try:
        response = await call_next(request)
        return response
    finally:
        close_old_connections()

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

# Adds security headers, request logging, a global rate-limit backstop, and
# CORS (env-driven via Django's CORS_ALLOWED_ORIGINS setting — the single
# source of truth now; this used to be duplicated as a separate hardcoded
# CORSMiddleware call here, drifting out of sync with settings.py over time).
setup_security_middleware(app)

# 4️⃣ Include routers
router = APIRouter()
app.include_router(api_v1_router)
app.include_router(ai_router)
# uvicorn main:app --reload