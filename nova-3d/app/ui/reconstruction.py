"""
NOVA 3D - Video Ingestion & 3D Reconstruction Pipeline UI View
Handles video upload, validation, OpenCV frame extraction, SfM execution, and Splat training.
"""
import os
import shutil
import json
import streamlit as st
from pathlib import Path
from app.core.database import SessionLocal
from app.models import Project, Asset, ReconstructionJob
from app.config import PROJECTS_DIR, SAMPLES_DIR
from app.core.security import validate_file_upload, generate_secure_filename, sanitize_filename
from app.reconstruction.video_processor import inspect_video
from app.workers.local_worker import job_worker

def render_reconstruction_view(reconstruction_mode="environment", navigate_fn=None):
    mode_title = "Environment Reconstruction" if reconstruction_mode == "environment" else "Object Reconstruction"
    st.markdown(f'<div class="nova-logo-badge">{reconstruction_mode.upper()} PIPELINE</div>', unsafe_allow_html=True)
    st.title(mode_title)
    st.markdown("Convert monocular smartphone video into an explorable 3D Gaussian / point cloud representation.")

    # Project Selector
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.project_type.in_(["environment", "object"])).all()
        if not projects:
            st.warning("No reconstruction projects found. Please create one first.")
            if st.button("➕ Create New Project"):
                if navigate_fn:
                    navigate_fn("Create Project")
            return

        proj_options = {p.id: f"{p.name} ({p.project_type})" for p in projects}
        default_id = st.session_state.get("active_project_id", list(proj_options.keys())[0])
        if default_id not in proj_options:
            default_id = list(proj_options.keys())[0]

        selected_project_id = st.selectbox(
            "Select Target Project:",
            options=list(proj_options.keys()),
            format_func=lambda x: proj_options[x],
            index=list(proj_options.keys()).index(default_id)
        )
        st.session_state["active_project_id"] = selected_project_id
        target_project = db.query(Project).filter(Project.id == selected_project_id).first()
    finally:
        db.close()

    # Capture Guidance Accordion
    with st.expander("💡 Essential Video Capture Guidance", expanded=False):
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("""
            - **Smooth Camera Path:** Walk slowly in a circular orbit or continuous arc around the scene.
            - **High Overlap:** Keep 70-80% overlap between consecutive frames.
            - **Avoid Motion Blur:** Turn fast motions into slow pans; ensure adequate lighting.
            """)
        with g_col2:
            st.markdown("""
            - **Lighting Consistency:** Avoid harsh moving shadows, flickering lamps, or backlights.
            - **Texture Richness:** Blank walls, mirrors, and glass surfaces cannot be triangulated easily.
            - **Static Objects:** Ensure no moving people, vehicles, or pets enter the capture.
            """)

    # Video Upload or Sample Selection Tabs
    tab_upload, tab_sample = st.tabs(["📤 Upload User Video", "🎯 Use Pre-Calibrated Sample Video"])

    uploaded_video_asset = None

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose a video file (MP4, MOV, AVI, MKV):",
            type=["mp4", "mov", "avi", "mkv"],
            key=f"video_uploader_{selected_project_id}"
        )

        if uploaded_file is not None:
            bytes_data = uploaded_file.read()
            safe_name = sanitize_filename(uploaded_file.name)
            is_valid, err_msg = validate_file_upload(bytes_data, safe_name, asset_type="video")

            if not is_valid:
                st.error(f"Validation Error: {err_msg}")
            else:
                # Save asset to project directory
                secure_name = generate_secure_filename(safe_name, prefix="video")
                target_p = PROJECTS_DIR / selected_project_id / "input" / secure_name
                target_p.parent.mkdir(parents=True, exist_ok=True)

                with open(target_p, "wb") as f:
                    f.write(bytes_data)

                # Inspect metadata
                ok, v_meta, err = inspect_video(str(target_p))
                if ok:
                    st.success(f"Video uploaded successfully! ({v_meta['resolution']} @ {v_meta['fps']} FPS, {v_meta['duration_seconds']}s)")
                    # Save to DB
                    db = SessionLocal()
                    try:
                        asset = Asset(
                            project_id=selected_project_id,
                            asset_type="video",
                            original_filename=safe_name,
                            storage_path=str(target_p),
                            file_size_bytes=len(bytes_data),
                            metadata_json=json.dumps(v_meta)
                        )
                        db.add(asset)
                        db.commit()
                        db.refresh(asset)
                        uploaded_video_asset = asset
                    finally:
                        db.close()
                else:
                    st.error(f"Video stream error: {err}")

    with tab_sample:
        sample_video_path = SAMPLES_DIR / "sample_walkthrough.mp4"
        st.markdown("Load the built-in orbital test capture video (simulated calibrated sensor walkthrough):")
        if sample_video_path.exists():
            if st.button("Load Built-in Sample Video (sample_walkthrough.mp4)"):
                target_p = PROJECTS_DIR / selected_project_id / "input" / "sample_walkthrough.mp4"
                shutil.copyfile(sample_video_path, target_p)

                ok, v_meta, _ = inspect_video(str(target_p))
                db = SessionLocal()
                try:
                    asset = Asset(
                        project_id=selected_project_id,
                        asset_type="video",
                        original_filename="sample_walkthrough.mp4",
                        storage_path=str(target_p),
                        file_size_bytes=os.path.getsize(target_p),
                        metadata_json=json.dumps(v_meta)
                    )
                    db.add(asset)
                    db.commit()
                    db.refresh(asset)
                    st.success("Sample walkthrough video imported successfully!")
                    st.rerun()
                finally:
                    db.close()
        else:
            st.info("Sample video was not found on disk.")

    # Video Asset Selection & Configuration
    st.markdown("---")
    st.subheader("Configure & Launch 3D Reconstruction")

    db = SessionLocal()
    try:
        available_videos = db.query(Asset).filter(
            Asset.project_id == selected_project_id,
            Asset.asset_type == "video"
        ).all()
    finally:
        db.close()

    if not available_videos:
        st.info("Upload or import a video above to configure reconstruction parameters.")
        return

    vid_choices = {a.id: f"{a.original_filename} ({round(a.file_size_bytes/(1024*1024), 1)} MB)" for a in available_videos}
    selected_asset_id = st.selectbox(
        "Select Source Video Asset:",
        options=list(vid_choices.keys()),
        format_func=lambda x: vid_choices[x]
    )

    # Reconstruction Hyperparameters
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    with cfg_col1:
        interval = st.slider("Frame Extraction Interval (s)", min_value=0.1, max_value=2.0, value=0.5, step=0.1,
                             help="Sampling interval in seconds between extracted frames.")
    with cfg_col2:
        max_dim = st.selectbox("Max Frame Dimension (px)", options=[800, 1000, 1200, 1600], index=2,
                               help="Max width or height. 1000-1200 recommended for 4GB VRAM GPU.")
    with cfg_col3:
        iterations = st.selectbox("Splat Training Iterations", options=[1500, 2500, 4000, 10000], index=1,
                                  help="Training steps. Lower iterations recommended for rapid validation.")

    # Launch Button
    if st.button("🚀 Start Full 3D Reconstruction Pipeline", type="primary", use_container_width=True):
        db = SessionLocal()
        try:
            job = ReconstructionJob(
                project_id=selected_project_id,
                source_asset_id=selected_asset_id,
                stage="Pending",
                status="pending",
                progress_percent=0.0,
                current_step_info="Job queued for processing."
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Submit to worker
            job_worker.submit_reconstruction_job(
                job_id=job.id,
                project_id=selected_project_id,
                video_asset_id=selected_asset_id,
                interval_seconds=interval,
                max_dimension=max_dim,
                training_iterations=iterations
            )
            st.success(f"Reconstruction job `{job.id}` submitted successfully!")
            if navigate_fn:
                navigate_fn("Processing Monitor")
        finally:
            db.close()
