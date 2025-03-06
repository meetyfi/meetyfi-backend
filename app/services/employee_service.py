from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date, timezone, time

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


def get_manager_availability(db: Session, manager_id: int, date_param: date, time_param: time) -> dict:
    """
    Check if a manager is available at a specific date and time

    Args:
        db: Database session
        manager_id: ID of the manager
        date_param: Date to check availability
        time_param: Time to check availability

    Returns:
        dict: Manager's availability status for the specific date and time
    """
    # Check if manager exists
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise UserNotFoundException("Manager not found")

    # Round time to nearest 30-minute slot
    minutes = time_param.minute
    if minutes < 30:
        rounded_minutes = 0
    else:
        rounded_minutes = 30

    slot_time = datetime.combine(date_param, time(hour=time_param.hour, minute=rounded_minutes))
    next_slot = slot_time + timedelta(minutes=30)

    # Get meetings that might overlap with this time slot
    meetings = db.query(Meeting).filter(
        Meeting.manager_id == manager_id,
        Meeting.status.in_(["accepted", "pending"]),
        Meeting.date <= next_slot,
        Meeting.date + timedelta(minutes=Meeting.duration) >= slot_time
    ).all()

    # Check if this specific time slot overlaps with any meeting
    is_available = True
    for meeting in meetings:
        meeting_start = meeting.date
        meeting_end = meeting_start + timedelta(minutes=meeting.duration)

        if (slot_time >= meeting_start and slot_time < meeting_end) or \
           (next_slot > meeting_start and next_slot <= meeting_end) or \
           (slot_time <= meeting_start and next_slot >= meeting_end):
            is_available = False
            break

    # Return simple availability status
    return {
        "date": date_param.isoformat(),
        "time": time_param.strftime("%H:%M"),
        "status": "available" if is_available else "unavailable",
        "available_slots": {}  # Empty dict to satisfy the response model
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
    Request a meeting with the manager and a client

    Args:
        db: Database session
        employee_id: ID of the employee
        meeting_data: Meeting request data

    Returns:
        int: ID of the created meeting
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise UserNotFoundException("Employee not found")

    # Get manager details
    manager = db.query(Manager).filter(Manager.id == employee.manager_id).first()
    if not manager:
        raise UserNotFoundException("Manager not found")

    # Create new meeting with client info
    new_meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        duration=meeting_data.duration,
        location=meeting_data.location,
        status="pending",
        created_by_id=employee_id,
        created_by_type="employee",
        manager_id=employee.manager_id,
        client_name=meeting_data.client_info.name,
        client_email=meeting_data.client_info.email,
        client_phone=meeting_data.client_info.phone
    )

    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # Add proposed dates
    for date_obj in meeting_data.proposed_dates:
        proposed_date = ProposedDate(
            meeting_id=new_meeting.id,
            date=date_obj,
            proposed_by_id=employee_id,
            proposed_by_type="employee",
            status="pending"  # Use string instead of enum
        )
        db.add(proposed_date)

    db.commit()

    # Since we need to pass a single datetime to send_meeting_notification,
    # use the first proposed date for the notification
    if meeting_data.proposed_dates and len(meeting_data.proposed_dates) > 0:
        first_date = meeting_data.proposed_dates[0]
        
        # Send notification to manager
        send_meeting_notification(
            manager.email,                # email
            meeting_data.title,           # meeting_title
            first_date,                   # meeting_date (using first proposed date)
            meeting_data.location,        # meeting_location
            f"{employee.name}",           # created_by
            True                          # is_request
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

        # Include client information
        client_info = {
            "name": meeting.client_name,
            "email": meeting.client_email,
            "phone": meeting.client_phone
        }

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
            "client_info": client_info,
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