# WorkProof Client Agent

Python-based client agent that runs on employee laptops to monitor work activity and submit data to the WorkProof backend.

## Features

- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Activity Monitoring**: Tracks active applications and window titles
- **Idle Detection**: Automatically detects idle time using OS-specific APIs
- **Screenshot Capture**: Optional screenshot capture with privacy features (blur/redaction)
- **Offline Support**: Queues data locally when server is unreachable
- **Privacy-Focused**: Non-intrusive monitoring (no keylogging)
- **Configurable**: Easy configuration via JSON file

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the agent:
```bash
# Edit config.json with your settings
{
  "server_url": "http://your-server:5000",
  "user_email": "your.email@company.com",
  "user_password": "your-password",
  "collection_interval": 60,
  "screenshot_enabled": true,
  "screenshot_interval": 300,
  "idle_threshold": 300
}
```

3. Run the agent:
```bash
python main.py
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `server_url` | Backend server URL | `http://localhost:5000` |
| `user_email` | Employee email for authentication | Required |
| `user_password` | Employee password | Required |
| `collection_interval` | Activity collection interval (seconds) | 60 |
| `screenshot_enabled` | Enable screenshot capture | true |
| `screenshot_interval` | Screenshot capture interval (seconds) | 300 |
| `idle_threshold` | Idle detection threshold (seconds) | 300 |
| `approved_applications` | List of allowed applications to track | [] (all) |
| `blur_screenshots` | Apply blur to screenshots for privacy | true |
| `offline_storage_path` | Path for offline data storage | `./offline_data` |

## What is Monitored

✅ **Monitored:**
- Active application names
- Window titles
- Mouse/keyboard activity timestamps (NOT content)
- Idle time
- Optional screenshots (with blur/redaction)

❌ **NOT Monitored:**
- Actual keystrokes or typed content
- Clipboard data
- Personal browsing outside approved applications
- System passwords or credentials

## Privacy & Security

- All data is encrypted during transmission (HTTPS)
- Screenshots can be blurred or disabled
- No keylogging - only activity detection
- Offline data is stored locally and encrypted
- User has visibility into what is being monitored

## Platform-Specific Notes

### Windows
- Requires `pygetwindow` for window detection
- May need to run as administrator for some features

### macOS
- Requires accessibility permissions
- Install via: `pip install pyobjc-framework-Quartz`

### Linux
- Requires `xdotool` and `xprintidle`
- Install via: `sudo apt-get install xdotool xprintidle`

## Troubleshooting

**Agent won't start:**
- Check that config.json has valid credentials
- Verify server URL is correct and reachable
- Ensure all dependencies are installed

**Screenshots not working:**
- Check screenshot_enabled is true in config
- Verify permissions (especially on macOS/Linux)
- Check available disk space

**Activities not submitting:**
- Check network connection
- Verify server is running
- Check offline queue: activities will sync when connection restored

## Auto-Start on Boot

### Windows
Create a shortcut to `main.py` and place in:
```
C:\Users\<Username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

### macOS
Create a LaunchAgent plist file in:
```
~/Library/LaunchAgents/com.workproof.agent.plist
```

### Linux
Add to crontab:
```bash
@reboot /usr/bin/python3 /path/to/client-agent/main.py
```

## Development

Run in debug mode:
```bash
python main.py --debug
```

Test individual components:
```bash
# Test activity collector
python collector/activity.py

# Test idle tracker
python collector/idle_tracker.py

# Test screenshot capture
python collector/screenshot.py

# Test API client
python sender/api_client.py
```

## License

Proprietary - Internal use only
