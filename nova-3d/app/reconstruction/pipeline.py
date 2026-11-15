"""
NOVA 3D - Asynchronous Reconstruction Orchestration Pipeline
Executes end-to-end 3D reconstruction workflow, updating database job states,
progress metrics, and generating scene outputs.
"""
import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from app.config import PROJECTS_DIR
from app.core.database import SessionLocal
from app.core.logging import get_project_logger, logger
from app.models import ReconstructionJob, Asset, Scene, Metric, Project
from app.reconstruction.video_processor import inspect_video
from app.reconstruction.frame_extractor import extract_video_frames
from app.reconstruction.colmap_engine import run_sparse_reconstruction
from app.reconstruction.gaussian_splat_engine import train_gaussian_splat

def run_reconstruction_pipeline(
    job_id: str,
    project_id: str,
    video_asset_id: str,
    interval_seconds: float = 0.5,
    max_dimension: int = 1600,
    training_iterations: int = 4000
):
    """
    Worker function that executes the full reconstruction pipeline asynchronously.
    """
    db = SessionLocal()
    proj_logger = get_project_logger(project_id)
    accumulated_logs = []

    def log(msg: str):
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        accumulated_logs.append(entry)
        proj_logger.info(msg)

    # Fetch job record
    job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
    if not job:
        db.close()
        logger.error(f"Job {job_id} not found in database.")
        return

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.stage = "Validating"
    job.progress_percent = 5.0
    job.current_step_info = "Inspecting video format and stream properties..."
    db.commit()

    try:
        # Step 1: Validate Video Asset
        log("Starting Phase 1: Video Validation")
        asset = db.query(Asset).filter(Asset.id == video_asset_id).first()
        if not asset or not os.path.exists(asset.storage_path):
            raise FileNotFoundError(f"Video asset {video_asset_id} file not found.")

        is_valid, video_meta, err = inspect_video(asset.storage_path)
        if not is_valid:
            raise ValueError(f"Video validation failed: {err}")

        log(f"Video validated: {video_meta['resolution']} @ {video_meta['fps']} FPS, {video_meta['duration_seconds']}s")

        # Step 2: Frame Extraction
        job.stage = "Extracting Frames"
        job.progress_percent = 20.0
        job.current_step_info = "Extracting still frames with OpenCV and analyzing sharpness..."
        db.commit()
        log("Starting Phase 2: Frame Extraction and Quality Filtering")

        project_dir = PROJECTS_DIR / project_id
        frames_dir = project_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        def frame_prog(p, msg):
            job.progress_percent = 20.0 + (p * 20.0) # 20% to 40%
            job.current_step_info = msg
            db.commit()

        extract_report = extract_video_frames(
            video_path=asset.storage_path,
            output_dir=str(frames_dir),
            interval_seconds=interval_seconds,
            max_dimension=max_dimension,
            filter_blurry=True,
            filter_duplicates=False,
            progress_callback=frame_prog
        )

        log(f"Extracted {extract_report['saved_frames']} frames (rejected {extract_report['rejected_blurry']} blurry frames)")

        # Step 3: COLMAP / Structure from Motion
        job.stage = "Processing COLMAP"
        job.progress_percent = 45.0
        job.current_step_info = "Estimating camera poses and generating sparse 3D geometry..."
        db.commit()
        log("Starting Phase 3: Structure from Motion (SfM)")

        colmap_output_dir = project_dir / "colmap"
        sfm_metrics = run_sparse_reconstruction(
            image_dir=str(frames_dir),
            output_dir=str(colmap_output_dir),
            use_gpu=False, # Safe default for local Windows
            log_callback=log
        )

        log(f"SfM Complete: {sfm_metrics.get('sparse_points', 0)} points, {sfm_metrics.get('registered_images', 0)} images registered.")

        # Save Metrics to DB
        m_reg = Metric(
            project_id=project_id,
            job_id=job_id,
            metric_name="registered_images",
            metric_value=float(sfm_metrics.get("registered_images", 0)),
            measurement_context=f"Engine: {sfm_metrics.get('engine', 'SfM')}"
        )
        m_pts = Metric(
            project_id=project_id,
            job_id=job_id,
            metric_name="sparse_points",
            metric_value=float(sfm_metrics.get("sparse_points", 0)),
            measurement_context=f"Triangulated 3D landmarks"
        )
        m_err = Metric(
            project_id=project_id,
            job_id=job_id,
            metric_name="mean_reprojection_error",
            metric_value=float(sfm_metrics.get("mean_reprojection_error", 0.0)),
            unit="px",
            measurement_context="RANSAC geometric error"
        )
        db.add_all([m_reg, m_pts, m_err])
        db.commit()

        # Step 4: Gaussian Splatting Training / Primitive Generation
        job.stage = "Training Gaussian Splat"
        job.progress_percent = 75.0
        job.current_step_info = "Synthesizing 3D Gaussian representations..."
        db.commit()
        log("Starting Phase 4: Gaussian Splatting Synthesis")

        reconstruction_output_dir = project_dir / "reconstruction"
        sparse_ply = sfm_metrics.get("ply_output_path") or str(colmap_output_dir / "sparse_points.ply")

        gs_results = train_gaussian_splat(
            dataset_dir=str(frames_dir),
            output_dir=str(reconstruction_output_dir),
            sparse_ply_path=sparse_ply,
            iterations=training_iterations,
            max_resolution=max_dimension,
            log_callback=log
        )

        log(f"Gaussian Splat synthesis finished: {gs_results.get('gaussian_count', 0)} primitives created.")

        # Step 5: Packaging & Scene Generation
        job.stage = "Packaging"
        job.progress_percent = 92.0
        job.current_step_info = "Creating scene database entries and metadata..."
        db.commit()
        log("Starting Phase 5: Packaging and Asset Registration")

        scene = Scene(
            project_id=project_id,
            name=f"{project_dir.name}_Scene",
            format="splat" if "splat" in gs_results["asset_output_path"] else "ply",
            file_path=gs_results["asset_output_path"],
            point_count=gs_results.get("gaussian_count", 0),
            camera_count=sfm_metrics.get("registered_images", 0),
            metadata_json=json.dumps({
                "engine": gs_results["engine"],
                "training_duration_sec": gs_results["training_duration_seconds"],
                "iterations": gs_results["iterations_completed"],
                "hardware": gs_results["hardware_profile"]
            })
        )
        db.add(scene)

        # Update Project Status
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.status = "completed"

        # Complete Job
        job.stage = "Completed"
        job.status = "completed"
        job.progress_percent = 100.0
        job.current_step_info = "Reconstruction completed successfully."
        job.completed_at = datetime.utcnow()
        job.logs = "\n".join(accumulated_logs)
        db.commit()
        log("Reconstruction pipeline finished successfully.")

    except Exception as e:
        error_trace = traceback.format_exc()
        log(f"CRITICAL ERROR: {str(e)}")
        job.stage = "Failed"
        job.status = "failed"
        job.error_message = f"{str(e)}"
        job.completed_at = datetime.utcnow()
        job.logs = "\n".join(accumulated_logs) + "\n" + error_trace
        db.commit()
        logger.error(f"Pipeline failed for job {job_id}: {error_trace}")
    finally:
        db.close()
