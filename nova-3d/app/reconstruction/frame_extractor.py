"""
NOVA 3D - OpenCV Frame Extractor & Dataset Builder
Extracts frames at configured intervals, resizes within limits, detects blur & duplicates,
creates thumbnail previews, and compiles quality statistics.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
import cv2
import numpy as np

from app.reconstruction.image_quality import assess_frame_quality
from app.core.logging import logger

def are_frames_duplicate(frame1_gray: np.ndarray, frame2_gray: np.ndarray, threshold: float = 0.998) -> bool:
    """Checks histogram correlation to detect near-duplicate stationary frames."""
    hist1 = cv2.calcHist([frame1_gray], [0], None, [32], [0, 256])
    hist2 = cv2.calcHist([frame2_gray], [0], None, [32], [0, 256])
    cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return score >= threshold

def extract_video_frames(
    video_path: str,
    output_dir: str,
    interval_seconds: float = 0.5,
    max_dimension: int = 1600,
    filter_blurry: bool = True,
    filter_duplicates: bool = True,
    min_sharpness: float = 35.0,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    Extracts frames from video into output_dir.
    Generates preview thumbnails in output_dir/thumbnails.
    Returns extraction summary report.
    """
    video_p = Path(video_path)
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    thumb_dir = out_p / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_p))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0 or total_frames <= 0:
        cap.release()
        raise RuntimeError(f"Invalid video FPS ({fps}) or total frames ({total_frames})")

    step = max(1, round(fps * interval_seconds))
    frame_index = 0
    saved_count = 0
    rejected_blurry = 0
    rejected_duplicates = 0

    sharpness_scores = []
    exposure_stats = []
    saved_files = []
    thumbnail_files = []

    last_gray_frame = None

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        if frame_index % step == 0:
            h, w = frame.shape[:2]

            # Resize if max dimension is exceeded
            scale = min(1.0, max_dimension / max(w, h))
            if scale < 1.0:
                frame_resized = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            else:
                frame_resized = frame

            # Quality assessment
            acceptable, q_meta = assess_frame_quality(frame_resized, min_sharpness=min_sharpness)
            sharpness_scores.append(q_meta["sharpness"])
            exposure_stats.append(q_meta["exposure"]["mean_brightness"])

            # Blur rejection
            if filter_blurry and q_meta["is_blurry"]:
                rejected_blurry += 1
                frame_index += 1
                continue

            # Duplicate rejection
            gray_current = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            if filter_duplicates and last_gray_frame is not None and are_frames_duplicate(gray_current, last_gray_frame):
                rejected_duplicates += 1
                frame_index += 1
                continue

            last_gray_frame = gray_current

            # Save full image
            frame_filename = f"frame_{saved_count + 1:06d}.jpg"
            target_path = out_p / frame_filename
            cv2.imwrite(str(target_path), frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_files.append(str(target_path))

            # Save thumbnail (320px wide)
            thumb_scale = 320.0 / max(frame_resized.shape[1], 1)
            thumb_img = cv2.resize(frame_resized, None, fx=thumb_scale, fy=thumb_scale, interpolation=cv2.INTER_AREA)
            thumb_path = thumb_dir / f"thumb_{saved_count + 1:06d}.jpg"
            cv2.imwrite(str(thumb_path), thumb_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            thumbnail_files.append(str(thumb_path))

            saved_count += 1

            if progress_callback:
                progress = min(1.0, frame_index / max(1, total_frames))
                progress_callback(progress, f"Extracted {saved_count} frames (frame {frame_index}/{total_frames})")

        frame_index += 1

    cap.release()

    avg_sharpness = round(float(np.mean(sharpness_scores)), 2) if sharpness_scores else 0.0
    avg_brightness = round(float(np.mean(exposure_stats)), 2) if exposure_stats else 0.0

    report = {
        "total_video_frames": total_frames,
        "sampled_frames": len(sharpness_scores),
        "saved_frames": saved_count,
        "rejected_blurry": rejected_blurry,
        "rejected_duplicates": rejected_duplicates,
        "average_sharpness": avg_sharpness,
        "average_brightness": avg_brightness,
        "output_directory": str(out_p),
        "frame_files": saved_files,
        "thumbnail_files": thumbnail_files,
        "extraction_interval_sec": interval_seconds,
        "max_dimension_px": max_dimension
    }

    logger.info(f"Frame extraction finished: {saved_count} saved, {rejected_blurry} rejected (blurry), {rejected_duplicates} rejected (duplicates).")
    return report
