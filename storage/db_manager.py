import os
from pymongo import MongoClient
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', '.env'))

import logging

logger = logging.getLogger("WorkProof.Storage")

class DBManager:
    """
    Handles MongoDB operations for session tracking.
    """
    def __init__(self, db_name="workproof_db"):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        logger.info(f"Connecting to MongoDB at {uri.split('@')[-1]}") # Obfuscate user/pass if any
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.client.server_info() # Force connection check
            self.db = self.client[db_name]
            self.sessions = self.db.sessions
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def save_session(self, session_data):
        """
        Saves a session record to MongoDB.
        """
        session_data['timestamp'] = datetime.datetime.now()
        result = self.sessions.insert_one(session_data)
        return result.inserted_id

    def get_recent_sessions(self, limit=10):
        """
        Retrieves the most recent sessions.
        """
        return list(self.sessions.find().sort("timestamp", -1).limit(limit))

if __name__ == "__main__":
    # Test connection
    try:
        mgr = DBManager()
        test_id = mgr.save_session({"test": True, "accuracy": 95.5})
        print(f"Saved test session with ID: {test_id}")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
