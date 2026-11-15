"""
NOVA 3D - Interactive 3D Scene Viewer View
Visualizes reconstructed 3D Gaussian splat point clouds, sparse SfM geometry,
and camera poses using WebGL Three.js or Plotly engines within Streamlit.
"""
import os
import json
import streamlit as st
import streamlit.components.v1 as components_v1
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from app.core.database import SessionLocal
from app.models import Scene, Project, Asset
from app.config import THEME_COLORS
from app.ui.three_viewer import generate_threejs_gaussian_splat_viewer_html

def load_ply_points_and_colors(ply_path: str, max_points: int = 15000):
    """Parses ASCII PLY file for x, y, z positions and r, g, b colors."""
    if not os.path.exists(ply_path):
        return None, None

    points = []
    colors = []

    with open(ply_path, "r", encoding="utf-8", errors="ignore") as f:
        header = True
        for line in f:
            if header:
                if line.strip() == "end_header":
                    header = False
                continue
            parts = line.strip().split()
            if len(parts) >= 6:
                try:
                    x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                    r, g, b = int(parts[3]), int(parts[4]), int(parts[5])
                    points.append([x, y, z])
                    colors.append(f"rgb({r},{g},{b})")
                    if len(points) >= max_points:
                        break
                except ValueError:
                    pass

    if not points:
        return None, None

    return np.array(points), colors

def render_scene_viewer(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">3D SPATIAL RECONSTRUCTION</div>', unsafe_allow_html=True)
    st.title("Interactive 3D Scene Viewer")
    st.markdown("Navigate photorealistic Gaussian Splat scenes, sparse SfM camera trajectories, and triangulated points.")

    db = SessionLocal()
    try:
        scenes = db.query(Scene).order_by(Scene.created_at.desc()).all()
    finally:
        db.close()

    if not scenes:
        st.info("No reconstructed 3D scenes available yet. Go to 'Environment Reconstruction' to ingest a video.")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Ingest Video for 3D Reconstruction"):
                if navigate_fn:
                    navigate_fn("Environment Reconstruction")
        return

    scene_choices = {s.id: f"{s.name} ({s.format.upper()}, {s.point_count} primitives)" for s in scenes}
    selected_scene_id = st.selectbox(
        "Select 3D Scene to Inspect:",
        options=list(scene_choices.keys()),
        format_func=lambda x: scene_choices[x]
    )

    db = SessionLocal()
    try:
        scene = db.query(Scene).filter(Scene.id == selected_scene_id).first()
        proj = db.query(Project).filter(Project.id == scene.project_id).first()
    finally:
        db.close()

    if not scene:
        return

    # Metadata Row
    meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
    meta_c1.metric("Primitive Count", f"{scene.point_count:,}")
    meta_c2.metric("Camera Poses", f"{scene.camera_count}")
    meta_c3.metric("Representation", scene.format.upper())
    meta_c4.metric("File Size", f"{round(os.path.getsize(scene.file_path)/(1024*1024), 2) if os.path.exists(scene.file_path) else 0} MB")

    # Viewer Engine Selector & Controls
    ctl_c1, ctl_c2, ctl_c3 = st.columns(3)
    with ctl_c1:
        engine_type = st.radio("Renderer Architecture", ["WebGL Three.js Engine (Recommended)", "Plotly 3D Engine"], horizontal=True)
    with ctl_c2:
        point_size = st.slider("Primitive Display Radius", min_value=1.0, max_value=8.0, value=3.0, step=0.5)
    with ctl_c3:
        max_render_pts = st.select_slider("Point Density Budget", options=[2500, 5000, 10000, 20000, 50000], value=10000)

    # Render via Selected Engine
    if "Three.js" in engine_type:
        html_code = generate_threejs_gaussian_splat_viewer_html(
            ply_path=scene.file_path,
            point_budget=max_render_pts,
            point_size=point_size,
            height=600
        )
        components_v1.html(html_code, height=620)
    else:
        # Plotly Fallback Engine
        points, colors = load_ply_points_and_colors(scene.file_path, max_points=max_render_pts)

        if points is None or len(points) == 0:
            st.warning(f"Could not load point data from `{scene.file_path}`. File may be empty or missing.")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode='markers',
            marker=dict(
                size=point_size,
                color=colors if colors else '#00f0ff',
                opacity=0.88
            ),
            name='Gaussian Primitives'
        ))

        # Add Camera Trajectory Arc
        cam_angles = np.linspace(0, 2 * np.pi, max(2, scene.camera_count))
        cam_r = np.max(np.abs(points)) * 1.3 if len(points) > 0 else 2.0
        cam_x = cam_r * np.sin(cam_angles)
        cam_y = cam_r * np.cos(cam_angles)
        cam_z = np.full_like(cam_x, float(np.mean(points[:, 2])))

        fig.add_trace(go.Scatter3d(
            x=cam_x, y=cam_y, z=cam_z,
            mode='lines+markers',
            line=dict(color='#a855f7', width=3),
            marker=dict(size=4, color='#00f0ff'),
            name='Estimated Camera Orbit'
        ))

        fig.update_layout(
            paper_bgcolor="#0b0d13",
            plot_bgcolor="#0b0d13",
            margin=dict(l=0, r=0, t=10, b=0),
            height=600,
            scene=dict(
                xaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                yaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                zaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True)
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Scene Metadata Panel
    with st.expander("📄 Reconstructed Scene Metadata & Evaluation", expanded=True):
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            st.markdown(f"**Asset Path:** `{scene.file_path}`")
            st.markdown(f"**Associated Project:** {proj.name if proj else 'Unknown'}")
            st.markdown(f"**Reconstructed At:** {scene.created_at.strftime('%Y-%m-%d %H:%M:%S') if scene.created_at else 'N/A'}")
        with m_c2:
            import json
            meta = {}
            if scene.metadata_json:
                try:
                    meta = json.loads(scene.metadata_json)
                except Exception:
                    pass
            st.json(meta)
