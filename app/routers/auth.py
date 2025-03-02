from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.auth import (
    ManagerSignupRequest, ManagerSignupResponse,
    VerifyOTPRequest, VerifyOTPResponse,
    LoginRequest, LoginResponse,
    EmployeeVerifyRequest, EmployeeVerifyResponse
)
from app.services.auth_service import (
    register_manager, verify_manager_otp,
    login_user, verify_employee
)
from app.dependencies import get_db_session

router = APIRouter()

@router.post("/manager/signup", response_model=ManagerSignupResponse)
async def signup_manager(
    request: ManagerSignupRequest,
    db: Session = Depends(get_db_session)
):
    """Register a new manager"""
    return register_manager(db, request)

@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db_session)
):
    """Verify OTP for manager signup"""
    return verify_manager_otp(db, request)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session)
):
    """Login for managers and employees"""
    return login_user(db, request)

@router.post("/employee/verify", response_model=EmployeeVerifyResponse)
async def verify_employee_account(
    request: EmployeeVerifyRequest,
    db: Session = Depends(get_db_session)
):
    """Employee verification and password setup"""
    return verify_employee(db, request)