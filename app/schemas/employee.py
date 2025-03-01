from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.utils.validators import validate_phone, validate_proposed_dates

class EmployeeProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool
    created_at: datetime
    manager: Dict[str, Any]  # Basic manager info

class EmployeeProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

    @field_validator('phone')
    def validate_phone_number(cls, v):
        if v:
            validate_phone(v)
        return v

# Manager details
class ManagerResponse(BaseModel):
    id: int
    name: str
    email: str
    company_name: str
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

# Manager availability
class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime

class ManagerAvailabilityResponse(BaseModel):
    available_slots: List[TimeSlot]

# Location
class LocationCreateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str

# Meetings
class MeetingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class MeetingRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    proposed_dates: List[datetime] = Field(..., min_items=1, max_items=5)
    duration: int = Field(..., gt=0, le=480)  # Max 8 hours
    location: Optional[str] = None

    @field_validator('proposed_dates')
    def validate_dates(cls, v):
        validate_proposed_dates(v)
        return v

class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    date: datetime
    duration: int
    location: Optional[str] = None
    status: MeetingStatus
    rejection_reason: Optional[str] = None
    manager: Dict[str, Any]  # Basic manager info
    created_at: datetime

class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    limit: int