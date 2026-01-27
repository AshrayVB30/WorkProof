from datetime import datetime, timedelta
from typing import Tuple
from app.models.activity import ActivityType


def calculate_idle_status(last_activity_time: datetime, current_time: datetime, idle_threshold_seconds: int = 300) -> Tuple[ActivityType, int]:
    """
    Calculate if the current period should be marked as idle
    
    Args:
        last_activity_time: Timestamp of last recorded activity
        current_time: Current timestamp
        idle_threshold_seconds: Threshold in seconds to consider as idle (default 5 minutes)
    
    Returns:
        Tuple of (ActivityType, duration_seconds)
    """
    time_diff = (current_time - last_activity_time).total_seconds()
    
    if time_diff >= idle_threshold_seconds:
        return ActivityType.IDLE, int(time_diff)
    else:
        return ActivityType.ACTIVE, int(time_diff)


def is_idle_period(duration_seconds: int, idle_threshold_seconds: int = 300) -> bool:
    """Check if a duration qualifies as an idle period"""
    return duration_seconds >= idle_threshold_seconds


def classify_activity_intensity(
    mouse_movements: int,
    keyboard_presses: int,
    duration_seconds: int
) -> ActivityType:
    """
    Classify activity intensity based on input events
    
    Args:
        mouse_movements: Number of mouse movements
        keyboard_presses: Number of keyboard presses
        duration_seconds: Duration of the period
    
    Returns:
        ActivityType (ACTIVE or IDLE)
    """
    # Calculate events per minute
    if duration_seconds == 0:
        return ActivityType.IDLE
    
    events_per_minute = (mouse_movements + keyboard_presses) / (duration_seconds / 60)
    
    # Threshold: at least 10 events per minute to be considered active
    ACTIVITY_THRESHOLD = 10
    
    if events_per_minute >= ACTIVITY_THRESHOLD:
        return ActivityType.ACTIVE
    else:
        return ActivityType.IDLE
