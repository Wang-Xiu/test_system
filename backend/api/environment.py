from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.model.models import Environment, Project
from backend.api.project_schemas import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse

router = APIRouter(tags=["Environments"])


@router.post("/api/projects/{project_id}/envs", response_model=EnvironmentResponse)
def create_environment(project_id: int, data: EnvironmentCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(Environment).filter(
        Environment.project_id == project_id,
        Environment.name == data.name,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Environment name already exists in this project")

    env = Environment(project_id=project_id, **data.model_dump())
    # If this is set as default, unset other defaults
    if env.is_default:
        db.query(Environment).filter(
            Environment.project_id == project_id,
            Environment.is_default == True,
        ).update({"is_default": False})
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


@router.get("/api/projects/{project_id}/envs", response_model=List[EnvironmentResponse])
def list_environments(project_id: int, db: Session = Depends(get_db)):
    return db.query(Environment).filter(Environment.project_id == project_id).all()


@router.put("/api/envs/{env_id}", response_model=EnvironmentResponse)
def update_environment(env_id: int, data: EnvironmentUpdate, db: Session = Depends(get_db)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(env, key, value)

    # If setting as default, unset other defaults in same project
    if data.is_default:
        db.query(Environment).filter(
            Environment.project_id == env.project_id,
            Environment.id != env.id,
            Environment.is_default == True,
        ).update({"is_default": False})

    db.commit()
    db.refresh(env)
    return env


@router.delete("/api/envs/{env_id}")
def delete_environment(env_id: int, db: Session = Depends(get_db)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    db.delete(env)
    db.commit()
    return {"message": "Environment deleted successfully"}
