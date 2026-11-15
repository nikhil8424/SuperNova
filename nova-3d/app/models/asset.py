"""
NOVA 3D - Asset Database Model
Represents uploaded videos, images, GLB models, splats, point clouds, etc.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(32), nullable=False, index=True) # video, model, frames, sparse_model, splat, pointcloud
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    metadata_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="assets")

    def to_dict(self):
        import json
        meta = {}
        try:
            if self.metadata_json:
                meta = json.loads(self.metadata_json)
        except Exception:
            pass
        return {
            "id": self.id,
            "project_id": self.project_id,
            "asset_type": self.asset_type,
            "original_filename": self.original_filename,
            "storage_path": self.storage_path,
            "file_size_bytes": self.file_size_bytes,
            "metadata": meta,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
