"""
NOVA 3D - Hand Gesture Recognition Studio View
Enables opt-in webcam tracking, visualizes 21-landmark skeletal HUD,
detects 9 interaction gestures, and maps them to real-time 3D viewport actions.
"""
import time
import streamlit as st
import numpy as np
import cv2
from PIL import Image
import plotly.graph_objects as go

from app.gestures.hand_tracker import HandTracker
from app.gestures.gesture_mapper import DEFAULT_ACTION_MAP, map_gesture_to_action
from app.core.logging import logger

def render_gesture_studio():
    st.markdown('<div class="nova-logo-badge">COMPUTER VISION INTERACTION</div>', unsafe_allow_html=True)
    st.title("Gesture Studio & Landmark Tracking")
    st.markdown("Interact naturally with 3D scenes and machine components using camera-based hand landmark tracking.")

    # Privacy & Opt-in Notice
    st.info("🔒 **Privacy Guarantee:** Webcam tracking is processed 100% locally on your machine. Footage is never recorded, transmitted, or stored.")

    # Session State for Gesture-Driven 3D Canvas
    if "gesture_cam_rot_x" not in st.session_state:
        st.session_state["gesture_cam_rot_x"] = 1.6
    if "gesture_cam_rot_y" not in st.session_state:
        st.session_state["gesture_cam_rot_y"] = 1.6
    if "gesture_cam_zoom" not in st.session_state:
        st.session_state["gesture_cam_zoom"] = 1.8
    if "gesture_selected_part" not in st.session_state:
        st.session_state["gesture_selected_part"] = "None"

    # Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    with ctrl_col1:
        enable_camera = st.toggle("📷 Enable Webcam Tracking", value=False, help="Activates local camera feed and landmark inference.")
    with ctrl_col2:
        conf_threshold = st.slider("Min Confidence Threshold", min_value=0.4, max_value=0.95, value=0.65, step=0.05)
    with ctrl_col3:
        smoothing_window = st.select_slider("Temporal Smoothing Window", options=[1, 3, 5, 7, 9], value=5)

    # 9 Supported Gestures Legend
    with st.expander("🖐️ Supported Gesture Interaction Legend (9 Gestures)", expanded=True):
        g_c1, g_c2, g_c3 = st.columns(3)
        with g_c1:
            st.markdown("""
            - ✋ **Open Palm:** Pause / neutralize interaction.
            - ☝️ **Index Pointing:** Hover / focus 3D part.
            - 🤏 **Pinch:** Select / grab component.
            """)
        with g_c2:
            st.markdown("""
            - ↔️ **Horizontal Movement:** Rotate camera orbit.
            - ↕️ **Vertical Movement:** Adjust camera elevation.
            - 👐 **Two-Hand Spread:** Zoom in closer.
            """)
        with g_c3:
            st.markdown("""
            - 🤲 **Two-Hand Contraction:** Zoom out.
            - ✊ **Closed Fist:** Release selection / pause.
            - 💨 **Swipe:** Cycle next part or viewpoint.
            """)

    st.markdown("---")

    cam_col, hud_col = st.columns([6, 6])

    latest_gesture = "Neutral"
    latest_conf = 0.0
    latest_action = map_gesture_to_action("Neutral")

    if enable_camera:
        with cam_col:
            st.subheader("Live Optical HUD Feed")
            camera_image = st.camera_input("Optical Sensor Stream", key="gesture_cam_feed")

            if camera_image is not None:
                img_pil = Image.open(camera_image)
                frame_rgb = np.array(img_pil)
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

                tracker = HandTracker(
                    min_detection_confidence=conf_threshold,
                    min_tracking_confidence=0.55
                )
                annotated_bgr, results = tracker.process_frame(frame_bgr)
                annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

                st.image(annotated_rgb, caption="Processed HUD with 21 Landmark Keypoints", use_container_width=True)

                if results["hand_detected"]:
                    latest_gesture = results['smoothed_gesture']
                    latest_conf = results['confidence']
                    latest_action = results['action']

                    # Map gesture actions to 3D canvas session states
                    if latest_gesture == "Horizontal Hand Movement":
                        st.session_state["gesture_cam_rot_x"] += 0.25
                    elif latest_gesture == "Vertical Hand Movement":
                        st.session_state["gesture_cam_rot_y"] += 0.20
                    elif "Zoom In" in latest_gesture:
                        st.session_state["gesture_cam_zoom"] = max(0.8, st.session_state["gesture_cam_zoom"] - 0.2)
                    elif "Zoom Out" in latest_gesture:
                        st.session_state["gesture_cam_zoom"] = min(3.5, st.session_state["gesture_cam_zoom"] + 0.2)
                    elif latest_gesture == "Pinch":
                        st.session_state["gesture_selected_part"] = "Target Core Assembly"
                    elif latest_gesture == "Closed Fist":
                        st.session_state["gesture_selected_part"] = "None"
        with hud_col:
            st.subheader("Gesture Telemetry & Live 3D Target")

            if latest_gesture != "Neutral":
                st.markdown(f"""
                <div class="nova-card" style="border-color: #00f0ff;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">ACTIVE GESTURE DETECTED</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #00f0ff;">
                        {latest_gesture.upper()}
                    </div>
                    <div style="font-size: 0.95rem; color: #a855f7; margin-top: 4px;">
                        Triggered Action: <strong>{latest_action['action']}</strong> ({latest_action['target']})
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem;">Confidence: <strong>{int(latest_conf * 100)}%</strong></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="nova-card">
                    <div style="color: #94a3b8;">Ready for gesture input. Show your hand to the sensor.</div>
                </div>
                """, unsafe_allow_html=True)

            # Interactive 3D Gesture Target Mesh Canvas
            fig = go.Figure()
            # Render a 3D target calibration geometry
            t = np.linspace(0, 2*np.pi, 30)
            u = np.linspace(0, np.pi, 15)
            x = 1.0 * np.outer(np.cos(t), np.sin(u))
            y = 1.0 * np.outer(np.sin(t), np.sin(u))
            z = 1.0 * np.outer(np.ones(np.size(t)), np.cos(u))

            is_part_selected = st.session_state["gesture_selected_part"] != "None"
            mesh_color = "#ffffff" if is_part_selected else "#00f0ff"

            fig.add_trace(go.Surface(
                x=x, y=y, z=z,
                colorscale=[[0, '#00f0ff'], [0.5, '#a855f7'], [1, '#38bdf8']],
                showscale=False,
                opacity=0.85
            ))

            cam_eye = dict(
                x=float(st.session_state["gesture_cam_zoom"] * np.cos(st.session_state["gesture_cam_rot_x"])),
                y=float(st.session_state["gesture_cam_zoom"] * np.sin(st.session_state["gesture_cam_rot_x"])),
                z=float(st.session_state["gesture_cam_rot_y"])
            )

            fig.update_layout(
                paper_bgcolor="#0b0d13",
                plot_bgcolor="#0b0d13",
                margin=dict(l=0, r=0, t=10, b=0),
                height=340,
                scene=dict(
                    xaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    yaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    zaxis=dict(backgroundcolor="#12151f", gridcolor="#262c40", showbackground=True),
                    camera=dict(eye=cam_eye)
                )
            )
            st.plotly_chart(fig, use_container_width=True)

            btn_r1, btn_r2 = st.columns(2)
            with btn_r1:
                if st.button("Reset 3D Canvas"):
                    st.session_state["gesture_cam_rot_x"] = 1.6
                    st.session_state["gesture_cam_rot_y"] = 1.6
                    st.session_state["gesture_cam_zoom"] = 1.8
                    st.session_state["gesture_selected_part"] = "None"
                    st.rerun()
            with btn_r2:
                st.caption(f"Part Status: **{st.session_state['gesture_selected_part']}**")
    else:
        with cam_col:
            st.subheader("Optical Sensor Status")
            st.info("Webcam input is currently OFF. Toggle 'Enable Webcam Tracking' above to start real-time tracking.")
            st.markdown("""
            **Alternative Controls Always Available:**
            - **Orbit:** Left-click and drag in 3D Viewport.
            - **Pan:** Right-click and drag.
            - **Zoom:** Mouse scroll wheel.
            - **Select Component:** Click component name in hierarchy or interactive tree.
            - **Explode:** Use the exploded-view slider in Machine Explorer.
            """)

        with hud_col:
            st.subheader("Sensor Configurations")
            st.markdown(f"**Confidence Threshold:** `{conf_threshold}`")
            st.markdown(f"**Smoothing Window:** `{smoothing_window} frames`")
            st.markdown(f"**Webcam Mode:** `Opt-in (Local Processing Only)`")
            st.markdown("**Action Mappings:**")
            st.json(DEFAULT_ACTION_MAP)
