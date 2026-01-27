import time
import platform
from datetime import datetime
from typing import Optional

# Platform-specific idle detection
if platform.system() == "Windows":
    try:
        import ctypes
        from ctypes import Structure, POINTER, c_uint, c_ulong, windll
        
        class LASTINPUTINFO(Structure):
            _fields_ = [
                ('cbSize', c_uint),
                ('dwTime', c_ulong)
            ]
    except ImportError:
        ctypes = None

elif platform.system() == "Darwin":  # macOS
    try:
        import Quartz
    except ImportError:
        Quartz = None

else:  # Linux
    try:
        import subprocess
    except ImportError:
        subprocess = None


class IdleTracker:
    """Tracks system idle time"""
    
    def __init__(self, idle_threshold_seconds: int = 300):
        """
        Initialize idle tracker
        
        Args:
            idle_threshold_seconds: Threshold in seconds to consider as idle (default 5 minutes)
        """
        self.idle_threshold = idle_threshold_seconds
        self.platform = platform.system()
    
    def get_idle_time_seconds(self) -> Optional[float]:
        """Get the current system idle time in seconds"""
        try:
            if self.platform == "Windows":
                return self._get_windows_idle_time()
            elif self.platform == "Darwin":
                return self._get_macos_idle_time()
            else:
                return self._get_linux_idle_time()
        except Exception as e:
            print(f"Error getting idle time: {e}")
            return None
    
    def _get_windows_idle_time(self) -> Optional[float]:
        """Get idle time on Windows"""
        if ctypes is None:
            return None
        
        try:
            last_input_info = LASTINPUTINFO()
            last_input_info.cbSize = ctypes.sizeof(last_input_info)
            
            if windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
                millis = windll.kernel32.GetTickCount() - last_input_info.dwTime
                return millis / 1000.0
        except Exception as e:
            print(f"Windows idle detection error: {e}")
        
        return None
    
    def _get_macos_idle_time(self) -> Optional[float]:
        """Get idle time on macOS"""
        if Quartz is None:
            return None
        
        try:
            idle_time = Quartz.CGEventSourceSecondsSinceLastEventType(
                Quartz.kCGEventSourceStateHIDSystemState,
                Quartz.kCGAnyInputEventType
            )
            return idle_time
        except Exception as e:
            print(f"macOS idle detection error: {e}")
        
        return None
    
    def _get_linux_idle_time(self) -> Optional[float]:
        """Get idle time on Linux"""
        try:
            # Using xprintidle (requires installation)
            idle_ms = subprocess.check_output(['xprintidle']).decode().strip()
            return int(idle_ms) / 1000.0
        except Exception as e:
            print(f"Linux idle detection error: {e}")
        
        return None
    
    def is_idle(self) -> bool:
        """Check if the system is currently idle"""
        idle_time = self.get_idle_time_seconds()
        if idle_time is None:
            return False
        return idle_time >= self.idle_threshold
    
    def get_activity_status(self) -> dict:
        """Get current activity status"""
        idle_time = self.get_idle_time_seconds()
        
        if idle_time is None:
            return {
                "status": "unknown",
                "idle_seconds": 0,
                "is_idle": False
            }
        
        is_idle = idle_time >= self.idle_threshold
        
        return {
            "status": "idle" if is_idle else "active",
            "idle_seconds": idle_time,
            "is_idle": is_idle,
            "threshold_seconds": self.idle_threshold
        }


# For testing
if __name__ == "__main__":
    tracker = IdleTracker(idle_threshold_seconds=30)  # 30 seconds for testing
    
    print(f"Idle tracker started on {platform.system()}")
    print(f"Idle threshold: {tracker.idle_threshold} seconds")
    print("Monitoring idle time... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            status = tracker.get_activity_status()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Status: {status['status'].upper():8} | "
                  f"Idle time: {status['idle_seconds']:.1f}s")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping idle tracker...")
