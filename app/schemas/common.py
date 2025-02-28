from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 10
    sort_by: Optional[str] = None
    sort_desc: bool = False

class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool

class TimeStampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    field: Optional[str] = None

class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None