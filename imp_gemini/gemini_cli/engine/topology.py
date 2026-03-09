import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

class GraphTopology:
    """Loads and enforces the asset graph structure (REQ-GRAPH-001, 002)."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.config_path = workspace_root / "graph" / "graph_topology.yml"
        self.topology = self._load_topology()

    def _load_topology(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f) or {}

    def get_asset_types(self) -> List[str]:
        return list(self.topology.get("asset_types", {}).keys())

    def is_admissible(self, source: str, target: str) -> bool:
        transitions = self.topology.get("transitions", [])
        for t in transitions:
            if t.get("source") == source and t.get("target") == target:
                return True
        return False

    def get_edge_config_path(self, edge_name: str) -> Optional[Path]:
        transitions = self.topology.get("transitions", [])
        for t in transitions:
            name = t.get("name", "")
            src_tgt = f"{t.get('source')}\u2192{t.get('target')}"
            if edge_name in [name, src_tgt]:
                cfg = t.get("edge_config")
                if cfg:
                    return self.workspace_root / "graph" / "edges" / Path(cfg).name
        return None

class CompositionCompiler:
    """Compiles Level 3 Compositions into Level 5 Graph Fragments (ADR-S-029)."""
    
    def __init__(self, topology: GraphTopology):
        self.topology = topology
        self.macro_registry = {
            "PLAN": ["intent\u2192requirements"],
            "POC": ["intent\u2192requirements", "requirements\u2192design", "design\u2192code", "code\u2194unit_tests"],
            "BUILD": ["design\u2192code", "code\u2194unit_tests"],
            "CONSENSUS": ["requirements\u2192design"] # Default consensus edge
        }

    def compile(self, composition_expression: Dict[str, Any]) -> List[str]:
        """Translates a macro + bindings into an executable edge sequence."""
        macro = composition_expression.get("macro")
        bindings = composition_expression.get("bindings", {})
        
        if macro not in self.macro_registry:
            raise ValueError(f"Unknown macro: {macro}")
            
        edges = self.macro_registry[macro]
        
        # Binding-driven expansion (e.g. override edges based on unit_category)
        # This is where the 'compiler' logic lives
        return edges

    def get_graph_fragment(self, edges: List[str]) -> Dict[str, Any]:
        """Returns the full Level 5 fragment (nodes, edges, configs) for the given edges."""
        fragment = {"edges": [], "nodes": set()}
        for edge_name in edges:
            cfg_path = self.topology.get_edge_config_path(edge_name)
            fragment["edges"].append({
                "name": edge_name,
                "config_path": str(cfg_path) if cfg_path else None
            })
            # Extract nodes from edge name (e.g. "source\u2192target")
            parts = edge_name.replace("\u2194", "\u2192").split("\u2192")
            for p in parts: fragment["nodes"].add(p.strip())
            
        fragment["nodes"] = list(fragment["nodes"])
        return fragment
