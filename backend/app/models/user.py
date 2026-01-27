from beanie import Document, Indexed
from pydantic import Field, EmailStr
from typing import Optional, Annotated
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    EMPLOYEE = "employee"


class User(Document):
    """User model for authentication and profile"""
    
    email: Annotated[EmailStr, Indexed(unique=True)]
    password_hash: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE
    
    # Employee-specific fields
    expected_daily_hours: float = 8.0
    department: Optional[str] = None
    employee_id: Annotated[Optional[str], Indexed(unique=True)] = None
    consent_accepted: bool = False
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"  # Collection name
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


