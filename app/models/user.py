from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

from app.utils.validators import validate_email, validate_password, validate_phone

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator('email')
    def validate_email_format(cls, v):
        validate_email(v)
        return v

class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        validate_password(v)
        return v

class ManagerBase(UserBase):
    company_name: str = Field(..., min_length=2, max_length=100)
    company_size: int = Field(..., gt=0)
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    otp: Optional[str] = None  
    
    @field_validator('phone')
    def validate_phone(cls, v):
        # This is likely where the validation happens
        # Check what format is expected here
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v

class ManagerCreate(ManagerBase, PasswordMixin):
    pass

class ManagerInDB(ManagerBase):
    id: int
    is_verified: bool = False
    is_approved: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class ManagerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    
    @field_validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

class EmployeeBase(UserBase):
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    
    @field_validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

class EmployeeCreate(EmployeeBase):
    manager_id: int

class EmployeeInDB(EmployeeBase):
    id: int
    manager_id: int
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    
    @field_validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

class AdminBase(UserBase, PasswordMixin):
    pass

class AdminInDB(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True