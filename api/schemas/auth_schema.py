from pydantic import BaseModel, EmailStr


class SignupSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str