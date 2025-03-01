from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.database import Meeting, Employee, Manager, MeetingStatus
from app.schemas.meeting import MeetingFilterParams
from app.exceptions import NotFoundException

def get_meetings(
    db: Session,
    user_id: int,
    user_type: str,
    filters: MeetingFilterParams,
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get meetings for a user (manager or employee)

    Args:
        db: Database session
        user_id: ID of the user
        user_type: Type of the user (manager or employee)
        filters: Meeting filter parameters
        page: Page number
        limit: Items per page

    Returns:
        Dict: Meetings with pagination info
    """
    query = db.query(Meeting)

    # Filter by user type
    if user_type == "manager":
        query = query.filter(Meeting.manager_id == user_id)
    elif user_type == "employee":
        query = query.filter(Meeting.employees.any(id=user_id))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type"
        )

    # Apply filters
    if filters.status:
        query = query.filter(Meeting.status == filters.status)
    if filters.start_date:
        query = query.filter(Meeting.date >= filters.start_date)
    if filters.end_date:
        query = query.filter(Meeting.date <= filters.end_date)
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(Meeting.title.ilike(search_term))

    # Get total count
    total = query.count()

    # Get paginated results
    meetings = query.order_by(Meeting.date.desc()).offset((page - 1) * limit).limit(limit).all()

    # Format response
    meeting_list = []
    for meeting in meetings:
        meeting_dict = {
            "id": meeting.id,
            "title": meeting.title,
            "description": meeting.description,
            "date": meeting.date,
            "duration": meeting.duration,
            "location": meeting.location,
            "status": meeting.status,
            "created_by_type": meeting.created_by_type,
            "created_at": meeting.created_at
        }

        # Add manager or employee details based on user type
        if user_type == "manager":
            meeting_dict["employees"] = [
                {
                    "id": employee.id,
                    "name": employee.name,
                    "email": employee.email
                }
                for employee in meeting.employees
            ]
        elif user_type == "employee":
            manager = db.query(Manager).filter(Manager.id == meeting.manager_id).first()
            meeting_dict["manager"] = {
                "id": manager.id,
                "name": manager.name,
                "email": manager.email,
                "company_name": manager.company_name
            }

        meeting_list.append(meeting_dict)

    return {
        "meetings": meeting_list,
        "total": total,
        "page": page,
        "limit": limit
    }

def get_meeting_details(db: Session, meeting_id: int, user_id: int, user_type: str) -> Dict[str, Any]:
    """
    Get details of a specific meeting

    Args:
        db: Database session
        meeting_id: ID of the meeting
        user_id: ID of the user
        user_type: Type of the user (manager or employee)

    Returns:
        Dict: Meeting details
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise NotFoundException("Meeting not found")

    # Check if the user is authorized to view the meeting
    if user_type == "manager" and meeting.manager_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this meeting"
        )
    elif user_type == "employee" and not any(employee.id == user_id for employee in meeting.employees):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this meeting"
        )

    # Format response
    meeting_dict = {
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "date": meeting.date,
        "duration": meeting.duration,
        "location": meeting.location,
        "status": meeting.status,
        "created_by_type": meeting.created_by_type,
        "created_at": meeting.created_at
    }

    # Add manager or employee details based on user type
    if user_type == "manager":
        meeting_dict["employees"] = [
            {
                "id": employee.id,
                "name": employee.name,
                "email": employee.email
            }
            for employee in meeting.employees
        ]
    elif user_type == "employee":
        manager = db.query(Manager).filter(Manager.id == meeting.manager_id).first()
        meeting_dict["manager"] = {
            "id": manager.id,
            "name": manager.name,
            "email": manager.email,
            "company_name": manager.company_name
        }

    return meeting_dict