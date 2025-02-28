from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.models.meeting import Meeting, MeetingCreate, MeetingUpdate
from app.db.mongodb import get_database
from app.api.v1.deps import get_current_user
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()

@router.post("/meetings", response_model=dict)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    meeting_dict = meeting.dict()
    # Convert string ID to ObjectId for MongoDB
    meeting_dict["creator_id"] = ObjectId(current_user["_id"])
    meeting_dict["status"] = "pending"
    meeting_dict["created_at"] = datetime.utcnow()
    
    result = await db.meetings.insert_one(meeting_dict)
    return {"id": str(result.inserted_id)}

@router.get("/meetings", response_model=List[dict])
async def get_meetings(
    current_user: dict = Depends(get_current_user),
    date: Optional[str] = None,
    client_name: Optional[str] = None,
    location: Optional[str] = None
):
    db = await get_database()
    query = {"creator_id": ObjectId(current_user["_id"])}
    
    if date:
        query["date"] = date
    if client_name:
        query["client_name"] = {"$regex": client_name, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
        
    meetings = []
    async for meeting in db.meetings.find(query):
        # Convert ObjectId to string for JSON serialization
        meeting["_id"] = str(meeting["_id"])
        meeting["creator_id"] = str(meeting["creator_id"])
        meetings.append(meeting)
    
    return meetings

@router.post("/meetings/{meeting_id}/cancel", response_model=dict)
async def cancel_meeting(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    
    try:
        meeting_obj_id = ObjectId(meeting_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")
    
    result = await db.meetings.update_one(
        {
            "_id": meeting_obj_id,
            "creator_id": ObjectId(current_user["_id"])
        },
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting cancelled successfully"}

# Add a new endpoint to get a single meeting
@router.get("/meetings/{meeting_id}", response_model=dict)
async def get_meeting(
    meeting_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    
    try:
        meeting_obj_id = ObjectId(meeting_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid meeting ID format")
    
    meeting = await db.meetings.find_one({
        "_id": meeting_obj_id,
        "creator_id": ObjectId(current_user["_id"])
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Convert ObjectIds to strings for JSON serialization
    meeting["_id"] = str(meeting["_id"])
    meeting["creator_id"] = str(meeting["creator_id"])
    
    return meeting