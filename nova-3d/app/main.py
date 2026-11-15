"""
NOVA 3D - FastAPI Main Application Entrypoint
Provides OpenAPI documentation, CORS, REST routers, and lifecycle events.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import APP_TITLE, APP_TAGLINE, APP_VERSION, DATA_DIR
from app.core.database import init_db
from app.core.logging import logger
from app.api.routes import (
    projects_router,
    assets_router,
    reconstruction_router,
    machine_router,
    scenes_router,
    system_router
)

app = FastAPI(
    title=APP_TITLE,
    description=f"{APP_TAGLINE} — Unified AI-Powered 3D Reconstruction & Machine Exploration Platform API.",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for cross-origin browser viewer integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API Routers
app.include_router(projects_router)
app.include_router(assets_router)
app.include_router(reconstruction_router)
app.include_router(machine_router)
app.include_router(scenes_router)
app.include_router(system_router)

@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}...")
    init_db()
    logger.info("NOVA 3D API server is ready.")

@app.get("/")
def root():
    return {
        "app": APP_TITLE,
        "tagline": APP_TAGLINE,
        "version": APP_VERSION,
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
