from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TestCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    yaml_content: str
    project_id: Optional[int] = None


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    yaml_content: Optional[str] = None
    project_id: Optional[int] = None


class TestCaseResponse(TestCaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
