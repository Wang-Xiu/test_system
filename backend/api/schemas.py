from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    yaml_content: str

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(TestCaseBase):
    pass

class TestCaseResponse(TestCaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
