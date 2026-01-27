#!/usr/bin/env python3
"""
WorkProof Client Agent
Privacy-focused work activity monitoring client
"""

import os
import sys
import json
import time
import threading
import schedule
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collector.activity import ActivityCollector
from collector.idle_tracker import IdleTracker
from collector.screenshot import ScreenshotCapture
from sender.api_client import APIClient


class WorkProofAgent:
    """Main client agent for WorkProof"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the WorkProof agent"""
        self.config = self._load_config(config_path)
        self.running = False
        
        # Initialize components
        self.activity_collector = None
        self.idle_tracker = None
        self.screenshot_capture = None
        self.api_client = None
        
        # Activity buffer
        self.activity_buffer = []
        self.max_buffer_size = 100
        
        print("=" * 60)
        print("WorkProof Client Agent")
        print("=" * 60)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✓ Configuration loaded from {config_path}")
            return config
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            print("Using default configuration...")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            "server_url": "http://localhost:5000",
            "user_email": "",
            "user_password": "",
            "collection_interval": 60,
            "screenshot_enabled": True,
            "screenshot_interval": 300,
            "idle_threshold": 300,
            "approved_applications": [],
            "blur_screenshots": True,
            "offline_storage_path": "./offline_data"
        }
    
    def initialize(self) -> bool:
        """Initialize all components"""
        print("\nInitializing components...")
        
        # Check credentials
        if not self.config.get("user_email") or not self.config.get("user_password"):
            print("✗ Error: User credentials not configured!")
            print("Please edit config.json and add your email and password.")
            return False
        
        # Initialize API client
        self.api_client = APIClient(
            server_url=self.config["server_url"],
            email=self.config["user_email"],
            password=self.config["user_password"]
        )
        
        # Login to server
        print("\nAuthenticating with server...")
        if not self.api_client.login():
            print("✗ Authentication failed!")
            return False
        
        # Initialize activity collector
        self.activity_collector = ActivityCollector()
        print("✓ Activity collector initialized")
        
        # Initialize idle tracker
        self.idle_tracker = IdleTracker(
            idle_threshold_seconds=self.config.get("idle_threshold", 300)
        )
        print("✓ Idle tracker initialized")
        
        # Initialize screenshot capture if enabled
        if self.config.get("screenshot_enabled", True):
            screenshot_dir = os.path.join(
                self.config.get("offline_storage_path", "./offline_data"),
                "screenshots"
            )
            self.screenshot_capture = ScreenshotCapture(
                screenshot_dir=screenshot_dir,
                blur_enabled=self.config.get("blur_screenshots", True)
            )
            print("✓ Screenshot capture initialized")
        
        print("\n✓ All components initialized successfully!")
        return True
    
    def collect_and_submit_activity(self):
        """Collect current activity and submit to server"""
        try:
            # Collect activity data
            activity_data = self.activity_collector.collect_activity_data()
            
            # Get idle status
            idle_status = self.idle_tracker.get_activity_status()
            
            # Determine activity type based on idle status and input events
            if idle_status["is_idle"]:
                activity_type = "idle"
                duration = int(idle_status["idle_seconds"])
            else:
                # Check if there was actual activity
                has_activity = (
                    activity_data.get("mouse_movements", 0) > 0 or
                    activity_data.get("keyboard_presses", 0) > 0
                )
                activity_type = "active" if has_activity else "idle"
                duration = self.config.get("collection_interval", 60)
            
            # Check if application is approved (if filter is enabled)
            approved_apps = self.config.get("approved_applications", [])
            if approved_apps and activity_data.get("application_name"):
                if activity_data["application_name"] not in approved_apps:
                    print(f"⊘ Skipping unapproved application: {activity_data['application_name']}")
                    return
            
            # Prepare activity payload
            activity_payload = {
                "application_name": activity_data.get("application_name"),
                "window_title": activity_data.get("window_title"),
                "activity_type": activity_type,
                "duration_seconds": duration,
                "metadata": {
                    "mouse_movements": activity_data.get("mouse_movements", 0),
                    "keyboard_presses": activity_data.get("keyboard_presses", 0),
                    "platform": activity_data.get("metadata", {}).get("platform")
                }
            }
            
            # Add to buffer
            self.activity_buffer.append(activity_payload)
            
            # Submit if buffer is full or periodically
            if len(self.activity_buffer) >= self.max_buffer_size:
                self._submit_buffered_activities()
            
            # Log activity
            status_icon = "●" if activity_type == "active" else "○"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} "
                  f"{activity_data.get('application_name', 'Unknown'):20} | "
                  f"{activity_type:6} | {duration}s")
        
        except Exception as e:
            print(f"Error collecting activity: {e}")
    
    def _submit_buffered_activities(self):
        """Submit all buffered activities"""
        if not self.activity_buffer:
            return
        
        success = self.api_client.submit_batch_activities(self.activity_buffer)
        if success:
            self.activity_buffer = []
    
    def capture_and_upload_screenshot(self):
        """Capture screenshot and upload to server"""
        if not self.screenshot_capture:
            return
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📸 Capturing screenshot...")
            
            # Capture screenshot
            screenshot_path = self.screenshot_capture.capture_thumbnail()
            
            if screenshot_path:
                # Upload to server
                success = self.api_client.upload_screenshot(screenshot_path)
                
                # Delete local copy after successful upload
                if success:
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
    
    def sync_offline_data(self):
        """Sync any offline queued data"""
        try:
            if self.api_client.is_server_reachable():
                self.api_client.sync_offline_queue()
        except Exception as e:
            print(f"Error syncing offline data: {e}")
    
    def start(self):
        """Start the agent"""
        if not self.initialize():
            print("\n✗ Failed to initialize agent!")
            return
        
        self.running = True
        
        print("\n" + "=" * 60)
        print("WorkProof Agent Started")
        print("=" * 60)
        print(f"Collection interval: {self.config.get('collection_interval')}s")
        print(f"Screenshot interval: {self.config.get('screenshot_interval')}s")
        print(f"Idle threshold: {self.config.get('idle_threshold')}s")
        print("=" * 60)
        print("\nMonitoring activity... (Press Ctrl+C to stop)\n")
        
        # Schedule tasks
        collection_interval = self.config.get("collection_interval", 60)
        screenshot_interval = self.config.get("screenshot_interval", 300)
        
        schedule.every(collection_interval).seconds.do(self.collect_and_submit_activity)
        
        if self.config.get("screenshot_enabled", True):
            schedule.every(screenshot_interval).seconds.do(self.capture_and_upload_screenshot)
        
        # Sync offline data every 5 minutes
        schedule.every(5).minutes.do(self.sync_offline_data)
        
        # Run immediately once
        self.collect_and_submit_activity()
        
        # Main loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping agent...")
            self.stop()
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        
        # Submit any remaining buffered activities
        if self.activity_buffer:
            print("Submitting remaining activities...")
            self._submit_buffered_activities()
        
        # Stop collectors
        if self.activity_collector:
            self.activity_collector.stop()
        
        print("\n✓ WorkProof Agent stopped")
        print("=" * 60)


def main():
    """Main entry point"""
    agent = WorkProofAgent()
    agent.start()


if __name__ == "__main__":
    main()
