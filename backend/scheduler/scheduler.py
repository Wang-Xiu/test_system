"""
Celery Beat task that checks scheduled jobs every 60 seconds.
Uses croniter to match cron expressions.
"""
import sys
from pathlib import Path
from datetime import datetime
from croniter import croniter
from sqlalchemy import insert
from backend.scheduler.celery_app import celery_app
from backend.database import SessionLocal
from backend.model.models import (
    ScheduledJob, TestTask, TaskStatus,
    suite_case_association, task_case_association,
)
from backend.scheduler.tasks import run_test_cases_task

# Add test-engine to path for logger access
engine_dir = Path(__file__).parent.parent.parent / "test-engine"
if str(engine_dir) not in sys.path:
    sys.path.insert(0, str(engine_dir))


@celery_app.task
def check_scheduled_jobs():
    """Scan scheduled_jobs table and trigger any due jobs."""
    db = SessionLocal()
    try:
        jobs = db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
        now = datetime.now()

        for job in jobs:
            try:
                cron = croniter(job.cron_expression, job.last_run_at or job.created_at)
                next_run = cron.get_next(datetime)

                if next_run <= now:
                    _trigger_job(db, job)
                    job.last_run_at = now
                    db.commit()
            except Exception as e:
                import logging
                logging.error(f"Error checking scheduled job {job.id}: {e}")
    finally:
        db.close()


def _trigger_job(db, job: ScheduledJob):
    """Create and trigger a test task from a scheduled job."""
    rows = db.execute(
        suite_case_association.select()
        .where(suite_case_association.c.suite_id == job.suite_id)
        .order_by(suite_case_association.c.order)
    ).fetchall()
    case_ids = [r.case_id for r in rows]
    if not case_ids:
        return

    db_task = TestTask(
        case_ids=",".join(map(str, case_ids)),
        status=TaskStatus.PENDING,
        project_id=job.project_id,
        environment_id=job.environment_id,
        suite_id=job.suite_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    for order, cid in enumerate(case_ids):
        db.execute(insert(task_case_association).values(
            task_id=db_task.id, case_id=cid, order=order
        ))
    db.commit()

    run_test_cases_task.delay(db_task.id, case_ids, environment_id=job.environment_id)
