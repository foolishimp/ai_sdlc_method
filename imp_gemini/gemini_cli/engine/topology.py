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
        # edge_name can be "intent\u2192requirements" or similar
        transitions = self.topology.get("transitions", [])
        for t in transitions:
            # Try matching by name or source\u2192target
            name = t.get("name", "")
            src_tgt = f"{t.get('source')}\u2192{t.get('target')}"
            if edge_name in [name, src_tgt]:
                cfg = t.get("edge_config")
                if cfg:
                    return self.workspace_root / "graph" / "edges" / Path(cfg).name
        return None
