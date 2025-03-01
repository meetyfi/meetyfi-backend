from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import jwt
import secrets
import string
from typing import Dict, Any, Optional

from app.database import Manager, Employee, Admin, UserType
from app.schemas.auth import (
    ManagerSignupRequest, LoginRequest, VerifyOTPRequest, 
    EmployeeVerifyRequest, UserData
)
from app.config import settings
from app.utils.email import send_otp_email, send_employee_verification_email
from app.utils.password import hash_password, verify_password
from app.exceptions import (
    CredentialsException, UserNotFoundException, 
    OTPVerificationException, VerificationTokenException
)

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def register_manager(db: Session, manager_data: ManagerSignupRequest) -> int:
    """
    Register a new manager
    
    Args:
        db: Database session
        manager_data: Manager signup data
        
    Returns:
        int: ID of the created manager
    """
    # Check if email already exists
    existing_manager = db.query(Manager).filter(Manager.email == manager_data.email).first()
    if existing_manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new manager
    hashed_password = hash_password(manager_data.password)
    otp = generate_otp()
    
    new_manager = Manager(
        email=manager_data.email,
        password=hashed_password,
        name=manager_data.name,
        company_name=manager_data.company_name,
        company_size=manager_data.company_size,
        phone=manager_data.phone,
        profile_picture=manager_data.profile_picture,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        is_verified=False,
        is_approved=False
    )
    
    try:
        db.add(new_manager)
        db.commit()
        db.refresh(new_manager)
        
        # Send OTP email
        send_otp_email(manager_data.email, otp, manager_data.name)
        
        return {"manager_id": new_manager.id, "message": "Manager registered successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating manager account"
        )

def verify_manager_otp(db: Session, verify_data: VerifyOTPRequest) -> str:
    """
    Verify OTP for manager account
    
    Args:
        db: Database session
        verify_data: OTP verification data
        
    Returns:
        str: Access token
    """
    manager = db.query(Manager).filter(Manager.email == verify_data.email).first()
    if not manager:
        raise UserNotFoundException("Manager not found")
    
    # Check if OTP is valid
    if manager.otp != verify_data.otp:
        raise OTPVerificationException("Invalid OTP")
    
    # Check if OTP is expired (10 minutes validity)
    otp_expiry = manager.otp_created_at + timedelta(minutes=10)
    if datetime.utcnow() > otp_expiry:
        raise OTPVerificationException("OTP expired")
    
    # Mark manager as verified
    manager.is_verified = True
    manager.otp = None
    manager.otp_created_at = None
    db.commit()
    
    # Generate access token
    access_token = create_access_token({
        "sub": manager.id,
        "type": UserType.MANAGER.value
    })
    
    return access_token

def login_user(db: Session, login_data: LoginRequest) -> Dict[str, Any]:
    """
    Authenticate a user
    
    Args:
        db: Database session
        login_data: Login credentials
        
    Returns:
        Dict: Access token and user data
    """
    if login_data.user_type == UserType.MANAGER:
        user = db.query(Manager).filter(Manager.email == login_data.email).first()
    elif login_data.user_type == UserType.EMPLOYEE:
        user = db.query(Employee).filter(Employee.email == login_data.email).first()
    elif login_data.user_type == UserType.ADMIN:
        user = db.query(Admin).filter(Admin.email == login_data.email).first()
    else:
        raise CredentialsException("Invalid user type")
    
    if not user:
        raise CredentialsException("Invalid credentials")
    
    if not verify_password(login_data.password, user.password):
        raise CredentialsException("Invalid credentials")
    
    if not user.is_verified:
        raise CredentialsException("Account not verified")
    
    # For managers, check if approved
    if login_data.user_type == UserType.MANAGER and not user.is_approved:
        raise CredentialsException("Manager account not approved by admin")
    
    # Generate access token
    access_token = create_access_token({
        "sub": user.id,
        "type": login_data.user_type
    })
    
    # Prepare user data based on type
    user_data = UserData(
        id=user.id,
        email=user.email,
        name=user.name,
        user_type=login_data.user_type,
        is_verified=user.is_verified
    )
    
    if login_data.user_type == UserType.MANAGER:
        user_data.company_name = user.company_name
        user_data.company_size = user.company_size
    elif login_data.user_type == UserType.EMPLOYEE:
        user_data.role = user.role
        user_data.department = user.department
        user_data.manager_id = user.manager_id
    
    return {
        "access_token": access_token,
        "user_data": user_data
    }

def create_employee(db: Session, manager_id: int, name: str, email: str, role: Optional[str] = None, department: Optional[str] = None) -> int:
    """
    Create a new employee
    
    Args:
        db: Database session
        manager_id: ID of the manager creating the employee
        name: Employee name
        email: Employee email
        role: Employee role
        department: Employee department
        
    Returns:
        int: ID of the created employee
    """
    # Check if email already exists
    existing_employee = db.query(Employee).filter(Employee.email == email).first()
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create new employee
    new_employee = Employee(
        email=email,
        name=name,
        role=role,
        department=department,
        manager_id=manager_id,
        verification_token=verification_token,
        verification_token_created_at=datetime.utcnow(),
        is_verified=False
    )
    
    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        
        # Get manager details
        manager = db.query(Manager).filter(Manager.id == manager_id).first()
        
        # Send verification email
        send_employee_verification_email(
            email, 
            name, 
            verification_token, 
            manager.name, 
            manager.company_name
        )
        
        return new_employee.id
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating employee account"
        )

def verify_employee(db: Session, verify_data: EmployeeVerifyRequest) -> str:
    """
    Verify employee account with verification token and set password
    
    Args:
        db: Database session
        verify_data: Employee verification data
        
    Returns:
        str: Access token
    """
    employee = db.query(Employee).filter(Employee.verification_token == verify_data.verification_token).first()
    if not employee:
        raise VerificationTokenException("Invalid verification token")
    
    # Check if token is expired (24 hours validity)
    token_expiry = employee.verification_token_created_at + timedelta(hours=24)
    if datetime.utcnow() > token_expiry:
        raise VerificationTokenException("Verification token expired")
    
    # Set password and mark as verified
    hashed_password = hash_password(verify_data.password)
    employee.password = hashed_password
    employee.is_verified = True
    employee.verification_token = None
    employee.verification_token_created_at = None
    db.commit()
    
    # Generate access token
    access_token = create_access_token({
        "sub": employee.id,
        "type": UserType.EMPLOYEE.value
    })
    
    return access_token