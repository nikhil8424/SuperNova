"""
NOVA 3D - Assets API Endpoints
"""
import os
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Asset, Project
from app.schemas import AssetResponse
from app.api.dependencies import get_project_or_404
from app.core.security import validate_file_upload, generate_secure_filename, sanitize_filename
from app.config import PROJECTS_DIR, UPLOADS_DIR
from app.reconstruction.video_processor import inspect_video

router = APIRouter(tags=["Assets"])

@router.post("/api/projects/{project_id}/upload", response_model=AssetResponse, status_code=201)
async def upload_project_asset(
    project_id: str,
    file: UploadFile = File(...),
    asset_type: str = Form("video"),
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    orig_name = sanitize_filename(file.filename or "uploaded_file")

    is_valid, err_msg = validate_file_upload(contents, orig_name, asset_type=asset_type)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Secure storage
    secure_name = generate_secure_filename(orig_name, prefix=asset_type)
    proj_input_dir = PROJECTS_DIR / project_id / "input"
    proj_input_dir.mkdir(parents=True, exist_ok=True)
    target_path = proj_input_dir / secure_name

    with open(target_path, "wb") as f:
        f.write(contents)

    metadata = {}
    if asset_type == "video":
        ok, vid_meta, _ = inspect_video(str(target_path))
        if ok:
            metadata = vid_meta

    asset = Asset(
        project_id=project_id,
        asset_type=asset_type,
        original_filename=orig_name,
        storage_path=str(target_path),
        file_size_bytes=len(contents),
        metadata_json=json.dumps(metadata)
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset.to_dict()

@router.get("/api/projects/{project_id}/assets", response_model=List[AssetResponse])
def list_project_assets(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    assets = db.query(Asset).filter(Asset.project_id == project.id).all()
    return [a.to_dict() for a in assets]

@router.delete("/api/assets/{asset_id}", status_code=200)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    if os.path.exists(asset.storage_path):
        try:
            os.remove(asset.storage_path)
        except OSError:
            pass

    db.delete(asset)
    db.commit()
    return {"message": f"Asset '{asset_id}' deleted successfully."}
