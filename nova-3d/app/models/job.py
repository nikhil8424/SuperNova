"""
NOVA 3D - Reconstruction Job Database Model
Tracks asynchronous processing jobs with progress, stage, logs, and timing.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ReconstructionJob(Base):
    __tablename__ = "reconstruction_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_asset_id = Column(String(36), nullable=True)
    stage = Column(String(64), nullable=False, default="Pending")
    # Stages: Pending, Queued, Validating, Extracting Frames, Processing COLMAP, Training Gaussian Splat, Packaging, Completed, Failed, Cancelled
    status = Column(String(32), nullable=False, default="pending", index=True) # pending, running, completed, failed, cancelled
    progress_percent = Column(Float, nullable=False, default=0.0)
    current_step_info = Column(String(255), nullable=True, default="")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="jobs")

    def to_dict(self):
        duration_sec = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            duration_sec = round((end_time - self.started_at).total_seconds(), 2)

        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_asset_id": self.source_asset_id,
            "stage": self.stage,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_step_info": self.current_step_info,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration_sec,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
