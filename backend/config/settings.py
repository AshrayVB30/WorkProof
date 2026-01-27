from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "WorkProof"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database (MongoDB)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "workproof_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # File Storage
    UPLOAD_DIR: str = "storage/raw/uploads"
    SCREENSHOT_DIR: str = "storage/raw/screenshots"
    PROCESSED_DIR: str = "storage/processed"
    TEMP_DIR: str = "storage/temp"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Activity Tracking
    IDLE_THRESHOLD_SECONDS: int = 300  # 5 minutes
    SCREENSHOT_INTERVAL_SECONDS: int = 300  # 5 minutes
    ACTIVITY_BATCH_SIZE: int = 100
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
