"""
NOVA 3D - Asynchronous Background Job Worker
Manages background job queues, concurrent task threading, cancellations, and status polling.
"""
import threading
import queue
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import SessionLocal
from app.models import ReconstructionJob
from app.core.logging import logger
from app.reconstruction.pipeline import run_reconstruction_pipeline

class LocalJobWorker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalJobWorker, cls).__new__(cls)
            cls._instance._init_worker()
        return cls._instance

    def _init_worker(self):
        self.job_queue = queue.Queue()
        self.active_jobs: Dict[str, threading.Thread] = {}
        self.cancellation_requested: Dict[str, bool] = {}
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info("Local background job worker started.")

    def submit_reconstruction_job(
        self,
        job_id: str,
        project_id: str,
        video_asset_id: str,
        interval_seconds: float = 0.5,
        max_dimension: int = 1600,
        training_iterations: int = 4000
    ):
        """Enqueues a reconstruction job for asynchronous execution."""
        db = SessionLocal()
        job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
        if job:
            job.status = "queued"
            job.stage = "Queued"
            job.current_step_info = "Waiting in processing queue..."
            db.commit()
        db.close()

        task_payload = {
            "job_id": job_id,
            "project_id": project_id,
            "video_asset_id": video_asset_id,
            "interval_seconds": interval_seconds,
            "max_dimension": max_dimension,
            "training_iterations": training_iterations
        }
        self.job_queue.put(task_payload)
        logger.info(f"Enqueued reconstruction job {job_id} for project {project_id}.")

    def _process_queue(self):
        while True:
            try:
                task = self.job_queue.get()
                job_id = task["job_id"]

                if self.cancellation_requested.get(job_id, False):
                    self._mark_cancelled(job_id)
                    self.job_queue.task_done()
                    continue

                thread = threading.Thread(
                    target=self._execute_job,
                    args=(task,),
                    daemon=True
                )
                self.active_jobs[job_id] = thread
                thread.start()
                thread.join()

                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
                self.job_queue.task_done()
            except Exception as e:
                logger.error(f"Worker queue processing error: {e}")
                time.sleep(1)

    def _execute_job(self, task: Dict[str, Any]):
        run_reconstruction_pipeline(
            job_id=task["job_id"],
            project_id=task["project_id"],
            video_asset_id=task["video_asset_id"],
            interval_seconds=task["interval_seconds"],
            max_dimension=task["max_dimension"],
            training_iterations=task["training_iterations"]
        )

    def cancel_job(self, job_id: str) -> bool:
        """Flags job for cancellation."""
        self.cancellation_requested[job_id] = True
        self._mark_cancelled(job_id)
        return True

    def _mark_cancelled(self, job_id: str):
        db = SessionLocal()
        job = db.query(ReconstructionJob).filter(ReconstructionJob.id == job_id).first()
        if job and job.status not in ("completed", "failed"):
            job.status = "cancelled"
            job.stage = "Cancelled"
            job.current_step_info = "Job was cancelled by user request."
            job.completed_at = datetime.utcnow()
            db.commit()
        db.close()

# Singleton worker instance
job_worker = LocalJobWorker()
