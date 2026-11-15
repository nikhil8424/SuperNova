"""
NOVA 3D - API Routes Package
"""
from app.api.routes.projects import router as projects_router
from app.api.routes.assets import router as assets_router
from app.api.routes.reconstruction import router as reconstruction_router
from app.api.routes.machine import router as machine_router
from app.api.routes.scenes import router as scenes_router
from app.api.routes.system import router as system_router

__all__ = [
    "projects_router",
    "assets_router",
    "reconstruction_router",
    "machine_router",
    "scenes_router",
    "system_router"
]
