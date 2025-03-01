from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.database import Employee, Manager, Meeting, Location, MeetingStatus, ProposedDate
from app.schemas.employee import (
    EmployeeProfileUpdate, LocationCreateRequest, MeetingRequestCreate
)
from app.exceptions import NotFoundException, PermissionDeniedException
from app.utils.email import send_meeting_notification

def get_employee_profile(db: Session, employee_id: int) -> Dict[str, Any]:
    """
    Get employee profile with manager info
    
    Args:
        db: Database session
        employee_id: ID of the employee
        
    Returns:
        Dict: Employee profile data
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    manager = db.query(Manager).filter(Manager.id == employee.manager_id).first()
    if not manager:
        raise NotFoundException("Manager not found")
    
    return {
        "id": employee.id,
        "email": employee.email,
        "name": employee.name,
        "role": employee.role,
        "department": employee.department,
        "phone": employee.phone,
        "profile_picture": employee.profile_picture,
        "is_verified": employee.is_verified,
        "created_at": employee.created_at,
        "manager": {
            "id": manager.id,
            "name": manager.name,
            "email": manager.email,
            "company_name": manager.company_name,
            "phone": manager.phone,
            "profile_picture": manager.profile_picture
        }
    }


def get_manager_availability(manager_id: int, start_date: datetime, end_date: datetime, db: Session):
    """
    Get a manager's availability within a specified date range.

    :param manager_id: ID of the manager
    :param start_date: Start date for the availability check
    :param end_date: End date for the availability check
    :param db: Database session
    :return: List of time slots when the manager is available
    """
    # Get all meetings for the manager within the date range
    meetings = db.query(Meeting).filter(
        Meeting.manager_id == manager_id,
        Meeting.date >= start_date,
        Meeting.date <= end_date,
        Meeting.status.in_([MeetingStatus.APPROVED, MeetingStatus.PENDING])
    ).all()

    # Create a list of busy time slots based on meetings
    busy_slots = []
    for meeting in meetings:
        meeting_start = meeting.date
        meeting_end = meeting_start + timedelta(minutes=meeting.duration)
        busy_slots.append({
            "start": meeting_start,
            "end": meeting_end,
            "title": meeting.title
        })

    # Define working hours (e.g., 9 AM to 5 PM)
    working_start_hour = 9
    working_end_hour = 17

    # Generate available time slots
    available_slots = []
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59)

    while current_date <= end_date:
        # Skip weekends (assuming Monday=0, Sunday=6)
        if current_date.weekday() >= 5:  # Saturday or Sunday
            current_date += timedelta(days=1)
            continue

        # Start from working hours
        day_start = current_date.replace(hour=working_start_hour, minute=0)
        day_end = current_date.replace(hour=working_end_hour, minute=0)

        # Check availability in 30-minute increments
        slot_start = day_start
        while slot_start < day_end:
            slot_end = slot_start + timedelta(minutes=30)
            
            # Check if this slot overlaps with any busy slot
            is_available = True
            for busy in busy_slots:
                if (slot_start < busy["end"] and slot_end > busy["start"]):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start": slot_start,
                    "end": slot_end
                })
            
            slot_start = slot_end
        
        # Move to next day
        current_date += timedelta(days=1)

    return {
        "manager_id": manager_id,
        "available_slots": available_slots,
        "busy_slots": busy_slots
    }

    
def update_employee_profile(db: Session, employee_id: int, profile_data: EmployeeProfileUpdate) -> Dict[str, Any]:
    """
    Update employee profile
    
    Args:
        db: Database session
        employee_id: ID of the employee
        profile_data: Profile update data
        
    Returns:
        Dict: Updated employee profile
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    # Update fields if provided
    if profile_data.name is not None:
        employee.name = profile_data.name
    if profile_data.phone is not None:
        employee.phone = profile_data.phone
    if profile_data.profile_picture is not None:
        employee.profile_picture = profile_data.profile_picture
    
    db.commit()
    db.refresh(employee)
    
    # Return updated profile
    return get_employee_profile(db, employee_id)

