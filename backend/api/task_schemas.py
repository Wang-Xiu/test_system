from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.model.models import TaskStatus


class TaskCreate(BaseModel):
    case_ids: List[int] = []
    project_id: Optional[int] = None
    environment_id: Optional[int] = None
    suite_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    case_ids: Optional[str] = None
    status: TaskStatus
    celery_task_id: Optional[str] = None
    report_path: Optional[str] = None
    error_msg: Optional[str] = None
    project_id: Optional[int] = None
    environment_id: Optional[int] = None
    suite_id: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
