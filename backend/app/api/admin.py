from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date, datetime
from beanie import PydanticObjectId
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.dependencies import get_current_admin
from pydantic import BaseModel
from app.models.activity import Activity

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    expected_daily_hours: Optional[float] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/employees", response_model=List[UserResponse])
async def get_employees(
    current_admin: User = Depends(get_current_admin)
):
    """Get all employees"""
    employees = await User.find(User.role == UserRole.EMPLOYEE).to_list()
    return employees


@router.get("/employees/{id}", response_model=UserResponse)
async def get_employee_details(
    id: PydanticObjectId,
    current_admin: User = Depends(get_current_admin)
):
    """Get details for a specific employee"""
    employee = await User.get(id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    return employee


@router.put("/employees/{id}", response_model=UserResponse)
async def update_employee(
    id: PydanticObjectId,
    data: EmployeeUpdate,
    current_admin: User = Depends(get_current_admin)
):
    """Update employee details"""
    employee = await User.get(id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(employee, key, value)
    
    await employee.save()
    return employee


@router.get("/employees/{id}/activity")
async def get_employee_activity(
    id: PydanticObjectId,
    report_date: Optional[date] = None,
    current_admin: User = Depends(get_current_admin)
):
    """Get activity timeline for a specific employee"""
    
    if not report_date:
        report_date = datetime.utcnow().date()
    
    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())
    
    activities = await Activity.find(
        Activity.user_id == id,
        Activity.timestamp >= start_datetime,
        Activity.timestamp <= end_datetime
    ).sort(Activity.timestamp).to_list()
    
    return activities


@router.get("/alerts")
async def get_alerts(
    current_admin: User = Depends(get_current_admin)
):
    """Get system alerts (e.g., low productivity, long idle time)"""
    # For now return empty list
    return []


@router.get("/settings")
async def get_admin_settings(
    current_admin: User = Depends(get_current_admin)
):
    """Get system-wide admin settings"""
    return {
        "idle_timeout_minutes": 5,
        "screenshot_interval_minutes": 10,
        "tracking_enabled": True,
        "privacy_mode": "balanced"
    }


@router.put("/settings")
async def update_admin_settings(
    data: dict,
    current_admin: User = Depends(get_current_admin)
):
    """Update system-wide admin settings"""
    return {"message": "Settings updated successfully", "settings": data}
