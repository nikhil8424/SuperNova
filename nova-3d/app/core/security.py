"""
NOVA 3D - Security and Privacy Subsystem
Protects against path traversal, validates file uploads by signature and extension,
enforces size limits, and sanitizes subprocess executions.
"""
import os
import uuid
import re
from pathlib import Path
from typing import Tuple, Optional
from app.config import (
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_MODEL_EXTENSIONS,
    MAX_UPLOAD_SIZE_MB,
    DATA_DIR
)
from app.core.logging import logger

# Magic numbers / byte signatures for accepted media
MAGIC_SIGNATURES = {
    # MP4 / MOV (ftyp box)
    b"ftyp": "video/mp4",
    # AVI (RIFF ... AVI)
    b"RIFF": "video/avi",
    # Matroska / MKV
    b"\x1a\x45\xdf\xa3": "video/mkv",
    # GLB header (magic 0x46546C67 = "glTF")
    b"glTF": "model/gltf-binary"
}

def sanitize_filename(filename: str) -> str:
    """Removes path separators and dangerous characters, leaving only safe alphanumeric + standard punctuation."""
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base)
    return clean

def generate_secure_filename(original_name: str, prefix: str = "") -> str:
    """Generates an unguessable unique filename preserving only the validated extension."""
    ext = Path(original_name).suffix.lower()
    unique_id = uuid.uuid4().hex[:12]
    prefix_str = f"{prefix}_" if prefix else ""
    return f"{prefix_str}{unique_id}{ext}"

def validate_safe_path(target_path: Path, base_dir: Path = DATA_DIR) -> bool:
    """Prevents directory traversal by verifying resolved path is inside allowed base_dir."""
    try:
        resolved_target = Path(target_path).resolve()
        resolved_base = Path(base_dir).resolve()
        return resolved_base in resolved_target.parents or resolved_target == resolved_base
    except Exception:
        return False

def validate_file_upload(
    file_bytes: bytes,
    original_filename: str,
    asset_type: str = "video"
) -> Tuple[bool, str]:
    """
    Validates file size, extension, and binary header.
    Returns (is_valid, error_message).
    """
    if len(file_bytes) == 0:
        return False, "Uploaded file is empty (0 bytes)."

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB} MB."

    ext = Path(original_filename).suffix.lower()

    if asset_type == "video":
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            return False, f"Unsupported video extension '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        
        # Check signature in first 32 bytes
        header = file_bytes[:32]
        is_mp4_mov = b"ftyp" in header
        is_avi = header.startswith(b"RIFF")
        is_mkv = header.startswith(b"\x1a\x45\xdf\xa3")

        if not (is_mp4_mov or is_avi or is_mkv):
            # Fallback warning but permit if extension is known
            logger.warning(f"Video file header check was inconclusive for '{original_filename}'.")
            
        return True, ""

    elif asset_type in ("model", "mesh"):
        if ext not in ALLOWED_MODEL_EXTENSIONS:
            return False, f"Unsupported 3D model extension '{ext}'. Allowed: {', '.join(ALLOWED_MODEL_EXTENSIONS)}"
        
        if ext == ".glb":
            if not file_bytes.startswith(b"glTF"):
                return False, "Invalid GLB file: missing standard glTF binary header signature."
        elif ext == ".gltf":
            # Must be valid JSON string
            try:
                import json
                json.loads(file_bytes.decode("utf-8", errors="ignore"))
            except Exception:
                return False, "Invalid GLTF file: payload is not valid JSON."

        return True, ""

    return False, f"Unknown asset type '{asset_type}'."
