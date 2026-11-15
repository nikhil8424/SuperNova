"""
NOVA 3D - Machine Model Explorer View
Loads structured GLB/GLTF engineering models, displays component tree,
provides component isolation, selection, and animated exploded-view inspection via WebGL Three.js or Plotly.
"""
import os
import shutil
import json
import streamlit as st
import streamlit.components.v1 as components_v1
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from app.core.database import SessionLocal
from app.models import MachineModel, Component, Project
from app.config import SAMPLES_DIR, PROJECTS_DIR
from app.machine.model_loader import inspect_3d_model
from app.machine.component_tree import ComponentTree
from app.machine.exploded_view import compute_exploded_transforms
from app.ui.three_viewer import generate_threejs_mesh_viewer_html

def render_machine_explorer(navigate_fn=None):
    st.markdown('<div class="nova-logo-badge">ENGINEERING EXPLORER</div>', unsafe_allow_html=True)
    st.title("Machine Model Explorer")
    st.markdown("Inspect structured 3D CAD/GLB assemblies, explore hierarchical parts, isolate components, and simulate exploded views.")

    db = SessionLocal()
    try:
        models = db.query(MachineModel).order_by(MachineModel.created_at.desc()).all()
    finally:
        db.close()

    # Model Ingestion / Sample Selector
    with st.expander("📥 Upload or Load Structured 3D Model", expanded=(len(models) == 0)):
        tab1, tab2 = st.tabs(["Upload GLB/GLTF Model", "Load Built-in Engine Assembly"])

        with tab1:
            uploaded_file = st.file_uploader("Select GLB/GLTF Assembly File:", type=["glb", "gltf"])
            if uploaded_file is not None:
                bytes_data = uploaded_file.read()
                model_name = Path(uploaded_file.name).stem

                # Find or create a machine project
                db = SessionLocal()
                try:
                    proj = db.query(Project).filter(Project.project_type == "machine").first()
                    if not proj:
                        proj = Project(name="CAD Engineering Lab", project_type="machine", description="Structured mechanical models")
                        db.add(proj)
                        db.commit()
                        db.refresh(proj)

                    target_path = PROJECTS_DIR / proj.id / "input" / uploaded_file.name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(bytes_data)

                    m_info = inspect_3d_model(str(target_path))

                    mach = MachineModel(
                        project_id=proj.id,
                        model_name=model_name,
                        format=m_info["format"],
                        storage_path=str(target_path),
                        vertex_count=m_info["total_vertices"],
                        face_count=m_info["total_faces"],
                        component_count=m_info["component_count"],
                        bounding_box_json=json.dumps(m_info["bounding_box"])
                    )
                    db.add(mach)
                    db.flush()

                    for comp in m_info["components"]:
                        c = Component(
                            machine_model_id=mach.id,
                            node_name=comp["node_name"],
                            display_name=comp["display_name"],
                            parent_name=comp["parent_name"],
                            category=comp["category"],
                            vertex_count=comp["vertex_count"],
                            face_count=comp["face_count"],
                            center_json=json.dumps(comp["center"]),
                            bounds_json=json.dumps(comp["bounds"]),
                            transform_json=json.dumps(comp["transform"]),
                            is_visible=True
                        )
                        db.add(c)

                    db.commit()
                    st.success(f"Model '{mach.model_name}' parsed: {len(m_info['components'])} components extracted!")
                    st.rerun()
                finally:
                    db.close()

        with tab2:
            st.markdown("Load the built-in multi-component Engine Assembly (EngineBlock, Pistons, Crankshaft, CylinderHead, SparkPlug):")
            sample_glb = SAMPLES_DIR / "engine_assembly.glb"
            if sample_glb.exists():
                if st.button("Load Built-in Engine Assembly (engine_assembly.glb)"):
                    db = SessionLocal()
                    try:
                        proj = db.query(Project).filter(Project.project_type == "machine").first()
                        if not proj:
                            proj = Project(name="Engineering CAD Assembly", project_type="machine", description="Engine kinematics")
                            db.add(proj)
                            db.commit()
                            db.refresh(proj)

                        target_p = PROJECTS_DIR / proj.id / "input" / "engine_assembly.glb"
                        target_p.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(sample_glb, target_p)

                        m_info = inspect_3d_model(str(target_p))
                        mach = MachineModel(
                            project_id=proj.id,
                            model_name="Engine Assembly V1",
                            format="glb",
                            storage_path=str(target_p),
                            vertex_count=m_info["total_vertices"],
                            face_count=m_info["total_faces"],
                            component_count=m_info["component_count"],
                            bounding_box_json=json.dumps(m_info["bounding_box"])
                        )
                        db.add(mach)
                        db.flush()

                        for comp in m_info["components"]:
                            c = Component(
                                machine_model_id=mach.id,
                                node_name=comp["node_name"],
                                display_name=comp["display_name"],
                                parent_name=comp["parent_name"],
                                category=comp["category"],
                                vertex_count=comp["vertex_count"],
                                face_count=comp["face_count"],
                                center_json=json.dumps(comp["center"]),
                                bounds_json=json.dumps(comp["bounds"]),
                                transform_json=json.dumps(comp["transform"]),
                                is_visible=True
                            )
                            db.add(c)
                        db.commit()
                        st.success("Sample Engine Assembly loaded successfully!")
                        st.rerun()
                    finally:
                        db.close()

    if not models:
        st.info("No 3D machine models loaded yet. Upload a model or click 'Load Built-in Engine Assembly' above.")
        return

    # Select Active Model
    model_choices = {m.id: f"{m.model_name} ({m.component_count} parts, {m.vertex_count:,} vertices)" for m in models}
    selected_model_id = st.selectbox("Select Machine Model:", options=list(model_choices.keys()), format_func=lambda x: model_choices[x])

    db = SessionLocal()
    try:
        active_model = db.query(MachineModel).filter(MachineModel.id == selected_model_id).first()
        components = [c.to_dict() for c in active_model.components]
    finally:
        db.close()

    if not components:
        st.warning("No components extracted for this model.")
        return

    # Initialize Session State for Tree
    if f"tree_{selected_model_id}" not in st.session_state:
        st.session_state[f"tree_{selected_model_id}"] = ComponentTree(components)
    tree: ComponentTree = st.session_state[f"tree_{selected_model_id}"]

    # Assembly Top KPI Bar
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Components", len(components))
    k2.metric("Total Vertices", f"{active_model.vertex_count:,}")
    k3.metric("Total Faces", f"{active_model.face_count:,}")
    k4.metric("Format", active_model.format.upper())

    # Exploded View Intensity Slider & Renderer Selector
    st.markdown("---")
    r_sel_col, c_slider, c_btn1 = st.columns([3, 4, 2])
    with r_sel_col:
        renderer_mode = st.radio("3D Viewport Engine", ["Three.js WebGL (Interactive PBR)", "Plotly 3D (Wireframe)"], horizontal=True)
    with c_slider:
        explosion_intensity = st.slider(
            "💥 Exploded View Separation Intensity",
            min_value=0.0,
            max_value=2.5,
            value=0.0,
            step=0.05,
            help="0.0 represents fully assembled original model. Higher values separate components along directional vectors."
        )
    with c_btn1:
        if st.button("Reset Assembly (0%)"):
            tree.restore_all()
            st.rerun()

    # Calculate Exploded Transforms
    import json
    bbox = json.loads(active_model.bounding_box_json) if active_model.bounding_box_json else {}
    assembly_center = bbox.get("center", [0.0, 0.0, 0.0])
    exploded_transforms = compute_exploded_transforms(
        components,
        assembly_center=assembly_center,
        intensity=explosion_intensity
    )

    # Main Workspace Layout: 3D Viewport on Left, Hierarchy & Component Info on Right
    view_col, side_col = st.columns([7, 5])

    with view_col:
        st.subheader("3D Interactive Assembly Viewport")

        if "Three.js" in renderer_mode:
            # High-performance Three.js WebGL Renderer
            threejs_html = generate_threejs_mesh_viewer_html(
                model_glb_path=active_model.storage_path,
                components=components,
                exploded_transforms=exploded_transforms,
                explosion_intensity=explosion_intensity,
                selected_component=tree.selected_node,
                isolated_component=tree.isolated_node,
                hidden_components=list(tree.hidden_nodes),
                height=580
            )
            components_v1.html(threejs_html, height=600)
        else:
            # Plotly 3D Wireframe / Bounding Box Renderer
            fig = go.Figure()
            palette = ["#00f0ff", "#a855f7", "#38bdf8", "#f59e0b", "#10b981", "#ec4899", "#8b5cf6"]

            for idx, comp in enumerate(components):
                name = comp["node_name"]
                if name in tree.hidden_nodes:
                    continue

                is_selected = (name == tree.selected_node)
                base_color = palette[idx % len(palette)]
                render_color = "#ffffff" if is_selected else base_color

                disp = exploded_transforms.get(name, {}).get("displacement", [0.0, 0.0, 0.0])
                c_orig = comp.get("center", [0.0, 0.0, 0.0])
                cx, cy, cz = c_orig[0] + disp[0], c_orig[1] + disp[1], c_orig[2] + disp[2]

                ext = comp.get("bounds", {}).get("extents", [0.4, 0.4, 0.4])
                sx = max(0.15, float(ext[0])) / 2.0
                sy = max(0.15, float(ext[1])) / 2.0
                sz = max(0.15, float(ext[2])) / 2.0

                bx = [cx - sx, cx + sx, cx + sx, cx - sx, cx - sx, cx + sx, cx + sx, cx - sx]
                by = [cy - sy, cy - sy, cy + sy, cy + sy, cy - sy, cy - sy, cy + sy, cy + sy]
                bz = [cz - sz, cz - sz, cz - sz, cz - sz, cz + sz, cz + sz, cz + sz, cz + sz]

                fig.add_trace(go.Scatter3d(
                    x=bx, y=by, z=bz,
                    mode='lines+markers',
                    marker=dict(size=4 if not is_selected else 6, color=render_color),
                    line=dict(color=render_color, width=3 if is_selected else 2),
                    name=comp["display_name"],
                    hovertext=f"{comp['display_name']} ({comp['category']})<br>Vertices: {comp['vertex_count']:,}",
                    hoverinfo="text"
                ))

                if explosion_intensity > 0.1:
                    fig.add_trace(go.Scatter3d(
                        x=[c_orig[0], cx],
                        y=[c_orig[1], cy],
                        z=[c_orig[2], cz],
                        mode='lines',
                        line=dict(color='rgba(168, 85, 247, 0.4)', width=1, dash='dot'),
                        showlegend=False,
                        hoverinfo='none'
                    ))

            fig.update_layout(
                paper_bgcolor="#0b0d13",
                plot_bgcolor="#0b0d13",
                height=580,
                margin=dict(l=0, r=0, t=10, b=0),
                scene=dict(
                    xaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    yaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    zaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    camera=dict(eye=dict(x=1.8, y=1.8, z=1.4))
                )
            )
            st.plotly_chart(fig, use_container_width=True)

    with side_col:
        st.subheader("Component Tree & Hierarchy")
        tree_hierarchy = tree.get_tree_hierarchy()

        for group in tree_hierarchy:
            st.markdown(f"**📂 {group['category']}**")
            for item in group["items"]:
                c_name = item["node_name"]
                d_name = item["display_name"]
                is_sel = item["is_selected"]
                is_vis = item["is_visible"]

                row1, row2, row3 = st.columns([6, 3, 3])
                with row1:
                    label = f"✨ **{d_name}**" if is_sel else d_name
                    if st.button(label, key=f"sel_{c_name}", use_container_width=True):
                        tree.select(c_name)
                        st.rerun()

                with row2:
                    eye_icon = "👁️" if is_vis else "🚫"
                    if st.button(eye_icon, key=f"vis_{c_name}"):
                        tree.toggle_visibility(c_name)
                        st.rerun()

                with row3:
                    if st.button("Isolate", key=f"iso_{c_name}"):
                        tree.isolate(c_name)
                        st.rerun()

        # Selected Component Inspector
        st.markdown("---")
        st.subheader("Component Information")
        if tree.selected_node:
            sel_comp = tree.components[tree.selected_node]
            disp = exploded_transforms.get(tree.selected_node, {}).get("displacement", [0, 0, 0])

            st.markdown(f"### {sel_comp['display_name']}")
            st.markdown(f"**Category:** `{sel_comp['category']}`")
            st.markdown(f"**Node Identifier:** `{sel_comp['node_name']}`")

            i1, i2 = st.columns(2)
            i1.metric("Mesh Vertices", f"{sel_comp['vertex_count']:,}")
            i2.metric("Polygon Faces", f"{sel_comp['face_count']:,}")

            st.markdown("**Component Centroid (Assembly Space):**")
            st.code(f"X: {sel_comp['center'][0]:.3f}, Y: {sel_comp['center'][1]:.3f}, Z: {sel_comp['center'][2]:.3f}")

            st.markdown(f"**Exploded Offset (Intensity {int(explosion_intensity * 100)}%):**")
            st.code(f"ΔX: {disp[0]:+.3f}, ΔY: {disp[1]:+.3f}, ΔZ: {disp[2]:+.3f}")

            if st.button("Restore All Components", use_container_width=True):
                tree.restore_all()
                st.rerun()
        else:
            st.info("Click any component from the hierarchy above to inspect its metrics.")
