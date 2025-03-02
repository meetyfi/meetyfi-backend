from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.admin import (
    ManagerRequestListResponse, ManagerStatusUpdateRequest,
    ManagerListResponse
)
from app.services.admin_service import (
    get_manager_requests, update_manager_status,
    get_all_managers
)
from app.dependencies import get_db, get_current_admin

router = APIRouter()

@router.get("/managers/requests", response_model=ManagerRequestListResponse)
async def list_manager_requests(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all manager signup requests"""
    skip = (page - 1) * limit  # Adjust skip for pagination
    return get_manager_requests(db, status, skip, limit)

@router.put("/managers/{manager_id}/status")
async def update_manager_request(
    manager_id: int,
    status_update: ManagerStatusUpdateRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve or reject manager signup"""
    update_manager_status(db, manager_id, status_update)
    return {"message": f"Manager {status_update.status} successfully"}

@router.get("/managers", response_model=ManagerListResponse)
async def list_managers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all managers"""
    return get_all_managers(db, page, limit)