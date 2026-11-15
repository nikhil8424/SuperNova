"""
NOVA 3D - Scene Viewer API Endpoints
"""
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Scene

router = APIRouter(tags=["Scenes"])

@router.get("/api/scenes/{scene_id}")
def get_scene(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    return scene.to_dict()

@router.get("/api/scenes/{scene_id}/metadata")
def get_scene_metadata(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    meta = {}
    try:
        if scene.metadata_json:
            meta = json.loads(scene.metadata_json)
    except Exception:
        pass

    return {
        "id": scene.id,
        "name": scene.name,
        "format": scene.format,
        "point_count": scene.point_count,
        "camera_count": scene.camera_count,
        "file_path": scene.file_path,
        "file_exists": os.path.exists(scene.file_path),
        "file_size_bytes": os.path.getsize(scene.file_path) if os.path.exists(scene.file_path) else 0,
        "metadata": meta
    }

@router.get("/api/scenes/{scene_id}/download")
def download_scene_asset(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene or not os.path.exists(scene.file_path):
        raise HTTPException(status_code=404, detail="Scene asset file not found on disk.")
    return FileResponse(
        scene.file_path,
        filename=os.path.basename(scene.file_path),
        media_type="application/octet-stream"
    )
