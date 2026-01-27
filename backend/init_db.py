"""
MongoDB Database Initialization Script
Initializes the MongoDB database with indexes and creates a default admin user
"""
import asyncio
from datetime import datetime
from app.database import connect_to_mongo, close_mongo_connection
from app.models.user import User, UserRole
from app.utils.encryption import hash_password


async def init_database():
    """Initialize MongoDB database with indexes and default data"""
    print("=" * 60)
    print("MongoDB Database Initialization")
    print("=" * 60)
    
    # Connect to MongoDB
    print("\n1. Connecting to MongoDB...")
    await connect_to_mongo()
    print("   ✓ Connected successfully")
    
    # Create indexes (Beanie handles this automatically on initialization)
    print("\n2. Creating indexes...")
    print("   ✓ Indexes created automatically by Beanie")
    
    # Check if admin user exists
    print("\n3. Checking for admin user...")
    admin_email = "admin@workproof.com"
    existing_admin = await User.find_one(User.email == admin_email)
    
    if existing_admin:
        print(f"   ℹ Admin user already exists: {admin_email}")
    else:
        # Create default admin user
        print("   Creating default admin user...")
        admin_user = User(
            email=admin_email,
            password_hash=hash_password("admin123"),  # Change this in production!
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        await admin_user.insert()
        print(f"   ✓ Admin user created: {admin_email}")
        print(f"   ⚠ Default password: admin123 (CHANGE THIS IN PRODUCTION!)")
    
    # Check if employee user exists
    print("\n4. Checking for dummy employee user...")
    employee_email = "employee@workproof.com"
    existing_employee = await User.find_one(User.email == employee_email)
    
    if existing_employee:
        print(f"   ℹ Employee user already exists: {employee_email}")
    else:
        # Create default employee user
        print("   Creating dummy employee user...")
        employee_user = User(
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
        await employee_user.insert()
        print(f"   ✓ Employee user created: {employee_email}")
        print(f"   ⚠ Default password: employee123")
    
    # Display database info
    print("\n5. Database Information:")
    user_count = await User.count()
    print(f"   Total users: {user_count}")
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    
    # Close connection
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(init_database())
