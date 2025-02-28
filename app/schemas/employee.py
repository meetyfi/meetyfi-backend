from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class EmployeeRole(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    MANAGER = "manager"
    ADMIN = "admin"

class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EmployeeBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)
    role: EmployeeRole
    description: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')

class EmployeeCreate(EmployeeBase):
    manager_id: str
    initial_password: str = Field(..., min_length=8)

class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    role: Optional[EmployeeRole] = None
    description: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    profile_photo: Optional[str] = None

class EmployeeLocation(BaseModel):
    employee_id: str
    location: LocationUpdate

    @validator('location')
    def validate_timestamp(cls, v):
        if v.timestamp > datetime.utcnow():
            raise ValueError('Location timestamp cannot be in the future')
        return v

class EmployeeResponse(EmployeeBase):
    id: str
    manager_id: str
    profile_photo: Optional[str] = None
    last_location: Optional[LocationUpdate] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class EmployeeSearchParams(BaseModel):
    role: Optional[EmployeeRole] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None
    search_term: Optional[str] = None