"""
NOVA 3D - Main Application Dashboard View
Queries live application database for projects, jobs, assets, and reads real-time hardware telemetry.
"""
import streamlit as st
from datetime import datetime
from app.core.database import SessionLocal
from app.models import Project, ReconstructionJob, Asset, Scene, MachineModel
from app.core.hardware import get_system_hardware_profile

def render_dashboard(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">SYSTEM OVERVIEW</div>', unsafe_allow_html=True)
    st.title("NOVA 3D Command Center")
    st.markdown("Reconstruct Reality. Explore Beyond. Real-time platform status and asset telemetry.")

    # Fetch actual metrics from database
    db = SessionLocal()
    try:
        total_projects = db.query(Project).count()
        completed_reconstructions = db.query(ReconstructionJob).filter(ReconstructionJob.status == "completed").count()
        processing_jobs = db.query(ReconstructionJob).filter(ReconstructionJob.status.in_(["running", "queued"])).count()
        failed_jobs = db.query(ReconstructionJob).filter(ReconstructionJob.status == "failed").count()
        uploaded_videos = db.query(Asset).filter(Asset.asset_type == "video").count()
        generated_scenes = db.query(Scene).count()
        machine_models = db.query(MachineModel).count()
        total_3d_assets = generated_scenes + machine_models

        recent_projects = db.query(Project).order_by(Project.created_at.desc()).limit(5).all()
        recent_jobs = db.query(ReconstructionJob).order_by(ReconstructionJob.created_at.desc()).limit(5).all()
    finally:
        db.close()

    # Hardware Telemetry Query
    hardware = get_system_hardware_profile()

    # Primary KPI Row
    st.subheader("Platform Telemetry")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{total_projects}</div>
            <div class="nova-stat-label">Total Projects</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{completed_reconstructions}</div>
            <div class="nova-stat-label">Completed Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{processing_jobs}</div>
            <div class="nova-stat-label">Active Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{failed_jobs}</div>
            <div class="nova-stat-label">Failed Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{uploaded_videos}</div>
            <div class="nova-stat-label">Source Videos</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
        <div class="nova-card">
            <div class="nova-stat-value">{total_3d_assets}</div>
            <div class="nova-stat-label">3D Assets</div>
        </div>
        """, unsafe_allow_html=True)

    # Hardware Utilization Row
    st.subheader("Host Compute & Resource Utilization")
    h_col1, h_col2, h_col3, h_col4 = st.columns(4)

    with h_col1:
        cpu = hardware["cpu"]
        st.metric(
            label="CPU Load",
            value=f"{cpu['cpu_percent']}%",
            delta=f"{cpu['logical_cores']} Cores ({cpu['architecture']})"
        )

    with h_col2:
        ram = hardware["ram"]
        st.metric(
            label="System RAM",
            value=f"{ram['used_gb']} / {ram['total_gb']} GB",
            delta=f"{ram['percent']}% Used",
            delta_color="inverse" if ram['percent'] > 85 else "normal"
        )

    with h_col3:
        gpu = hardware["gpu"]
        if gpu["available"]:
            v_used = round(gpu["vram_used_mb"] / 1024.0, 1)
            v_total = round(gpu["vram_total_mb"] / 1024.0, 1)
            util = f"{gpu['gpu_utilization_percent']}%" if gpu.get("gpu_utilization_percent") is not None else "Active"
            st.metric(
                label=f"NVIDIA GPU: {gpu['name']}",
                value=f"{v_used} / {v_total} GB VRAM",
                delta=f"Driver {gpu['driver_version']} (CUDA {gpu['cuda_version_supported']})"
            )
        else:
            st.metric(
                label="NVIDIA GPU",
                value="Not Detected",
                delta="CPU Fallback Active",
                delta_color="off"
            )

    with h_col4:
        disk = hardware["disk"]
        st.metric(
            label="Storage Utilization",
            value=f"{disk['used_gb']} / {disk['total_gb']} GB",
            delta=f"{disk['free_gb']} GB Free ({disk['percent']}%)"
        )

    # Quick Action Buttons
    st.markdown("---")
    st.subheader("Quick Launch Actions")
    qa_col1, qa_col2, qa_col3 = st.columns(3)

    with qa_col1:
        if st.button("➕ Create New Project", use_container_width=True):
            if navigate_fn:
                navigate_fn("Create Project")

    with qa_col2:
        if st.button("📹 Ingest & Reconstruct Video", use_container_width=True):
            if navigate_fn:
                navigate_fn("Environment Reconstruction")

    with qa_col3:
        if st.button("⚙️ Open Machine Explorer", use_container_width=True):
            if navigate_fn:
                navigate_fn("Machine Explorer")

    # Recent Projects & Activity Table
    st.markdown("---")
    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.subheader("Recent Projects")
        if not recent_projects:
            st.info("No projects created yet. Click 'Create New Project' to get started.")
        else:
            for p in recent_projects:
                status_badge = "badge-success" if p.status == "completed" else ("badge-running" if p.status == "processing" else "badge-warning")
                st.markdown(f"""
                <div class="nova-card" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>{p.name}</strong>
                        <span class="{status_badge}">{p.status.upper()}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                        Type: {p.project_type.capitalize()} • Created: {p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else 'N/A'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with r_col2:
        st.subheader("Recent Processing Activity")
        if not recent_jobs:
            st.info("No reconstruction jobs submitted yet.")
        else:
            for j in recent_jobs:
                badge = "badge-success" if j.status == "completed" else ("badge-danger" if j.status == "failed" else "badge-running")
                st.markdown(f"""
                <div class="nova-card" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>Stage: {j.stage}</strong>
                        <span class="{badge}">{int(j.progress_percent)}%</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                        {j.current_step_info or 'Status: ' + j.status}
                    </div>
                </div>
                """, unsafe_allow_html=True)
