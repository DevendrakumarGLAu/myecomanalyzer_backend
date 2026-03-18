from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    first_name: Optional[str] = Field(None, max_length=150)
    last_name: Optional[str] = Field(None, max_length=150)
    email: EmailStr
    mobile_number: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    use_trial: Optional[bool] = True  # default to True if not provided

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v
class LoginRequest(BaseModel):
    email: str
    password: str
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
       # frontend sends True for trial, False if paying

class PlatformCreate(BaseModel):
    name: str

class ProductCreate(BaseModel):
    sku: str
    category:str
    barcode: str
    platform_id: int
    cost_price: float
    selling_price: float
    packaging_cost: float = 0
    rto_cost: float = 0

class ProfitResponse(BaseModel):
    profit: float