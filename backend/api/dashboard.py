from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from backend.database import get_db
from backend.model.models import TestCase, TestTask, TaskStatus

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Total test cases
    total_cases = db.query(func.count(TestCase.id)).scalar() or 0
    
    # Total tasks
    total_tasks = db.query(func.count(TestTask.id)).scalar() or 0
    
    # Today's tasks
    today = date.today()
    today_tasks = db.query(func.count(TestTask.id)).filter(
        func.date(TestTask.created_at) == today
    ).scalar() or 0
    
    # Task success rate
    success_tasks = db.query(func.count(TestTask.id)).filter(
        TestTask.status == TaskStatus.SUCCESS
    ).scalar() or 0
    
    # Calculate success rate (only considering finished tasks)
    finished_tasks = db.query(func.count(TestTask.id)).filter(
        TestTask.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.ERROR])
    ).scalar() or 0
    
    success_rate = 0
    if finished_tasks > 0:
        success_rate = round((success_tasks / finished_tasks) * 100, 2)
        
    # Recent tasks for chart
    recent_tasks = db.query(TestTask).order_by(TestTask.id.desc()).limit(5).all()
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
