from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class MeetingBase(BaseModel):
    date: str
    time: str
    client_name: str
    location: str
    employee_name: str
    description: Optional[str] = None

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(MeetingBase):
    status: Optional[str] = None

class Meeting(MeetingBase):
    id: str
    creator_id: str
    status: str = "pending"  # pending, confirmed, cancelled
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True