from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestAccountCreate(BaseModel):
    project_id: int
    name: str
    username: str
    password: Optional[str] = None
    description: Optional[str] = None
    status: int = 1

class TestAccountUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

class TestAccountResponse(BaseModel):
    id: int
    project_id: int
    name: str
    username: str
    password: Optional[str] = None
    description: Optional[str] = None
    status: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
