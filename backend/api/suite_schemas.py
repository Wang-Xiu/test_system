from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------- Suite ----------

class SuiteCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    case_ids: List[int] = []


class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    case_ids: Optional[List[int]] = None


class SuiteCaseItem(BaseModel):
    id: int
    name: str
    order: int

    class Config:
        from_attributes = True


class SuiteResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SuiteDetailResponse(SuiteResponse):
    cases: List[SuiteCaseItem] = []


# ---------- Schedule ----------

class ScheduleCreate(BaseModel):
    project_id: int
    environment_id: int
    suite_id: int
    name: str
    cron_expression: str
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    environment_id: Optional[int] = None
    suite_id: Optional[int] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    project_id: int
    environment_id: int
    suite_id: int
    name: str
    cron_expression: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Webhook ----------

class WebhookTriggerRequest(BaseModel):
    project_name: str
    environment: Optional[str] = None
    suite_id: Optional[int] = None
    secret: str
    callback_url: Optional[str] = None
