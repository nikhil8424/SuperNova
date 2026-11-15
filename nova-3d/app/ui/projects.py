"""
NOVA 3D - Project Management UI View
Create, list, edit, view history, and delete reconstruction and machine projects.
"""
import streamlit as st
import shutil
from datetime import datetime
from app.core.database import SessionLocal
from app.models import Project, Asset, ReconstructionJob, Scene, MachineModel
from app.config import PROJECTS_DIR

def render_create_project(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">WORKSPACE CREATION</div>', unsafe_allow_html=True)
    st.title("Create New Project")
    st.markdown("Configure a dedicated workspace for 3D reconstruction or machine exploration.")

    with st.form("create_project_form"):
        name = st.text_input("Project Name *", placeholder="e.g. Industrial Turbine Inspection")
        desc = st.text_area("Description", placeholder="Objectives, location or subject details...")
        p_type = st.selectbox(
            "Project Type *",
            options=["environment", "object", "machine"],
            format_func=lambda x: {
                "environment": "Environment Reconstruction (Rooms, Buildings, Walkthroughs)",
                "object": "Object Reconstruction (360° Multi-view Captures)",
                "machine": "Machine Exploration (Structured GLB/GLTF CAD Assemblies)"
            }[x]
        )

        submitted = st.form_submit_button("Create Workspace")
        if submitted:
            if not name.strip():
                st.error("Project name cannot be empty.")
            else:
                db = SessionLocal()
                try:
                    new_proj = Project(
                        name=name.strip(),
                        description=desc.strip(),
                        project_type=p_type,
                        status="active"
                    )
                    db.add(new_proj)
                    db.commit()
                    db.refresh(new_proj)

                    # Create folders
                    p_dir = PROJECTS_DIR / new_proj.id
                    for sub in ["input", "frames", "colmap", "reconstruction", "exports", "logs"]:
                        (p_dir / sub).mkdir(parents=True, exist_ok=True)

                    st.success(f"Project '{new_proj.name}' created successfully!")
                    if navigate_fn:
                        if p_type == "machine":
                            navigate_fn("Machine Explorer")
                        else:
                            navigate_fn("Environment Reconstruction")
                finally:
                    db.close()

def render_projects_manager(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">PROJECT INVENTORY</div>', unsafe_allow_html=True)
    st.title("Projects & Workspaces")

    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
        if not projects:
            st.info("No projects found in database. Create your first project using the sidebar or button below.")
            if st.button("➕ Create Project"):
                if navigate_fn:
                    navigate_fn("Create Project")
            return

        for p in projects:
            with st.expander(f"📁 {p.name} ({p.project_type.upper()}) - {p.status.upper()}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**ID:** `{p.id}`")
                    st.markdown(f"**Description:** {p.description or 'No description provided.'}")
                    st.markdown(f"**Created:** {p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else 'N/A'}")

                    # List Assets
                    assets = db.query(Asset).filter(Asset.project_id == p.id).all()
                    st.markdown(f"**Associated Assets ({len(assets)}):**")
                    for a in assets:
                        st.markdown(f"- 📄 `{a.original_filename}` ({a.asset_type}, {round(a.file_size_bytes/(1024*1024), 2)} MB)")

                    # List Scenes
                    scenes = db.query(Scene).filter(Scene.project_id == p.id).all()
                    if scenes:
                        st.markdown(f"**Generated 3D Scenes ({len(scenes)}):**")
                        for s in scenes:
                            st.markdown(f"- 🌐 `{s.name}` ({s.format.upper()}, {s.point_count} points)")

                with col2:
                    st.markdown("#### Actions")
                    if p.project_type == "machine":
                        if st.button(f"Open Machine Explorer", key=f"open_m_{p.id}"):
                            st.session_state["active_project_id"] = p.id
                            if navigate_fn:
                                navigate_fn("Machine Explorer")
                    else:
                        if st.button(f"Open Scene Viewer", key=f"open_s_{p.id}"):
                            st.session_state["active_project_id"] = p.id
                            if navigate_fn:
                                navigate_fn("Scene Viewer")

                    if st.button(f"🗑️ Delete Project", key=f"del_{p.id}", type="primary"):
                        db.delete(p)
                        db.commit()
                        p_dir = PROJECTS_DIR / p.id
                        if p_dir.exists():
                            shutil.rmtree(p_dir, ignore_errors=True)
                        st.success(f"Project '{p.name}' deleted.")
                        st.rerun()
    finally:
        db.close()
