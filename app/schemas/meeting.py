from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.utils.validators import validate_proposed_dates, validate_meeting_dates

class MeetingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class MeetingCreatorType(str, Enum):
    MANAGER = "manager"
    EMPLOYEE = "employee"

# Client information
class ClientInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None

# Base meeting schema with common fields
class MeetingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    duration: int = Field(..., gt=0, le=480)  # Max 8 hours (in minutes)
    location: Optional[str] = None
    client_info: ClientInfo  # Added client information

# For creating a meeting by a manager
class MeetingCreateRequest(MeetingBase):
    date: datetime
    employee_ids: Optional[List[int]] = None  # Optional for client meetings

# For creating a meeting request by an employee
class MeetingRequestCreate(MeetingBase):
    proposed_dates: List[datetime] = Field(..., min_items=1, max_items=5)

    @field_validator('proposed_dates')
    def validate_dates(cls, v):
        validate_proposed_dates(v)
        return v

# For selecting a date from proposed dates (by manager)
class MeetingDateSelection(BaseModel):
    selected_date: datetime

# For updating meeting status
class MeetingStatusUpdate(BaseModel):
    status: MeetingStatus
    reason: Optional[str] = None

    @field_validator('status')
    def validate_status(cls, v, values, **kwargs):
        if v not in [MeetingStatus.ACCEPTED, MeetingStatus.REJECTED, MeetingStatus.CANCELLED]:
            raise ValueError(f"Invalid status: {v}")
        return v

# Employee in meeting response
class EmployeeInMeeting(BaseModel):
    id: int
    name: str
    email: str
    role: Optional[str] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None

# Manager in meeting response
class ManagerInMeeting(BaseModel):
    id: int
    name: str
    email: str
    company_name: str
    profile_picture: Optional[str] = None

# Client information response
class ClientInfoResponse(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

# Meeting response for both manager and employee views
class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    date: datetime
    duration: int
    location: Optional[str] = None
    status: MeetingStatus
    rejection_reason: Optional[str] = None
    created_by_type: MeetingCreatorType
    created_at: datetime
    updated_at: Optional[datetime] = None
    client_info: ClientInfoResponse  # Added client information
    
    # These fields will be populated based on the viewer's role
    employees: Optional[List[EmployeeInMeeting]] = None
    manager: Optional[ManagerInMeeting] = None

    class Config:
        orm_mode = True

# Meeting list response with pagination
class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    limit: int

# Meeting statistics for managers
class MeetingStatistics(BaseModel):
    total_meetings: int
    pending_meetings: int
    accepted_meetings: int
    rejected_meetings: int
    cancelled_meetings: int
    upcoming_meetings: int
    past_meetings: int

# Meeting filter parameters
class MeetingFilterParams(BaseModel):
    status: Optional[MeetingStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    employee_id: Optional[int] = None
    search: Optional[str] = None

# Proposed dates response for employee meeting requests
class ProposedDate(BaseModel):
    date: datetime
    is_selected: bool = False

class MeetingWithProposedDates(MeetingResponse):
    proposed_dates: List[ProposedDate]

# Meeting reminder
class MeetingReminder(BaseModel):
    meeting_id: int
    title: str
    date: datetime
    location: Optional[str] = None
    minutes_until: int

# Meeting calendar event
class CalendarEvent(BaseModel):
    id: int
    title: str
    start: datetime
    end: datetime
    status: MeetingStatus
    location: Optional[str] = None
    description: Optional[str] = None
    client_name: str  # Added client name for calendar events
    
    class Config:
        orm_mode = True

# Calendar events response
class CalendarEventsResponse(BaseModel):
    events: List[CalendarEvent]