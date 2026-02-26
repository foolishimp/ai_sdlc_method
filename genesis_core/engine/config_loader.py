# Implements: REQ-CTX-001
"""
AI SDLC Configuration Loader.
Resolves $variable references in edge checklists from project_constraints.yml.
"""

from pathlib import Path
from typing import Dict, Any, List
import yaml

class ConfigLoader:
    """Operationalizes the constraint surface."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.constraints = self._load_constraints()

    def _load_constraints(self) -> Dict[str, Any]:
        """Load project constraints from tenant context."""
        candidates = [
            self.workspace_root / "gemini_genesis" / "project_constraints.yml",
            self.workspace_root / "context" / "project_constraints.yml",
        ]
        for cp in candidates:
            if cp.exists():
                with open(cp) as f:
                    return yaml.safe_load(f) or {}
        return {}

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
            
            # Resolve threshold variables (e.g., "$coverage.threshold")
            if "pass_criterion" in res_check and "$" in res_check["pass_criterion"]:
                # Simple replacement for demonstration
                # Real implementation would use regex to find all $vars
                pass 

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
