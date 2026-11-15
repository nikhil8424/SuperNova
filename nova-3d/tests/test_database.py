"""
Unit tests for Database Models & Relationships
"""
from app.models import Project, Asset, ReconstructionJob, Scene, MachineModel, Component

def test_project_crud(db_session):
    p = Project(name="Laboratory Scan", description="Test scan", project_type="environment")
    db_session.add(p)
    db_session.commit()

    retrieved = db_session.query(Project).filter(Project.id == p.id).first()
    assert retrieved is not None
    assert retrieved.name == "Laboratory Scan"
    assert retrieved.status == "active"
    assert retrieved.project_type == "environment"

def test_project_relationships_cascade(db_session):
    p = Project(name="Cascade Test", project_type="machine")
    db_session.add(p)
    db_session.commit()

    asset = Asset(
        project_id=p.id,
        asset_type="model",
        original_filename="assembly.glb",
        storage_path="/data/assembly.glb",
        file_size_bytes=5000
    )
    job = ReconstructionJob(project_id=p.id, stage="Validating", status="pending")
    db_session.add_all([asset, job])
    db_session.commit()

    assert len(p.assets) == 1
    assert len(p.jobs) == 1

    # Cascade delete
    db_session.delete(p)
    db_session.commit()

    assert db_session.query(Asset).filter(Asset.project_id == p.id).count() == 0
    assert db_session.query(ReconstructionJob).filter(ReconstructionJob.project_id == p.id).count() == 0
