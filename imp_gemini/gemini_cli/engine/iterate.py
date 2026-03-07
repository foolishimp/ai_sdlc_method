# Implements: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004, REQ-F-EDGE-001, REQ-EVAL-001, REQ-EVAL-002, REQ-F-EVAL-001, REQ-EVENT-002, REQ-EVENT-003, REQ-GRAPH-001, REQ-GRAPH-003
# Implements: REQ-EVENT-001, REQ-EVENT-004, REQ-ITER-001, REQ-ITER-002
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
from datetime import datetime, timezone

from .models import IterationRecord, IterationReport, FunctorResult, Outcome, ConstructResult
from .state import EventStore

class IterateEngine:
    """Universal iteration engine for all graph edges.
    Implements the Markov Blanket pattern via project fingerprinting and run archival.
    """
    
    def __init__(self, functor_map: Dict[str, Any], project_root: Path, constraints: Dict[str, Any] = None):
        self.functor_map = functor_map
        self.project_root = project_root
        self.workspace_root = project_root / ".ai-workspace"
        
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
        start_event = self.store.emit(event_type="iteration_started", project=context.get("project", "imp_gemini"), feature=feature_id, edge=edge, data={**context, "iteration": iteration, "mode": mode, "regime": "probabilistic" if mode == "prefect" else "deterministic"}, eventType="START", inputs=[asset_path] if asset_path.exists() else [])
        transaction_id = start_event["run"]["runId"]
        from .guardrails import GuardrailEngine
        guardrails = GuardrailEngine(self.constraints)
        gr_results = guardrails.validate_pre_flight(edge, context)
        if any(not r.passed for r in gr_results):
            report = IterationReport(asset_path=str(asset_path), delta=-1, converged=False, functor_results=[], guardrail_results=gr_results)
            self._archive_iteration(feature_id, edge, iteration, failed=True)
            self.store.emit(event_type="iteration_failed", project=context.get("project", "imp_gemini"), feature=feature_id, edge=edge, delta=-1, data={"reason": "pre-flight guardrail failure"}, eventType="FAIL", parent_run_id=transaction_id)
            return IterationRecord(edge=edge, iteration=iteration, report=report)
        construct_result = None
        candidate = asset_path.read_text() if asset_path.exists() else ""
        if construct:
            construct_result = ConstructResult(artifact=candidate, reasoning="Construction skipped (stub).")
            candidate = construct_result.artifact or candidate
        results = []
        checks = checklist if checklist else [{"evaluator": f.__class__.__name__.replace("Functor", "").lower()} for f in self.functor_map.values()]
        if mode == "prefect":
            from .prefect import run_sdlc_workflow
            agent_functor = next((f for f in self.functor_map.values() if f.__class__.__name__ == "ProbabilisticFunctor"), None) or self.functor_map.get("agent") or list(self.functor_map.values())[0]
            workflow_res = run_sdlc_workflow(edge=edge, feature_id=feature_id, asset_path=asset_path, context={**context, "checklist": checks, "parent_run_id": transaction_id}, agent_class=agent_functor.__class__, config=self.constraints)
            if workflow_res.get("status") == "success":
                from .models import FunctorResult, Outcome
                res_data = workflow_res.get("result_data", {})
                res = FunctorResult(name=f"prefect_{edge}_agent", outcome=Outcome.PASS if res_data.get("delta") == 0 else Outcome.FAIL, delta=res_data.get("delta", 0), reasoning=res_data.get("message", "Autonomous vector traversal complete."), next_candidate=None)
                results.append(res)
            else:
                report = IterationReport(asset_path=str(asset_path), delta=-1, converged=False, functor_results=[])
                self._archive_iteration(feature_id, edge, iteration, failed=True)
                self.store.emit(event_type="iteration_failed", project=context.get("project", "imp_gemini"), feature=feature_id, edge=edge, delta=-1, data={"reason": "prefect workflow failed"}, eventType="FAIL", parent_run_id=transaction_id)
                return IterationRecord(edge=edge, iteration=iteration, report=report)
        else:
            for check in checks:
                eval_type = check.get("evaluator", "agent")
                if eval_type == "deterministic_shell": eval_type = "deterministic"
                if eval_type == "sub_agent_eval": eval_type = "agent"
                f = self.functor_map.get(eval_type)
                if not f or (mode == "headless" and f.__class__.__name__ == "HumanFunctor"): continue
                res = f.evaluate(candidate, {**context, **check, "constraints": self.constraints, "iteration_count": iteration, "mode": mode, "parent_run_id": transaction_id})
                results.append(res)
                if res.next_candidate is not None: candidate = res.next_candidate
        if candidate and asset_path.exists() and asset_path.read_text() != candidate: asset_path.write_text(candidate)
        elif candidate and not asset_path.exists(): asset_path.parent.mkdir(parents=True, exist_ok=True); asset_path.write_text(candidate)
        total_delta = sum(r.delta for r in results); spawn_req = next((r.spawn for r in results if r.spawn), None)
        post_gr_results = guardrails.validate_post_flight(edge, candidate); gr_results.extend(post_gr_results)
        report = IterationReport(asset_path=str(asset_path), delta=total_delta if all(r.passed for r in post_gr_results) else -1, converged=(total_delta == 0 and not spawn_req and all(r.passed for r in post_gr_results)), functor_results=results, guardrail_results=gr_results, spawn=spawn_req, construct_result=construct_result)
        self._archive_iteration(feature_id, edge, iteration, failed=not report.converged)
        self.store.emit(event_type="iteration_completed", project=context.get("project", "imp_gemini"), feature=feature_id, edge=edge, delta=report.delta, data={"iteration": iteration, "converged": report.converged, "functor_results": [r.outcome.value for r in results]}, eventType="COMPLETE", outputs=[asset_path] if asset_path.exists() else [], parent_run_id=transaction_id)
        return IterationRecord(edge=edge, iteration=iteration, report=report, construct_result=construct_result)

    def run_edge(self, edge: str, feature_id: str, asset_path: Path, context: Dict[str, Any], mode: str = "auto", checklist: List[Dict[str, Any]] = None, construct: bool = False, max_iterations: int = 10, wall_timeout: int = 3600, stall_timeout: int = 300, parent_run_id: str = None) -> List[IterationRecord]:
        """Iterate on a single edge until convergence or budget exhaustion (Finding #1)."""
        base_iteration = context.get("iteration_count", 0); records = []
        start_time = time.time(); last_mtime, last_count = self.get_liveness_signal()
        last_activity = time.time(); active_spawns = []
        for i in range(1, max_iterations + 1):
            iter_num = base_iteration + i
            record = self.iterate_edge(edge=edge, feature_id=feature_id, asset_path=asset_path, context={**context, "parent_run_id": parent_run_id}, iteration=iter_num, mode=mode, checklist=checklist, construct=construct)
            records.append(record)
            if record.report.converged or record.report.spawn: break
            # Wall-clock timeout check (Finding #1)
            if time.time() - start_time > wall_timeout: break
            # Stall Detection via pluggable signal (Finding #4)
            cur_mtime, cur_count = self.get_liveness_signal()
            if cur_mtime > last_mtime or cur_count != last_count:
                last_mtime, last_count = cur_mtime, cur_count; last_activity = time.time()
            elif time.time() - last_activity > stall_timeout: break
        return records
