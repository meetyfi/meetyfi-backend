from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str

class LocationCreate(LocationBase):
    pass

class LocationInDB(LocationBase):
    id: int
    employee_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class EmployeeLocation(BaseModel):
    employee_id: int
    name: str
    latitude: float
    longitude: float
    address: str
    timestamp: datetime

    class Config:
        orm_mode = True

class EmployeeLocationResponse(BaseModel):
    employee_locations: list[EmployeeLocation]