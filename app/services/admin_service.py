from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import Manager, Employee, Meeting, MeetingStatus
from app.exceptions import CustomException
from app.schemas.admin import ManagerRequestItem 
from app.utils.email import send_manager_approval_email, send_manager_rejection_email

def get_manager_requests(db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = db.query(Manager).filter(Manager.is_approved == False)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Manager.status == status)  # Assuming `status` is a field on Manager model

    # Get the total count of the requests
    total = query.count()

    # Get the list of manager requests (with pagination)
    managers = query.offset(skip).limit(limit).all()

    # Convert Manager objects to ManagerRequestItem Pydantic models
    manager_requests = [
        ManagerRequestItem.from_orm(manager) for manager in managers
    ]

    # Return the result in the structure that matches ManagerRequestListResponse
    return {
        "requests": manager_requests,
        "total": total,
        "page": (skip // limit) + 1,  # Calculate page based on skip/limit
        "limit": limit
    }


def get_all_managers(db: Session, page: int = 1, limit: int = 10):
    """
    Get all approved managers with pagination.

    :param db: Database session
    :param page: Page number (starting from 1)
    :param limit: Maximum number of records per page
    :return: Dictionary with managers, total count, page, and limit
    """
    skip = (page - 1) * limit
    
    # Query for approved managers
    query = db.query(Manager).filter(Manager.is_approved == True)
    
    # Get total count
    total = query.count()
    
    # Get managers with pagination
    managers = query.offset(skip).limit(limit).all()
    
    # Count employees for each manager
    manager_items = []
    for manager in managers:
        employee_count = db.query(func.count(Employee.id)).filter(
            Employee.manager_id == manager.id
        ).scalar()
        
        manager_item = {
            "id": manager.id,
            "email": manager.email,
            "name": manager.name,
            "company_name": manager.company_name,
            "company_size": manager.company_size,
            "phone": manager.phone,
            "profile_picture": manager.profile_picture,
            "is_verified": manager.is_verified,
            "is_approved": manager.is_approved,
            "created_at": manager.created_at,
            "employee_count": employee_count
        }
        manager_items.append(manager_item)
    
    return {
        "managers": manager_items,
        "total": total,
        "page": page,
        "limit": limit
    }

def update_manager_status(db: Session, manager_id: int, status_update):
    """
    Update a manager's approval status.

    :param db: Database session
    :param manager_id: ID of the manager
    :param status_update: ManagerStatusUpdateRequest object
    :return: Updated manager object
    :raises: CustomException if manager not found
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise CustomException(status_code=404, detail="Manager not found")

    is_approved = status_update.status == "approved"
    manager.is_approved = is_approved

    if not is_approved and status_update.reason:
        manager.rejection_reason = status_update.reason

    db.commit()
    db.refresh(manager)

    # Send email notification
    if is_approved:
        send_manager_approval_email(manager.email, manager.name)
    else:
        send_manager_rejection_email(manager.email, manager.name, status_update.reason)

    return manager

def get_manager_details(manager_id: int, db: Session):
    """
    Get detailed information about a manager.

    :param manager_id: ID of the manager
    :param db: Database session
    :return: Manager details with employee and meeting counts
    :raises: CustomException if manager not found
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise CustomException(status_code=404, detail="Manager not found")

    # Count employees
    employee_count = db.query(func.count(Employee.id)).filter(Employee.manager_id == manager_id).scalar()

    # Count meetings
    meeting_count = db.query(func.count(Meeting.id)).filter(Meeting.manager_id == manager_id).scalar()

    # Count pending meetings
    pending_meeting_count = db.query(func.count(Meeting.id)).filter(
        Meeting.manager_id == manager_id,
        Meeting.status == MeetingStatus.PENDING
    ).scalar()

    return {
        "id": manager.id,
        "name": manager.name,
        "email": manager.email,
        "phone": manager.phone,
        "company": manager.company,
        "department": manager.department,
        "is_approved": manager.is_approved,
        "created_at": manager.created_at,
        "employee_count": employee_count,
        "meeting_count": meeting_count,
        "pending_meeting_count": pending_meeting_count
    }

def get_admin_dashboard_stats(db: Session):
    """
    Get statistics for the admin dashboard.

    :param db: Database session
    :return: Dictionary with various statistics
    """
    # Count managers
    total_managers = db.query(func.count(Manager.id)).scalar()
    pending_managers = db.query(func.count(Manager.id)).filter(Manager.is_approved == False).scalar()
    approved_managers = db.query(func.count(Manager.id)).filter(Manager.is_approved == True).scalar()

    # Count employees
    total_employees = db.query(func.count(Employee.id)).scalar()

    # Count meetings
    total_meetings = db.query(func.count(Meeting.id)).scalar()
    pending_meetings = db.query(func.count(Meeting.id)).filter(Meeting.status == MeetingStatus.PENDING).scalar()
    approved_meetings = db.query(func.count(Meeting.id)).filter(Meeting.status == MeetingStatus.APPROVED).scalar()
    completed_meetings = db.query(func.count(Meeting.id)).filter(Meeting.status == MeetingStatus.COMPLETED).scalar()

    # Recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    new_managers = db.query(func.count(Manager.id)).filter(Manager.created_at >= seven_days_ago).scalar()
    new_employees = db.query(func.count(Employee.id)).filter(Employee.created_at >= seven_days_ago).scalar()
    new_meetings = db.query(func.count(Meeting.id)).filter(Meeting.created_at >= seven_days_ago).scalar()

    return {
        "managers": {
            "total": total_managers,
            "pending": pending_managers,
            "approved": approved_managers,
            "new_last_7_days": new_managers
        },
        "employees": {
            "total": total_employees,
            "new_last_7_days": new_employees
        },
        "meetings": {
            "total": total_meetings,
            "pending": pending_meetings,
            "approved": approved_meetings,
            "completed": completed_meetings,
            "new_last_7_days": new_meetings
        }
    }

def delete_manager(manager_id: int, db: Session):
    """
    Delete a manager and all associated data.

    :param manager_id: ID of the manager to delete
    :param db: Database session
    :return: True if deletion was successful
    :raises: CustomException if manager not found
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise CustomException(status_code=404, detail="Manager not found")

    # Delete the manager (cascade should handle associated records)
    db.delete(manager)
    db.commit()

    return True