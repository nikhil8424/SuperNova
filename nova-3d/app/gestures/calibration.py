"""
NOVA 3D - Gesture Calibration & Temporal Smoothing
Maintains a rolling buffer of gesture classifications, suppresses noise,
and enforces cooldown timers to eliminate false activations.
"""
import time
from collections import deque
from typing import Optional, Tuple, Dict, Any

from app.config import (
    GESTURE_CONFIDENCE_THRESHOLD,
    GESTURE_COOLDOWN_SECONDS,
    GESTURE_SMOOTHING_WINDOW
)

class GestureSmoothingEngine:
    def __init__(
        self,
        window_size: int = GESTURE_SMOOTHING_WINDOW,
        min_confidence: float = GESTURE_CONFIDENCE_THRESHOLD,
        cooldown_sec: float = GESTURE_COOLDOWN_SECONDS
    ):
        self.window_size = window_size
        self.min_confidence = min_confidence
        self.cooldown_sec = cooldown_sec

        self.history = deque(maxlen=window_size)
        self.last_triggered_gesture: Optional[str] = None
        self.last_trigger_time: float = 0.0

    def update(self, detected_gesture: str, confidence: float) -> Tuple[Optional[str], float, bool]:
        """
        Updates buffer with current frame detection.
        Returns (smoothed_gesture, mean_confidence, did_trigger_action).
        """
        now = time.time()
        self.history.append((detected_gesture, confidence))

        if len(self.history) < max(2, self.window_size // 2):
            return None, 0.0, False

        # Count frequencies
        counts: Dict[str, int] = {}
        conf_sums: Dict[str, float] = {}
        for g, c in self.history:
            counts[g] = counts.get(g, 0) + 1
            conf_sums[g] = conf_sums.get(g, 0.0) + c

        # Find majority gesture
        majority_gesture, majority_count = max(counts.items(), key=lambda item: item[1])
        avg_conf = conf_sums[majority_gesture] / max(1, majority_count)

        # Check threshold
        if majority_count < (len(self.history) * 0.55) or avg_conf < self.min_confidence:
            return "Neutral", avg_conf, False

        # Neutral gestures don't trigger discrete actions
        if majority_gesture in ("Neutral", "Unknown"):
            return majority_gesture, avg_conf, False

        # Enforce cooldown for discrete events
        is_discrete = majority_gesture in ("Pinch", "Swipe", "Closed Fist")
        did_trigger = False

        if is_discrete:
            if (now - self.last_trigger_time) > self.cooldown_sec:
                self.last_triggered_gesture = majority_gesture
                self.last_trigger_time = now
                did_trigger = True
        else:
            # Continuous gestures (like rotate, zoom) trigger continuously
            did_trigger = True

        return majority_gesture, round(avg_conf, 2), did_trigger
