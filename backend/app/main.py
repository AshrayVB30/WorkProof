from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.settings import settings
from app.api import auth, activity, reports, admin
from app.database import connect_to_mongo, close_mongo_connection
import os

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="WorkProof - Privacy-focused work verification platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup"""
    await connect_to_mongo()
    # Seed default users
    await seed_default_users()

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    await close_mongo_connection()

# Ensure storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)

# Mount static files for screenshots (admin only in production)
if os.path.exists(settings.SCREENSHOT_DIR):
    app.mount("/screenshots", StaticFiles(directory=settings.SCREENSHOT_DIR), name="screenshots")

async def seed_default_users():
    """Seed default admin and employee users if they don't exist"""
    from app.models.user import User, UserRole
    from app.utils.encryption import hash_password
    from datetime import datetime

    # Seed Admin
    admin_email = "admin@workproof.com"
    admin = await User.find_one(User.email == admin_email)
    if not admin:
        print(f"Seeding admin user: {admin_email}")
        admin = User(
            email=admin_email,
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        await admin.insert()

    # Seed Employee
    employee_email = "employee@workproof.com"
    employee = await User.find_one(User.email == employee_email)
    if not employee:
        print(f"Seeding employee user: {employee_email}")
        employee = User(
            email=employee_email,
            password_hash=hash_password("employee123"),
            full_name="John Doe",
            role=UserRole.EMPLOYEE,
            employee_id="EMP001",
            department="Engineering",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        await employee.insert()


# Register routers
app.include_router(auth.router)
app.include_router(activity.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to WorkProof API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2026-01-27T11:14:38+05:30"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG
    )
