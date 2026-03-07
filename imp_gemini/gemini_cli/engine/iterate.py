# Implements: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004, REQ-F-EDGE-001, REQ-EVAL-001, REQ-EVAL-002, REQ-F-EVAL-001, REQ-EVENT-002, REQ-EVENT-003, REQ-GRAPH-001, REQ-GRAPH-003
# Implements: REQ-EVENT-001, REQ-EVENT-004, REQ-ITER-001, REQ-ITER-002
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Protocol
import shutil
from datetime import datetime, timezone

from .models import IterationRecord, IterationReport, FunctorResult, Outcome, ConstructResult
from .state import EventStore

from .stateless import run_iteration

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

# Implements: REQ-ITER-001, REQ-ITER-002, REQ-ROBUST-002, REQ-GRAPH-004, REQ-EVOL-001, REQ-F-EVOL-001, ADR-S-018
class IterateEngine:
    """Universal iteration engine for all graph edges.
    Implements the Markov Blanket pattern via project fingerprinting and run archival.
    """
    
    def __init__(self, functor_map: Dict[str, Any] = None, project_root: Path = None, constraints: Dict[str, Any] = None, **kwargs):
        # Support both functor_map and functors (list or dict) for backward compatibility
        self.functor_map = functor_map or kwargs.get("functors") or {}
        if isinstance(self.functor_map, list):
            # Convert list of functors to map
            self.functor_map = {f.__class__.__name__.replace("Functor", "").lower(): f for f in self.functor_map}
            
        self.project_root = project_root or Path.cwd()
        if (self.project_root / ".ai-workspace").exists():
            self.workspace_root = self.project_root / ".ai-workspace"
        else:
            self.workspace_root = self.project_root
            if not self.workspace_root.name == ".ai-workspace":
                self.workspace_root = self.project_root / ".ai-workspace"
        
        if constraints is None:
            constraints_path = self.workspace_root / "context" / "project_constraints.yml"
            if constraints_path.exists():
                import yaml
                self.constraints = yaml.safe_load(constraints_path.read_text())
            else:
                self.constraints = {}
        else:
            self.constraints = constraints
            
        self.store = EventStore(self.workspace_root)

    def _get_project_fingerprint(self) -> tuple[float, int]:
        """Return (latest_mtime, total_file_count) for key project locations.
        Implementation of the Markov Blanket boundary check.
        """
        latest = 0.0
        count = 0
        sentinel_dirs = [
            self.project_root / "code",
            self.project_root / "tests",
            self.project_root / "specification",
            self.project_root / ".ai-workspace" / "events",
            self.project_root / ".ai-workspace" / "features",
        ]
        for d in sentinel_dirs:
            if not d.exists(): continue
            try:
                mt = d.stat().st_mtime
                if mt > latest: latest = mt
                for child in d.iterdir():
                    count += 1
                    try:
                        mt = child.stat().st_mtime
                        if mt > latest: latest = mt
                    except OSError: continue
            except OSError: continue
        return latest, count

    def get_liveness_signal(self, transport: str = "filesystem") -> tuple[float, int]:
        """Pluggable liveness signal (Finding #4). 
        Defaults to filesystem fingerprint but can be extended for cloud heartbeats.
        """
        if transport == "filesystem":
            return self._get_project_fingerprint()
        # Fallback to local time for unknown transports
        return time.time(), 0

    def _archive_iteration(self, feature_id: str, edge: str, iteration: int, failed: bool = False):
        """Archive the project state for this iteration to ensure audit reproducibility."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        status = "FAILED" if failed else "OK"
        archive_name = f"run_{feature_id}_{edge.replace('→', '_').replace('↔', '_')}_iter{iteration}_{status}_{ts}"
        archive_dir = self.project_root / "runs" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        for d in ["code", "tests", "specification", ".ai-workspace"]:
            src = self.project_root / d
            if src.exists():
                shutil.copytree(src, archive_dir / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "runs"), dirs_exist_ok=True)
        latest = self.project_root / "runs" / "latest"
        latest.parent.mkdir(parents=True, exist_ok=True)
        if latest.exists() or latest.is_symlink(): latest.unlink()
        try: latest.symlink_to(archive_dir.name)
        except Exception: pass
        return archive_dir

    def detect_integrity_gaps(self) -> List[Dict[str, Any]]:
        """Find discrepancies between the Event Ledger (committed) and Filesystem (actual)."""
        events = self.store.load_all()
        last_committed_hashes = {}
        for ev in events:
            if ev.get("eventType") == "COMPLETE":
                for output in ev.get("outputs", []):
                    name = output.get("name")
                    facets = output.get("facets", {})
                    h = facets.get("sdlc:contentHash", {}).get("hash")
                    if name and h: last_committed_hashes[name] = h
        gaps = []
        for rel_path, committed_hash in last_committed_hashes.items():
            full_path = self.project_root / rel_path
            if not full_path.exists():
                gaps.append({"path": rel_path, "type": "MISSING_ARTIFACT", "expected": committed_hash})
                continue
            actual_hash = self.store._hash_file(full_path)
            if actual_hash != committed_hash:
                gaps.append({"path": rel_path, "type": "UNCOMMITTED_CHANGE", "expected": committed_hash, "actual": actual_hash})
        starts = {ev["run"]["runId"]: ev for ev in events if ev.get("eventType") == "START"}
        for ev in events:
            if ev.get("eventType") in ("COMPLETE", "FAIL", "ABORT"):
                parent_id = ev.get("run", {}).get("facets", {}).get("parent_run_id", {}).get("runId")
                if parent_id: starts.pop(parent_id, None)
                starts.pop(ev["run"]["runId"], None)
        for run_id, ev in starts.items():
            gaps.append({"type": "OPEN_TRANSACTION", "run_id": run_id, "event": ev.get("event_type")})
        return gaps

    def resolve_spawns(self, parent_run_id: str) -> List[Dict[str, Any]]:
        events = self.store.load_all()
        resolved = []
        for ev in events:
            if ev.get("eventType") == "COMPLETE":
                parent_facet = ev.get("run", {}).get("facets", {}).get("parent_run_id", {})
                if parent_facet.get("runId") == parent_run_id:
                    req_facet = ev.get("run", {}).get("facets", {}).get("sdlc_req_keys", {})
                    resolved.append({"child_run_id": ev["run"]["runId"], "feature_id": req_facet.get("feature_id"), "edge": req_facet.get("edge"), "outputs": ev.get("outputs", []), "delta": ev.get("run", {}).get("facets", {}).get("sdlc_delta", {}).get("value", 0)})
        return resolved

    def iterate_edge(self, edge: str, feature_id: str, asset_path: Path, context: Dict[str, Any], iteration: int = 1, mode: str = "auto", checklist: List[Dict[str, Any]] = None, construct: bool = False) -> IterationRecord:
        """Run one iteration on a single edge as a Unit of Work transaction."""
        report = run_iteration(
            feature_id=feature_id,
            edge=edge,
            asset_path=asset_path,
            context=context,
            functors=self.functor_map,
            store=self.store,
            constraints=self.constraints,
            iteration=iteration,
            construct=construct,
            checklist=checklist
        )
        
        # Archive for audit
        self._archive_iteration(feature_id, edge, iteration, failed=not report.converged)
        
        return IterationRecord(
            edge=edge, 
            iteration=iteration, 
            report=report, 
            construct_result=report.construct_result
        )

    def run(self, asset_path: Path, context: Dict[str, Any] = None, feature_id: str = "unknown", feature_type: str = "feature", mode: str = "auto", construct: bool = False, config: Any = None) -> IterationRecord:
        """Legacy full graph traversal loop."""
        # Simple loop for backward compatibility
        records = self.run_edge(edge="design→code", feature_id=feature_id, asset_path=asset_path, context=context or {}, mode=mode, construct=construct)
        return records[0] if records else None

    def emit_event(self, event_type: str, feature: str, edge: str, data: Dict[str, Any]):
        project_name = self.constraints.get("project_id") or self.constraints.get("name") or self.constraints.get("project", {}).get("name", "imp_gemini")
        return self.store.emit(event_type=event_type, project=project_name, feature=feature, edge=edge, delta=data.get("delta"), data=data)

    def update_feature_vector(self, feature_id: str, edge: str, iteration: int, status: str, delta: int, asset_path: str = None, mode: str = None, run_id: str = None):
        import yaml
        import re
        fv_path = self.workspace_root / "features" / "active" / f"{feature_id}.yml"
        if fv_path.exists():
            data = yaml.safe_load(fv_path.read_text())
        else:
            data = {"feature": feature_id, "status": "in_progress", "trajectory": {}}
        parts = re.split(r"->|\u2192|\u2194", edge)
        traj_key = parts[-1].strip()
        data.setdefault("trajectory", {})[traj_key] = {"status": status, "delta": delta, "iteration": iteration, "updated_at": datetime.now(timezone.utc).isoformat(), "mode": mode, "engine_run_id": run_id}
        if asset_path: data["trajectory"][traj_key]["asset"] = asset_path
        fv_path.parent.mkdir(parents=True, exist_ok=True)
        fv_path.write_text(yaml.dump(data))

    def validate_invariants(self, events: List[Dict]) -> List[str]:
        violations = []
        last_deltas = {}
        for ev in events:
            if ev.get("event_type") == "iteration_completed":
                key = (ev.get("feature"), ev.get("edge"))
                delta = ev.get("delta")
                if delta is not None:
                    if key in last_deltas and delta > last_deltas[key]:
                        violations.append(f"INVARIANT_VIOLATION: Delta increased for {key}")
                    last_deltas[key] = delta
        return violations

    def run_edge(self, edge: str, feature_id: str, asset_path: Path, context: Dict[str, Any], mode: str = "auto", checklist: List[Dict[str, Any]] = None, construct: bool = False, max_iterations: int = 10, wall_timeout: int = 3600, stall_timeout: int = 300, parent_run_id: str = None) -> List[IterationRecord]:
        """Iterate on a single edge until convergence or budget exhaustion (Finding #1)."""
        import time
        base_iteration = context.get("iteration_count", 0); records = []
        start_time = time.time(); last_mtime, last_count = self.get_liveness_signal()
        last_activity = time.time()
        for i in range(1, max_iterations + 1):
            iter_num = base_iteration + i
            record = self.iterate_edge(edge=edge, feature_id=feature_id, asset_path=asset_path, context={**context, "parent_run_id": parent_run_id}, iteration=iter_num, mode=mode, checklist=checklist, construct=construct)
            records.append(record)
            
            # Legacy event emission for tests
            status = "converged" if record.report.converged else "iterating"
            if record.report.spawn: 
                status = "blocked"
                self.emit_event("compensation_triggered", feature=feature_id, edge=edge, data={"reason": "recursion_spawned"})
            
            self.emit_event("iteration_completed", feature=feature_id, edge=edge, data={"status": status, "delta": record.report.delta, "iteration": iter_num})
            self.update_feature_vector(feature_id, edge, iter_num, status, record.report.delta, str(asset_path), mode=mode)

            if record.report.converged or record.report.spawn: break
            if time.time() - start_time > wall_timeout: break
            cur_mtime, cur_count = self.get_liveness_signal()
            if cur_mtime > last_mtime or cur_count != last_count:
                last_mtime, last_count = cur_mtime, cur_count; last_activity = time.time()
            elif time.time() - last_activity > stall_timeout: break
        return records

    def run_tournament(self, edge: str, feature_id: str, context: Dict[str, Any], candidates: List[str]) -> IterationRecord:
        """Execute a parallel competitive tournament (ADR-S-018).
        Spawns N child vectors, evaluates them, and merges the winner.
        """
        # 1. Parallel Spawn
        transaction_id = str(uuid.uuid4())
        spawn_event = self.store.emit(
            event_type="feature_spawned",
            feature=feature_id,
            edge=edge,
            data={"children_count": len(candidates), "type": "tournament"},
            eventType="START"
        )
        parent_run_id = spawn_event["run"]["runId"]

        print(f"  [TOURNAMENT] Spawning {len(candidates)} parallel candidates...")
        child_runs = []
        for i, c_content in enumerate(candidates):
            child_id = f"{feature_id}-V{i+1}"
            child_ev = self.store.emit(
                event_type="feature_spawned",
                feature=child_id,
                data={"parent": feature_id, "type": "candidate"},
                parent_run_id=parent_run_id
            )
            child_runs.append({"id": child_id, "run_id": child_ev["run"]["runId"]})

        # 2. Tournament Arbitration
        print(f"  [TOURNAMENT] Arbitrating candidates...")
        # In this stateless pass, we assume candidates are already built or we build them adhoc
        # Route to specialized 'arbitrator_agent'
        arbitrator = self.functor_map.get("agent")
        res = arbitrator.evaluate("\n---\n".join(candidates), {
            **context,
            "edge": "tournament_arbitration",
            "mode": "arbitration"
        })

        # 3. Merge and Fold-back
        winner_idx = 0 # Default to first for stub
        if "winner_index" in res.reasoning.lower():
            # Heuristic extraction for now
            try: winner_idx = int(re.search(r"winner_index: (\d+)", res.reasoning).group(1))
            except: pass

        self.store.emit(
            event_type="iteration_completed",
            feature=feature_id,
            edge=edge,
            delta=res.delta,
            data={
                "status": "converged" if res.delta == 0 else "iterating",
                "merge_provenance": {
                    "winner": child_runs[winner_idx]["id"],
                    "candidates": [c["id"] for c in child_runs],
                    "selection_policy": "single_winner"
                }
            },
            eventType="COMPLETE",
            parent_run_id=parent_run_id
        )

        return IterationRecord(edge=edge, iteration=1, report=IterationReport(
            asset_path="", delta=res.delta, converged=(res.delta == 0), functor_results=[res]
        ))

    def verify_protocol(self, start_time: datetime) -> List[str]:
        events = self.store.load_all()
        recent = []
        for e in events:
            ts_str = e.get("eventTime") or e.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts >= start_time: recent.append(e)
                except: continue
        if not any(e.get("event_type") == "iteration_completed" for e in recent): 
            return ["No event emitted.", "state not updated"]
        return []
