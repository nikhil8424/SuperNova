"""
NOVA 3D - Projects API Endpoints
"""
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api.dependencies import get_project_or_404
from app.config import PROJECTS_DIR

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name,
        description=data.description,
        project_type=data.project_type,
        status="active"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create project directory structure
    p_dir = PROJECTS_DIR / project.id
    for sub in ["input", "frames", "colmap", "reconstruction", "exports", "logs"]:
        (p_dir / sub).mkdir(parents=True, exist_ok=True)

    return project.to_dict()

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [p.to_dict() for p in projects]

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project: Project = Depends(get_project_or_404)):
    return project.to_dict()

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    data: ProjectUpdate,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status

    db.commit()
    db.refresh(project)
    return project.to_dict()

@router.delete("/{project_id}", status_code=200)
def delete_project(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    project_id = project.id
    db.delete(project)
    db.commit()

    # Remove project files
    p_dir = PROJECTS_DIR / project_id
    if p_dir.exists():
        shutil.rmtree(p_dir, ignore_errors=True)

    return {"message": f"Project '{project_id}' and all associated assets were deleted successfully."}
