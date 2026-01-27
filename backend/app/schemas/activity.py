from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.activity import ActivityType


class ActivityCreate(BaseModel):
    """Schema for creating an activity"""
    application_name: Optional[str] = Field(None, max_length=255)
    window_title: Optional[str] = Field(None, max_length=500)
    activity_type: ActivityType = ActivityType.ACTIVE
    duration_seconds: int = Field(default=0, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class ActivityBatchCreate(BaseModel):
    """Schema for batch activity submission"""
    activities: List[ActivityCreate]


from beanie import PydanticObjectId


class ActivityResponse(BaseModel):
    """Schema for activity response"""
    id: PydanticObjectId
    user_id: PydanticObjectId
    timestamp: datetime
    application_name: Optional[str]
    window_title: Optional[str]
    activity_type: ActivityType
    duration_seconds: int
    screenshot_path: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class WorkSessionResponse(BaseModel):
    """Schema for work session response"""
    id: PydanticObjectId
    user_id: PydanticObjectId
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: int
    active_duration_seconds: int
    idle_duration_seconds: int
    productive_percentage: float
    activity_count: int
    screenshot_count: int
    
    model_config = ConfigDict(from_attributes=True)


class DailyReportResponse(BaseModel):
    """Schema for daily report response"""
    id: PydanticObjectId
    user_id: PydanticObjectId
    report_date: datetime  # Beanie handles this serialization
    total_hours: float
    active_hours: float
    idle_hours: float
    productive_percentage: float
    total_activities: int
    session_count: int
    screenshot_count: int
    app_usage: Optional[Dict[str, int]]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActivityStatsResponse(BaseModel):
    """Schema for activity statistics"""
    total_activities: int
    active_time_seconds: int
    idle_time_seconds: int
    productive_percentage: float
    top_applications: List[Dict[str, Any]]
    sessions: List[WorkSessionResponse]
