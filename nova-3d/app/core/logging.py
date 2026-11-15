"""
NOVA 3D - Structured Logging Subsystem
Provides consistent logging to console and project-specific / global log files.
"""
import logging
import sys
from pathlib import Path
from app.config import LOGS_DIR

def get_logger(name: str = "nova3d") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Global Log File Handler
    global_log_path = LOGS_DIR / "nova3d_system.log"
    file_handler = logging.FileHandler(global_log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_project_logger(project_id: str) -> logging.Logger:
    """Creates or retrieves a project-specific logger saving to project directory."""
    logger_name = f"nova3d.project.{project_id}"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    from app.config import PROJECTS_DIR
    proj_log_dir = PROJECTS_DIR / project_id / "logs"
    proj_log_dir.mkdir(parents=True, exist_ok=True)
    proj_log_file = proj_log_dir / "pipeline.log"

    handler = logging.FileHandler(proj_log_file, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = get_logger("nova3d")
