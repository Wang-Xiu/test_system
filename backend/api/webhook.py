import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert
from backend.database import get_db
from backend.model.models import (
    Project, Environment, TestSuite, TestTask, TaskStatus,
    suite_case_association, task_case_association,
)
from backend.api.suite_schemas import WebhookTriggerRequest
from backend.scheduler.tasks import run_test_cases_task

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])


@router.post("/trigger")
def webhook_trigger(data: WebhookTriggerRequest, db: Session = Depends(get_db)):
    # Find project
    project = db.query(Project).filter(Project.name == data.project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify secret
    if not project.webhook_secret or project.webhook_secret != data.secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    # Resolve environment
    environment_id = None
    if data.environment:
        env = db.query(Environment).filter(
            Environment.project_id == project.id,
            Environment.name == data.environment,
        ).first()
        if env:
            environment_id = env.id

    # Resolve suite and get case_ids
    suite_id = data.suite_id
    if not suite_id:
        # Try to find a default suite for this project
        suite = db.query(TestSuite).filter(TestSuite.project_id == project.id).first()
        if not suite:
            raise HTTPException(status_code=400, detail="No suite specified and no suite found for project")
        suite_id = suite.id

    rows = db.execute(
        suite_case_association.select()
        .where(suite_case_association.c.suite_id == suite_id)
        .order_by(suite_case_association.c.order)
    ).fetchall()
    case_ids = [r.case_id for r in rows]
    if not case_ids:
        raise HTTPException(status_code=400, detail="Suite has no test cases")

    # Create task
    db_task = TestTask(
        case_ids=",".join(map(str, case_ids)),
        status=TaskStatus.PENDING,
        project_id=project.id,
        environment_id=environment_id,
        suite_id=suite_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    for order, cid in enumerate(case_ids):
        db.execute(insert(task_case_association).values(
            task_id=db_task.id, case_id=cid, order=order
        ))
    db.commit()

    celery_task = run_test_cases_task.delay(db_task.id, case_ids, environment_id=environment_id)
    db_task.celery_task_id = celery_task.id
    db.commit()

    return {
        "task_id": db_task.id,
        "message": "Webhook triggered successfully",
        "celery_task_id": celery_task.id,
    }
