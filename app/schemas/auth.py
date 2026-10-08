from pydantic import BaseModel, EmailStr, Field

class RequestOTP(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)