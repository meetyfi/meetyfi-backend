from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.database import Manager, Employee, Meeting, Location, MeetingStatus, EmployeeMeeting, ProposedDate
from app.schemas.manager import (
    ManagerProfileUpdate, MeetingCreateRequest, MeetingStatusUpdateRequest
)
from app.exceptions import UserNotFoundException, PermissionDeniedException
from app.utils.email import (
    send_meeting_notification, send_meeting_status_update, send_employee_verification_email
)
from app.utils.security import generate_verification_token
import logging


logger = logging.getLogger(__name__)

def get_manager_profile(db: Session, manager_id: int) -> Dict[str, Any]:
    """
    Get manager profile
    
    Args:
        db: Database session
        manager_id: ID of the manager
        
    Returns:
        Dict: Manager profile data
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise UserNotFoundException("Manager not found")
    
    return {
        "id": manager.id,
        "email": manager.email,
        "name": manager.name,
        "company_name": manager.company_name,
        "company_size": manager.company_size,
        "is_verified": manager.is_verified,
        "is_approved": manager.is_approved,
        "phone": manager.phone,
        "profile_picture": manager.profile_picture,
        "created_at": manager.created_at
    }

def update_manager_profile(db: Session, manager_id: int, profile_data: ManagerProfileUpdate) -> Dict[str, Any]:
    """
    Update manager profile
    
    Args:
        db: Database session
        manager_id: ID of the manager
        profile_data: Profile update data
        
    Returns:
        Dict: Updated manager profile
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise UserNotFoundException("Manager not found")
    
    # Update fields if provided
    if profile_data.name is not None:
        manager.name = profile_data.name
    if profile_data.phone is not None:
        manager.phone = profile_data.phone
    if profile_data.profile_picture is not None:
        manager.profile_picture = profile_data.profile_picture
    
    db.commit()
    db.refresh(manager)
    
    # Return updated profile
    return get_manager_profile(db, manager_id)

def get_employees(db: Session, manager_id: int, page: int = 1, limit: int = 10, search: Optional[str] = None) -> Dict[str, Any]:
    """
    Get employees for a manager with their latest location

    Args:
        db: Database session
        manager_id: ID of the manager
        page: Page number
        limit: Items per page
        search: Search term for name or email

    Returns:
        Dict: Employees with pagination info and location data
    """
    query = db.query(Employee).filter(Employee.manager_id == manager_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Employee.name.ilike(search_term),
                Employee.email.ilike(search_term),
                Employee.role.ilike(search_term),
                Employee.department.ilike(search_term)
            )
        )

    total = query.count()
    employees = query.order_by(Employee.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # Get all employee IDs for the current page
    employee_ids = [employee.id for employee in employees]
    
    # Add debug logging
    logger.info(f"Fetching locations for employee IDs: {employee_ids}")

    # Create a dictionary to store the latest location for each employee
    location_map = {}

    # Directly query the latest location for each employee
    for employee_id in employee_ids:
        latest_location = db.query(Location).filter(
            Location.employee_id == employee_id
        ).order_by(Location.timestamp.desc()).first()

        if latest_location:
            logger.info(f"Found location for employee {employee_id}: {latest_location.latitude}, {latest_location.longitude}")
            location_map[employee_id] = latest_location
        else:
            logger.info(f"No location found for employee {employee_id}")

    employee_list = []
    for employee in employees:
        # Get location data if available
        location_data = None
        if employee.id in location_map:
            loc = location_map[employee.id]
            location_data = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "timestamp": loc.timestamp
            }

        employee_dict = {
            "id": employee.id,
            "email": employee.email,
            "name": employee.name,
            "role": employee.role,
            "department": employee.department,
            "phone": employee.phone,
            "profile_picture": employee.profile_picture,
            "is_verified": employee.is_verified,
            "created_at": employee.created_at,
            "location": location_data  # Add the location data
        }
        employee_list.append(employee_dict)

    return {
        "employees": employee_list,
        "total": total,
        "page": page,
        "limit": limit
    }

