import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

class CloudEventStore:
    """GCP Firestore implementation of the Event Store with Unit of Work semantics."""
    def __init__(self, db, tenant_id: str, project_id: str, project_root: Path = None):
        self.db = db
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.project_root = project_root
        self.collection_path = f"tenants/{tenant_id}/projects/{project_id}/events"

    def _hash_file(self, path: Path) -> Optional[str]:
        if not path.exists() or not path.is_file():
            return None
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_artifact_facets(self, path: Path) -> Dict[str, Any]:
        h = self._hash_file(path)
        if not h:
            return {}
        return {
            "sdlc:contentHash": {
                "algorithm": "sha256",
                "hash": h
            }
        }

    def emit(
        self, 
        event_type: str, 
        feature: str = "", 
        edge: str = "", 
        delta: int = None, 
        data: Dict = None,
        eventType: str = "OTHER",
        inputs: List[Path] = None,
        outputs: List[Path] = None,
        parent_run_id: str = None
    ) -> Dict[str, Any]:
        """Schema-identical to local EventStore, but persisted to Firestore."""
        run_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        
        ol_type = eventType
        if ol_type == "OTHER":
            if event_type == "edge_started": ol_type = "START"
            elif event_type == "edge_converged" or (event_type == "iteration_completed" and delta == 0): ol_type = "COMPLETE"
            elif "failed" in event_type or "error" in event_type: ol_type = "FAIL"

        # Map Mandate to Intent (Mandate == Intent)
        facets = {
            "sdlc_req_keys": {"feature_id": feature, "edge": edge, "req_keys": data.get("affected_req_keys", []) if data else []},
            "sdlc_event_type": {"type": event_type, "regime": data.get("regime", "probabilistic") if data else "probabilistic"},
            "sdlc_delta": {"value": delta, "converged": (delta == 0)},
            "sdlc_intent": {
                "mandate": data.get("checklist", []),
                "constraints": data.get("constraints", {}),
                "description": data.get("description", f"Process delta for {feature}:{edge}")
            }
        }

        if parent_run_id:
            facets["parent_run_id"] = {"runId": parent_run_id}

        event = {
            "eventType": ol_type,
            "eventTime": ts,
            "run": {"runId": run_id, "facets": facets},
            "job": {"namespace": f"aisdlc://{self.tenant_id}", "name": f"{feature}:{edge}"},
            "inputs": [],
            "outputs": [],
            "producer": "aisdlc://imp_gemini_cloud/v2.8",
            "schemaURL": "https://openlineage.io/spec/1-0-2/OpenLineage.json#RunEvent",
            "_metadata": {"project": self.project_id, "tenant": self.tenant_id}
        }

        if inputs:
            for p in inputs:
                event["inputs"].append({
                    "namespace": f"gs://{self.project_id}",
                    "name": str(p.relative_to(self.project_root) if self.project_root and self.project_root in p.parents else p),
                    "facets": self._get_artifact_facets(p)
                })
        
        if outputs:
            for p in outputs:
                event["outputs"].append({
                    "namespace": f"gs://{self.project_id}",
                    "name": str(p.relative_to(self.project_root) if self.project_root and self.project_root in p.parents else p),
                    "facets": self._get_artifact_facets(p)
                })

        if data:
            for k, v in data.items():
                if k not in event:
                    event[k] = v

        if self.db:
            self.db.collection(self.collection_path).add(event)
            
        return event

class CloudProjector:
    """Projects Firestore events into Feature Vector views."""
    def __init__(self, db, tenant_id: str, project_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.project_id = project_id

    def project(self, events: List[Dict]) -> List[Dict]:
        features = {}
        for ev in events:
            facets = ev.get("run", {}).get("facets", {})
            req_facet = facets.get("sdlc_req_keys", {})
            f_id = req_facet.get("feature_id")
            if not f_id: continue
            
            if f_id not in features:
                features[f_id] = {"feature": f_id, "status": "active", "edges": {}}
            
            ol_type = ev.get("eventType")
            edge = req_facet.get("edge")
            
            if ol_type == "COMPLETE" and edge:
                features[f_id]["edges"][edge] = {"status": "converged"}
            elif ol_type == "START" and edge:
                features[f_id]["edges"][edge] = {"status": "iterating"}
                    
        return list(features.values())
