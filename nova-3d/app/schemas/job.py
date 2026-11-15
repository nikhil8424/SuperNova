"""
NOVA 3D - Pydantic Schemas for Reconstruction Jobs
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ReconstructionRequest(BaseModel):
    video_asset_id: str
    extraction_interval: float = Field(0.5, ge=0.1, le=5.0)
    max_image_dim: int = Field(1600, ge=400, le=3840)
    training_iterations: int = Field(4000, ge=500, le=30000)
    enable_gpu_fallback: bool = True

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    source_asset_id: Optional[str]
    stage: str
    status: str
    progress_percent: float
    current_step_info: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    created_at: Optional[str]