def get_employee_locations(db: Session, manager_id: int, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get employee locations for a manager
    
    Args:
        db: Database session
        manager_id: ID of the manager
        hours: Hours to look back for locations
        
    Returns:
        List: Employee locations
    """
    # Get all employees for this manager
    employees = db.query(Employee).filter(Employee.manager_id == manager_id).all()
    employee_ids = [employee.id for employee in employees]
    
    # Get latest location for each employee within the time window
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Subquery to get the latest location for each employee
    latest_locations = db.query(
        Location.employee_id,
        func.max(Location.timestamp).label('max_timestamp')
    ).filter(
        Location.employee_id.in_(employee_ids),
        Location.timestamp >= time_threshold
    ).group_by(Location.employee_id).subquery()
    
    # Join with locations to get the full location data
    # Join with locations to get the full location data
    locations = db.query(
        Location.employee_id,
        Location.latitude,
        Location.longitude,
        Location.address,
        Location.timestamp
    ).join(
        latest_locations,
        and_(
            Location.employee_id == latest_locations.c.employee_id,
            Location.timestamp == latest_locations.c.max_timestamp
        )
    ).all()

    # Format the response
    location_list = []
    for location in locations:
        employee = db.query(Employee).filter(Employee.id == location.employee_id).first()
        location_list.append({
            "employee_id": location.employee_id,
            "name": employee.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address,
            "timestamp": location.timestamp
        })

    return location_list

def create_meeting(db: Session, manager_id: int, meeting_data: MeetingCreateRequest) -> int:
    """
    Create a new meeting by a manager

    Args:
        db: Database session
        manager_id: ID of the manager
        meeting_data: Meeting creation data

    Returns:
        int: ID of the created meeting
    """
    # Verify all employees exist and belong to this manager
    employees = db.query(Employee).filter(
        and_(
            Employee.id.in_(meeting_data.employee_ids),
            Employee.manager_id == manager_id
        )
    ).all()

    if len(employees) != len(meeting_data.employee_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more employees do not belong to this manager"
        )

    # Create the meeting
    new_meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        date=meeting_data.date,
        duration=meeting_data.duration,
        location=meeting_data.location,
        status=MeetingStatus.PENDING,
        created_by_id=manager_id,
        created_by_type="manager"
    )

    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # Add employees to the meeting
    for employee in employees:
        new_meeting.employees.append(employee)

    db.commit()

    # Notify employees about the meeting
    for employee in employees:
        send_meeting_notification(
            employee.email,
            employee.name,
            new_meeting.title,
            new_meeting.date,
            new_meeting.location
        )

    return new_meeting.id

def update_meeting_status(
    db: Session,
    manager_id: int,
    meeting_id: int,
    status_data: MeetingStatusUpdateRequest
) -> None:
    """
    Update the status of a meeting

    Args:
        db: Database session
        manager_id: ID of the manager
        meeting_id: ID of the meeting
        status_data: Status update data
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise UserNotFoundException("Meeting not found")

    # Check if the manager is authorized to update the meeting
    if meeting.created_by_id != manager_id or meeting.created_by_type != "manager":
        raise PermissionDeniedException("You are not authorized to update this meeting")

    # Validate status transition
    MeetingStatusUpdateRequest(meeting.status, status_data.status)

    # Update the meeting status
    meeting.status = status_data.status
    meeting.rejection_reason = status_data.reason if status_data.status == MeetingStatus.REJECTED else None
    meeting.updated_at = datetime.utcnow()
    db.commit()

    # Notify employees about the status update
    for employee in meeting.employees:
        send_meeting_status_update(
            employee.email,
            employee.name,
            meeting.title,
            meeting.status,
            meeting.rejection_reason
        )

from app.utils.email import send_employee_verification_email
from app.utils.security import generate_verification_token
from datetime import datetime, timedelta

def add_employee(db: Session, manager_id: int, employee_data):
    """
    Add a new employee under a manager.
    """
    logger.info(f"Adding employee with email {employee_data.email} for manager {manager_id}")

    # Check if an employee with the same email already exists
    existing_employee = db.query(Employee).filter(Employee.email == employee_data.email).first()
    if existing_employee:
        logger.warning(f"Employee with email {employee_data.email} already exists")
        raise HTTPException(status_code=400, detail="Employee with this email already exists.")

    # Get manager details for the email
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        logger.error(f"Manager with ID {manager_id} not found")
        raise HTTPException(status_code=404, detail="Manager not found")

    logger.info(f"Found manager: {manager.name}, company: {manager.company_name}")

    # Generate verification token
    verification_token = generate_verification_token()
    token_expiry = datetime.utcnow() + timedelta(days=7)

    logger.info(f"Generated verification token: {verification_token[:10]}... (expires: {token_expiry})")

    # Create a new employee
    try:
        new_employee = Employee(
            name=employee_data.name,
            email=employee_data.email,
            role=employee_data.role if hasattr(employee_data, 'role') else None,
            department=employee_data.department if hasattr(employee_data, 'department') else None,
            manager_id=manager_id,
            verification_token=verification_token,
            token_expiry=token_expiry,
            is_verified=False
        )

        logger.info("Adding employee to database")
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        logger.info(f"Employee added with ID: {new_employee.id}")

        # Send invitation email
        logger.info("Attempting to send verification email")
        try:
            email_sent = send_employee_verification_email(
                email=employee_data.email,
                manager_name=manager.name,
                company_name=manager.company_name,
                verification_token=verification_token
            )

            if email_sent:
                logger.info(f"Verification email sent successfully to {employee_data.email}")
            else:
                logger.warning(f"Failed to send verification email to {employee_data.email}")
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            # Continue even if email fails - we've already created the employee

        return new_employee.id
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating employee: {str(e)}")
        raise


def get_employee_by_id(db: Session, manager_id: int, employee_id: int):
    """
    Get an employee by ID, ensuring they belong to the specified manager.
    """
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.manager_id == manager_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found or doesn't belong to this manager"
        )

    # Return a dictionary instead of the SQLAlchemy model
    return {
        "id": employee.id,
        "email": employee.email,
        "name": employee.name,
        "role": employee.role,
        "department": employee.department,
        "phone": employee.phone,
        "profile_picture": employee.profile_picture,
        "is_verified": employee.is_verified,
        "created_at": employee.created_at
    }

