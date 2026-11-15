"""
Unit tests for Video Processor and OpenCV Frame Extraction
"""
import os
from pathlib import Path
from app.reconstruction.video_processor import inspect_video
from app.reconstruction.frame_extractor import extract_video_frames
from app.reconstruction.image_quality import assess_frame_quality, calculate_blur_score
import numpy as np

def test_inspect_video(synthetic_video):
    ok, meta, err = inspect_video(synthetic_video)
    assert ok is True
    assert err == ""
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["fps"] == 30.0
    assert meta["total_frames"] == 60
    assert meta["duration_seconds"] == 2.0

def test_blur_detection():
    # Sharp image: high contrast checkerboard
    sharp = np.zeros((100, 100, 3), dtype=np.uint8)
    sharp[::2, ::2] = 255
    sharp_score = calculate_blur_score(sharp)

    # Blurry image: flat gray
    blurry = np.full((100, 100, 3), 128, dtype=np.uint8)
    blurry_score = calculate_blur_score(blurry)

    assert sharp_score > blurry_score
    acceptable, q_meta = assess_frame_quality(blurry, min_sharpness=35.0)
    assert q_meta["is_blurry"] is True

def test_extract_video_frames(synthetic_video, temp_dir):
    out_dir = temp_dir / "extracted_frames"
    report = extract_video_frames(
        video_path=synthetic_video,
        output_dir=str(out_dir),
        interval_seconds=0.5,
        max_dimension=800,
        filter_blurry=False,
        filter_duplicates=False
    )

    assert report["saved_frames"] >= 2
    assert os.path.exists(out_dir / "thumbnails")
    assert len(report["frame_files"]) == report["saved_frames"]
