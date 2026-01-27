import psutil
import platform
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pynput import mouse, keyboard

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import pygetwindow as gw
    except ImportError:
        gw = None
elif platform.system() == "Darwin":  # macOS
    try:
        from AppKit import NSWorkspace
    except ImportError:
        NSWorkspace = None
else:  # Linux
    try:
        import subprocess
    except ImportError:
        subprocess = None


class ActivityCollector:
    """Collects activity data from the system"""
    
    def __init__(self):
        self.last_activity_time = datetime.now()
        self.mouse_movements = 0
        self.keyboard_presses = 0
        self.current_app = None
        self.current_window = None
        
        # Start input listeners
        self._start_listeners()
    
    def _start_listeners(self):
        """Start mouse and keyboard listeners"""
        # Mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()
        
        # Keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_keyboard_press
        )
        self.keyboard_listener.start()
    
    def _on_mouse_move(self, x, y):
        """Callback for mouse movement"""
        self.mouse_movements += 1
        self.last_activity_time = datetime.now()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Callback for mouse click"""
        if pressed:
            self.mouse_movements += 1
            self.last_activity_time = datetime.now()
    
    def _on_keyboard_press(self, key):
        """Callback for keyboard press"""
        self.keyboard_presses += 1
        self.last_activity_time = datetime.now()
    
    def get_active_window_info(self) -> Dict[str, Optional[str]]:
        """Get information about the currently active window"""
        try:
            if platform.system() == "Windows":
                return self._get_windows_active_window()
            elif platform.system() == "Darwin":
                return self._get_macos_active_window()
            else:
                return self._get_linux_active_window()
        except Exception as e:
            print(f"Error getting active window: {e}")
            return {"application": None, "window_title": None}
    
    def _get_windows_active_window(self) -> Dict[str, Optional[str]]:
        """Get active window on Windows"""
        if gw is None:
            return {"application": None, "window_title": None}
        
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                # Get process name
                try:
                    import win32process
                    import win32gui
                    hwnd = active_window._hWnd
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    app_name = process.name()
                except:
                    app_name = "Unknown"
                
                return {
                    "application": app_name,
                    "window_title": active_window.title
                }
        except Exception as e:
            print(f"Windows window detection error: {e}")
        
        return {"application": None, "window_title": None}
    
    def _get_macos_active_window(self) -> Dict[str, Optional[str]]:
        """Get active window on macOS"""
        if NSWorkspace is None:
            return {"application": None, "window_title": None}
        
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            app_name = active_app['NSApplicationName']
            # Note: Getting window title on macOS requires accessibility permissions
            return {
                "application": app_name,
                "window_title": None  # Requires additional permissions
            }
        except Exception as e:
            print(f"macOS window detection error: {e}")
        
        return {"application": None, "window_title": None}
    
    def _get_linux_active_window(self) -> Dict[str, Optional[str]]:
        """Get active window on Linux"""
        try:
            # Using xdotool (requires installation)
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_title = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            window_pid = subprocess.check_output(['xdotool', 'getwindowpid', window_id]).decode().strip()
            
            process = psutil.Process(int(window_pid))
            app_name = process.name()
            
            return {
                "application": app_name,
                "window_title": window_title
            }
        except Exception as e:
            print(f"Linux window detection error: {e}")
        
        return {"application": None, "window_title": None}
    
    def collect_activity_data(self) -> Dict[str, Any]:
        """Collect current activity data"""
        window_info = self.get_active_window_info()
        
        activity_data = {
            "timestamp": datetime.now().isoformat(),
            "application_name": window_info["application"],
            "window_title": window_info["window_title"],
            "mouse_movements": self.mouse_movements,
            "keyboard_presses": self.keyboard_presses,
            "metadata": {
                "platform": platform.system(),
                "platform_version": platform.version()
            }
        }
        
        # Reset counters
        self.mouse_movements = 0
        self.keyboard_presses = 0
        
        return activity_data
    
    def get_time_since_last_activity(self) -> float:
        """Get seconds since last user input"""
        return (datetime.now() - self.last_activity_time).total_seconds()
    
    def stop(self):
        """Stop the activity collector"""
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()


# For testing
if __name__ == "__main__":
    collector = ActivityCollector()
    
    try:
        print("Activity collector started. Press Ctrl+C to stop.")
        while True:
            time.sleep(10)  # Collect every 10 seconds
            data = collector.collect_activity_data()
            print(f"\nCollected activity data:")
            print(f"  Application: {data['application_name']}")
            print(f"  Window: {data['window_title']}")
            print(f"  Mouse movements: {data['mouse_movements']}")
            print(f"  Keyboard presses: {data['keyboard_presses']}")
            print(f"  Time since last activity: {collector.get_time_since_last_activity():.1f}s")
    except KeyboardInterrupt:
        print("\nStopping collector...")
        collector.stop()
