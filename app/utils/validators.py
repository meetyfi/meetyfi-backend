import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import phonenumbers

from app.exceptions import ValidationException

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
        
    Raises:
        ValidationException: If email is invalid
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationException("Invalid email format")
    return True

class MeetingStatusTransitionValidator:
    @staticmethod
    def validate(current_status: str, new_status: str) -> bool:
        """
        Validate if a status transition is allowed
        
        Args:
            current_status: Current meeting status
            new_status: New meeting status
            
        Returns:
            True if transition is valid, raises exception otherwise
        """
        # Define allowed transitions
        allowed_transitions = {
            "pending": ["accepted", "rejected", "cancelled"],
            "accepted": ["cancelled"],
            "rejected": [],  # No transitions allowed from rejected
            "cancelled": []  # No transitions allowed from cancelled
        }
        
        # Convert to lowercase for comparison
        current = current_status.lower()
        new = new_status.lower()
        
        if current not in allowed_transitions:
            raise ValueError(f"Invalid current status: {current}")
            
        if new not in allowed_transitions[current]:
            raise ValueError(f"Cannot transition from {current} to {new}")
            
        return True

def validate_password(password: str) -> bool:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        bool: True if password is valid, False otherwise
        
    Raises:
        ValidationException: If password is invalid
    """
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationException("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationException("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        raise ValidationException("Password must contain at least one digit")
    
    return True

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if phone number is valid, False otherwise
        
    Raises:
        ValidationException: If phone number is invalid
    """
    try:
        parsed_number = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationException("Invalid phone number")
        return True
    except phonenumbers.NumberParseException:
        raise ValidationException("Invalid phone number format")

def validate_meeting_dates(
    date: datetime,
    duration: int,
    existing_meetings: List[Dict[str, Any]]
) -> bool:
    """
    Validate meeting date and check for conflicts
    
    Args:
        date: Meeting date and time
        duration: Meeting duration in minutes
        existing_meetings: List of existing meetings
        
    Returns:
        bool: True if meeting date is valid, False otherwise
        
    Raises:
        ValidationException: If meeting date is invalid or conflicts with existing meetings
    """
    now = datetime.now()
    
    # Check if meeting is in the past
    if date < now:
        raise ValidationException("Meeting cannot be scheduled in the past")
    
    # Check if meeting is too far in the future (e.g., more than 1 year)
    if date > now + timedelta(days=365):
        raise ValidationException("Meeting cannot be scheduled more than 1 year in advance")
    
    # Check for conflicts with existing meetings
    meeting_end = date + timedelta(minutes=duration)
    
    for meeting in existing_meetings:
        existing_start = meeting["date"]
        existing_end = existing_start + timedelta(minutes=meeting["duration"])
        
        # Check if new meeting overlaps with existing meeting
        if (date < existing_end and meeting_end > existing_start):
            raise ValidationException(f"Meeting conflicts with existing meeting: {meeting['title']}")
    
    return True

def validate_proposed_dates(dates):
    """
    Validate proposed meeting dates
    
    Args:
        dates: List of proposed dates
        
    Returns:
        List: Validated dates
    """
    # Get current time in UTC with timezone info
    now = datetime.now(timezone.utc)
    
    # Ensure all dates are in the future
    for date in dates:
        # If date is naive (no timezone), assume it's UTC
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
            
        if date < now:
            raise ValueError("Proposed dates must be in the future")
    
    # Check for duplicate dates
    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate dates are not allowed")
    
    return dates

def validate_meeting_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validate meeting status transition
    
    Args:
        current_status: Current meeting status
        new_status: New meeting status
        
    Returns:
        bool: True if transition is valid, False otherwise
        
    Raises:
        ValidationException: If transition is invalid
    """
    valid_transitions = {
        "pending": ["accepted", "rejected", "cancelled"],
        "accepted": ["cancelled"],
        "rejected": [],
        "cancelled": []
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise ValidationException(f"Cannot transition from {current_status} to {new_status}")
    
    return True

def validate_manager_status_transition(current_status: bool, new_status: str) -> bool:
    """
    Validate manager approval status transition
    
    Args:
        current_status: Current approval status (True/False)
        new_status: New approval status ("approved"/"rejected")
        
    Returns:
        bool: True if transition is valid, False otherwise
        
    Raises:
        ValidationException: If transition is invalid
    """
    if current_status and new_status == "rejected":
        raise ValidationException("Cannot reject an already approved manager")
    
    return True