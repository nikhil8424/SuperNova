"""
NOVA 3D - Metric, Gesture Configuration & Audit Event Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), nullable=True, index=True)
    metric_name = Column(String(64), nullable=False) # registered_images, reprojection_error, sparse_points, etc.
    metric_value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=True, default="")
    measurement_context = Column(Text, nullable=True, default="") # Evaluation conditions, resolution, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="metrics")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "job_id": self.job_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "measurement_context": self.measurement_context,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class GestureConfiguration(Base):
    __tablename__ = "gesture_configurations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_or_project_id = Column(String(36), nullable=False, default="global", index=True)
    gesture_name = Column(String(64), nullable=False)
    mapped_action = Column(String(64), nullable=False)
    confidence_threshold = Column(Float, nullable=False, default=0.65)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_or_project_id": self.user_or_project_id,
            "gesture_name": self.gesture_name,
            "mapped_action": self.mapped_action,
            "confidence_threshold": self.confidence_threshold,
            "is_enabled": self.is_enabled
        }

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    details_json = Column(Text, nullable=True, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