def get_manager_details(db: Session, employee_id: int) -> Dict[str, Any]:
    """
    Get manager details for an employee
    
    Args:
        db: Database session
        employee_id: ID of the employee
        
    Returns:
        Dict: Manager details
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    manager = db.query(Manager).filter(Manager.id == employee.manager_id).first()
    if not manager:
        raise NotFoundException("Manager not found")
    
    return {
        "id": manager.id,
        "name": manager.name,
        "email": manager.email,
        "company_name": manager.company_name,
        "phone": manager.phone,
        "profile_picture": manager.profile_picture
    }

def post_location(db: Session, employee_id: int, location_data: LocationCreateRequest) -> Dict[str, Any]:
    """
    Post employee's current location
    
    Args:
        db: Database session
        employee_id: ID of the employee
        location_data: Location data
        
    Returns:
        Dict: Created location data
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    new_location = Location(
        employee_id=employee_id,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        address=location_data.address,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return {
        "id": new_location.id,
        "latitude": new_location.latitude,
        "longitude": new_location.longitude,
        "address": new_location.address,
        "timestamp": new_location.timestamp
    }

def request_meeting(db: Session, employee_id: int, meeting_data: MeetingRequestCreate) -> int:
    """
    Request a meeting with the manager
    
    Args:
        db: Database session
        employee_id: ID of the employee
        meeting_data: Meeting request data
        
    Returns:
        int: ID of the created meeting
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    # Create new meeting
    new_meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        duration=meeting_data.duration,
        location=meeting_data.location,
        status=MeetingStatus.PENDING,
        created_by_id=employee_id,
        created_by_type="employee",
        manager_id=employee.manager_id
    )
    
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    
    # Add proposed dates
    for date in meeting_data.proposed_dates:
        proposed_date = ProposedDate(
            meeting_id=new_meeting.id,
            date=date,
            is_selected=False
        )
        db.add(proposed_date)
    
    db.commit()
    
    # Get manager details
    manager = db.query(Manager).filter(Manager.id == employee.manager_id).first()
    
    # Send notification to manager
    send_meeting_request_notification(
        manager.email,
        manager.name,
        employee.name,
        new_meeting.title,
        meeting_data.proposed_dates,
        new_meeting.id
    )
    
    return new_meeting.id

def get_employee_meetings(db: Session, employee_id: int, page: int = 1, limit: int = 10, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get meetings for an employee
    
    Args:
        db: Database session
        employee_id: ID of the employee
        page: Page number
        limit: Items per page
        status: Filter by meeting status
        
    Returns:
        Dict: Meetings with pagination info
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise NotFoundException("Employee not found")
    
    # Base query for meetings where employee is involved
    query = db.query(Meeting).filter(
        or_(
            and_(
                Meeting.created_by_id == employee_id,
                Meeting.created_by_type == "employee"
            ),
            Meeting.employees.any(id=employee_id)
        )
    )
    
    # Apply status filter if provided
    if status:
        query = query.filter(Meeting.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    meetings = query.order_by(Meeting.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Format response
    meeting_list = []
    for meeting in meetings:
        # Get manager details
        manager = db.query(Manager).filter(Manager.id == meeting.manager_id).first()
        
        # Get proposed dates if this is an employee-created meeting
        proposed_dates = []
        if meeting.created_by_type == "employee" and meeting.created_by_id == employee_id:
            date_records = db.query(ProposedDate).filter(ProposedDate.meeting_id == meeting.id).all()
            proposed_dates = [
                {
                    "date": date.date,
                    "is_selected": date.is_selected
                }
                for date in date_records
            ]
        
        meeting_dict = {
            "id": meeting.id,
            "title": meeting.title,
            "description": meeting.description,
            "date": meeting.date,
            "duration": meeting.duration,
            "location": meeting.location,
            "status": meeting.status,
            "rejection_reason": meeting.rejection_reason,
            "created_by_type": meeting.created_by_type,
            "created_at": meeting.created_at,
            "manager": {
                "id": manager.id,
                "name": manager.name,
                "email": manager.email,
                "company_name": manager.company_name,
                "profile_picture": manager.profile_picture
            }
        }
        
        if proposed_dates:
            meeting_dict["proposed_dates"] = proposed_dates
        
        meeting_list.append(meeting_dict)
    
    return {
        "meetings": meeting_list,
        "total": total,
        "page": page,
        "limit": limit
    }

def cancel_meeting(db: Session, employee_id: int, meeting_id: int) -> None:
    """
    Cancel a meeting requested by the employee
    
    Args:
        db: Database session
        employee_id: ID of the employee
        meeting_id: ID of the meeting
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise NotFoundException("Meeting not found")
    
    # Check if employee is the creator of the meeting
    if meeting.created_by_id != employee_id or meeting.created_by_type != "employee":
        raise PermissionDeniedException("You can only cancel meetings you created")
    
    # Check if meeting can be cancelled
    if meeting.status != MeetingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel meeting with status: {meeting.status}"
        )
    
    # Update meeting status
    meeting.status = MeetingStatus.CANCELLED
    meeting.updated_at = datetime.utcnow()
    db.commit()