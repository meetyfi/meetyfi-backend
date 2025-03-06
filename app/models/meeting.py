# In app/schemas/meeting.py (or create this file if it doesn't exist)

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MeetingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ClientInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None

class MeetingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    duration: int = Field(..., gt=0, le=480)  # Max 8 hours
    location: Optional[str] = None
    client_info: ClientInfo

class MeetingCreate(MeetingBase):
    date: datetime
    employee_ids: Optional[List[int]] = None  # Optional for manager-created meetings

class MeetingRequest(MeetingBase):
    proposed_dates: List[datetime] = Field(..., min_items=1, max_items=5)