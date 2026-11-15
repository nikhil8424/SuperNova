"""
Unit tests for Local Background Worker & Job Queue
"""
import time
from app.workers.local_worker import LocalJobWorker, job_worker
from app.models import ReconstructionJob, Project

def test_worker_singleton():
    w1 = LocalJobWorker()
    w2 = LocalJobWorker()
    assert w1 is w2
    assert job_worker is w1

def test_worker_cancel_job(db_session):
    proj = Project(name="Worker Test Proj", project_type="environment")
    db_session.add(proj)
    db_session.commit()

    job = ReconstructionJob(project_id=proj.id, stage="Validating", status="running")
    db_session.add(job)
    db_session.commit()

    # Request cancellation
    canceled = job_worker.cancel_job(job.id)
    assert canceled is True
    assert job_worker.cancellation_requested.get(job.id) is True
