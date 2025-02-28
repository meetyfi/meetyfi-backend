from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class OrganizationType(str, Enum):
    CORPORATE = "corporate"
    STARTUP = "startup"
    AGENCY = "agency"
    FREELANCER = "freelancer"

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)
    organization: OrganizationType
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    organization: Optional[OrganizationType] = None
    manager_id: Optional[str] = None
    phone_number: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    location: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_verified: bool
    is_manager: bool
    profile_photo: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True