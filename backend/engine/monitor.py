import mss
import mss.tools
from PIL import Image
import os
import time
import logging

logger = logging.getLogger("WorkProof.Engine.Monitor")

class ScreenMonitor:
    """
    Captures screenshots of the screen for session logging.
    """
    def __init__(self, output_dir="backend/screenshots"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def capture_screenshot(self, filename=None):
        """
        Captures the primary monitor and saves it.
        """
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"
            
        filepath = os.path.join(self.output_dir, filename)
        
        with mss.mss() as sct:
            # Get the first monitor
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
            
        return filepath

if __name__ == "__main__":
    monitor = ScreenMonitor()
    path = monitor.capture_screenshot("test_shot.png")
    print(f"Saved screenshot to: {path}")
