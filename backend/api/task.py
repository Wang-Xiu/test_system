from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.model.models import TestTask, TaskStatus
from backend.api.task_schemas import TaskCreate, TaskResponse
from backend.scheduler.tasks import run_test_cases_task

router = APIRouter(prefix="/api/tasks", tags=["Test Tasks"])

@router.post("/run", response_model=TaskResponse)
def run_tests(task_data: TaskCreate, db: Session = Depends(get_db)):
    if not task_data.case_ids:
        raise HTTPException(status_code=400, detail="case_ids cannot be empty")
        
    # Create task record in DB
    db_task = TestTask(
        case_ids=",".join(map(str, task_data.case_ids)),
        status=TaskStatus.PENDING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Trigger Celery task
    celery_task = run_test_cases_task.delay(db_task.id, task_data.case_ids)
    
    # Update celery_task_id
    db_task.celery_task_id = celery_task.id
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("", response_model=List[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(TestTask).order_by(TestTask.id.desc()).offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
