from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import UserUpdate
from app.db.mongodb import get_database
from app.api.v1.deps import get_current_user
import aiofiles
import os
from datetime import datetime

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return current_user

@router.put("/profile")
async def update_profile(
    profile: UserUpdate,
    current_user = Depends(get_current_user)
):
    db = await get_database()
    update_data = profile.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": "Profile updated successfully"}

@router.post("/profile/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    upload_dir = "uploads/profile_photos"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{current_user['_id']}{file_extension}"
    file_path = os.path.join(upload_dir, file_name)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    db = await get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"profile_photo": file_path}}
    )
    
    return {"message": "Profile photo uploaded successfully"}