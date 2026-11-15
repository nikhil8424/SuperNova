"""
NOVA 3D - Pytest Global Fixtures & Test Setup
"""
import pytest
import os
import tempfile
import numpy as np
import cv2
import trimesh
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Project, Asset, ReconstructionJob, MachineModel, Component

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def db_session():
    """In-memory SQLite database session for unit testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def synthetic_video(temp_dir):
    """Creates a 2-second valid MP4 test video."""
    video_path = temp_dir / "test_capture.mp4"
    width, height = 320, 240
    fps = 30
    total_frames = 60

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw moving pattern
        cx = int(width / 2 + 40 * np.cos(i * 0.1))
        cy = int(height / 2 + 40 * np.sin(i * 0.1))
        cv2.circle(frame, (cx, cy), 25, (0, 240, 255), -1)
        cv2.putText(frame, f"F:{i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        out.write(frame)

    out.release()
    return str(video_path)

@pytest.fixture
def synthetic_glb(temp_dir):
    """Creates a multi-component GLB model."""
    glb_path = temp_dir / "test_machine.glb"
    scene = trimesh.Scene()

    box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    cyl = trimesh.creation.cylinder(radius=0.3, height=0.8)
    cyl.apply_translation([0, 0, 1.0])

    scene.add_geometry(box, node_name="Housing", geom_name="Housing")
    scene.add_geometry(cyl, node_name="Piston", geom_name="Piston")

    data = trimesh.exchange.gltf.export_glb(scene)
    with open(glb_path, "wb") as f:
        f.write(data)

    return str(glb_path)
