"""
NOVA 3D - Pydantic Schemas for Projects
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = ""
    project_type: str = Field("environment", pattern="^(environment|object|machine)$")

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    project_type: str
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]
    asset_count: int = 0
    job_count: int = 0

    class Config:
        from_attributes = True
