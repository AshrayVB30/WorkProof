import os
import time
import uuid
from datetime import datetime
from typing import Optional
from PIL import Image, ImageFilter, ImageDraw
import pyautogui


class ScreenshotCapture:
    """Handles screenshot capture with privacy features"""
    
    def __init__(self, screenshot_dir: str = "./screenshots", blur_enabled: bool = True):
        """
        Initialize screenshot capture
        
        Args:
            screenshot_dir: Directory to save screenshots
            blur_enabled: Whether to blur screenshots for privacy
        """
        self.screenshot_dir = screenshot_dir
        self.blur_enabled = blur_enabled
        
        # Create screenshot directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)
    
    def capture_screenshot(self, blur_radius: int = 5) -> Optional[str]:
        """
        Capture a screenshot
        
        Args:
            blur_radius: Radius for blur effect (higher = more blur)
        
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Apply blur if enabled
            if self.blur_enabled:
                screenshot = screenshot.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Compress and save
            screenshot.save(filepath, "PNG", optimize=True, quality=85)
            
            return filepath
        
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
    
    def capture_with_redaction(self, redaction_areas: list = None) -> Optional[str]:
        """
        Capture screenshot with specific areas redacted
        
        Args:
            redaction_areas: List of tuples (x, y, width, height) to redact
        
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Redact specified areas
            if redaction_areas:
                draw = ImageDraw.Draw(screenshot)
                for x, y, width, height in redaction_areas:
                    # Draw black rectangle over sensitive area
                    draw.rectangle([x, y, x + width, y + height], fill="black")
            
            # Apply blur if enabled
            if self.blur_enabled:
                screenshot = screenshot.filter(ImageFilter.GaussianBlur(radius=3))
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Compress and save
            screenshot.save(filepath, "PNG", optimize=True, quality=85)
            
            return filepath
        
        except Exception as e:
            print(f"Error capturing screenshot with redaction: {e}")
            return None
    
    def capture_thumbnail(self, max_size: tuple = (800, 600)) -> Optional[str]:
        """
        Capture a thumbnail screenshot (smaller size)
        
        Args:
            max_size: Maximum dimensions (width, height)
        
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Resize to thumbnail
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Apply blur if enabled
            if self.blur_enabled:
                screenshot = screenshot.filter(ImageFilter.GaussianBlur(radius=2))
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thumbnail_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Save with high compression
            screenshot.save(filepath, "PNG", optimize=True, quality=70)
            
            return filepath
        
        except Exception as e:
            print(f"Error capturing thumbnail: {e}")
            return None
    
    def cleanup_old_screenshots(self, max_age_hours: int = 24):
        """
        Delete screenshots older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours to keep screenshots
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.screenshot_dir):
                filepath = os.path.join(self.screenshot_dir, filename)
                
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        print(f"Deleted old screenshot: {filename}")
        
        except Exception as e:
            print(f"Error cleaning up screenshots: {e}")


# For testing
if __name__ == "__main__":
    print("Screenshot capture test")
    print("This will capture 3 screenshots with different settings\n")
    
    capture = ScreenshotCapture(screenshot_dir="./test_screenshots", blur_enabled=True)
    
    # Test 1: Regular screenshot with blur
    print("1. Capturing blurred screenshot...")
    path1 = capture.capture_screenshot(blur_radius=5)
    if path1:
        print(f"   Saved to: {path1}")
    
    time.sleep(2)
    
    # Test 2: Thumbnail
    print("2. Capturing thumbnail...")
    path2 = capture.capture_thumbnail()
    if path2:
        print(f"   Saved to: {path2}")
    
    time.sleep(2)
    
    # Test 3: Screenshot with redaction (example: top-left corner)
    print("3. Capturing with redaction...")
    path3 = capture.capture_with_redaction(redaction_areas=[(0, 0, 200, 100)])
    if path3:
        print(f"   Saved to: {path3}")
    
    print("\nTest complete!")
