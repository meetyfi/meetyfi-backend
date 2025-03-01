from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.utils.validators import validate_phone

class ManagerProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    company_name: str
    company_size: int
    is_verified: bool
    is_approved: bool
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime

class ManagerProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

    @validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

# Employee management
class EmployeeCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: Optional[str] = None
    department: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    email: str
    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool
    created_at: datetime

class EmployeeListResponse(BaseModel):
    employees: List[EmployeeResponse]
    total: int
    page: int
    limit: int

# Employee locations
class EmployeeLocationItem(BaseModel):
    employee_id: int
    name: str
    latitude: float
    longitude: float
    address: str
    timestamp: datetime

class EmployeeLocationResponse(BaseModel):
    employee_locations: List[EmployeeLocationItem]

# Meetings
class MeetingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class MeetingCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    date: datetime
    time: Optional[str] = None  # If time is separate from date
    duration: int = Field(..., gt=0, le=480)  # Max 8 hours
    employee_ids: List[int] = Field(..., min_items=1)
    location: Optional[str] = None

class EmployeeInMeeting(BaseModel):
    id: int
    name: str
    email: str
    role: Optional[str] = None
    department: Optional[str] = None

class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    date: datetime
    duration: int
    location: Optional[str] = None
    status: MeetingStatus
    rejection_reason: Optional[str] = None
    created_by_type: str
    created_at: datetime
    employees: List[EmployeeInMeeting]

class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    limit: int

class MeetingStatusUpdateRequest(BaseModel):
    status: MeetingStatus
    reason: Optional[str] = None