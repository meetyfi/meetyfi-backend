from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MeetingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class MeetingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    duration: int = Field(..., gt=0, le=480)  # Max 8 hours
    location: Optional[str] = None

class MeetingCreate(MeetingBase):
    date: datetime
    employee_ids: List[int] = Field(..., min_items=1)

class MeetingRequest(MeetingBase):
    proposed_dates: List[datetime] = Field(..., min_items=1, max_items=5)

class MeetingInDB(MeetingBase):
    id: int
    date: datetime
    status: MeetingStatus
    rejection_reason: Optional[str] = None
    manager_id: int
    created_by_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class MeetingWithEmployees(MeetingInDB):
    employees: List[dict]

class MeetingStatusUpdate(BaseModel):
    status: MeetingStatus
    reason: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        if v not in [MeetingStatus.ACCEPTED, MeetingStatus.REJECTED, MeetingStatus.CANCELLED]:
            raise ValueError(f"Invalid status: {v}")
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
    created_by_type: str
    created_at: datetime
    employees: List[dict]

    class Config:
        orm_mode = True

class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    limit: int