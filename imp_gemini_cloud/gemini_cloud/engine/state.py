import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class CloudEventStore:
    """GCP Firestore implementation of the Event Store."""
    def __init__(self, db, tenant_id: str, project_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.collection_path = f"tenants/{tenant_id}/projects/{project_id}/events"

    def emit(self, event_type: str, feature: str = "", edge: str = "", delta: int = None, data: Dict = None):
        """Schema-identical to local EventStore."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": self.project_id,
            "feature": feature,
            "edge": edge,
            "delta": delta,
            "data": data or {}
        }
        if self.db:
            # Atomic add to Firestore
            self.db.collection(self.collection_path).add(event)
        return event

class CloudProjector:
    """Projects Firestore events into Feature Vector views."""
    def __init__(self, db, tenant_id: str, project_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.project_id = project_id

    def project(self, events: List[Dict]) -> List[Dict]:
        """Simple projection of events into feature vectors."""
        features = {}
        for ev in events:
            f_id = ev.get("feature")
            if not f_id: continue
            
            if f_id not in features:
                features[f_id] = {"feature": f_id, "status": "active", "edges": {}}
            
            if ev.get("event_type") == "edge_converged":
                features[f_id]["status"] = "converged"
            elif ev.get("event_type") == "iteration_completed":
                edge = ev.get("edge")
                if edge:
                    features[f_id]["edges"][edge] = {"delta": ev.get("delta"), "status": ev.get("data", {}).get("status")}
                    
        return list(features.values())
