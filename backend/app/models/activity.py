from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
from typing import Optional, Dict, Any, Annotated
from datetime import datetime, date
import enum


class ActivityType(str, enum.Enum):
    """Activity type enumeration"""
    ACTIVE = "active"
    IDLE = "idle"
    BREAK = "break"


class Activity(Document):
    """Activity tracking model - stores individual activity events"""
    
    user_id: Annotated[PydanticObjectId, Indexed()]
    
    # Activity details
    timestamp: Annotated[datetime, Indexed()] = Field(default_factory=datetime.utcnow)
    application_name: Optional[str] = None
    window_title: Optional[str] = None
    activity_type: ActivityType = ActivityType.ACTIVE
    duration_seconds: int = 0
    
    # Additional metadata
    activity_metadata: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    
    class Settings:
        name = "activities"
    
    def __repr__(self):
        return f"<Activity {self.id} - {self.user_id} - {self.activity_type}>"


class WorkSession(Document):
    """Work session model - groups activities into logical work sessions"""
    
    user_id: Annotated[PydanticObjectId, Indexed()]
    
    # Session timing
    start_time: Annotated[datetime, Indexed()]
    end_time: Optional[datetime] = None
    
    # Session metrics
    total_duration_seconds: int = 0
    active_duration_seconds: int = 0
    idle_duration_seconds: int = 0
    productive_percentage: float = 0.0
    
    # Session metadata
    activity_count: int = 0
    screenshot_count: int = 0
    
    class Settings:
        name = "work_sessions"
    
    def __repr__(self):
        return f"<WorkSession {self.id} - User {self.user_id}>"


class DailyReport(Document):
    """Daily report model - aggregated daily statistics per user"""
    
    user_id: Annotated[PydanticObjectId, Indexed()]
    
    # Report date
    report_date: Annotated[date, Indexed()]
    
    # Time metrics
    total_hours: float = 0.0
    active_hours: float = 0.0
    idle_hours: float = 0.0
    productive_percentage: float = 0.0
    
    # Activity metrics
    total_activities: int = 0
    session_count: int = 0
    screenshot_count: int = 0
    
    # Application usage breakdown
    app_usage: Optional[Dict[str, int]] = None  # {"chrome.exe": 120, "excel.exe": 240}
    
    # Report metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "daily_reports"
    
    def __repr__(self):
        return f"<DailyReport {self.report_date} - User {self.user_id}>"


class AuditLog(Document):
    """Audit log model - tracks admin actions and data access"""
    
    user_id: Annotated[Optional[PydanticObjectId], Indexed()] = None
    
    # Action details
    action: str  # e.g., "view_report", "delete_user"
    resource_type: Optional[str] = None  # e.g., "user", "report"
    resource_id: Optional[int] = None
    
    # Additional context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    # Timestamp
    timestamp: Annotated[datetime, Indexed()] = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audit_logs"
    
    def __repr__(self):
        return f"<AuditLog {self.id} - {self.action}>"



