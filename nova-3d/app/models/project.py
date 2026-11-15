"""
NOVA 3D - Project Database Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    project_type = Column(String(32), nullable=False, default="environment") # environment, object, machine
    status = Column(String(32), nullable=False, default="active") # active, processing, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("ReconstructionJob", back_populates="project", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
    machine_models = relationship("MachineModel", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "asset_count": len(self.assets) if self.assets else 0,
            "job_count": len(self.jobs) if self.jobs else 0
        }
