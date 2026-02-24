# Implements: REQ-ITER-001, REQ-ITER-002, REQ-UX-005
"""AI SDLC Universal Iterate Engine.

This module implements the Python-side logic for the /gen-iterate command:
context loading, event emission, state updates, and protocol enforcement.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class IterateEngine:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.ws_dir = self.project_root / ".ai-workspace"
        self.events_file = self.ws_dir / "events" / "events.jsonl"

    def emit_event(self, event_type: str, feature: str, edge: str, data: dict[str, Any]):
        """Emit a JSON event to the immutable event log."""
        project_name = self._get_project_name()
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "feature": feature,
            "edge": edge,
            **data
        }
        
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def update_feature_vector(self, feature_id: str, edge: str, iteration: int, status: str, delta: int, asset_path: str = ""):
        """Update the state projection for a feature vector."""
        fv_path = self.ws_dir / "features" / "active" / f"{feature_id}.yml"
        if not fv_path.exists():
            # Create from template if missing
            template_path = self.ws_dir / "features" / "feature_vector_template.yml"
            if template_path.exists():
                with open(template_path) as f:
                    fv_data = yaml.safe_load(f)
            else:
                fv_data = {"feature": feature_id, "trajectory": {}}
        else:
            with open(fv_path) as f:
                fv_data = yaml.safe_load(f)

        fv_data["feature"] = feature_id
        traj = fv_data.setdefault("trajectory", {})
        
        # Source/Target decomposition
        source, target = edge.split("→") if "→" in edge else (edge, edge)
        
        edge_entry = traj.setdefault(target, {})
        edge_entry["status"] = status
        edge_entry["iteration"] = iteration
        edge_entry["delta"] = delta
        if asset_path:
            edge_entry["asset"] = asset_path
        
        if status == "converged":
            edge_entry["converged_at"] = datetime.now(timezone.utc).isoformat()

        with open(fv_path, "w") as f:
            yaml.dump(fv_data, f, sort_keys=False)

    def _get_project_name(self) -> str:
        """Load project name from constraints."""
        candidates = [
            self.ws_dir / "gemini_genesis" / "project_constraints.yml",
            self.ws_dir / "context" / "project_constraints.yml",
        ]
        for cp in candidates:
            if cp.exists():
                with open(cp) as f:
                    data = yaml.safe_load(f)
                if data and data.get("project"):
                    return data["project"].get("name", "unknown")
        return "unknown"

    def verify_protocol(self, start_time: datetime) -> list[str]:
        """Protocol enforcement hook: verify side effects occurred."""
        gaps = []
        
        # 1. Check Event Log
        if not self.events_file.exists() or self.events_file.stat().st_mtime < start_time.timestamp():
            gaps.append("PROTOCOL_VIOLATION: No event emitted to events.jsonl")
            
        # 2. Check Feature Vectors
        fv_dir = self.ws_dir / "features" / "active"
        fv_updated = any(p.stat().st_mtime >= start_time.timestamp() for p in fv_dir.glob("*.yml"))
        if not fv_updated:
            gaps.append("PROTOCOL_VIOLATION: Feature vector state not updated")
            
        return gaps
