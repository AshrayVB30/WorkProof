from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from beanie import PydanticObjectId


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.EMPLOYEE
    expected_daily_hours: float = Field(default=8.0, ge=0, le=24)
    department: Optional[str] = None
    employee_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    expected_daily_hours: Optional[float] = Field(None, ge=0, le=24)
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: PydanticObjectId
    role: UserRole
    expected_daily_hours: float
    department: Optional[str]
    employee_id: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    consent_accepted: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
