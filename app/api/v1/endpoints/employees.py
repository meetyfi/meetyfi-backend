# Updated Employee Router
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ....models.employee import Employee, EmployeeCreate, EmployeeLocation
from app.models.meeting import Meeting, MeetingCreate, MeetingUpdate
from ....db.mongodb import get_database
from ..deps import get_current_user, get_current_manager
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.get("/employees", response_model=List[dict])
async def get_employees(
    organization: Optional[str] = None,
    search_query: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    db = await get_database()
    query = {}
    
    # Add organization filter if provided
    if organization:
        query["organization"] = organization
        
    # Add name search if provided
    if search_query:
        query["$or"] = [
            {"name": {"$regex": search_query, "$options": "i"}},
            {"email": {"$regex": search_query, "$options": "i"}}
        ]
    
    # If user is a manager, only show their employees
    if current_user.get("is_manager"):
        query["manager_id"] = ObjectId(current_user["_id"])
    
    employees = await db.employees.find(query).to_list(None)
    
    # Convert ObjectId to string for JSON serialization
    for employee in employees:
        employee["_id"] = str(employee["_id"])
        employee["manager_id"] = str(employee["manager_id"])
        
    return employees

@router.post("/employees/location")
async def update_location(
    location: EmployeeLocation,
    current_user = Depends(get_current_user)
):
    if current_user.get("is_manager"):
        raise HTTPException(status_code=403, detail="Managers cannot update location")
        
    db = await get_database()
    
    # Update employee location
    result = await db.employees.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {
            "$set": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "last_location_update": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    return {"message": "Location updated successfully"}

@router.post("/managers/employees")
async def add_employee(
    employee: EmployeeCreate,
    current_user = Depends(get_current_manager)
):
    db = await get_database()
    
    # Check if email already exists
    if await db.users.find_one({"email": employee.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create employee document
    employee_dict = employee.dict()
    employee_dict["manager_id"] = ObjectId(current_user["_id"])
    employee_dict["organization"] = current_user["organization"]
    employee_dict["is_manager"] = False
    employee_dict["created_at"] = datetime.utcnow()
    
    result = await db.employees.insert_one(employee_dict)
    return {"id": str(result.inserted_id)}

@router.get("/managers")
async def get_managers(current_user = Depends(get_current_user)):
    if current_user.get("is_manager"):
        raise HTTPException(status_code=403, detail="Managers cannot view other managers")
        
    db = await get_database()
    managers = await db.users.find(
        {
            "is_manager": True,
            "organization": current_user["organization"]
        },
        {
            "password": 0,
            "verification_code": 0
        }
    ).to_list(None)
    
    # Convert ObjectId to string
    for manager in managers:
        manager["_id"] = str(manager["_id"])
        
    return managers

# Updated Meeting Router
@router.post("/meetings")
async def create_meeting(
    meeting: MeetingCreate,
    current_user = Depends(get_current_user)
):
    db = await get_database()
    
    # Validate manager_id if provided
    if meeting.manager_id:
        manager = await db.users.find_one({
            "_id": ObjectId(meeting.manager_id),
            "is_manager": True
        })
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
            
    meeting_dict = meeting.dict()
    meeting_dict["creator_id"] = ObjectId(current_user["_id"])
    meeting_dict["status"] = "pending"
    meeting_dict["created_at"] = datetime.utcnow()
    
    result = await db.meetings.insert_one(meeting_dict)
    return {"id": str(result.inserted_id)}
