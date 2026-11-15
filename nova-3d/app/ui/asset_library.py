"""
NOVA 3D - Asset Library View
Centralized catalog of all uploaded videos, 3D meshes, generated splats, and point clouds.
"""
import os
import streamlit as st
import pandas as pd
from app.core.database import SessionLocal
from app.models import Asset, Project, Scene, MachineModel

def render_asset_library(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">CENTRAL STORAGE</div>', unsafe_allow_html=True)
    st.title("Asset Library")
    st.markdown("Browse, inspect, and manage ingested video feeds, structured CAD meshes, and reconstructed point clouds.")

    db = SessionLocal()
    try:
        assets = db.query(Asset).order_by(Asset.created_at.desc()).all()
        scenes = db.query(Scene).order_by(Scene.created_at.desc()).all()
        models = db.query(MachineModel).order_by(MachineModel.created_at.desc()).all()
    finally:
        db.close()

    tab1, tab2, tab3 = st.tabs(["📹 Video Assets", "🌐 Reconstructed Scenes", "⚙️ Machine CAD Models"])

    with tab1:
        if not assets:
            st.info("No video assets uploaded yet.")
        else:
            table_data = []
            for a in assets:
                table_data.append({
                    "Asset ID": a.id[:8],
                    "Filename": a.original_filename,
                    "Type": a.asset_type.upper(),
                    "Size (MB)": round(a.file_size_bytes / (1024 * 1024), 2),
                    "Created At": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "N/A",
                    "Path": a.storage_path
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    with tab2:
        if not scenes:
            st.info("No 3D scenes reconstructed yet.")
        else:
            scene_data = []
            for s in scenes:
                scene_data.append({
                    "Scene Name": s.name,
                    "Format": s.format.upper(),
                    "Primitives": f"{s.point_count:,}",
                    "Cameras": s.camera_count,
                    "Created At": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "N/A"
                })
            st.dataframe(pd.DataFrame(scene_data), use_container_width=True)

    with tab3:
        if not models:
            st.info("No structured machine models uploaded yet.")
        else:
            m_data = []
            for m in models:
                m_data.append({
                    "Model Name": m.model_name,
                    "Components": m.component_count,
                    "Vertices": f"{m.vertex_count:,}",
                    "Faces": f"{m.face_count:,}",
                    "Format": m.format.upper()
                })
            st.dataframe(pd.DataFrame(m_data), use_container_width=True)
