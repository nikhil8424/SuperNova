"""
NOVA 3D - Pydantic Schemas for Assets
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any

class AssetResponse(BaseModel):
    id: str
    project_id: str
    asset_type: str
    original_filename: str
    storage_path: str
    file_size_bytes: int
    metadata: Dict[str, Any] = {}
    created_at: Optional[str]

    class Config:
        from_attributes = True
