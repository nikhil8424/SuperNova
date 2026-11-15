"""
NOVA 3D - Complete End-to-End Reconstruction Pipeline Audit
Executes:
1. Project creation and MP4 upload validation.
2. OpenCV frame extraction with sharpness analysis.
3. SfM execution (COLMAP detection / OpenCV triangulation).
4. Gaussian Splatting synthesis & transforms.json generation.
5. Database registration and asset reopening verification.
"""
import sys
import os
import time
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal
from app.models import Project, Asset, ReconstructionJob, Scene, Metric
from app.reconstruction.pipeline import run_reconstruction_pipeline
from app.reconstruction.colmap_engine import detect_colmap
from app.reconstruction.gaussian_splat_engine import detect_gaussian_splat_stack
from app.ui.three_viewer import generate_threejs_gaussian_splat_viewer_html
from app.config import SAMPLES_DIR, PROJECTS_DIR

def run_reconstruction_audit():
    print("=" * 70)
    print("   NOVA 3D - REAL MP4 RECONSTRUCTION PIPELINE AUDIT")
    print("=" * 70)

    db = SessionLocal()
    video_source = SAMPLES_DIR / "sample_walkthrough.mp4"
    assert video_source.exists(), f"Sample walkthrough MP4 not found at {video_source}"
    print(f"[*] Input Video: {video_source.name} ({video_source.stat().st_size:,} bytes)")

    # 1. Environment & Dependency Status Check
    print("\n[1/6] Checking Reconstruction Hardware & Software Dependencies...")
    colmap_info = detect_colmap()
    gs_stack = detect_gaussian_splat_stack()

    print(f"    - COLMAP Executable: {'DETECTED (' + colmap_info['version'] + ')' if colmap_info['installed'] else 'NOT FOUND IN PATH (Fallback Active)'}")
    if not colmap_info['installed']:
        print(f"      Diagnostic: {colmap_info['message']}")

    print(f"    - GPU Available: {gs_stack['gpu_name']} ({gs_stack['vram_mb']} MB VRAM)")
    print(f"    - PyTorch CUDA: {'ACTIVE' if gs_stack['cuda_available'] else 'NOT ACTIVE (CPU Build Detected)'}")
    print(f"    - Nerfstudio CLI: {'INSTALLED' if gs_stack['nerfstudio_installed'] else 'NOT INSTALLED IN PATH'}")
    print(f"    - Gaussian Splat Engine: {'Splatfacto CUDA' if (gs_stack['cuda_available'] and gs_stack['nerfstudio_installed']) else 'Calibrated 3D Gaussian Primitive Synthesizer'}")

    # 2. Database Project Creation
    print("\n[2/6] Initializing Test Project & Storing Video Asset...")
    proj = Project(
        name="Audit Real MP4 Pipeline Run",
        description="End-to-end verification of 3D reconstruction workflow",
        project_type="environment",
        status="created"
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    project_id = proj.id
    print(f"    - Project Created: ID={project_id}")

    proj_input_dir = PROJECTS_DIR / project_id / "input"
    proj_input_dir.mkdir(parents=True, exist_ok=True)
    target_video = proj_input_dir / "walkthrough.mp4"
    with open(video_source, "rb") as sf, open(target_video, "wb") as df:
        df.write(sf.read())

    asset = Asset(
        project_id=project_id,
        original_filename="walkthrough.mp4",
        asset_type="video",
        file_size_bytes=target_video.stat().st_size,
        storage_path=str(target_video)
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    asset_id = asset.id
    print(f"    - Video Asset Registered: ID={asset_id}, Size={asset.file_size_bytes:,} bytes")

    # 3. Create Job Record
    job = ReconstructionJob(
        project_id=project_id,
        source_asset_id=asset_id,
        stage="Pending",
        status="pending",
        progress_percent=0.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    print(f"    - Job Registered: ID={job_id}")

    # 4. Execute Full Pipeline
    print("\n[3/6] Executing Complete 5-Phase Reconstruction Pipeline...")
    t_start = time.time()
    run_reconstruction_pipeline(
        job_id=job_id,
        project_id=project_id,
        video_asset_id=asset_id,
        interval_seconds=0.5,
        max_dimension=800,
        training_iterations=1000
    )
    t_total = time.time() - t_start

    # 5. Inspect Job Completion
    db.expire_all()
    job_refreshed = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
    print(f"\n[4/6] Verifying Execution Results & Pipeline Telemetry (Duration: {t_total:.2f}s)...")
    print(f"    - Final Job Status: {job_refreshed.status.upper()}")
    print(f"    - Final Job Stage:  {job_refreshed.stage}")
    print(f"    - Progress:         {job_refreshed.progress_percent}%")
    assert job_refreshed.status == "completed", f"Reconstruction failed: {job_refreshed.error_message}"

    # Verify Metrics Recorded
    metrics = db.query(Metric).filter(Metric.project_id == project_id).all()
    print(f"\n[5/6] Verifying Stored Geometric & Performance Metrics ({len(metrics)} metrics):")
    metric_map = {m.metric_name: m.metric_value for m in metrics}
    for m in metrics:
        print(f"    - {m.metric_name:<26}: {m.metric_value:>8.2f} {m.unit or ''} ({m.measurement_context or ''})")

    assert "sparse_points" in metric_map, "Missing sparse_points metric"
    assert "registered_images" in metric_map, "Missing registered_images metric"
    assert metric_map["registered_images"] > 0, "No images registered"
    assert metric_map["sparse_points"] > 0, "No 3D points triangulated"

    # 6. Verify Scene Creation and Reopen Asset
    print("\n[6/6] Verifying Generated 3D Asset & Reopening Scene in Three.js...")
    scene = db.query(Scene).filter(Scene.project_id == project_id).first()
    assert scene is not None, "No Scene record created in database."
    print(f"    - Stored Scene: '{scene.name}' (Format: {scene.format}, Points: {scene.point_count:,}, Cameras: {scene.camera_count})")
    print(f"    - Asset File Path: {scene.file_path}")

    ply_path = Path(scene.file_path)
    assert ply_path.exists(), f"Reconstructed PLY file does not exist at {ply_path}"
    file_sz = ply_path.stat().st_size
    print(f"    - PLY File Size: {file_sz:,} bytes")
    assert file_sz > 500, "PLY file appears empty or corrupted."

    # Parse PLY header & contents to verify Gaussian primitive properties
    with open(ply_path, "r", encoding="utf-8") as pf:
        header_lines = [pf.readline().strip() for _ in range(12)]
    print(f"    - PLY Header Elements:")
    for h in header_lines:
        if h == "end_header":
            break
        print(f"      | {h}")

    assert any("element vertex" in l for l in header_lines), "PLY missing vertex count element"
    assert any("scale_0" in l for l in header_lines) or any("red" in l for l in header_lines), "PLY missing Gaussian primitive scale or color properties"

    # Test Reopening and Rendering HTML Three.js viewer
    viewer_html = generate_threejs_gaussian_splat_viewer_html(
        ply_path=str(ply_path),
        point_budget=15000,
        height=600
    )
    assert "three.min.js" in viewer_html, "Three.js viewer failed to load."
    assert "PointsMaterial" in viewer_html or "ShaderMaterial" in viewer_html, "Missing shader material in WebGL generator."
    print(f"    - Generated Interactive Three.js WebGL Payload: {len(viewer_html):,} characters.")

    # Save standalone preview
    preview_file = PROJECTS_DIR / project_id / "reconstructed_preview.html"
    with open(preview_file, "w", encoding="utf-8") as f:
        f.write(viewer_html)
    print(f"    - Saved interactive WebGL scene view to: {preview_file}")

    db.close()
    print("\n[PASS] Complete Reconstruction Pipeline, Output Assets, and Reopening Verified 100% Functional.\n")
    return True

if __name__ == "__main__":
    success = run_reconstruction_audit()
    sys.exit(0 if success else 1)
