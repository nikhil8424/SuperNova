"""
NOVA 3D - Gesture Action Mapper
Translates classified gestures into standard 3D viewer commands.
"""
from typing import Dict, Any, Optional

DEFAULT_ACTION_MAP = {
    "Open Palm": {
        "action": "PAUSE_NEUTRALIZE",
        "description": "Pause / neutralize interaction",
        "target": "viewer"
    },
    "Index Finger Pointing": {
        "action": "HOVER_POINT",
        "description": "Hover over / target component",
        "target": "raycaster"
    },
    "Pinch": {
        "action": "SELECT_GRAB",
        "description": "Select or grab focused component",
        "target": "component"
    },
    "Horizontal Hand Movement": {
        "action": "ROTATE_CAMERA",
        "description": "Orbit camera horizontally",
        "target": "camera"
    },
    "Vertical Hand Movement": {
        "action": "ELEVATE_CAMERA",
        "description": "Pan camera vertically",
        "target": "camera"
    },
    "Two-Hand Spread (Zoom In)": {
        "action": "ZOOM_IN",
        "description": "Zoom closer into scene",
        "target": "camera"
    },
    "Two-Hand Contraction (Zoom Out)": {
        "action": "ZOOM_OUT",
        "description": "Zoom back out of scene",
        "target": "camera"
    },
    "Closed Fist": {
        "action": "RELEASE_PAUSE",
        "description": "Release selection / pause input",
        "target": "viewer"
    },
    "Swipe": {
        "action": "NEXT_COMPONENT",
        "description": "Cycle to next part or viewpoint",
        "target": "navigation"
    }
}

def map_gesture_to_action(
    gesture_name: str,
    custom_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Retrieves action definition for given gesture."""
    active_map = custom_map or DEFAULT_ACTION_MAP
    return active_map.get(
        gesture_name,
        {
            "action": "NO_OP",
            "description": "No active mapping for this gesture",
            "target": "none"
        }
    )
