# main.py

import os
import django

# 1️⃣ Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# 2️⃣ Setup Django
django.setup()

# 3️⃣ Now import FastAPI and routers
from fastapi import FastAPI
from fastapi import APIRouter
from api.router import router as api_v1_router
from fastapi.middleware.cors import CORSMiddleware
# F:\project\ecomm-profit\backend\api\router.py

app = FastAPI(title="MyEcomAnalyzer API")
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
router = APIRouter(prefix="/api/v1")
app.include_router(api_v1_router)
# uvicorn main:app --reload