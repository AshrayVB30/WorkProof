from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional
from datetime import datetime, date, timedelta
from beanie import PydanticObjectId
from app.models.user import User
from app.models.activity import DailyReport, Activity, WorkSession, ActivityType
from app.schemas.activity import DailyReportResponse
from app.dependencies import get_current_user, get_current_admin
from app.services.reports import generate_daily_report, generate_pdf_report, generate_excel_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/daily/{user_id}", response_model=DailyReportResponse)
async def get_daily_report(
    user_id: PydanticObjectId,
    report_date: date,
    current_user: User = Depends(get_current_user)
):
    """Get daily work summary for a specific user and date"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's report"
        )
    
    # Check if report exists
    report = await DailyReport.find_one(
        DailyReport.user_id == user_id,
        DailyReport.report_date == report_date
    )
    
    # Generate report if it doesn't exist
    if not report:
        report = await generate_daily_report(user_id, report_date)
    
    if not report:
        # Return an empty report if no activities and can't generate
        return DailyReport(
            user_id=user_id,
            report_date=report_date,
            total_hours=0,
            active_hours=0,
            idle_hours=0,
            productive_percentage=0,
            total_activities=0,
            session_count=0,
            screenshot_count=0
        )
    
    return report


@router.get("/range/{user_id}", response_model=List[DailyReportResponse])
async def get_reports_range(
    user_id: PydanticObjectId,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user)
):
    """Get daily reports for a date range"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's reports"
        )
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    # Get existing reports
    reports = await DailyReport.find(
        DailyReport.user_id == user_id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    ).sort(DailyReport.report_date).to_list()
    
    # Generate missing reports
    existing_dates = {report.report_date for report in reports}
    current_date = start_date
    
    while current_date <= end_date:
        if current_date not in existing_dates:
            new_report = await generate_daily_report(user_id, current_date)
            if new_report:
                reports.append(new_report)
        current_date += timedelta(days=1)
    
    # Sort by date
    reports.sort(key=lambda x: x.report_date)
    
    return reports


@router.get("/export/pdf/{user_id}")
async def export_pdf_report(
    user_id: PydanticObjectId,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user)
):
    """Export report as PDF"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this user's report"
        )
    
    # Get user
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get reports
    reports = await DailyReport.find(
        DailyReport.user_id == user_id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    ).sort(DailyReport.report_date).to_list()
    
    # Generate PDF
    pdf_content = generate_pdf_report(user, reports, start_date, end_date)
    
    # Return PDF response
    filename = f"workproof_report_{user.full_name}_{start_date}_{end_date}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/excel/{user_id}")
async def export_excel_report(
    user_id: PydanticObjectId,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user)
):
    """Export report as Excel"""
    # Check permissions
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this user's report"
        )
    
    # Get user
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get reports
    reports = await DailyReport.find(
        DailyReport.user_id == user_id,
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    ).sort(DailyReport.report_date).to_list()
    
    # Generate Excel
    excel_content = generate_excel_report(user, reports, start_date, end_date)
    
    # Return Excel response
    filename = f"workproof_report_{user.full_name}_{start_date}_{end_date}.xlsx"
    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/team", dependencies=[Depends(get_current_admin)])
async def get_team_overview(
    report_date: Optional[date] = None
):
    """Get team-wide productivity overview (admin only)"""
    if not report_date:
        report_date = date.today()
    
    # Get all active employees
    employees = await User.find(User.role == "employee", User.is_active == True).to_list()
    
    team_data = []
    
    for employee in employees:
        # Get or generate daily report
        report = await DailyReport.find_one(
            DailyReport.user_id == employee.id,
            DailyReport.report_date == report_date
        )
        
        if not report:
            report = await generate_daily_report(employee.id, report_date)
        
        if report:
            team_data.append({
                "user_id": str(employee.id),
                "user_name": employee.full_name,
                "employee_id": employee.employee_id,
                "department": employee.department,
                "expected_hours": employee.expected_daily_hours,
                "actual_hours": report.total_hours,
                "active_hours": report.active_hours,
                "productive_percentage": report.productive_percentage,
                "status": "on_track" if report.total_hours >= employee.expected_daily_hours * 0.8 else "behind"
            })
        else:
            team_data.append({
                "user_id": str(employee.id),
                "user_name": employee.full_name,
                "employee_id": employee.employee_id,
                "department": employee.department,
                "expected_hours": employee.expected_daily_hours,
                "actual_hours": 0,
                "active_hours": 0,
                "productive_percentage": 0,
                "status": "absent"
            })
    
    return {
        "report_date": report_date,
        "total_employees": len(team_data),
        "employees": team_data
    }
