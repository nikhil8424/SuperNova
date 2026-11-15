"""
Unit tests for Machine Model Inspection & Exploded View Transforms
"""
from app.machine.model_loader import inspect_3d_model
from app.machine.component_tree import ComponentTree
from app.machine.exploded_view import compute_exploded_transforms

def test_inspect_3d_model(synthetic_glb):
    info = inspect_3d_model(synthetic_glb)
    assert info["format"] == "glb"
    assert info["component_count"] == 2
    assert info["total_vertices"] > 0
    assert info["total_faces"] > 0

    node_names = [c["node_name"] for c in info["components"]]
    assert "Housing" in node_names
    assert "Piston" in node_names

def test_component_tree(synthetic_glb):
    info = inspect_3d_model(synthetic_glb)
    tree = ComponentTree(info["components"])

    assert len(tree.get_visible_components()) == 2

    # Test Selection
    tree.select("Housing")
    assert tree.selected_node == "Housing"

    # Test Isolation
    tree.isolate("Piston")
    assert tree.isolated_node == "Piston"
    assert "Housing" in tree.hidden_nodes
    assert len(tree.get_visible_components()) == 1

    # Test Restore
    tree.restore_all()
    assert tree.isolated_node is None
    assert len(tree.get_visible_components()) == 2

def test_exploded_transforms(synthetic_glb):
    info = inspect_3d_model(synthetic_glb)
    assembly_center = info["bounding_box"]["center"]

    # At 0.0 intensity, displacement is 0
    t0 = compute_exploded_transforms(info["components"], assembly_center, intensity=0.0)
    for name, data in t0.items():
        assert data["displacement"] == [0.0, 0.0, 0.0]

    # At 1.0 intensity, components move apart
    t1 = compute_exploded_transforms(info["components"], assembly_center, intensity=1.0)
    for name, data in t1.items():
        assert len(data["displacement"]) == 3
        assert len(data["direction_vector"]) == 3
