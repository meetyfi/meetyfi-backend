from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class MeetingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class MeetingLocation(BaseModel):
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    room_number: Optional[str] = None

class MeetingBase(BaseModel):
    date: date
    time: time
    client_name: str = Field(..., min_length=2, max_length=100)
    location: MeetingLocation
    employee_name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    attendees: List[str] = []

class MeetingCreate(MeetingBase):
    @validator('date')
    def validate_date(cls, v):
        if v < date.today():
            raise ValueError('Meeting date cannot be in the past')
        return v

class MeetingUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    client_name: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[MeetingLocation] = None
    employee_name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[MeetingStatus] = None

class MeetingResponse(MeetingBase):
    id: str
    creator_id: str
    status: MeetingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MeetingSearchParams(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    client_name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[MeetingStatus] = None
    employee_name: Optional[str] = None