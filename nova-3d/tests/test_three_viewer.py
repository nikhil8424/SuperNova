"""
Unit tests for Three.js WebGL HTML Component Generators
"""
from app.ui.three_viewer import (
    generate_threejs_mesh_viewer_html,
    generate_threejs_gaussian_splat_viewer_html
)

def test_generate_threejs_mesh_viewer_html():
    sample_components = [
        {
            "node_name": "PartA",
            "display_name": "Piston",
            "category": "Kinematic",
            "center": [0.0, 1.0, 0.0],
            "bounds": {"extents": [0.5, 0.5, 0.5]}
        }
    ]
    sample_transforms = {
        "PartA": {
            "displacement": [0.2, 0.3, 0.0]
        }
    }

    html = generate_threejs_mesh_viewer_html(
        components=sample_components,
        exploded_transforms=sample_transforms,
        explosion_intensity=0.8,
        selected_component="PartA"
    )

    assert "<!DOCTYPE html>" in html
    assert "three.min.js" in html
    assert "OrbitControls.js" in html
    assert "Piston" in html
    assert "explosionIntensity = 0.8" in html

def test_generate_threejs_gaussian_splat_viewer_html(temp_dir):
    ply_path = temp_dir / "sample_cloud.ply"
    with open(ply_path, "w") as f:
        f.write("ply\nformat ascii 1.0\nelement vertex 2\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        f.write("1.0 2.0 3.0 255 0 0\n")
        f.write("-1.0 -2.0 -3.0 0 255 0\n")

    html = generate_threejs_gaussian_splat_viewer_html(
        ply_path=str(ply_path),
        point_budget=500,
        point_size=4.0
    )

    assert "<!DOCTYPE html>" in html
    assert "BufferGeometry" in html
    assert "PointsMaterial" in html
    assert "Float32Array" in html
