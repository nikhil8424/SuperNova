"""
NOVA 3D - Hand Gesture Recognition Studio View
Enables opt-in webcam tracking, visualizes 21-landmark skeletal HUD,
detects 9 interaction gestures, and maps them to 3D viewer actions.
"""
import time
import streamlit as st
import numpy as np
import cv2
from PIL import Image

from app.gestures.hand_tracker import HandTracker
from app.gestures.gesture_mapper import DEFAULT_ACTION_MAP, map_gesture_to_action
from app.core.logging import logger

def render_gesture_studio():
    st.markdown('<div class="nova-logo-badge">COMPUTER VISION INTERACTION</div>', unsafe_allow_html=True)
    st.title("Gesture Studio & Landmark Tracking")
    st.markdown("Interact naturally with 3D scenes and machine components using camera-based hand landmark tracking.")

    # Privacy & Opt-in Notice
    st.info("🔒 **Privacy Guarantee:** Webcam tracking is processed 100% locally on your machine. Footage is never recorded, transmitted, or stored.")

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
            - ↕️ **Vertical Movement:** Adjust elevation / pan.
            - 👐 **Two-Hand Spread:** Zoom in closer.
            """)
        with g_c3:
            st.markdown("""
            - 🤲 **Two-Hand Contraction:** Zoom out.
            - ✊ **Closed Fist:** Release selection / pause.
            - 💨 **Swipe:** Cycle next part or viewpoint.
            """)

    st.markdown("---")

    cam_col, hud_col = st.columns([7, 5])

    if enable_camera:
        with cam_col:
            st.subheader("Live Tracking HUD")
            # Streamlit camera input
            camera_image = st.camera_input("Optical Sensor Input", key="gesture_cam_feed")

            if camera_image is not None:
                # Convert PIL image to BGR numpy array
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

                with hud_col:
                    st.subheader("Gesture Telemetry")
                    if results["hand_detected"]:
                        st.markdown(f"""
                        <div class="nova-card" style="border-color: #00f0ff;">
                            <div style="font-size: 0.8rem; color: #94a3b8;">DETECTED GESTURE</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #00f0ff;">
                                {results['smoothed_gesture']}
                            </div>
                            <div style="font-size: 0.9rem; color: #a855f7; margin-top: 4px;">
                                Action: <strong>{results['action']['action']}</strong> ({results['action']['target']})
                            </div>
                            <div style="margin-top: 8px;">Confidence: <strong>{int(results['confidence'] * 100)}%</strong></div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="nova-card">
                            <div style="color: #94a3b8;">No hand detected in camera frame. Position your hand inside the frame.</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("**Viewer Action Mappings:**")
                    st.json(DEFAULT_ACTION_MAP)
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
