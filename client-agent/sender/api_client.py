import requests
import json
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class APIClient:
    """Client for communicating with WorkProof backend API"""
    
    def __init__(self, server_url: str, email: str = None, password: str = None):
        """
        Initialize API client
        
        Args:
            server_url: Base URL of the backend server
            email: User email for authentication
            password: User password for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        
        # Offline storage
        self.offline_queue_file = "offline_queue.json"
        self.offline_queue = self._load_offline_queue()
    
    def _load_offline_queue(self) -> List[Dict]:
        """Load offline queue from file"""
        if os.path.exists(self.offline_queue_file):
            try:
                with open(self.offline_queue_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading offline queue: {e}")
        return []
    
    def _save_offline_queue(self):
        """Save offline queue to file"""
        try:
            with open(self.offline_queue_file, 'w') as f:
                json.dump(self.offline_queue, f)
        except Exception as e:
            print(f"Error saving offline queue: {e}")
    
    def login(self) -> bool:
        """
        Authenticate with the server
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.user_info = data.get("user")
                print(f"✓ Logged in as: {self.user_info.get('full_name')}")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/api/auth/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                return True
            else:
                return False
        
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def submit_activity(self, activity_data: Dict[str, Any]) -> bool:
        """
        Submit a single activity to the server
        
        Args:
            activity_data: Activity data dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/activity/submit",
                json=activity_data,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 201:
                return True
            elif response.status_code == 401:
                # Try to refresh token and retry
                if self.refresh_access_token():
                    return self.submit_activity(activity_data)
                return False
            else:
                print(f"Activity submission failed: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"Activity submission error: {e}")
            # Add to offline queue
            self._queue_for_offline(activity_data)
            return False
    
    def submit_batch_activities(self, activities: List[Dict[str, Any]]) -> bool:
        """
        Submit multiple activities in a batch
        
        Args:
            activities: List of activity data dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.server_url}/api/activity/batch",
                json={"activities": activities},
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 201:
                print(f"✓ Submitted {len(activities)} activities")
                return True
            elif response.status_code == 401:
                # Try to refresh token and retry
                if self.refresh_access_token():
                    return self.submit_batch_activities(activities)
                return False
            else:
                print(f"Batch submission failed: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"Batch submission error: {e}")
            # Add all to offline queue
            for activity in activities:
                self._queue_for_offline(activity)
            return False
    
    def upload_screenshot(self, screenshot_path: str, activity_id: Optional[int] = None) -> bool:
        """
        Upload a screenshot to the server
        
        Args:
            screenshot_path: Path to screenshot file
            activity_id: Optional activity ID to associate with
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(screenshot_path):
            print(f"Screenshot file not found: {screenshot_path}")
            return False
        
        try:
            with open(screenshot_path, 'rb') as f:
                files = {'file': (os.path.basename(screenshot_path), f, 'image/png')}
                data = {}
                if activity_id:
                    data['activity_id'] = activity_id
                
                headers = {}
                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"
                
                response = requests.post(
                    f"{self.server_url}/api/activity/screenshot",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"✓ Screenshot uploaded: {os.path.basename(screenshot_path)}")
                    return True
                elif response.status_code == 401:
                    # Try to refresh token and retry
                    if self.refresh_access_token():
                        return self.upload_screenshot(screenshot_path, activity_id)
                    return False
                else:
                    print(f"Screenshot upload failed: {response.status_code}")
                    return False
        
        except Exception as e:
            print(f"Screenshot upload error: {e}")
            return False
    
    def _queue_for_offline(self, activity_data: Dict[str, Any]):
        """Add activity to offline queue"""
        self.offline_queue.append({
            "timestamp": datetime.now().isoformat(),
            "data": activity_data
        })
        self._save_offline_queue()
        print(f"⚠ Activity queued for offline sync ({len(self.offline_queue)} pending)")
    
    def sync_offline_queue(self) -> int:
        """
        Sync all queued offline activities
        
        Returns:
            Number of successfully synced activities
        """
        if not self.offline_queue:
            return 0
        
        print(f"Syncing {len(self.offline_queue)} offline activities...")
        
        # Try to submit in batches
        batch_size = 50
        synced_count = 0
        remaining_queue = []
        
        for i in range(0, len(self.offline_queue), batch_size):
            batch = self.offline_queue[i:i+batch_size]
            activities = [item["data"] for item in batch]
            
            if self.submit_batch_activities(activities):
                synced_count += len(activities)
            else:
                # Keep failed items in queue
                remaining_queue.extend(batch)
        
        self.offline_queue = remaining_queue
        self._save_offline_queue()
        
        if synced_count > 0:
            print(f"✓ Synced {synced_count} offline activities")
        
        return synced_count
    
    def is_server_reachable(self) -> bool:
        """Check if the server is reachable"""
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# For testing
if __name__ == "__main__":
    # Test configuration
    client = APIClient(
        server_url="http://localhost:5000",
        email="test@example.com",
        password="TestPassword123"
    )
    
    # Test login
    if client.login():
        print("\n✓ Login successful!")
        print(f"User: {client.user_info}")
        
        # Test activity submission
        test_activity = {
            "application_name": "chrome.exe",
            "window_title": "WorkProof - Test",
            "activity_type": "active",
            "duration_seconds": 60,
            "metadata": {"test": True}
        }
        
        print("\nSubmitting test activity...")
        if client.submit_activity(test_activity):
            print("✓ Activity submitted successfully!")
        
        # Test server reachability
        print(f"\nServer reachable: {client.is_server_reachable()}")
    else:
        print("\n✗ Login failed!")
