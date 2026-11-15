"""
NOVA 3D - Central Application Configuration
Defines paths, environment variables, hardware limits, and system parameters.
"""
from pathlib import Path
import os
import sys

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Data storage paths
DATA_DIR = BASE_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
LOGS_DIR = DATA_DIR / "logs"
SAMPLES_DIR = DATA_DIR / "samples"

# Ensure runtime directories exist
for path in [DATA_DIR, PROJECTS_DIR, UPLOADS_DIR, OUTPUTS_DIR, LOGS_DIR, SAMPLES_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_FILE = DATA_DIR / "nova3d.sqlite"
DATABASE_URL = os.getenv("NOVA_DATABASE_URL", f"sqlite:///{DATABASE_FILE.as_posix()}")

# Hardware & Processing Configuration
DEFAULT_MAX_IMAGE_DIM = int(os.getenv("NOVA_MAX_IMAGE_DIM", "1600"))
DEFAULT_EXTRACTION_INTERVAL = float(os.getenv("NOVA_EXTRACTION_INTERVAL", "0.5"))
MIN_FRAME_SHARPNESS_LAPLACIAN = float(os.getenv("NOVA_MIN_SHARPNESS", "40.0"))

# COLMAP Configuration
COLMAP_EXECUTABLE = os.getenv("NOVA_COLMAP_EXE", "colmap")
COLMAP_TIMEOUT_SECONDS = int(os.getenv("NOVA_COLMAP_TIMEOUT", "1800"))

# Gaussian Splatting Training Configuration
GSPLAT_DEFAULT_ITERATIONS = int(os.getenv("NOVA_GS_ITERATIONS", "4000"))
GSPLAT_RESOURCE_AWARE_ITERATIONS = 2000
LOW_VRAM_THRESHOLD_MB = 6000 # 6GB threshold for resource-aware mode

# Gesture Interaction Configuration
GESTURE_CONFIDENCE_THRESHOLD = float(os.getenv("NOVA_GESTURE_CONFIDENCE", "0.65"))
GESTURE_COOLDOWN_SECONDS = float(os.getenv("NOVA_GESTURE_COOLDOWN", "0.35"))
GESTURE_SMOOTHING_WINDOW = int(os.getenv("NOVA_GESTURE_SMOOTHING", "5"))

# Security Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("NOVA_MAX_UPLOAD_MB", "500"))
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
ALLOWED_MODEL_EXTENSIONS = {".glb", ".gltf"}

# UI & Brand System
APP_TITLE = "NOVA 3D"
APP_TAGLINE = "Reconstruct Reality. Explore Beyond."
APP_VERSION = "1.0.0"

# Dark graphite & electric cyan/violet design constants
THEME_COLORS = {
    "background": "#0b0d13",
    "surface": "#12151f",
    "surface_variant": "#1a1e2d",
    "border": "#262c40",
    "primary": "#00f0ff", # Electric cyan
    "secondary": "#a855f7", # Electric violet
    "accent": "#38bdf8",
    "text": "#f1f5f9",
    "text_muted": "#94a3b8",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444"
}
