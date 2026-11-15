"""
NOVA 3D - Exploded View Transformation Engine
Computes component directional separation vectors and offset transforms
based on assembly center of mass, enabling animated explosion and exact restoration.
"""
from typing import Dict, Any, List
import numpy as np
import trimesh

def compute_exploded_transforms(
    components: List[Dict[str, Any]],
    assembly_center: List[float],
    intensity: float = 1.0,
    axis_weights: List[float] = [1.0, 1.0, 1.0]
) -> Dict[str, Dict[str, Any]]:
    """
    Computes spatial translation offsets for each component.
    Direction vector points outward from assembly center towards component centroid.
    Preserves original rest transforms when intensity is 0.0.
    """
    center_arr = np.array(assembly_center, dtype=np.float64)
    weights = np.array(axis_weights, dtype=np.float64)
    results = {}

    for comp in components:
        node_name = comp["node_name"]
        comp_center = np.array(comp.get("center", [0.0, 0.0, 0.0]), dtype=np.float64)

        # Direction vector from model center to part center
        direction = comp_center - center_arr
        distance = np.linalg.norm(direction)

        if distance < 1e-4:
            # Fallback direction along Z or X if exactly at center
            direction = np.array([0.0, 0.0, 1.0])
        else:
            direction = direction / distance

        # Apply weights and intensity
        displacement = direction * weights * (distance * 0.8 + 0.5) * intensity

        # Transform matrix (4x4)
        transform_mat = np.eye(4, dtype=np.float64)
        transform_mat[:3, 3] = displacement

        results[node_name] = {
            "displacement": [round(float(d), 4) for d in displacement],
            "direction_vector": [round(float(v), 4) for v in direction],
            "transform_matrix": transform_mat.tolist()
        }

    return results

def apply_explosion_to_scene(
    scene: trimesh.Scene,
    intensity: float = 1.0
) -> trimesh.Scene:
    """
    Creates a new trimesh Scene with transformed geometries displaced along exploded vectors.
    """
    exploded = scene.copy()
    if intensity <= 0.001:
        return exploded

    centroid = scene.centroid
    for name, geom in exploded.geometry.items():
        if not isinstance(geom, trimesh.Trimesh):
            continue
        c = geom.centroid
        direction = c - centroid
        norm = np.linalg.norm(direction)
        if norm > 1e-4:
            direction = direction / norm
        else:
            direction = np.array([0.0, 0.0, 1.0])

        offset = direction * (norm * 0.75 + 0.4) * intensity
        geom.apply_translation(offset)

    return exploded
