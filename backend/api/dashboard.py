from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, date, timedelta
from backend.database import get_db
from backend.model.models import TestCase, TestTask, TaskStatus

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(project_id: int = None, db: Session = Depends(get_db)):
    case_query = db.query(func.count(TestCase.id))
    task_query = db.query(func.count(TestTask.id))
    if project_id:
        case_query = case_query.filter(TestCase.project_id == project_id)
        task_query = task_query.filter(TestTask.project_id == project_id)

    total_cases = case_query.scalar() or 0
    total_tasks = task_query.scalar() or 0

    today = date.today()
    today_query = db.query(func.count(TestTask.id)).filter(func.date(TestTask.created_at) == today)
    if project_id:
        today_query = today_query.filter(TestTask.project_id == project_id)
    today_tasks = today_query.scalar() or 0

    success_query = db.query(func.count(TestTask.id)).filter(TestTask.status == TaskStatus.SUCCESS)
    finished_query = db.query(func.count(TestTask.id)).filter(
        TestTask.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.ERROR])
    )
    if project_id:
        success_query = success_query.filter(TestTask.project_id == project_id)
        finished_query = finished_query.filter(TestTask.project_id == project_id)

    success_tasks = success_query.scalar() or 0
    finished_tasks = finished_query.scalar() or 0
    success_rate = round((success_tasks / finished_tasks) * 100, 2) if finished_tasks > 0 else 0

    recent_query = db.query(TestTask).order_by(TestTask.id.desc())
    if project_id:
        recent_query = recent_query.filter(TestTask.project_id == project_id)
    recent_tasks = recent_query.limit(5).all()
    recent_tasks_data = [
        {
            "id": task.id,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
        for task in recent_tasks
    ]

    return {
        "total_cases": total_cases,
        "total_tasks": total_tasks,
        "today_tasks": today_tasks,
        "success_rate": success_rate,
        "recent_tasks": recent_tasks_data
    }


@router.get("/trends")
def get_trends(project_id: int = None, days: int = 7, db: Session = Depends(get_db)):
    """Get daily task result trends for the last N days."""
    start_date = date.today() - timedelta(days=days - 1)

    query = db.query(
        cast(TestTask.created_at, Date).label("day"),
        TestTask.status,
        func.count(TestTask.id).label("count"),
    ).filter(
        func.date(TestTask.created_at) >= start_date,
        TestTask.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.ERROR]),
    )
    if project_id:
        query = query.filter(TestTask.project_id == project_id)

    rows = query.group_by("day", TestTask.status).all()

    # Build result dict keyed by date string
    trends = {}
    for i in range(days):
        d = (start_date + timedelta(days=i)).isoformat()
        trends[d] = {"date": d, "success": 0, "failed": 0, "error": 0}

    for row in rows:
        day_str = row.day.isoformat() if hasattr(row.day, 'isoformat') else str(row.day)
        if day_str in trends:
            status_key = row.status.value if hasattr(row.status, 'value') else row.status
            if status_key in trends[day_str]:
                trends[day_str][status_key] = row.count

    return list(trends.values())
