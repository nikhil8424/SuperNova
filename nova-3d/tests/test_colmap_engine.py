"""
Unit tests for COLMAP Engine & SfM Triangulator
"""
from app.reconstruction.colmap_engine import detect_colmap, parse_colmap_analyzer_output, export_points_to_ply
import numpy as np
import os

def test_detect_colmap():
    # Should detect status without crashing
    info = detect_colmap()
    assert "installed" in info
    assert "message" in info

def test_parse_colmap_analyzer_output():
    sample_output = """
    Reconstruction statistics
    -------------------------
    Registered images: 45
    Points: 12450
    Mean reprojection error: 0.72px
    Mean track length: 4.8
    """
    metrics = parse_colmap_analyzer_output(sample_output)
    assert metrics["registered_images"] == 45
    assert metrics["sparse_points"] == 12450
    assert metrics["mean_reprojection_error"] == 0.72

def test_export_points_to_ply(temp_dir):
    ply_path = temp_dir / "test.ply"
    pts = np.array([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]])
    colors = np.array([[255, 0, 0], [0, 255, 0]])

    export_points_to_ply(pts, colors, str(ply_path))
    assert os.path.exists(ply_path)

    with open(ply_path, "r") as f:
        content = f.read()
    assert "element vertex 2" in content
    assert "property float x" in content
