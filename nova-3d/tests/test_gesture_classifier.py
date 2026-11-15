"""
Unit tests for Gesture Classification & Action Mapping
"""
from app.gestures.gesture_classifier import (
    classify_single_hand_gesture,
    classify_two_hand_gesture
)
from app.gestures.calibration import GestureSmoothingEngine
from app.gestures.gesture_mapper import map_gesture_to_action

def create_synthetic_landmarks(fingers_extended=[True, True, True, True, True]):
    """
    Synthesizes 21 landmarks based on finger extension booleans:
    [Thumb, Index, Middle, Ring, Pinky]
    """
    lms = []
    # Wrist
    lms.append([0.5, 0.9, 0.0])

    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]
    mcps = [2, 5, 9, 13, 17]

    for i in range(1, 21):
        # Default placeholder
        lms.append([0.5, 0.5, 0.0])

    # Assign MCP, PIP, TIP positions based on extension state
    for f_idx, is_ext in enumerate(fingers_extended[1:], start=1):
        tip_i = tips[f_idx]
        pip_i = pips[f_idx]
        mcp_i = mcps[f_idx]

        mcp_y = 0.6
        if is_ext:
            pip_y = 0.4
            tip_y = 0.2 # Farther from wrist (extended upward)
        else:
            pip_y = 0.7
            tip_y = 0.8 # Folded into palm (close to wrist)

        lms[mcp_i] = [0.2 * f_idx, mcp_y, 0.0]
        lms[pip_i] = [0.2 * f_idx, pip_y, 0.0]
        lms[tip_i] = [0.2 * f_idx, tip_y, 0.0]

    # Thumb
    lms[1] = [0.4, 0.8, 0.0]
    lms[2] = [0.35, 0.7, 0.0]
    lms[3] = [0.3, 0.6, 0.0]
    lms[4] = [0.25, 0.5, 0.0]

    return lms

def test_open_palm_classification():
    open_lms = create_synthetic_landmarks([True, True, True, True, True])
    gesture, conf = classify_single_hand_gesture(open_lms)
    assert gesture == "Open Palm"
    assert conf >= 0.85

def test_closed_fist_classification():
    fist_lms = create_synthetic_landmarks([False, False, False, False, False])
    gesture, conf = classify_single_hand_gesture(fist_lms)
    assert gesture == "Closed Fist"
    assert conf >= 0.85

def test_index_pointing_classification():
    # Only index extended
    point_lms = create_synthetic_landmarks([False, True, False, False, False])
    gesture, conf = classify_single_hand_gesture(point_lms)
    assert gesture == "Index Finger Pointing"

def test_pinch_classification():
    pinch_lms = create_synthetic_landmarks([True, True, False, False, False])
    # Place thumb tip and index tip right next to each other
    pinch_lms[4] = [0.3, 0.3, 0.0]
    pinch_lms[8] = [0.31, 0.31, 0.0]

    gesture, conf = classify_single_hand_gesture(pinch_lms)
    assert gesture == "Pinch"

def test_smoothing_and_cooldown():
    engine = GestureSmoothingEngine(window_size=3, min_confidence=0.6, cooldown_sec=0.2)

    # First update
    g, c, trig = engine.update("Pinch", 0.9)
    # Consecutive updates
    g, c, trig = engine.update("Pinch", 0.9)
    g, c, trig = engine.update("Pinch", 0.9)
    assert g == "Pinch"

def test_map_gesture_to_action():
    act = map_gesture_to_action("Open Palm")
    assert act["action"] == "PAUSE_NEUTRALIZE"

    act_pinch = map_gesture_to_action("Pinch")
    assert act_pinch["action"] == "SELECT_GRAB"
