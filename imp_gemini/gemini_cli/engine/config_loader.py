# Implements: REQ-CTX-001
"""
AI SDLC Configuration Loader.
Resolves $variable references in edge checklists from project_constraints.yml.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List
import yaml

class ConfigLoader:
    """Operationalizes the constraint surface (REQ-CTX-001, REQ-CTX-002)."""
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.constraints = self._load_hierarchical_constraints()

    def _load_hierarchical_constraints(self) -> Dict[str, Any]:
        """Load constraints from multiple levels (ADR-004)."""
        levels = [
            Path("/etc/ai-sdlc/global_constraints.yml"),
            Path.home() / ".ai-sdlc" / "org_constraints.yml",
            self.workspace_root / self.design_name / "project_constraints.yml",
            self.workspace_root / "project_constraints.yml",
        ]
        
        merged = {}
        for path in levels:
            if path.exists():
                with open(path, "r") as f:
                    data = yaml.safe_load(f) or {}
                    self._deep_merge(merged, data)
        return merged

    def _deep_merge(self, base: Dict, update: Dict):
        """Recursively merge two dictionaries."""
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def compute_spec_hash(self, intent_content: str) -> str:
        """Computes a stable hash of the specification (ADR-005)."""
        spec_data = {
            "intent": intent_content,
            "constraints": self.constraints
        }
        canonical = json.dumps(spec_data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def resolve_checklist(self, edge_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Resolve $variable references in the edge checklist."""
        checklist = edge_config.get("checklist", [])
        resolved = []
        
        for check in checklist:
            res_check = dict(check)
            
            # Resolve command variables (e.g., "$tools.test_runner.command")
            if "command" in res_check and res_check["command"].startswith("$"):
                var_path = res_check["command"][1:].split(".")
                res_check["command"] = self._get_nested_val(self.constraints, var_path)
            
            resolved.append(res_check)
        return resolved

    def _get_nested_val(self, data: Dict, path: List[str]) -> Any:
        """Helper to get nested values from dict."""
        for key in path:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return None
        return data if data != {} else None
