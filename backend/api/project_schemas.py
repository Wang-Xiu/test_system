from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# ---------- Project ----------

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_url: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    notification_config: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    notification_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Environment ----------

class EnvironmentCreate(BaseModel):
    name: str
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_config: Optional[Dict[str, Any]] = None
    is_default: bool = False


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class EnvironmentResponse(BaseModel):
    id: int
    project_id: int
    name: str
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_config: Optional[Dict[str, Any]] = None
    is_default: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Variable ----------

class VariableCreate(BaseModel):
    project_id: Optional[int] = None
    environment_id: Optional[int] = None
    key: str
    value: str
    var_type: str = "string"
    description: Optional[str] = None


class VariableUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    var_type: Optional[str] = None
    description: Optional[str] = None


class VariableResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    environment_id: Optional[int] = None
    key: str
    value: str
    var_type: str = "string"
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
