from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
from enum import Enum

from app.utils.validators import validate_email, validate_password, validate_phone

class UserType(str, Enum):
    MANAGER = "manager"
    EMPLOYEE = "employee"
    ADMIN = "admin"

# Manager Signup
class ManagerSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=100)
    company_name: str = Field(..., min_length=2, max_length=100)
    company_size: int = Field(..., gt=0)
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

    @field_validator('email')
    def validate_email_format(cls, v):
        validate_email(v)
        return v

    @field_validator('password')
    def validate_password_strength(cls, v):
        validate_password(v)
        return v

    @field_validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

class ManagerSignupResponse(BaseModel):
    message: str
    manager_id: int

# OTP Verification
class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class VerifyOTPResponse(BaseModel):
    message: str
    access_token: str

# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: UserType

class UserData(BaseModel):
    id: int
    email: str
    name: str
    user_type: UserType
    is_verified: bool
    # Additional fields based on user type
    company_name: Optional[str] = None
    company_size: Optional[int] = None
    role: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None

class LoginResponse(BaseModel):
    access_token: str
    user_data: UserData

# Employee Verification
class EmployeeVerifyRequest(BaseModel):
    verification_token: str
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def validate_password_strength(cls, v):
        validate_password(v)
        return v

class EmployeeVerifyResponse(BaseModel):
    message: str
    access_token: str