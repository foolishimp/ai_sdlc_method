# Implements: REQ-CTX-001, REQ-F-CTX-001
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
        self.constraints["context"] = self.constraints.get("context", {})
        self.constraints["context"]["adrs"] = self._load_context_adrs()

    def _load_context_adrs(self) -> Dict[str, str]:
        """Index ADR content for the constraint surface."""
        adrs = {}
        # Search paths for ADRs (Cascading context)
        search_dirs = [
            self.workspace_root / self.design_name / "adrs",
            self.workspace_root / self.design_name / "context" / "adrs",
            self.workspace_root / "adrs",
            self.workspace_root.parent / "adrs", # Support root-level adrs
            self.workspace_root.parent / "specification" / "adrs",
            self.workspace_root.parent / "design" / "adrs",
        ]
        
        for adr_dir in search_dirs:
            if adr_dir.exists():
                for path in adr_dir.glob("*.md"):
                    # Extract ID (e.g., ADR-001) from filename
                    import re
                    match = re.search(r"(ADR-[A-Z0-9]+-\d+)", path.name)
                    if not match:
                        # Fallback for GG style: ADR-GG-001
                        match = re.search(r"(ADR-GG-\d+)", path.name)
                    
                    key = match.group(1) if match else path.stem
                    try:
                        # Later dirs override earlier ones if keys collide
                        adrs[key] = path.read_text(errors="ignore")
                    except:
                        continue
        return adrs

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
        
        import re
        # Pattern to match $var or ${var}
        pattern = re.compile(r"\$\{?([a-zA-Z0-9_.]+)\}?")
        
        def interpolator(text: str) -> str:
            if not isinstance(text, str):
                return text
            
            def replacer(match):
                var_path = match.group(1).split(".")
                val = self._get_nested_val(self.constraints, var_path)
                return str(val) if val is not None else match.group(0)
            
            return pattern.sub(replacer, text)

        for check in checklist:
            res_check = {}
            for k, v in check.items():
                if isinstance(v, str):
                    res_check[k] = interpolator(v)
                else:
                    res_check[k] = v
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
