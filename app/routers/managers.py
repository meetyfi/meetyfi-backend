from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.schemas.manager import (
    ManagerProfileResponse, ManagerProfileUpdate,
    EmployeeCreateRequest, EmployeeResponse, EmployeeListResponse,
    EmployeeLocationResponse, MeetingCreateRequest, MeetingResponse,
    MeetingListResponse, MeetingStatusUpdateRequest
)
from app.services.manager_service import (
    get_manager_profile, update_manager_profile,
    add_employee, get_employees, get_employee_by_id,
    delete_employee, get_employee_locations,
    create_meeting, get_meetings, update_meeting_status,
    
)
from app.dependencies import get_db, get_current_manager
import logging


logger = logging.getLogger(__name__)


router = APIRouter()

@router.get("/profile", response_model=ManagerProfileResponse)
async def get_profile(
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Get manager profile"""
    return get_manager_profile(db, current_manager.id)

@router.put("/profile", response_model=ManagerProfileResponse)
async def update_profile(
    profile_update: ManagerProfileUpdate,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Update manager profile"""
    return update_manager_profile(db, current_manager.id, profile_update)

@router.post("/employees", response_model=dict)
async def create_employee(
    employee: EmployeeCreateRequest,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Add a new employee"""
    try:
        employee_id = add_employee(db, current_manager.id, employee)
        return {
            "message": "Employee added successfully",
            "employee_id": employee_id,
            "email_sent": True
        }
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        if "email" in str(e).lower():
            # If it's an email-related error but employee was created
            return {
                "message": "Employee added successfully, but invitation email could not be sent",
                "employee_id": employee_id,
                "email_sent": False
            }
        # Re-raise other exceptions
        raise

@router.get("/employees", response_model=EmployeeListResponse)
async def list_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Get all employees under a manager"""
    return get_employees(db, current_manager.id, page, limit)

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Get specific employee details"""
    # Note the order: db, manager_id, employee_id
    return get_employee_by_id(db, current_manager.id, employee_id)

@router.delete("/employees/{employee_id}")
async def remove_employee(
    employee_id: int,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Delete an employee"""
    delete_employee(db, current_manager.id, employee_id)
    return {"message": "Employee deleted successfully"}

@router.get("/employees/locations", response_model=EmployeeLocationResponse)
async def view_employee_locations(
    date: Optional[date] = None,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """View employee locations"""
    return get_employee_locations(db, current_manager.id, date)

@router.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """View all meetings"""
    return get_meetings(db, current_manager.id, status, date_from, date_to, page, limit)

@router.post("/meetings", response_model=dict)
async def schedule_meeting(
    meeting: MeetingCreateRequest,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Create a new meeting"""
    meeting_id = create_meeting(db, current_manager.id, meeting)
    return {"message": "Meeting created successfully", "meeting_id": meeting_id}

@router.put("/meetings/{meeting_id}/status", response_model=dict)
async def update_meeting(
    meeting_id: int,
    status_update: MeetingStatusUpdateRequest,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Accept or reject meeting"""
    meeting = update_meeting_status(db, current_manager.id, meeting_id, status_update)
    return {"message": f"Meeting {status_update.status}", "meeting": meeting}

@router.delete("/meetings/{meeting_id}")
async def cancel_meeting(
    meeting_id: int,
    current_manager = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Cancel a meeting"""
    delete_meeting(db, current_manager.id, meeting_id)
    return {"message": "Meeting cancelled successfully"}