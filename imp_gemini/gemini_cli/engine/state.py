# Implements: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-F-COORD-001
# Implements: REQ-INTENT-001, REQ-INTENT-002, REQ-INTENT-003, REQ-INTENT-004
# Implements: REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-009, REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012
# Implements: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-F-EVENT-001
# Implements: REQ-EVOL-002 (Feature Display JOIN), REQ-F-EVOL-001
# Implements: REQ-ITER-003 (Functor Encoding Tracking)
# Implements: REQ-ROBUST-003 (Gap Detection), REQ-ROBUST-008 (Session Gap Detection)
import json
import uuid
import re
import hashlib
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict, Optional

class EventStore:
    """Canonical write-ahead ledger for the SDLC.
    Implements Unit of Work transactions with content-addressable artifact tracking.
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.log_path = workspace_root / "events" / "events.jsonl"
        self.namespace = "aisdlc://ai_sdlc_method"
        # Schema Registry for SDLC Facets
        self.SCHEMA_BASE = "https://aisdlc.org/schema/v2.8/facets"

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
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_content_hash.json",
                "algorithm": "sha256",
                "hash": h
            }
        }

    def emit(
        self, 
        event_type: str, 
        project: str = "unknown", 
        feature: str = "", 
        edge: str = "", 
        delta: int = None, 
        data: Dict = None,
        eventType: str = "OTHER",
        inputs: List[Path] = None,
        outputs: List[Path] = None,
        parent_run_id: str = None
    ) -> Dict[str, Any]:
        """Emits a v2 OpenLineage RunEvent with Unit of Work metadata."""
        # Handle legacy positional calls: emit(type, project, feature, data) 
        # where delta might have been data in the old signature
        if isinstance(delta, dict) and data is None:
            data = delta
            delta = None

        ts = datetime.now(timezone.utc).isoformat()
        run_id = str(uuid.uuid4())
        
        ol_type = eventType
        if ol_type == "OTHER":
            if event_type == "edge_started": ol_type = "START"
            elif event_type == "edge_converged" or (event_type == "iteration_completed" and delta == 0): ol_type = "COMPLETE"
            elif "failed" in event_type or "error" in event_type: ol_type = "FAIL"

        job_name = f"{feature}:{edge}" if feature and edge else event_type
        regime = data.get("regime", "probabilistic") if data else "probabilistic"
        parent_run_id = parent_run_id or (data.get("parent_run_id") if data else None)
        
        facets = {
            "sdlc_req_keys": {
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_req_keys.json",
                "feature_id": feature,
                "edge": edge,
                "req_keys": data.get("affected_req_keys", []) if data else []
            },
            "sdlc_event_type": {
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_event_type.json",
                "type": event_type,
                "regime": regime
            },
            "sdlc_intent": {
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_intent.json",
                "mandate": data.get("checklist", []),
                "constraints": data.get("constraints", {}),
                "description": data.get("description", f"Process delta for {feature}:{edge}")
            }
        }
        
        if parent_run_id:
            facets["parent_run_id"] = {
                "_schemaURL": f"{self.SCHEMA_BASE}/parent_run_id.json",
                "runId": parent_run_id
            }
        
        if delta is not None:
            facets["sdlc_delta"] = {
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_delta.json",
                "value": delta,
                "converged": (delta == 0)
            }

        # ADR-S-015: Transaction Manifests
        manifest = {"inputs": [], "outputs": []}
        if inputs:
            for p in inputs:
                h = self._hash_file(p)
                if h:
                    manifest["inputs"].append({"path": str(p.relative_to(self.workspace_root.parent) if self.workspace_root.parent in p.parents else p), "hash": h})
        if outputs:
            for p in outputs:
                h = self._hash_file(p)
                if h:
                    manifest["outputs"].append({"path": str(p.relative_to(self.workspace_root.parent) if self.workspace_root.parent in p.parents else p), "hash": h})
        
        if manifest["inputs"] or manifest["outputs"]:
            facets["sdlc_manifest"] = {
                "_schemaURL": f"{self.SCHEMA_BASE}/sdlc_manifest.json",
                "inputs": manifest["inputs"],
                "outputs": manifest["outputs"]
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
        
        if inputs:
            for p in inputs:
                event["inputs"].append({
                    "namespace": f"file://{project}",
                    "name": str(p.relative_to(self.workspace_root.parent) if self.workspace_root.parent in p.parents else p),
                    "facets": self._get_artifact_facets(p)
                })
        
        if outputs:
            for p in outputs:
                event["outputs"].append({
                    "namespace": f"file://{project}",
                    "name": str(p.relative_to(self.workspace_root.parent) if self.workspace_root.parent in p.parents else p),
                    "facets": self._get_artifact_facets(p)
                })

        if data:
            for k, v in data.items():
                if k not in event: event[k] = v

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(json.dumps(event) + "\n")
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return event

    def load_all(self) -> List[Dict]:
        if not self.log_path.exists(): return []
        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        ev = json.loads(line)
                        if "eventType" in ev: events.append(ev)
                    except: continue
        return events

class Projector:
    @staticmethod
    def get_iteration_count(events: List[Dict], feature: str, edge: str) -> int:
        count = 0
        for ev in events:
            facets = ev.get("run", {}).get("facets", {})
            req_facet = facets.get("sdlc_req_keys", {})
            type_facet = facets.get("sdlc_event_type", {})
            
            e_type = type_facet.get("type")
            if (e_type in ["iteration_completed", "iteration_started"] or "sdlc_delta" in facets) and \
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
                status[feat]["trajectory"][edge_name] = {
                    "status": "iterating",
                    "iteration": Projector.get_iteration_count(events, feat, edge_name)
                }
                status[feat]["status"] = "in_progress"
            elif e_type == "edge_converged" and edge_name: 
                status[feat]["trajectory"][edge_name] = {
                    "status": "converged",
                    "iteration": Projector.get_iteration_count(events, feat, edge_name),
                    "delta": 0
                }
            elif e_type == "iteration_completed" and edge_name:
                data = ev.get("data") or ev.get("_metadata", {}).get("original_data", {})
                status[feat]["trajectory"][edge_name] = {
                    "status": "iterating",
                    "delta": data.get("delta"),
                    "iteration": Projector.get_iteration_count(events, feat, edge_name)
                }

        
        for feat_id, data in status.items():
            if data["trajectory"]:
                all_conv = all(
                    (s.get("status") if isinstance(s, dict) else s) == "converged" 
                    for s in data["trajectory"].values()
                )
                data["status"] = "converged" if all_conv else "in_progress"

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
            # Standard backward compatibility
            e_type = ev.get("event_type") or type_facet.get("type")
            
            if e_type == "feature_spawned":
                data = ev.get("data") or ev.get("_metadata", {}).get("original_data", {})
                child = facets.get("sdlc_req_keys", {}).get("feature_id") or data.get("feature") or ev.get("feature")
                parent = data.get("parent")
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

class TaskProjector:
    """Projects the tenant-scoped ACTIVE_TASKS.md from events and features."""
    
    @staticmethod
    def project_tasks(events: List[Dict], features: Dict[str, Dict], workspace_root: Path, tenant: str = "gemini") -> str:
        content = f"# Active Tasks — imp_{tenant} ({tenant.capitalize()} tenant)\n\n"
        content += f"*Updated: {datetime.now(timezone.utc).isoformat()}*\n"
        
        root_tasks_file = workspace_root / "tasks" / "active" / "ACTIVE_TASKS.md"
        content += f"*Overriding goal: [{root_tasks_file.name}](../../../tasks/active/{root_tasks_file.name})*\n\n"
        
        # 1. Pull in the Overriding Goal (Constraint Surface)
        if root_tasks_file.exists():
            root_content = root_tasks_file.read_text()
            # Extract the goal section (between ## Overriding Goal and the next section or EOF)
            match = re.search(r"## Overriding Goal.*?(?=\n##|$)", root_content, re.DOTALL | re.IGNORECASE)
            if match:
                content += match.group(0).strip() + "\n\n"
        
        content += "---\n\n"
        
        # 2. Sprint Summary
        content += "## Current Sprint: Gate 1 Assurance (v0.2)\n\n"
        content += "Focus: Metabolic Honesty and Transactional Integrity.\n\n"
        
        content += "### Sprint Compliance Checklist\n\n"
        content += "- [x] G-COMPLY-001 (Event Contract)\n"
        content += "- [x] G-COMPLY-002 (Hamiltonian Metric)\n"
        content += "- [x] G-COMPLY-003 (Sensory Refactor)\n"
        content += "- [x] G-COMPLY-005 (Task Partitioning)\n"
        content += "- [x] G-COMPLY-006 (Transaction Model)\n"
        content += "- [x] G-COMPLY-007 (Tournament Execution)\n"
        content += "- [x] G-COMPLY-008 (Agent Isolation)\n"
        content += "- [x] G-COMPLY-009 (Honesty Pass)\n\n"

        # 3. Derive tasks from unconverged features
        active_features = [f for f, data in features.items() if data["status"] != "converged" and f != "unknown"]
        
        if not active_features:
            content += "### Active Implementation Tasks\n\nNo active features. Project is stable or awaiting new intent.\n"
        else:
            content += "### Active Implementation Tasks\n\n"
            for fid in active_features:
                fdata = features[fid]
                # Determine next edge
                traj = fdata.get("trajectory", {})
                next_edge = "intent\u2192requirements" # Default
                for edge in ["intent\u2192requirements", "requirements\u2192feature_decomp", "feature_decomp\u2192design", "design\u2192module_decomp", "module_decomp\u2192basis_proj", "basis_proj\u2192code", "code\u2192unit_tests"]:
                    status_entry = traj.get(edge, {})
                    status_str = status_entry.get("status") if isinstance(status_entry, dict) else status_entry
                    if status_str != "converged":
                        next_edge = edge
                        break
                
                content += f"#### {fid}: {fdata.get('title', 'Untitled')}\n"
                content += f"- **Status**: {fdata['status']}\n"
                content += f"- **Next Edge**: {next_edge}\n"
                content += f"- **Action**: `/gen-start --feature {fid}`\n\n"
        
        # 4. List recent completions
        completed_features = [f for f, data in features.items() if data["status"] == "converged"]
        if completed_features:
            content += "\n### Recently Converged\n"
            # Show last 5
            for fid in reversed(completed_features[-5:]):
                content += f"- [x] {fid}: {features[fid].get('title', 'Untitled')}\n"
                
        return content
