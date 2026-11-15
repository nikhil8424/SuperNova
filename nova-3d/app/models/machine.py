"""
NOVA 3D - Machine Model & Component Database Models
Represents structured GLB/GLTF engineering models and hierarchical assembly parts.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class MachineModel(Base):
    __tablename__ = "machine_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(String(36), nullable=True)
    model_name = Column(String(120), nullable=False)
    format = Column(String(16), nullable=False, default="glb") # glb, gltf
    storage_path = Column(String(512), nullable=False)
    vertex_count = Column(Integer, nullable=False, default=0)
    face_count = Column(Integer, nullable=False, default=0)
    component_count = Column(Integer, nullable=False, default=0)
    bounding_box_json = Column(Text, nullable=True, default="{}")
    metadata_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="machine_models")
    components = relationship("Component", back_populates="machine_model", cascade="all, delete-orphan")

    def to_dict(self):
        import json
        bbox = {}
        try:
            if self.bounding_box_json:
                bbox = json.loads(self.bounding_box_json)
        except Exception:
            pass
        return {
            "id": self.id,
            "project_id": self.project_id,
            "model_name": self.model_name,
            "format": self.format,
            "storage_path": self.storage_path,
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "component_count": self.component_count,
            "bounding_box": bbox,
            "components": [c.to_dict() for c in self.components] if self.components else []
        }

class Component(Base):
    __tablename__ = "components"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    machine_model_id = Column(String(36), ForeignKey("machine_models.id", ondelete="CASCADE"), nullable=False, index=True)
    node_name = Column(String(120), nullable=False)
    display_name = Column(String(120), nullable=False)
    parent_name = Column(String(120), nullable=True)
    category = Column(String(64), nullable=False, default="Component")
    vertex_count = Column(Integer, nullable=False, default=0)
    face_count = Column(Integer, nullable=False, default=0)
    center_json = Column(String(255), nullable=True, default="[0,0,0]")
    bounds_json = Column(Text, nullable=True, default="{}")
    transform_json = Column(Text, nullable=True, default="{}")
    is_visible = Column(Boolean, nullable=False, default=True)

    # Relationships
    machine_model = relationship("MachineModel", back_populates="components")

    def to_dict(self):
        import json
        center = [0.0, 0.0, 0.0]
        bounds = {}
        transform = {}
        try:
            if self.center_json:
                center = json.loads(self.center_json)
            if self.bounds_json:
                bounds = json.loads(self.bounds_json)
            if self.transform_json:
                transform = json.loads(self.transform_json)
        except Exception:
            pass

        return {
            "id": self.id,
            "machine_model_id": self.machine_model_id,
            "node_name": self.node_name,
            "display_name": self.display_name,
            "parent_name": self.parent_name,
            "category": self.category,
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "center": center,
            "bounds": bounds,
            "transform": transform,
            "is_visible": self.is_visible
        }
