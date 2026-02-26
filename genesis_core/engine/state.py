# Implements: REQ-CLI-002, REQ-NF-CLI-002
"""
AI SDLC State Engine: Pure Event Sourcing.
All state is a projection of the immutable events.jsonl log.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict

class EventStore:
    """Manages the append-only event log."""
    
    def __init__(self, workspace_root: Path):
        self.log_path = workspace_root / "events" / "events.jsonl"

    def emit(self, event_type: str, project: str, feature: str = "", edge: str = "", delta: int = None, data: Dict = None):
        """Append an event to the log. delta is TOP-LEVEL for state-machine routing."""
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
        """Read all events from the log."""
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events

class Projector:
    """Derives materialized views from the event log."""
    
    @staticmethod
    def get_iteration_count(events: List[Dict], feature: str, edge: str) -> int:
        """Count iterations for a specific feature and edge."""
        return sum(
            1 for ev in events 
            if ev.get("event_type") == "iteration_completed" 
            and ev.get("feature") == feature 
            and ev.get("edge") == edge
        )

    @staticmethod
    def get_feature_status(events: List[Dict]) -> Dict[str, Dict]:
        """Project current status of all feature vectors."""
        status = {}
        for ev in events:
            feat = ev.get("feature")
            if not feat:
                continue
            
            if feat not in status:
                status[feat] = {"status": "pending", "trajectory": {}}
            
            e_type = ev["event_type"]
            edge_name = ev.get("edge")
            
            if e_type == "edge_started":
                if edge_name:
                    status[feat]["trajectory"][edge_name] = "iterating"
            elif e_type == "edge_converged":
                if edge_name:
                    status[feat]["trajectory"][edge_name] = "converged"
        return status
