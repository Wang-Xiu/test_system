from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from typing import List
from backend.database import get_db
from backend.model.models import TestSuite, TestCase, suite_case_association, task_case_association, TestTask, TaskStatus
from backend.api.suite_schemas import SuiteCreate, SuiteUpdate, SuiteResponse, SuiteDetailResponse, SuiteCaseItem
from backend.scheduler.tasks import run_test_cases_task

router = APIRouter(prefix="/api/suites", tags=["Test Suites"])


@router.post("", response_model=SuiteResponse)
def create_suite(data: SuiteCreate, db: Session = Depends(get_db)):
    suite = TestSuite(project_id=data.project_id, name=data.name, description=data.description)
    db.add(suite)
    db.commit()
    db.refresh(suite)

    # Add case associations
    for order, cid in enumerate(data.case_ids):
        db.execute(insert(suite_case_association).values(
            suite_id=suite.id, case_id=cid, order=order
        ))
    db.commit()
    return suite


@router.get("", response_model=List[SuiteResponse])
def list_suites(project_id: int = None, db: Session = Depends(get_db)):
    query = db.query(TestSuite)
    if project_id is not None:
        query = query.filter(TestSuite.project_id == project_id)
    return query.all()


@router.get("/{suite_id}", response_model=SuiteDetailResponse)
def get_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")

    # Get ordered case list
    rows = db.execute(
        suite_case_association.select()
        .where(suite_case_association.c.suite_id == suite_id)
        .order_by(suite_case_association.c.order)
    ).fetchall()

    case_ids = [r.case_id for r in rows]
    cases_map = {}
    if case_ids:
        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        cases_map = {c.id: c for c in cases}

    case_items = []
    for r in rows:
        c = cases_map.get(r.case_id)
        if c:
            case_items.append(SuiteCaseItem(id=c.id, name=c.name, order=r.order))

    return SuiteDetailResponse(
        id=suite.id,
        project_id=suite.project_id,
        name=suite.name,
        description=suite.description,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
        cases=case_items,
    )


@router.put("/{suite_id}", response_model=SuiteResponse)
def update_suite(suite_id: int, data: SuiteUpdate, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")

    if data.name is not None:
        suite.name = data.name
    if data.description is not None:
        suite.description = data.description

    # Replace case associations if provided
    if data.case_ids is not None:
        db.execute(delete(suite_case_association).where(suite_case_association.c.suite_id == suite_id))
        for order, cid in enumerate(data.case_ids):
            db.execute(insert(suite_case_association).values(
                suite_id=suite_id, case_id=cid, order=order
            ))

    db.commit()
    db.refresh(suite)
    return suite


@router.delete("/{suite_id}")
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    db.delete(suite)
    db.commit()
    return {"message": "Suite deleted successfully"}


@router.post("/{suite_id}/run")
def run_suite(suite_id: int, env_id: int = None, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")

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
        project_id=suite.project_id,
        environment_id=env_id,
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

    celery_task = run_test_cases_task.delay(db_task.id, case_ids, environment_id=env_id)
    db_task.celery_task_id = celery_task.id
    db.commit()

    return {"task_id": db_task.id, "message": "Suite execution started"}
