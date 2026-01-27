from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timedelta, date
import os
import uuid
from beanie import PydanticObjectId
from app.models.user import User
from app.models.activity import Activity, ActivityType, WorkSession, DailyReport
from app.schemas.activity import (
    ActivityCreate, ActivityBatchCreate, ActivityResponse,
    ActivityStatsResponse, WorkSessionResponse
)
from app.dependencies import get_current_user, get_current_admin
from app.utils.validators import sanitize_filename
from config.settings import settings

router = APIRouter(prefix="/api/activity", tags=["Activity"])


@router.post("/submit", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def submit_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user)
):
    """Submit a single activity event"""
    # Create activity
    activity = Activity(
        user_id=current_user.id,
        timestamp=activity_data.timestamp or datetime.utcnow(),
        application_name=activity_data.application_name,
        window_title=activity_data.window_title,
        activity_type=activity_data.activity_type,
        duration_seconds=activity_data.duration_seconds,
        activity_metadata=activity_data.metadata
    )
    
    await activity.insert()
    return activity


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def submit_batch_activities(
    batch_data: ActivityBatchCreate,
    current_user: User = Depends(get_current_user)
):
    """Submit multiple activities at once"""
    activities = []
    
    for activity_data in batch_data.activities:
        activity = Activity(
            user_id=current_user.id,
            timestamp=activity_data.timestamp or datetime.utcnow(),
            application_name=activity_data.application_name,
            window_title=activity_data.window_title,
            activity_type=activity_data.activity_type,
            duration_seconds=activity_data.duration_seconds,
            activity_metadata=activity_data.metadata
        )
        activities.append(activity)
    
    if activities:
        await Activity.insert_many(activities)
    
    return {
        "message": f"Successfully submitted {len(activities)} activities",
        "count": len(activities)
    }


@router.post("/screenshot")
async def upload_screenshot(
    file: UploadFile = File(...),
    activity_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a screenshot"""
    # Validate file type
    allowed_extensions = ['png', 'jpg', 'jpeg']
    if not file.filename or '.' not in file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format"
        )
    
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename
    filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(settings.SCREENSHOT_DIR, filename)
    
    # Ensure directory exists
    os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
    
    # Save file
    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update activity if activity_id provided
    if activity_id:
        activity = await Activity.find_one(
            Activity.id == PydanticObjectId(activity_id), 
            Activity.user_id == current_user.id
        )
        
        if activity:
            activity.screenshot_path = filepath
            await activity.save()
    
    return {
        "message": "Screenshot uploaded successfully",
        "filepath": filepath
    }


@router.get("/user/{user_id}", response_model=List[ActivityResponse])
async def get_user_activities(
    user_id: PydanticObjectId,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get activities for a specific user"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's activities"
        )
    
    # Build query
    query = Activity.find(Activity.user_id == user_id)
    
    if start_date:
        query = query.find(Activity.timestamp >= start_date)
    if end_date:
        query = query.find(Activity.timestamp <= end_date)
    
    activities = await query.sort(-Activity.timestamp).limit(limit).to_list()
    return activities


@router.get("/stats/{user_id}", response_model=ActivityStatsResponse)
async def get_activity_stats(
    user_id: PydanticObjectId,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get activity statistics for a user"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's statistics"
        )
    
    # Default to last 7 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    # Get activities
    activities = await Activity.find(
        Activity.user_id == user_id,
        Activity.timestamp >= start_date,
        Activity.timestamp <= end_date
    ).to_list()
    
    # Calculate stats
    total_activities = len(activities)
    active_time = sum(a.duration_seconds for a in activities if a.activity_type == ActivityType.ACTIVE)
    idle_time = sum(a.duration_seconds for a in activities if a.activity_type == ActivityType.IDLE)
    total_time = active_time + idle_time
    productive_percentage = (active_time / total_time * 100) if total_time > 0 else 0
    
    # Top applications
    app_usage = {}
    for activity in activities:
        if activity.application_name:
            app_usage[activity.application_name] = app_usage.get(activity.application_name, 0) + activity.duration_seconds
    
    top_applications = [
        {"application": app, "duration_seconds": duration}
        for app, duration in sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # Get work sessions
    sessions = await WorkSession.find(
        WorkSession.user_id == user_id,
        WorkSession.start_time >= start_date,
        WorkSession.start_time <= end_date
    ).to_list()
    
    return ActivityStatsResponse(
        total_activities=total_activities,
        active_time_seconds=active_time,
        idle_time_seconds=idle_time,
        productive_percentage=round(productive_percentage, 2),
        top_applications=top_applications,
        sessions=sessions
    )


@router.get("/live", dependencies=[Depends(get_current_admin)])
async def get_live_activity():
    """Get real-time activity status for all users (admin only)"""
    # Get latest activity for each user in the last 10 minutes
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
    
    # Get all activities in the last 10 minutes, sorted by latest first
    activities = await Activity.find(
        Activity.timestamp >= ten_minutes_ago
    ).sort(-Activity.timestamp).to_list()
    
    # Group by user to get the latest activity for each
    user_latest = {}
    for act in activities:
        uid_str = str(act.user_id)
        if uid_str not in user_latest:
            user_latest[uid_str] = act
    
    latest_results = user_latest.values()
    
    result = []
    for act in latest_results:
        user = await User.get(act.user_id)
        if user:
            result.append({
                "user_id": str(user.id),
                "user_name": user.full_name,
                "user_email": user.email,
                "last_activity": act.timestamp,
                "application": act.application_name,
                "status": "active" if act.activity_type == ActivityType.ACTIVE else "idle"
            })
    
    return result


@router.get("/tracking-status")
async def get_tracking_status(
    current_user: User = Depends(get_current_user)
):
    """Get current tracking status for the user"""
    # In a real app, this might check a local agent status or a flag
    return {"enabled": current_user.consent_accepted}


@router.post("/tracking-status")
async def toggle_tracking(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Toggle tracking status"""
    # This might send a signal to the agent if we had websockets
    return {"enabled": data.get("enabled", True)}


@router.get("/timeline")
async def get_timeline(
    report_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get activity timeline for a specific date"""
    if not report_date:
        report_date = datetime.utcnow().date()
    
    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())
    
    activities = await Activity.find(
        Activity.user_id == current_user.id,
        Activity.timestamp >= start_datetime,
        Activity.timestamp <= end_datetime
    ).sort(Activity.timestamp).to_list()
    
    return activities


@router.get("/daily-summary")
async def get_daily_summary(
    report_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get daily summary for the user"""
    if not report_date:
        report_date = datetime.utcnow().date()
    
    report = await DailyReport.find_one(
        DailyReport.user_id == current_user.id,
        DailyReport.report_date == report_date
    )
    
    if not report:
        # Try to generate it
        from app.services.reports import generate_daily_report
        report = await generate_daily_report(current_user.id, report_date)
    
    return report
