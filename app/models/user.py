from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class OrganizationType(str, Enum):
    CORPORATE = "corporate"
    STARTUP = "startup"
    AGENCY = "agency"
    INDIVIDUAL = "individual"

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None

class UserInDB(UserBase):
    hashed_password: str
    is_verified: bool = False
    profile_photo: Optional[str] = None
    manager_id: Optional[str] = None
    created_at: datetime = datetime.utcnow()

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    manager_id: Optional[str] = None
    organization: Optional[str] = None

class ManagerSignup(UserBase):
    organization_type: OrganizationType
    is_manager: bool = True
    company_size: Optional[int] = None
    industry: Optional[str] = None

class EmployeeCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None

