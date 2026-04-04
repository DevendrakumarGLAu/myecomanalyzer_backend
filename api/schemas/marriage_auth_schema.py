from pydantic import BaseModel, EmailStr


class SignupSchema(BaseModel):
    firstName: str
    middleName: str | None = None
    lastName: str
    mobile: str
    email: EmailStr
    password: str
    confirmPassword: str


class LoginSchema(BaseModel):
    username: str
    password: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    trial_end: str | None = None
    subscription_end: str | None = None
    payment_verified: bool