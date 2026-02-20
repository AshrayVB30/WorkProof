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
            self.use_sqlite = False
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB: {e}. Falling back to SQLite.")
            self.use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        import sqlite3
        import json
        self.sqlite_db_path = os.path.join(os.path.dirname(__file__), 'workproof.db')
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        # Create a simple table to store sessions as JSON
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                data TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_session(self, session_data):
        """
        Saves a session record to MongoDB or SQLite.
        """
        session_data['timestamp'] = datetime.datetime.now().isoformat()
        
        if not self.use_sqlite:
            # MongoDB
            result = self.sessions.insert_one(session_data)
            return result.inserted_id
        else:
            # SQLite
            import sqlite3
            import json
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (timestamp, data) VALUES (?, ?)",
                (session_data['timestamp'], json.dumps(session_data, default=str))
            )
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return session_id

    def get_recent_sessions(self, limit=10):
        """
        Retrieves the most recent sessions.
        """
        if not self.use_sqlite:
            return list(self.sessions.find().sort("timestamp", -1).limit(limit))
        else:
            import sqlite3
            import json
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                data = json.loads(row['data'])
                # Add ID and timestamp from row if not in data or to ensure consistency
                data['_id'] = row['id']
                # data['timestamp'] is already in data but we can overwrite if needed
                sessions.append(data)
            return sessions

if __name__ == "__main__":
    # Test connection
    try:
        mgr = DBManager()
        test_id = mgr.save_session({"test": True, "accuracy": 95.5})
        print(f"Saved test session with ID: {test_id}")
        recent = mgr.get_recent_sessions(1)
        print(f"Retrieved session: {recent}")
    except Exception as e:
        print(f"Database operation failed: {e}")
