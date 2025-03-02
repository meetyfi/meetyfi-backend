from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ManagerStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"

class ManagerRequestItem(BaseModel):
    id: int
    email: str
    name: str
    company_name: str
    company_size: int
    phone: Optional[str] = None
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True 

class ManagerRequestListResponse(BaseModel):
    requests: List[ManagerRequestItem]
    total: int
    page: int
    limit: int

class ManagerStatusUpdateRequest(BaseModel):
    status: ManagerStatus
    reason: Optional[str] = None

class ManagerListItem(BaseModel):
    id: int
    email: str
    name: str
    company_name: str
    company_size: int
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool
    is_approved: bool
    created_at: datetime
    employee_count: int

class ManagerListResponse(BaseModel):
    managers: List[ManagerListItem]
    total: int
    page: int
    limit: int