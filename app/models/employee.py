from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class EmployeeBase(BaseModel):
    email: EmailStr
    name: str
    description: Optional[str] = None
    mobile_number: Optional[str] = None
    location: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeLocation(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None

class EmployeeUpdate(EmployeeBase):
    profile_photo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Employee(EmployeeBase):
    id: str
    manager_id: str
    profile_photo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


    class Config:
        from_attributes = True