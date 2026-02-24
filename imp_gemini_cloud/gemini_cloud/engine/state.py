
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

    def emit(self, event_type: str, project: str = "", feature: str = "", edge: str = "", delta: int = None, data: Dict = None):
        """Schema-identical to local EventStore."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project or self.project_id,
            "feature": feature,
            "edge": edge,
            "delta": delta,
            "data": data or {}
        }
        if self.db:
            # Atomic add to Firestore
            self.db.collection(self.collection_path).add(event)
        return event
