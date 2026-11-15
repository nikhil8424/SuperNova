"""
NOVA 3D - Machine Models & Components API Endpoints
"""
import json
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import MachineModel, Component, Project
from app.schemas import MachineModelResponse, ComponentResponse
from app.api.dependencies import get_project_or_404
from app.core.security import validate_file_upload, generate_secure_filename, sanitize_filename
from app.config import PROJECTS_DIR
from app.machine.model_loader import inspect_3d_model

router = APIRouter(tags=["Machine Models"])

@router.post("/api/projects/{project_id}/models", response_model=MachineModelResponse, status_code=201)
async def upload_machine_model(
    project_id: str,
    file: UploadFile = File(...),
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    orig_name = sanitize_filename(file.filename or "model.glb")

    is_valid, err_msg = validate_file_upload(contents, orig_name, asset_type="model")
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Save to project input dir
    secure_name = generate_secure_filename(orig_name, prefix="machine")
    target_path = PROJECTS_DIR / project_id / "input" / secure_name
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as f:
        f.write(contents)

    # Parse 3D model
    try:
        model_info = inspect_3d_model(str(target_path))
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to inspect 3D model: {str(e)}")

    machine_model = MachineModel(
        project_id=project_id,
        model_name=Path(orig_name).stem,
        format=model_info["format"],
        storage_path=str(target_path),
        vertex_count=model_info["total_vertices"],
        face_count=model_info["total_faces"],
        component_count=model_info["component_count"],
        bounding_box_json=json.dumps(model_info["bounding_box"])
    )
    db.add(machine_model)
    db.flush()

    # Add components
    for comp in model_info["components"]:
        c = Component(
            machine_model_id=machine_model.id,
            node_name=comp["node_name"],
            display_name=comp["display_name"],
            parent_name=comp["parent_name"],
            category=comp["category"],
            vertex_count=comp["vertex_count"],
            face_count=comp["face_count"],
            center_json=json.dumps(comp["center"]),
            bounds_json=json.dumps(comp["bounds"]),
            transform_json=json.dumps(comp["transform"]),
            is_visible=True
        )
        db.add(c)

    db.commit()
    db.refresh(machine_model)

    return machine_model.to_dict()

@router.get("/api/models/{model_id}/components", response_model=List[ComponentResponse])
def get_model_components(model_id: str, db: Session = Depends(get_db)):
    model = db.query(MachineModel).filter(MachineModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Machine model not found.")
    return [c.to_dict() for c in model.components]

@router.get("/api/models/{model_id}", response_model=MachineModelResponse)
def get_machine_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(MachineModel).filter(MachineModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Machine model not found.")
    return model.to_dict()
