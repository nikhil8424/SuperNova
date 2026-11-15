"""
NOVA 3D - Reconstruction Jobs API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ReconstructionJob, Project, Asset
from app.schemas import ReconstructionRequest, JobResponse
from app.api.dependencies import get_project_or_404
from app.workers.local_worker import job_worker

router = APIRouter(tags=["Reconstruction"])

@router.post("/api/projects/{project_id}/reconstruct", response_model=JobResponse, status_code=202)
def start_reconstruction(
    project_id: str,
    req: ReconstructionRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db)
):
    # Verify video asset exists
    asset = db.query(Asset).filter(Asset.id == req.video_asset_id, Asset.project_id == project_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Specified video asset does not exist in this project.")

    job = ReconstructionJob(
        project_id=project_id,
        source_asset_id=req.video_asset_id,
        stage="Pending",
        status="pending",
        progress_percent=0.0,
        current_step_info="Job registered, queuing for processing..."
    )
    db.add(job)
    project.status = "processing"
    db.commit()
    db.refresh(job)
    job_dict = job.to_dict()

    # Submit to background worker
    job_worker.submit_reconstruction_job(
        job_id=job.id,
        project_id=project_id,
        video_asset_id=req.video_asset_id,
        interval_seconds=req.extraction_interval,
        max_dimension=req.max_image_dim,
        training_iterations=req.training_iterations
    )

    return job_dict

@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_dict()

@router.post("/api/jobs/{job_id}/cancel", status_code=200)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Cannot cancel an already completed or failed job.")

    job_worker.cancel_job(job_id)
    return {"message": f"Cancellation requested for job '{job_id}'."}

@router.post("/api/jobs/{job_id}/retry", response_model=JobResponse, status_code=202)
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if not job.source_asset_id:
        raise HTTPException(status_code=400, detail="Cannot retry job without source asset reference.")

    # Reset job
    job.status = "pending"
    job.stage = "Pending"
    job.progress_percent = 0.0
    job.error_message = None
    job.current_step_info = "Retrying job..."
    db.commit()

    job_worker.submit_reconstruction_job(
        job_id=job.id,
        project_id=job.project_id,
        video_asset_id=job.source_asset_id
    )

    return job.to_dict()
