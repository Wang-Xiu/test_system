import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from backend.database import get_db

# Add test-engine to path
engine_dir = Path(__file__).parent.parent.parent / "test-engine"
if str(engine_dir) not in sys.path:
    sys.path.insert(0, str(engine_dir))

router = APIRouter(prefix="/api/debug", tags=["Debug"])


class DebugRequest(BaseModel):
    yaml_content: str
    environment_id: Optional[int] = None


@router.post("/test/login")
def mock_login(req: dict):
    if req.get("username") == "testuser" and req.get("password") == "123":
        return {"code": 0, "token": "mock_token_123456"}
    return {"code": 1, "msg": "invalid credentials"}

@router.post("/run")
def debug_run(data: DebugRequest, db: Session = Depends(get_db)):
    """Run a single test case synchronously for debugging."""
    env_config = None

    if data.environment_id:
        from backend.model.models import Environment, Variable
        env = db.query(Environment).filter(Environment.id == data.environment_id).first()
        if env:
            env_config = {
                "base_url": env.base_url or "",
                "headers": env.headers or {},
                "variables": {},
            }
            # Collect variables
            variables = {}
            global_vars = db.query(Variable).filter(
                Variable.project_id.is_(None), Variable.environment_id.is_(None)
            ).all()
            for v in global_vars:
                variables[v.key] = v.value
            if env.project_id:
                project_vars = db.query(Variable).filter(
                    Variable.project_id == env.project_id, Variable.environment_id.is_(None)
                ).all()
                for v in project_vars:
                    variables[v.key] = v.value
            env_vars = db.query(Variable).filter(Variable.environment_id == data.environment_id).all()
            for v in env_vars:
                variables[v.key] = v.value
            env_config["variables"] = variables

    from core.debug_runner import run_single_case
    return run_single_case(data.yaml_content, env_config=env_config)
