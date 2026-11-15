"""
NOVA 3D - Component Tree & Selection Management
Manages component hierarchy, isolation, selection, and visibility states.
"""
from typing import Dict, Any, List, Optional, Set

class ComponentTree:
    def __init__(self, components: List[Dict[str, Any]]):
        self.components = {c["node_name"]: dict(c) for c in components}
        self.selected_node: Optional[str] = None
        self.isolated_node: Optional[str] = None
        self.hidden_nodes: Set[str] = set()

    def select(self, node_name: Optional[str]):
        """Selects a component for detailed inspection."""
        self.selected_node = node_name if node_name in self.components else None

    def isolate(self, node_name: str):
        """Hides all components except the isolated component."""
        if node_name in self.components:
            self.isolated_node = node_name
            self.hidden_nodes = {k for k in self.components.keys() if k != node_name}

    def restore_all(self):
        """Restores visibility of all components and clears isolation."""
        self.isolated_node = None
        self.hidden_nodes.clear()

    def toggle_visibility(self, node_name: str):
        """Toggles visibility of a specific component."""
        if node_name in self.hidden_nodes:
            self.hidden_nodes.remove(node_name)
        else:
            self.hidden_nodes.add(node_name)

    def get_visible_components(self) -> List[Dict[str, Any]]:
        """Returns list of all currently visible components."""
        return [
            c for name, c in self.components.items()
            if name not in self.hidden_nodes
        ]

    def get_tree_hierarchy(self) -> List[Dict[str, Any]]:
        """Returns components structured by category and selection state."""
        categories = {}
        for name, comp in self.components.items():
            cat = comp.get("category", "Uncategorized")
            if cat not in categories:
                categories[cat] = []
            comp_copy = dict(comp)
            comp_copy["is_selected"] = (name == self.selected_node)
            comp_copy["is_visible"] = (name not in self.hidden_nodes)
            comp_copy["is_isolated"] = (name == self.isolated_node)
            categories[cat].append(comp_copy)

        return [{"category": cat, "items": items} for cat, items in categories.items()]
