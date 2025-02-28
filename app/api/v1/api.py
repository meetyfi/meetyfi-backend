from fastapi import APIRouter
from app.api.v1.endpoints import auth, meetings, employees, profile

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])