from beanie import Document

# Import models for easy access
from app.models.user import User
from app.models.activity import Activity, WorkSession, DailyReport, AuditLog

__all__ = ["Document", "User", "Activity", "WorkSession", "DailyReport", "AuditLog"]

