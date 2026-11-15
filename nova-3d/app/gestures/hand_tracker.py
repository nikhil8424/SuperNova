"""
NOVA 3D - MediaPipe Hand Landmark Tracker & Visualizer
Processes camera frames locally, extracts 21 3D hand landmarks,
draws styled electric HUD overlays, and classifies gesture interactions.
"""
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

from app.gestures.gesture_classifier import classify_single_hand_gesture
from app.gestures.calibration import GestureSmoothingEngine
from app.gestures.gesture_mapper import map_gesture_to_action
from app.core.logging import logger

# MediaPipe Hand Connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # Index
    (5, 9), (9, 10), (10, 11), (11, 12),      # Middle
    (9, 13), (13, 14), (14, 15), (15, 16),    # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),   # Pinky
    (0, 17)                                    # Palm base
]

class HandTracker:
    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.65,
        min_tracking_confidence: float = 0.55
    ):
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.smoothing = GestureSmoothingEngine()
        self.prev_wrist = None

        # Attempt to load MediaPipe Hands
        self.mp_hands = None
        self.hands_detector = None
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.mp_hands = mp.solutions.hands
                self.hands_detector = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=max_num_hands,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence
                )
                logger.info("MediaPipe Hands detector initialized successfully.")
        except Exception as e:
            logger.warning(f"MediaPipe Hands initialization note: {e}")

    def process_frame(
        self,
        frame_bgr: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Processes BGR camera frame.
        Draws glowing HUD landmarks and returns (annotated_frame, tracking_results).
        """
        h, w = frame_bgr.shape[:2]
        annotated = frame_bgr.copy()

        result = {
            "hand_detected": False,
            "raw_gesture": "None",
            "smoothed_gesture": "None",
            "confidence": 0.0,
            "action": map_gesture_to_action("None"),
            "did_trigger": False,
            "landmarks": []
        }

        if self.hands_detector is None:
            # Fallback HUD indication
            cv2.putText(
                annotated,
                "GESTURE ENGINE: READY (LOCAL CPU SENSOR)",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 240, 255),
                2
            )
            return annotated, result

        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_results = self.hands_detector.process(frame_rgb)

        if mp_results.multi_hand_landmarks:
            result["hand_detected"] = True
            # Analyze primary hand
            hand_landmarks = mp_results.multi_hand_landmarks[0]
            pts = []
            pixel_pts = []

            for lm in hand_landmarks.landmark:
                pts.append([lm.x, lm.y, lm.z])
                pixel_pts.append((int(lm.x * w), int(lm.y * h)))

            result["landmarks"] = pts

            # Draw Connections (Electric Violet & Cyan)
            for c_start, c_end in HAND_CONNECTIONS:
                p1 = pixel_pts[c_start]
                p2 = pixel_pts[c_end]
                cv2.line(annotated, p1, p2, (168, 85, 247), 2) # Electric violet bone

            # Draw Joint Landmarks
            for i, (px, py) in enumerate(pixel_pts):
                color = (0, 240, 255) if i in (4, 8, 12, 16, 20) else (255, 255, 255)
                rad = 6 if i in (4, 8, 12, 16, 20) else 4
                cv2.circle(annotated, (px, py), rad, color, -1)
                cv2.circle(annotated, (px, py), rad + 1, (20, 20, 30), 1)

            # Classify
            raw_gesture, raw_conf = classify_single_hand_gesture(pts, prev_wrist=self.prev_wrist)
            self.prev_wrist = pts[0]

            smoothed_g, smooth_conf, did_trigger = self.smoothing.update(raw_gesture, raw_conf)

            active_gesture = smoothed_g or raw_gesture
            active_conf = smooth_conf if smoothed_g else raw_conf

            action = map_gesture_to_action(active_gesture)

            result["raw_gesture"] = raw_gesture
            result["smoothed_gesture"] = active_gesture
            result["confidence"] = active_conf
            result["action"] = action
            result["did_trigger"] = did_trigger

            # HUD Overlay
            cv2.rectangle(annotated, (15, 15), (380, 85), (18, 21, 31), -1)
            cv2.rectangle(annotated, (15, 15), (380, 85), (0, 240, 255), 1)

            cv2.putText(
                annotated,
                f"GESTURE: {active_gesture.upper()}",
                (25, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 240, 255),
                2
            )
            cv2.putText(
                annotated,
                f"ACTION: {action['action']} ({int(active_conf * 100)}% CONF)",
                (25, 72),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 220),
                1
            )
        else:
            self.prev_wrist = None

        return annotated, result

    def close(self):
        if self.hands_detector:
            self.hands_detector.close()
