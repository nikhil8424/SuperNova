"""
NOVA 3D - Scene Database Model
Represents reconstructed 3D environments, point clouds, and Gaussian Splat scenes.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    format = Column(String(32), nullable=False, default="splat") # splat, ply, pointcloud, mesh
    file_path = Column(String(512), nullable=False)
    point_count = Column(Integer, nullable=False, default=0)
    camera_count = Column(Integer, nullable=False, default=0)
    coordinate_metadata_json = Column(Text, nullable=True, default="{}")
    metadata_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="scenes")

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
            "name": self.name,
            "format": self.format,
            "file_path": self.file_path,
            "point_count": self.point_count,
            "camera_count": self.camera_count,
            "metadata": meta,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
