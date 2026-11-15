"""
NOVA 3D - Video Processor & Metadata Inspection
Extracts video metadata using OpenCV and validates readability.
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import cv2
from app.core.logging import logger

def inspect_video(video_path: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Opens video file with OpenCV and extracts detailed metadata.
    Returns: (is_valid, metadata_dict, error_message)
    """
    path = Path(video_path)
    if not path.exists():
        return False, {}, f"File does not exist: {video_path}"

    file_size_bytes = path.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return False, {}, "OpenCV was unable to open or decode this video file."

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))

        # FourCC codec string
        fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])

        if fps <= 0 or total_frames <= 0 or width <= 0 or height <= 0:
            cap.release()
            return False, {}, f"Invalid video stream properties: {width}x{height} @ {fps} FPS, {total_frames} frames."

        duration_sec = round(total_frames / fps, 2)

        # Read first frame to ensure actual decodability
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return False, {}, "Failed to decode the first video frame."

        metadata = {
            "file_name": path.name,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_mb,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": duration_sec,
            "codec": fourcc_str.strip() or "Unknown",
            "aspect_ratio": round(width / height, 2)
        }

        return True, metadata, ""
    except Exception as e:
        if cap.isOpened():
            cap.release()
        return False, {}, f"Error inspecting video stream: {str(e)}"