def delete_employee(employee_id: int, manager_id: int, db: Session):
    """
    Delete an employee by ID, ensuring they belong to the specified manager.
    
    :param employee_id: ID of the employee to delete
    :param manager_id: ID of the manager
    :param db: Database session
    :return: True if deletion was successful
    :raises: CustomException if employee not found or doesn't belong to the manager
    """
    # First, check if the employee exists and belongs to this manager
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.manager_id == manager_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found or doesn't belong to this manager"
        )
    
    # Delete the employee
    db.delete(employee)
    db.commit()
    
    return True


def select_meeting_date(
    db: Session,
    manager_id: int,
    meeting_id: int,
    selected_date: datetime
) -> None:
    """
    Select a date for a meeting from proposed dates
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.manager_id != manager_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this meeting")
    
    proposed_dates = db.query(ProposedDate).filter(ProposedDate.meeting_id == meeting_id).all()
    if not any(date.date == selected_date for date in proposed_dates):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected date is not in the proposed dates")

    meeting.date = selected_date
    for date in proposed_dates:
        date.is_selected = (date.date == selected_date)

    db.commit()

    for employee in meeting.employees:
        send_meeting_notification(employee.email, employee.name, meeting.title, selected_date)

def get_meetings(
    db: Session,  # ✅ Add this parameter
    manager_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None, 
    employee_id: Optional[int] = None,
) -> List[Meeting]:
    """
    Get meetings for a manager with optional filtering by status and employee.
    """
    query = db.query(Meeting).filter(Meeting.manager_id == manager_id)
    
    if status:
        query = query.filter(Meeting.status == status)
    
    if employee_id:
        query = query.join(EmployeeMeeting).filter(EmployeeMeeting.meeting_id == Meeting.id, EmployeeMeeting.employee_id == employee_id)
    
    meetings = query.order_by(Meeting.date.desc()).offset(skip).limit(limit).all()
    
    return meetings