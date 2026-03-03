import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict

class EventStore:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.log_path = workspace_root / "events" / "events.jsonl"
        # Job namespace from project_constraints.yml
        self.namespace = "aisdlc://ai_sdlc_method"

    def emit(self, event_type: str, project: str, feature: str = "", edge: str = "", delta: int = None, data: Dict = None):
        """Emits a v2 OpenLineage RunEvent."""
        import fcntl
        ts = datetime.now(timezone.utc).isoformat()
        run_id = str(uuid.uuid4())
        
        ol_type = "OTHER"
        if event_type == "edge_started":
            ol_type = "START"
        elif event_type == "edge_converged" or (event_type == "iteration_completed" and delta == 0):
            ol_type = "COMPLETE"
        elif "failed" in event_type or "error" in event_type:
            ol_type = "FAIL"

        job_name = f"{feature}:{edge}" if feature and edge else event_type
        
        facets = {
            "sdlc_req_keys": {
                "_schemaURL": "https://aisdlc.org/schema/v2.8/facets/sdlc_req_keys.json",
                "feature_id": feature,
                "edge": edge,
                "req_keys": data.get("affected_req_keys", []) if data else []
            },
            "sdlc_event_type": {
                "_schemaURL": "https://aisdlc.org/schema/v2.8/facets/sdlc_event_type.json",
                "type": event_type
            }
        }
        
        if delta is not None:
            facets["sdlc_delta"] = {
                "_schemaURL": "https://aisdlc.org/schema/v2.8/facets/sdlc_delta.json",
                "value": delta,
                "converged": (delta == 0)
            }

        if data and "valence" in data:
            facets["sdlc_valence"] = {
                "_schemaURL": "https://aisdlc.org/schema/v2.8/facets/sdlc_valence.json",
                **data["valence"]
            }

        event = {
            "event_type": event_type, # Backward compatibility
            "timestamp": ts,           # Backward compatibility
            "project": project,         # Backward compatibility
            "data": data or {},         # Backward compatibility (explicit data key)
            "eventType": ol_type,
            "eventTime": ts,
            "run": {"runId": run_id, "facets": facets},
            "job": {"namespace": self.namespace, "name": job_name},
            "inputs": [],
            "outputs": [],
            "producer": "aisdlc://imp_gemini/v2.8",
            "schemaURL": "https://openlineage.io/spec/1-0-2/OpenLineage.json#RunEvent",
            "_metadata": {"project": project, "original_data": data or {}}
        }
        
        # Merge original data for backward compatibility (flattened)
        if data:
            for k, v in data.items():
                if k not in event:
                    event[k] = v

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Use advisory locking for atomic append
        with open(self.log_path, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(json.dumps(event) + "\n")
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return event

    def load_all(self) -> List[Dict]:
        """Loads all events, assuming v2 OpenLineage schema."""
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        ev = json.loads(line)
                        if "eventType" in ev:
                            events.append(ev)
                    except:
                        continue
        return events

class Projector:
    @staticmethod
    def get_iteration_count(events: List[Dict], feature: str, edge: str) -> int:
        count = 0
        for ev in events:
            facets = ev.get("run", {}).get("facets", {})
            req_facet = facets.get("sdlc_req_keys", {})
            type_facet = facets.get("sdlc_event_type", {})
            
            if (type_facet.get("type") == "iteration_completed" or "sdlc_delta" in facets) and \
               req_facet.get("feature_id") == feature and req_facet.get("edge") == edge:
                count += 1
        return count

    @staticmethod
    def get_feature_status(events: List[Dict], project_root: Path = None) -> Dict[str, Dict]:
        status = {}
        
        if project_root:
            spec_features_path = project_root / "specification" / "features" / "FEATURE_VECTORS.md"
            if spec_features_path.exists():
                content = spec_features_path.read_text()
                feat_matches = re.finditer(r"### (REQ-F-[A-Z0-9-]+): (.*)", content)
                for m in feat_matches:
                    fid, title = m.group(1), m.group(2)
                    status[fid] = {"title": title, "status": "pending", "trajectory": {}, "source": "spec"}

        for ev in events:
            facets = ev.get("run", {}).get("facets", {})
            req_facet = facets.get("sdlc_req_keys", {})
            type_facet = facets.get("sdlc_event_type", {})
            
            feat = req_facet.get("feature_id")
            edge_name = req_facet.get("edge")
            ol_type = ev.get("eventType")
            
            e_type = None
            if ol_type == "START": e_type = "edge_started"
            elif ol_type == "COMPLETE": e_type = "edge_converged"
            elif ol_type == "OTHER": e_type = type_facet.get("type")

            if not feat: continue
            if feat not in status: 
                status[feat] = {"status": "pending", "trajectory": {}, "source": "workspace"}
            
            if edge_name:
                edge_name = edge_name.replace("->", "\u2192").replace("\u2194", "\u2192")
            
            if e_type == "edge_started" and edge_name: 
                status[feat]["trajectory"][edge_name] = "iterating"
                status[feat]["status"] = "in_progress"
            elif e_type == "edge_converged" and edge_name: 
                status[feat]["trajectory"][edge_name] = "converged"
        
        for data in status.values():
            if data["trajectory"]:
                data["status"] = "converged" if all(s == "converged" for s in data["trajectory"].values()) else "in_progress"

        return status

class DependencyResolver:
    def __init__(self, events: List[Dict]):
        self.events = events
        self.dependencies = self._build_graph()

    def _build_graph(self) -> Dict[str, List[str]]:
        graph = {}
        for ev in self.events:
            facets = ev.get("run", {}).get("facets", {})
            type_facet = facets.get("sdlc_event_type", {})
            if type_facet.get("type") == "feature_spawned":
                meta = ev.get("_metadata", {}).get("original_data", {})
                child = facets.get("sdlc_req_keys", {}).get("feature_id")
                parent = meta.get("parent")
                if child and parent:
                    graph.setdefault(child, []).append(parent)
        return graph

    def get_all_dependencies(self, feature_id: str) -> List[str]:
        return self.dependencies.get(feature_id, [])

    def is_blocked(self, feature_id: str, converged_features: List[str]) -> bool:
        for d in self.get_all_dependencies(feature_id):
            if d not in converged_features:
                return True
        return False
