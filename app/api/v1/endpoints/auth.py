from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from app.core.security import create_access_token
from app.models.user import UserInDB, UserBase, ManagerSignup, EmployeeCreate
from app.db.mongodb import get_database
from datetime import timedelta
from app.config import get_settings
from email_validator import validate_email, EmailNotValidError
import random
from app.core.email_utils import EmailService
from ..deps import get_current_manager


router = APIRouter()
settings = get_settings()
email_service = EmailService()


@router.post("/manager/signup")
async def manager_signup(user: ManagerSignup):
    """Only managers can sign up directly"""
    db = await get_database()
    
    try:
        # Validate email format
        valid = validate_email(user.email)
        user.email = valid.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    # Check if email exists
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    
    # Create manager user
    user_dict = user.dict()
    user_dict["verification_code"] = otp
    user_dict["is_verified"] = False
    user_dict["is_manager"] = True  # This is a manager account
    
    await db.users.insert_one(user_dict)
    
    # Send verification email
    await email_service.send_verification_email(user.email, otp)
    
    return {"message": "Manager signup successful. Please verify your email."}


@router.post("/employee/create")
async def create_employee(
    employee: EmployeeCreate,
    current_user = Depends(get_current_manager)
):
    """Only managers can create employee accounts"""
    db = await get_database()
    
    try:
        valid = validate_email(employee.email)
        employee.email = valid.email
    except EmailNotValidError:
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    if await db.users.find_one({"email": employee.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    
    # Create employee user
    employee_dict = employee.dict()
    employee_dict["verification_code"] = otp
    employee_dict["is_verified"] = False
    employee_dict["is_manager"] = False
    employee_dict["manager_id"] = str(current_user["_id"])
    employee_dict["organization"] = current_user["organization"]
    
    result = await db.users.insert_one(employee_dict)
    
    # Send verification email to employee
    await email_service.send_verification_email(employee.email, otp)
    
    return {
        "message": "Employee account created successfully",
        "employee_id": str(result.inserted_id)
    }


@router.post("/verify-email")
async def verify_email(
    email: str = Form(...),
    otp: str = Form(...)
):
    db = await get_database()
    user = await db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user["verification_code"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "is_verified": True,
                "verification_code": None  # Clear the OTP after verification
            }
        }
    )
    
    return {"message": "Email verified successfully"}


@router.post("/login")
async def login(email: str = Form(...)):
    db = await get_database()
    user = await db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    # Generate and send OTP
    otp = str(random.randint(100000, 999999))
    await email_service.send_verification_email(user["email"], otp)
    
    # Store OTP
    await db.users.update_one(
        {"email": email},
        {"$set": {"verification_code": otp}}
    )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "OTP sent to your email. Please verify to login."}
    )


@router.post("/verify-login")
async def verify_login(
    email: str = Form(...),
    otp: str = Form(...)
):
    db = await get_database()
    user = await db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    if user["verification_code"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clear the OTP after successful verification
    await db.users.update_one(
        {"email": email},
        {"$set": {"verification_code": None}}
    )
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_manager": user.get("is_manager", False)
    }
