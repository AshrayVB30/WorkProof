from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config.settings import settings
from typing import Optional

# MongoDB client instance
mongodb_client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie ODM"""
    global mongodb_client
    
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = mongodb_client[settings.MONGODB_DB_NAME]
    
    # Import all document models
    from app.models.user import User
    from app.models.activity import Activity, WorkSession, DailyReport, AuditLog
    
    # Initialize Beanie with document models
    await init_beanie(
        database=database,
        document_models=[
            User,
            Activity,
            WorkSession,
            DailyReport,
            AuditLog
        ]
    )
    
    print(f"✓ Connected to MongoDB: {settings.MONGODB_URL}/{settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✓ Closed MongoDB connection")


def get_database():
    """Get MongoDB database instance"""
    if mongodb_client is None:
        raise Exception("MongoDB client not initialized. Call connect_to_mongo() first.")
    return mongodb_client[settings.MONGODB_DB_NAME]
