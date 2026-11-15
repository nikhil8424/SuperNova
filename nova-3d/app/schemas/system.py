"""
NOVA 3D - Pydantic Schemas for Machine Models & System Telemetry
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ComponentResponse(BaseModel):
    id: str
    node_name: str
    display_name: str
    parent_name: Optional[str]
    category: str
    vertex_count: int
    face_count: int
    center: List[float]
    bounds: Dict[str, Any]
    is_visible: bool

class MachineModelResponse(BaseModel):
    id: str
    project_id: str
    model_name: str
    format: str
    storage_path: str
    vertex_count: int
    face_count: int
    component_count: int
    bounding_box: Dict[str, Any]
    components: List[ComponentResponse] = []

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database_connected: bool

class HardwareProfileResponse(BaseModel):
    os: str
    platform: str
    cpu: Dict[str, Any]
    ram: Dict[str, Any]
    disk: Dict[str, Any]
    gpu: Dict[str, Any]
    pytorch: Dict[str, Any]
    warnings: List[str]
    recommendations: List[str]
    resource_mode: str
