import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict

class EventStore:
    def __init__(self, workspace_root: Path):
        self.log_path = workspace_root / "events" / "events.jsonl"

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

    def load_all(self) -> List[Dict]:
        """Loads all events from the immutable log."""
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        continue
        return events

class Projector:
    @staticmethod
    def get_iteration_count(events: List[Dict], feature: str, edge: str) -> int:
        return sum(1 for ev in events if ev.get("event_type") == "iteration_completed" and ev.get("feature") == feature and ev.get("edge") == edge)

    @staticmethod
    def get_feature_status(events: List[Dict]) -> Dict[str, Dict]:
        status = {}
        for ev in events:
            feat = ev.get("feature")
            if not feat: continue
            if feat not in status: status[feat] = {"status": "pending", "trajectory": {}}
            e_type, edge_name = ev["event_type"], ev.get("edge")
            if e_type == "edge_started" and edge_name: status[feat]["trajectory"][edge_name] = "iterating"
            elif e_type == "edge_converged" and edge_name: status[feat]["trajectory"][edge_name] = "converged"
        return status
