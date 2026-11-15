"""
NOVA 3D - User Manual & Technical Documentation View
"""
import streamlit as st

def render_documentation():
    st.markdown('<div class="nova-logo-badge">SYSTEM MANUAL</div>', unsafe_allow_html=True)
    st.title("NOVA 3D Documentation")
    st.markdown("Comprehensive technical blueprint, capture protocols, and interaction guide.")

    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Quick Start", "📹 Capture Protocol", "🖐️ Gesture Manual", "⚙️ Architecture"])

    with tab1:
        st.markdown("""
        ### Getting Started with NOVA 3D
        1. **Create a Project:** Choose **Environment Reconstruction** for real-world spaces or **Machine Exploration** for CAD models.
        2. **Upload or Sample Video:** Ingest an MP4/MOV capture or use the built-in `sample_walkthrough.mp4`.
        3. **Start Reconstruction:** Run frame extraction, Structure from Motion, and Gaussian Splatting synthesis.
        4. **Interactive 3D Viewer:** Orbit, pan, and zoom through the reconstructed scene.
        5. **Machine Explorer:** Upload a GLB model or load the built-in Engine Assembly, isolate components, and explode the assembly.
        """)

    with tab2:
        st.markdown("""
        ### Video Capture Guidelines for Photogrammetry & Splatting
        - **Speed:** Walk or move the camera slowly to avoid motion blur.
        - **Overlap:** Ensure 70% to 80% visual overlap between adjacent viewpoints.
        - **Subject Matter:** Reconstructing textured, non-reflective, non-transparent surfaces yields the best point geometry.
        - **Lighting:** Maintain consistent diffuse lighting; avoid moving shadows.
        """)

    with tab3:
        st.markdown("""
        ### 9 Supported Hand Gestures
        1. **Open Palm:** Pause / neutralize interaction.
        2. **Index Finger Pointing:** Hover or aim at a component.
        3. **Pinch:** Select or grab a focused part.
        4. **Horizontal Hand Movement:** Rotate camera orbit.
        5. **Vertical Hand Movement:** Adjust camera elevation.
        6. **Two-Hand Spread:** Zoom in closer.
        7. **Two-Hand Contraction:** Zoom out.
        8. **Closed Fist:** Release selection / pause.
        9. **Swipe:** Cycle to the next component.
        """)

    with tab4:
        st.markdown("""
        ### Python-First Architecture
        - **Backend & REST API:** FastAPI with interactive OpenAPI docs (`/docs`).
        - **Data Layer:** SQLite with SQLAlchemy ORM.
        - **Computer Vision:** OpenCV for frame sampling, blur detection, and triangulation.
        - **Structure from Motion:** COLMAP subprocess integration with OpenCV SfM fallback.
        - **Gaussian Splatting:** Splatfacto / Nerfstudio stack with resource-aware primitive generation.
        - **3D Machine Engine:** Trimesh and pygltflib for GLB/GLTF hierarchy parsing and vector explosions.
        - **Gesture Recognition:** MediaPipe 21-landmark tracking with temporal smoothing and cooldowns.
        """)
