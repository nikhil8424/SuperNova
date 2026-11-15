"""
Unit and Integration tests for FastAPI Route Functions and Handlers
"""
import pytest
from app.api.routes.system import get_health, get_hardware_telemetry, get_dependencies_status
from app.api.routes.projects import create_project, list_projects, get_project, update_project, delete_project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models import Project

def test_system_endpoints(db_session):
    health = get_health(db=db_session)
    assert health["app"] == "NOVA 3D"
    assert health["database_connected"] is True
    assert health["status"] == "healthy"

    hw = get_hardware_telemetry()
    assert "cpu" in hw
    assert "ram" in hw
    assert "gpu" in hw

    deps = get_dependencies_status()
    assert "opencv" in deps
    assert "mediapipe" in deps
    assert "colmap" in deps

def test_project_endpoints(db_session):
    # 1. Create Project
    data = ProjectCreate(
        name="API Test Workspace",
        description="Testing route handlers",
        project_type="environment"
    )
    created = create_project(data=data, db=db_session)
    assert created["name"] == "API Test Workspace"
    proj_id = created["id"]

    # 2. List Projects
    all_projs = list_projects(db=db_session)
    assert len(all_projs) >= 1
    assert any(p["id"] == proj_id for p in all_projs)

    # 3. Get Project
    proj_obj = db_session.query(Project).filter(Project.id == proj_id).first()
    res = get_project(project=proj_obj)
    assert res["name"] == "API Test Workspace"

    # 4. Update Project
    update_data = ProjectUpdate(name="Renamed Workspace", status="processing")
    updated = update_project(data=update_data, project=proj_obj, db=db_session)
    assert updated["name"] == "Renamed Workspace"
    assert updated["status"] == "processing"

    # 5. Delete Project
    del_res = delete_project(project=proj_obj, db=db_session)
    assert "deleted successfully" in del_res["message"]
    assert db_session.query(Project).filter(Project.id == proj_id).count() == 0
