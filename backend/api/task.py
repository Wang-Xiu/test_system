from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert
from typing import List
from backend.database import get_db
from backend.model.models import TestTask, TestCase, TaskStatus, task_case_association, TestSuite, suite_case_association
from backend.api.task_schemas import TaskCreate, TaskResponse
from backend.scheduler.tasks import run_test_cases_task

router = APIRouter(prefix="/api/tasks", tags=["Test Tasks"])


@router.post("/run", response_model=TaskResponse)
def run_tests(task_data: TaskCreate, db: Session = Depends(get_db)):
    # Determine case_ids: from suite or from request body
    case_ids = list(task_data.case_ids) if task_data.case_ids else []

    if task_data.suite_id:
        # Fetch case ids from suite in order
        suite = db.query(TestSuite).filter(TestSuite.id == task_data.suite_id).first()
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")
        suite_rows = db.execute(
            suite_case_association.select()
            .where(suite_case_association.c.suite_id == task_data.suite_id)
            .order_by(suite_case_association.c.order)
        ).fetchall()
        case_ids = [row.case_id for row in suite_rows]

    if not case_ids:
        raise HTTPException(status_code=400, detail="case_ids cannot be empty")

    # Create task record in DB
    db_task = TestTask(
        case_ids=",".join(map(str, case_ids)),
        status=TaskStatus.PENDING,
        project_id=task_data.project_id,
        environment_id=task_data.environment_id,
        suite_id=task_data.suite_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Write association table rows
    for order, cid in enumerate(case_ids):
        db.execute(
            insert(task_case_association).values(
                task_id=db_task.id, case_id=cid, order=order
            )
        )
    db.commit()

    # Trigger Celery task
    celery_task = run_test_cases_task.delay(
        db_task.id, case_ids, environment_id=task_data.environment_id
    )

    # Update celery_task_id
    db_task.celery_task_id = celery_task.id
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db),
):
    query = db.query(TestTask)
    if project_id is not None:
        query = query.filter(TestTask.project_id == project_id)
    tasks = query.order_by(TestTask.id.desc()).offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
