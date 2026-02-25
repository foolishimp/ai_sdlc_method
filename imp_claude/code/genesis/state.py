
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict

class EventStore:
    def __init__(self, workspace_root: Path):
        self.log_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    def emit(self, event_type: str, project: str, feature: str = "", edge: str = "", delta: int = None, data: Dict = None):
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project,
            "feature": feature,
            "edge": edge,
            "delta": delta,
            "data": data or {}
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
        return event

class Projector:
    @staticmethod
    def get_feature_status(events: List[Dict]) -> Dict[str, Dict]:
        status = {}
        for ev in events:
            feat = ev.get("feature")
            if not feat: continue
            if feat not in status:
                status[feat] = {"status": "pending", "trajectory": {}}
            e_type = ev["event_type"]
            if e_type == "edge_started":
                status[feat]["trajectory"][ev.get("edge")] = "iterating"
            elif e_type == "edge_converged":
                status[feat]["trajectory"][ev.get("edge")] = "converged"
        return status
