# Implements: ADR-004, REQ-CTX-002
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Any

class SyncContextCommand:
    """Resolves context_sources and copies them to the workspace.
    Implements: ADR-004, REQ-CTX-002
    """
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.project_root = workspace_root.parent
        self.context_dir = workspace_root / design_name / "context"

    def run(self):
        constraints_path = self.workspace_root / self.design_name / "project_constraints.yml"
        if not constraints_path.exists():
            print(f"Constraints not found at {constraints_path}")
            return

        with open(constraints_path, "r") as f:
            config = yaml.safe_load(f)
        
        sources = config.get("context_sources", [])
        if not sources:
            print("No context sources defined.")
            return

        print(f"\nSyncing Context Sources (Tenant: {self.design_name})")
        print("="*40)

        for source in sources:
            uri = source.get("uri")
            scope = source.get("scope", "adrs")
            
            if not uri: continue
            
            # Resolve URI (file scheme)
            src_path = self._resolve_uri(uri)
            if not src_path or not src_path.exists():
                print(f"✗ [{scope}] Source not found: {uri}")
                continue
            
            target_dir = self.context_dir / scope
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files (REQ-CTX-002)
            print(f"  [{scope}] Syncing {uri} -> {target_dir}")
            if src_path.is_dir():
                for item in src_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, target_dir / item.name)
            else:
                shutil.copy2(src_path, target_dir / src_path.name)
        
        print("\nContext sync complete.")

    def _resolve_uri(self, uri: str) -> Path:
        if uri.startswith("file://"):
            return Path(uri[7:])
        if uri.startswith("/"):
            return Path(uri)
        if uri.startswith("../") or uri.startswith("./"):
            return (self.project_root / uri).resolve()
        return Path(uri)
