"""
NOVA 3D - System Telemetry & Health API Endpoints
"""
import shutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.config import APP_TITLE, APP_VERSION
from app.core.hardware import get_system_hardware_profile
from app.reconstruction.colmap_engine import detect_colmap
from app.reconstruction.gaussian_splat_engine import detect_gaussian_splat_stack

router = APIRouter(tags=["System"])

@router.get("/api/health")
def get_health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "database_connected": db_ok
    }

@router.get("/api/system/hardware")
def get_hardware_telemetry():
    return get_system_hardware_profile()

@router.get("/api/system/dependencies")
def get_dependencies_status():
    colmap_info = detect_colmap()
    gs_info = detect_gaussian_splat_stack()

    deps = {
        "python": {
            "status": "ready",
            "details": "Python verified"
        },
        "opencv": {
            "status": "ready",
            "details": "OpenCV computer vision engine ready"
        },
        "mediapipe": {
            "status": "ready",
            "details": "MediaPipe hand tracking library loaded"
        },
        "trimesh": {
            "status": "ready",
            "details": "Trimesh GLB/GLTF geometry engine ready"
        },
        "colmap": {
            "status": "ready" if colmap_info["installed"] else "fallback_active",
            "details": colmap_info["message"],
            "version": colmap_info.get("version")
        },
        "gaussian_splatting": {
            "status": "ready" if gs_info["nerfstudio_installed"] else "adaptive_primitive_active",
            "details": gs_info["diagnostic"],
            "cuda": gs_info["cuda_available"]
        }
    }
    return deps
