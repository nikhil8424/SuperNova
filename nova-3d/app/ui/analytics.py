"""
NOVA 3D - Reconstruction Analytics & Quality Metrics View
Displays genuine Structure-from-Motion metrics, training benchmarks, and evaluation reports.
Strictly adheres to evaluation integrity (no artificial PSNR/SSIM numbers).
"""
import json
import streamlit as st
import pandas as pd
from app.core.database import SessionLocal
from app.models import Metric, Project, ReconstructionJob, Scene

def render_analytics(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">PERFORMANCE EVALUATION</div>', unsafe_allow_html=True)
    st.title("Metrics & Reconstruction Analytics")
    st.markdown("Quantitative reconstruction accuracy, camera registration ratios, and execution benchmarks.")

    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            st.info("No projects available to analyze.")
            return

        proj_choices = {p.id: p.name for p in projects}
        selected_p_id = st.selectbox("Select Project for Deep Dive:", options=list(proj_choices.keys()), format_func=lambda x: proj_choices[x])

        metrics = db.query(Metric).filter(Metric.project_id == selected_p_id).all()
        jobs = db.query(ReconstructionJob).filter(ReconstructionJob.project_id == selected_p_id).all()
        scenes = db.query(Scene).filter(Scene.project_id == selected_p_id).all()
    finally:
        db.close()

    # SfM Metric Summary Cards
    st.subheader("Structure from Motion (SfM) Accuracy")

    reg_images = next((m.metric_value for m in metrics if m.metric_name == "registered_images"), None)
    sparse_pts = next((m.metric_value for m in metrics if m.metric_name == "sparse_points"), None)
    reproj_err = next((m.metric_value for m in metrics if m.metric_name == "mean_reprojection_error"), None)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registered Images", f"{int(reg_images):,}" if reg_images is not None else "N/A")
    m2.metric("Sparse 3D Points", f"{int(sparse_pts):,}" if sparse_pts is not None else "N/A")
    m3.metric("Reprojection Error", f"{reproj_err:.2f} px" if reproj_err is not None else "N/A", delta="Sub-pixel" if reproj_err and reproj_err < 1.0 else None)
    m4.metric("Generated Scenes", len(scenes))

    st.markdown("---")

    # Benchmarks & Training Duration Table
    st.subheader("Reconstruction Pipeline Benchmarks")
    if not jobs:
        st.info("No jobs recorded for this project.")
    else:
        job_data = []
        for j in jobs:
            job_data.append({
                "Job ID": j.id[:8],
                "Stage": j.stage,
                "Status": j.status.upper(),
                "Progress": f"{int(j.progress_percent)}%",
                "Duration (s)": j.to_dict()["duration_seconds"] or "In progress",
                "Started At": j.started_at.strftime('%Y-%m-%d %H:%M:%S') if j.started_at else "N/A"
            })
        st.dataframe(pd.DataFrame(job_data), use_container_width=True)

    # Scientific Quality Protocol (PSNR / SSIM Rule)
    st.markdown("---")
    st.subheader("Photometric Quality Evaluation Protocol (PSNR / SSIM)")
    st.info("""
    🔬 **NOVA 3D Evaluation Standard:**
    In accordance with rigorous computer vision practice, **PSNR (Peak Signal-to-Noise Ratio)** and **SSIM (Structural Similarity)**
    are only reported when held-out reference evaluation viewpoints are supplied and aligned.
    NOVA 3D never fabricates artificial quality scores. Visual inspection and reprojection error serve as the primary indicators for casual video captures.
    """)

    # Downloadable Reconstruction Report
    st.subheader("Export Project Audit Report")
    report_dict = {
        "project_id": selected_p_id,
        "metrics": [m.to_dict() for m in metrics],
        "jobs": [j.to_dict() for j in jobs],
        "scenes": [s.to_dict() for s in scenes]
    }
    report_json = json.dumps(report_dict, indent=2)

    st.download_button(
        label="📥 Download JSON Reconstruction Report",
        data=report_json,
        file_name=f"nova3d_report_{selected_p_id[:8]}.json",
        mime="application/json"
    )
