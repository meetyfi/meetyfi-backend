from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.schemas.employee import (
    EmployeeProfileResponse, EmployeeProfileUpdate,
    ManagerResponse, ManagerAvailabilityResponse,
    LocationCreateRequest, MeetingRequestCreate,
    MeetingListResponse
)
from app.services.employee_service import (
    get_employee_profile, update_employee_profile,
    get_manager_details, get_manager_availability,
    post_location, request_meeting, get_employee_meetings
)
from app.dependencies import get_db, get_current_employee

router = APIRouter()

@router.get("/profile", response_model=EmployeeProfileResponse)
async def get_profile(
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get employee profile"""
    return get_employee_profile(db, current_employee.id)

@router.put("/profile", response_model=EmployeeProfileResponse)
async def update_profile(
    profile_update: EmployeeProfileUpdate,
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Update employee profile"""
    return update_employee_profile(db, current_employee.id, profile_update)

@router.get("/managers", response_model=ManagerResponse)
async def get_manager(
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get manager details"""
    return get_manager_details(db, current_employee.id)

@router.get("/managers/availability", response_model=ManagerAvailabilityResponse)
async def get_availability(
    date: date,
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get manager availability"""
    return get_manager_availability(db, current_employee.id, date)

@router.post("/location", response_model=dict)
async def create_location(
    location: LocationCreateRequest,
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Post current location"""
    location_id = post_location(db, current_employee.id, location)
    return {"message": "Location updated successfully", "location_id": location_id}

@router.post("/meetings", response_model=dict)
async def create_meeting_request(
    meeting: MeetingRequestCreate,
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Request a meeting with manager"""
    meeting_id = request_meeting(db, current_employee.id, meeting)
    return {"message": "Meeting request sent successfully", "meeting_id": meeting_id}

@router.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get all meetings"""
    return get_employee_meetings(db, current_employee.id, status, date_from, date_to, page, limit)