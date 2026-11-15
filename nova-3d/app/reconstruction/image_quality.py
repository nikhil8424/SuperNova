"""
NOVA 3D - Computer Vision Image Quality Analyzer
Calculates frame blur via Laplacian variance, analyzes exposure levels,
and computes a composite image quality score.
"""
from typing import Dict, Any, Tuple
import cv2
import numpy as np

def calculate_blur_score(image_bgr: np.ndarray) -> float:
    """Calculates sharpness score using variance of the Laplacian filter."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return float(variance)

def analyze_exposure(image_bgr: np.ndarray) -> Dict[str, float]:
    """Analyzes brightness distribution and exposure anomalies."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))

    # Calculate under-exposed (< 20) and over-exposed (> 235) pixel ratios
    total_pixels = gray.size
    under_exposed = float(np.sum(gray < 20) / total_pixels) * 100.0
    over_exposed = float(np.sum(gray > 235) / total_pixels) * 100.0

    return {
        "mean_brightness": round(mean_val, 2),
        "contrast_std": round(std_val, 2),
        "under_exposed_percent": round(under_exposed, 2),
        "over_exposed_percent": round(over_exposed, 2)
    }

def assess_frame_quality(
    image_bgr: np.ndarray,
    min_sharpness: float = 35.0
) -> Tuple[bool, Dict[str, Any]]:
    """
    Evaluates sharpness, exposure, and provides a composite score (0-100).
    Returns (is_acceptable, quality_metrics).
    """
    sharpness = calculate_blur_score(image_bgr)
    exposure = analyze_exposure(image_bgr)

    # Sharpness score normalized (100+ is sharp, below 35 is blurry)
    sharp_norm = min(100.0, (sharpness / 120.0) * 100.0)

    # Exposure score: optimal mean brightness is around 110-150
    b_diff = abs(exposure["mean_brightness"] - 128.0)
    exp_norm = max(0.0, 100.0 - (b_diff * 0.8) - exposure["under_exposed_percent"] - exposure["over_exposed_percent"])

    composite_score = round(0.65 * sharp_norm + 0.35 * exp_norm, 1)

    is_blurry = sharpness < min_sharpness
    is_poor_exposure = exposure["under_exposed_percent"] > 40.0 or exposure["over_exposed_percent"] > 40.0

    is_acceptable = (not is_blurry) and (not is_poor_exposure)

    metrics = {
        "sharpness": round(sharpness, 2),
        "is_blurry": is_blurry,
        "exposure": exposure,
        "composite_score": composite_score,
        "is_acceptable": is_acceptable
    }

    return is_acceptable, metrics
