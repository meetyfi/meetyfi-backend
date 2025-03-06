from pydantic import BaseModel, EmailStr, Field, field_validator
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

    @field_validator('phone')
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

class LocationData(BaseModel):
    latitude: float
    longitude: float
    address: str
    timestamp: datetime

    class Config:
        from_attributes = True

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
    location: Optional[LocationData] = None

    class Config:
        from_attributes = True

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

# Client information for meetings
class ClientInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None

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
    employee_ids: Optional[List[int]] = None  # Optional for client meetings
    location: Optional[str] = None
    client_info: ClientInfo  # Added client information

class EmployeeInMeeting(BaseModel):
    id: int
    name: str
    email: str
    role: Optional[str] = None
    department: Optional[str] = None

class ClientInfoResponse(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

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
    client_info: ClientInfoResponse  # Added client information
    employees: List[EmployeeInMeeting]

class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    limit: int

class MeetingStatusUpdateRequest(BaseModel):
    status: str  # Use str instead of enum to avoid case issues
    reason: Optional[str] = None

    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "accepted", "rejected", "cancelled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v.lower()  # Always return lowercase