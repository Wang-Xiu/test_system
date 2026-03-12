from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.model.models import ScheduledJob
from backend.api.suite_schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/api/schedules", tags=["Scheduled Jobs"])


@router.post("", response_model=ScheduleResponse)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    job = ScheduledJob(**data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(project_id: int = None, db: Session = Depends(get_db)):
    query = db.query(ScheduledJob)
    if project_id is not None:
        query = query.filter(ScheduledJob.project_id == project_id)
    return query.all()


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    job = db.query(ScheduledJob).filter(ScheduledJob.id == schedule_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.put("/{schedule_id}/toggle", response_model=ScheduleResponse)
def toggle_schedule(schedule_id: int, db: Session = Depends(get_db)):
    job = db.query(ScheduledJob).filter(ScheduledJob.id == schedule_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    job.is_active = not job.is_active
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    job = db.query(ScheduledJob).filter(ScheduledJob.id == schedule_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(job)
    db.commit()
    return {"message": "Schedule deleted successfully"}
