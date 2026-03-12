from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.model.models import Variable, Project, Environment
from backend.api.project_schemas import VariableCreate, VariableUpdate, VariableResponse

router = APIRouter(prefix="/api/variables", tags=["Variables"])


@router.post("", response_model=VariableResponse)
def create_variable(data: VariableCreate, db: Session = Depends(get_db)):
    # Validate project exists if provided
    if data.project_id:
        project = db.query(Project).filter(Project.id == data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    # Validate environment exists if provided
    if data.environment_id:
        env = db.query(Environment).filter(Environment.id == data.environment_id).first()
        if not env:
            raise HTTPException(status_code=404, detail="Environment not found")

    # Check uniqueness
    existing = db.query(Variable).filter(
        Variable.project_id == data.project_id,
        Variable.environment_id == data.environment_id,
        Variable.key == data.key,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Variable key already exists in this scope")

    var = Variable(**data.model_dump())
    db.add(var)
    db.commit()
    db.refresh(var)
    return var


@router.get("", response_model=List[VariableResponse])
def list_variables(
    project_id: Optional[int] = None,
    env_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Variable)
    if project_id is not None:
        query = query.filter(Variable.project_id == project_id)
    if env_id is not None:
        query = query.filter(Variable.environment_id == env_id)
    return query.all()


@router.put("/{variable_id}", response_model=VariableResponse)
def update_variable(variable_id: int, data: VariableUpdate, db: Session = Depends(get_db)):
    var = db.query(Variable).filter(Variable.id == variable_id).first()
    if not var:
        raise HTTPException(status_code=404, detail="Variable not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(var, key, value)
    db.commit()
    db.refresh(var)
    return var


@router.delete("/{variable_id}")
def delete_variable(variable_id: int, db: Session = Depends(get_db)):
    var = db.query(Variable).filter(Variable.id == variable_id).first()
    if not var:
        raise HTTPException(status_code=404, detail="Variable not found")
    db.delete(var)
    db.commit()
    return {"message": "Variable deleted successfully"}


@router.get("/resolved/{project_id}")
def get_resolved_variables(
    project_id: int,
    env_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get merged variables with priority: environment > project > global."""
    variables = {}

    # Global variables
    global_vars = db.query(Variable).filter(
        Variable.project_id.is_(None),
        Variable.environment_id.is_(None),
    ).all()
    for v in global_vars:
        variables[v.key] = {"value": v.value, "var_type": v.var_type, "source": "global"}

    # Project variables
    project_vars = db.query(Variable).filter(
        Variable.project_id == project_id,
        Variable.environment_id.is_(None),
    ).all()
    for v in project_vars:
        variables[v.key] = {"value": v.value, "var_type": v.var_type, "source": "project"}

    # Environment variables (highest priority)
    if env_id:
        env_vars = db.query(Variable).filter(
            Variable.environment_id == env_id,
        ).all()
        for v in env_vars:
            variables[v.key] = {"value": v.value, "var_type": v.var_type, "source": "environment"}

    return variables
