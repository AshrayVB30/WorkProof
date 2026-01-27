from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from app.models.activity import Activity, WorkSession, ActivityType
from app.models.user import User


def detect_work_sessions(user_id: int, activities: List[Activity], db: Session) -> List[WorkSession]:
    """
    Detect and create work sessions from activities
    A new session starts after a gap of more than 30 minutes
    """
    if not activities:
        return []
    
    # Sort activities by timestamp
    sorted_activities = sorted(activities, key=lambda x: x.timestamp)
    
    sessions = []
    current_session_start = sorted_activities[0].timestamp
    current_session_activities = []
    
    SESSION_GAP_MINUTES = 30
    
    for i, activity in enumerate(sorted_activities):
        # Check if this activity starts a new session
        if i > 0:
            time_gap = (activity.timestamp - sorted_activities[i-1].timestamp).total_seconds() / 60
            
            if time_gap > SESSION_GAP_MINUTES:
                # End current session and start new one
                if current_session_activities:
                    session = create_session_from_activities(
                        user_id, current_session_start, 
                        sorted_activities[i-1].timestamp,
                        current_session_activities, db
                    )
                    sessions.append(session)
                
                current_session_start = activity.timestamp
                current_session_activities = []
        
        current_session_activities.append(activity)
    
    # Create final session
    if current_session_activities:
        session = create_session_from_activities(
            user_id, current_session_start,
            sorted_activities[-1].timestamp,
            current_session_activities, db
        )
        sessions.append(session)
    
    return sessions


def create_session_from_activities(
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    activities: List[Activity],
    db: Session
) -> WorkSession:
    """Create a work session from a list of activities"""
    total_duration = sum(a.duration_seconds for a in activities)
    active_duration = sum(a.duration_seconds for a in activities if a.activity_type == ActivityType.ACTIVE)
    idle_duration = sum(a.duration_seconds for a in activities if a.activity_type == ActivityType.IDLE)
    
    productive_percentage = (active_duration / total_duration * 100) if total_duration > 0 else 0
    screenshot_count = sum(1 for a in activities if a.screenshot_path)
    
    session = WorkSession(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        total_duration_seconds=total_duration,
        active_duration_seconds=active_duration,
        idle_duration_seconds=idle_duration,
        productive_percentage=round(productive_percentage, 2),
        activity_count=len(activities),
        screenshot_count=screenshot_count
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session
