"""
NOVA 3D - Processing Job Monitor View
Tracks asynchronous job progress, stage transitions, logs, cancellation, and retry actions.
"""
import streamlit as st
from datetime import datetime
from app.core.database import SessionLocal
from app.models import ReconstructionJob, Project
from app.workers.local_worker import job_worker

def render_processing_monitor(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">JOB ORCHESTRATION</div>', unsafe_allow_html=True)
    st.title("Processing Monitor")
    st.markdown("Live status of asynchronous video frame extraction, Structure from Motion, and Gaussian Splatting jobs.")

    db = SessionLocal()
    try:
        jobs = db.query(ReconstructionJob).order_by(ReconstructionJob.created_at.desc()).all()
        if not jobs:
            st.info("No reconstruction jobs submitted yet. Start a job from Environment or Object Reconstruction.")
            return

        # Summary Bar
        active_cnt = sum(1 for j in jobs if j.status in ("running", "queued"))
        completed_cnt = sum(1 for j in jobs if j.status == "completed")
        failed_cnt = sum(1 for j in jobs if j.status == "failed")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Jobs", active_cnt)
        c2.metric("Completed Jobs", completed_cnt)
        c3.metric("Failed Jobs", failed_cnt)
        with c4:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()

        st.markdown("---")

        for job in jobs:
            proj = db.query(Project).filter(Project.id == job.project_id).first()
            p_name = proj.name if proj else "Unknown Project"

            is_running = job.status == "running"
            is_done = job.status == "completed"
            is_failed = job.status == "failed"

            badge_class = "badge-success" if is_done else ("badge-danger" if is_failed else "badge-running")

            with st.expander(f"⚙️ Job `{job.id[:8]}...` | {p_name} | Stage: {job.stage} ({int(job.progress_percent)}%)", expanded=is_running):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div><strong>Project:</strong> {p_name} (ID: `{job.project_id}`)</div>
                    <span class="{badge_class}">{job.status.upper()}</span>
                </div>
                """, unsafe_allow_html=True)

                # Progress bar
                st.progress(min(1.0, max(0.0, job.progress_percent / 100.0)))
                st.markdown(f"**Current Operation:** {job.current_step_info or 'In progress...'}")

                # Timestamps
                t1, t2, t3 = st.columns(3)
                t1.markdown(f"**Started:** {job.started_at.strftime('%H:%M:%S') if job.started_at else 'Pending'}")
                t2.markdown(f"**Completed:** {job.completed_at.strftime('%H:%M:%S') if job.completed_at else 'Running...'}")
                duration = job.to_dict()["duration_seconds"]
                t3.markdown(f"**Duration:** {duration}s" if duration is not None else "**Duration:** Running")

                if job.error_message:
                    st.error(f"Error Details: {job.error_message}")

                # Job Logs Box
                if job.logs:
                    st.markdown("**Live Pipeline Logs:**")
                    st.text_area("Logs", job.logs, height=180, disabled=True, key=f"log_{job.id}")

                # Action buttons
                btn_c1, btn_c2, btn_c3 = st.columns(3)
                with btn_c1:
                    if is_done and navigate_fn:
                        if st.button(f"🌐 View Reconstructed 3D Scene", key=f"view_scene_{job.id}", type="primary"):
                            st.session_state["active_project_id"] = job.project_id
                            navigate_fn("Scene Viewer")

                with btn_c2:
                    if is_running:
                        if st.button(f"⏹️ Cancel Job", key=f"cancel_{job.id}"):
                            job_worker.cancel_job(job.id)
                            st.warning("Cancellation requested.")
                            st.rerun()

                with btn_c3:
                    if is_failed:
                        if st.button(f"🔁 Retry Reconstruction", key=f"retry_{job.id}"):
                            job.status = "pending"
                            job.stage = "Pending"
                            job.progress_percent = 0.0
                            job.error_message = None
                            db.commit()
                            job_worker.submit_reconstruction_job(
                                job_id=job.id,
                                project_id=job.project_id,
                                video_asset_id=job.source_asset_id
                            )
                            st.info("Job resubmitted.")
                            st.rerun()
    finally:
        db.close()
