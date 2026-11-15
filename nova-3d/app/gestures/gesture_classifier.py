"""
NOVA 3D - Hand Gesture Classifier
Implements classification for the 9 specified gesture interactions using
21 hand landmark 3D positions, Euclidean distances, and geometric angles.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Landmark indices defined by standard MediaPipe hand model
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4

INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8

MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12

RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16

PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

def dist_3d(p1, p2) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def is_finger_extended(landmarks: List[List[float]], tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
    """A finger is extended if tip is farther from wrist than PIP and MCP."""
    wrist = landmarks[WRIST]
    tip_dist = dist_3d(landmarks[tip_idx], wrist)
    pip_dist = dist_3d(landmarks[pip_idx], wrist)
    mcp_dist = dist_3d(landmarks[mcp_idx], wrist)
    return tip_dist > pip_dist and pip_dist > mcp_dist

def classify_single_hand_gesture(
    landmarks: List[List[float]],
    prev_wrist: Optional[List[float]] = None
) -> Tuple[str, float]:
    """
    Classifies single-hand gestures:
    - Open Palm (neutral/pause)
    - Closed Fist (pause/release)
    - Pinch (select/grab)
    - Index Finger Pointing (point/hover)
    - Horizontal Movement (rotate)
    - Vertical Movement (elevate)
    - Swipe (switch view)
    Returns: (gesture_name, confidence)
    """
    if len(landmarks) < 21:
        return "Unknown", 0.0

    # Finger extension states
    index_ext = is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
    middle_ext = is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    ring_ext = is_finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP)
    pinky_ext = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)

    # Pinch detection: distance between thumb tip and index tip relative to hand scale
    wrist = landmarks[WRIST]
    middle_mcp = landmarks[MIDDLE_MCP]
    hand_scale = max(0.01, dist_3d(wrist, middle_mcp))

    pinch_dist = dist_3d(landmarks[THUMB_TIP], landmarks[INDEX_TIP]) / hand_scale
    is_pinch = pinch_dist < 0.35

    # Movement deltas if previous wrist position is known
    delta_x, delta_y = 0.0, 0.0
    if prev_wrist is not None:
        delta_x = (landmarks[WRIST][0] - prev_wrist[0]) / hand_scale
        delta_y = (landmarks[WRIST][1] - prev_wrist[1]) / hand_scale

    # Classification rules:
    # 1. Closed Fist: all fingers retracted
    if not index_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "Closed Fist", 0.92

    # 2. Pinch: thumb and index tips touching
    if is_pinch:
        conf = max(0.6, 1.0 - (pinch_dist * 1.5))
        return "Pinch", round(conf, 2)

    # 3. Index Finger Pointing: only index finger extended
    if index_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "Index Finger Pointing", 0.88

    # 4. Swipe: fast horizontal motion with open or relaxed hand
    if abs(delta_x) > 0.45 and abs(delta_x) > 2.0 * abs(delta_y):
        return "Swipe", 0.85

    # 5. Horizontal Hand Movement: steady horizontal drift
    if abs(delta_x) > 0.18 and abs(delta_x) > 1.5 * abs(delta_y):
        return "Horizontal Hand Movement", 0.80

    # 6. Vertical Hand Movement: steady vertical drift
    if abs(delta_y) > 0.18 and abs(delta_y) > 1.5 * abs(delta_x):
        return "Vertical Hand Movement", 0.80

    # 7. Open Palm: all fingers extended
    if index_ext and middle_ext and ring_ext and pinky_ext:
        return "Open Palm", 0.95

    return "Neutral", 0.50

def classify_two_hand_gesture(
    hand1_landmarks: List[List[float]],
    hand2_landmarks: List[List[float]],
    prev_distance: Optional[float] = None
) -> Tuple[str, float]:
    """
    Classifies two-hand gestures:
    - Two-hand spread (Zoom in)
    - Two-hand contraction (Zoom out)
    """
    if len(hand1_landmarks) < 21 or len(hand2_landmarks) < 21:
        return "Neutral", 0.0

    w1 = hand1_landmarks[WRIST]
    w2 = hand2_landmarks[WRIST]
    current_dist = dist_3d(w1, w2)

    if prev_distance is not None:
        delta = current_dist - prev_distance
        if delta > 0.05:
            return "Two-Hand Spread (Zoom In)", 0.85
        elif delta < -0.05:
            return "Two-Hand Contraction (Zoom Out)", 0.85

    return "Two Hands Active", 0.70
