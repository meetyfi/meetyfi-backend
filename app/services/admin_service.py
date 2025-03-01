from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import Manager, Employee, Meeting, MeetingStatus
from app.exceptions import CustomException
from app.utils.email import send_manager_approval_email, send_manager_rejection_email

def get_manager_requests(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all pending manager signup requests.

    :param db: Database session
    :param skip: Number of records to skip (for pagination)
    :param limit: Maximum number of records to return
    :return: List of pending manager requests
    """
    return db.query(Manager).filter(Manager.is_approved == False).offset(skip).limit(limit).all()

def get_all_managers(db: Session, skip: int = 0, limit: int = 100):
    """
    Get all approved managers with pagination.

    :param db: Database session
    :param skip: Number of records to skip (for pagination)
    :param limit: Maximum number of records to return
    :return: List of approved managers
    """
    return db.query(Manager).filter(Manager.is_approved == True).offset(skip).limit(limit).all()

def update_manager_status(manager_id: int, is_approved: bool, rejection_reason: Optional[str], db: Session):
    """
    Update a manager's approval status.

    :param manager_id: ID of the manager
    :param is_approved: Whether to approve the manager
    :param rejection_reason: Reason for rejection (if not approved)
    :param db: Database session
    :return: Updated manager object
    :raises: CustomException if manager not found
    """
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise CustomException(status_code=404, detail="Manager not found")

    manager.is_approved = is_approved
    if not is_approved and rejection_reason:
        manager.rejection_reason = rejection_reason

    db.commit()
    db.refresh(manager)

    # Send email notification
    if is_approved:
        send_manager_approval_email(manager.email, manager.name)
    else:
        send_manager_rejection_email(manager.email, manager.name, rejection_reason)

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