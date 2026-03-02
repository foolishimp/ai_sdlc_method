# Implements: REQ-GRAPH-002, REQ-UX-003
from pathlib import Path
from gemini_cli.engine.topology import GraphTopology

class ZoomCommand:
    """Zoom into a sub-graph for a specific edge (REQ-GRAPH-002)."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.topology = GraphTopology(workspace_root)

    def run(self, edge: str):
        print(f"\n[ZOOM] Zooming into edge: {edge}")
        print("="*40)
        
        # In a real implementation, this would look for a sub-graph definition for the edge.
        # For now, we will display any sub-edges we find in the topology that relate to this edge.
        
        # Example: 'design->code' zooms into 'module_decomp', 'basis_proj', 'code'
        zoom_map = {
            "design\u2192code": ["module_decomp\u2192basis_proj", "basis_proj\u2192code"],
            "requirements\u2192design": ["feature_decomp\u2192design"],
            "requirements": ["intent\u2192requirements", "requirements\u2192feature_decomp"]
        }
        
        normalized_edge = edge.replace("->", "\u2192").replace("\u2194", "\u2192")
        sub_edges = zoom_map.get(normalized_edge, [])
        
        if not sub_edges:
            # Fallback: look for edges starting with the same source
            src = normalized_edge.split("\u2192")[0] if "\u2192" in normalized_edge else normalized_edge
            transitions = self.topology.topology.get("transitions", [])
            for t in transitions:
                if t.get("source", "").lower() == src.lower():
                    sub_edges.append(f"{t.get('source')}\u2192{t.get('target')}")
        
        if sub_edges:
            print(f"Sub-graph for {edge}:")
            for se in sub_edges:
                print(f"  \u21AA {se}")
        else:
            print(f"No sub-graph defined for edge: {edge}")
            print("This edge is an atomic transition.")
