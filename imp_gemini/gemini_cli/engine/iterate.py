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
        
        # Load constraints if not provided
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
            if not d.exists():
                continue
            try:
                mt = d.stat().st_mtime
                if mt > latest:
                    latest = mt
                for child in d.iterdir():
                    count += 1
                    try:
                        mt = child.stat().st_mtime
                        if mt > latest:
                            latest = mt
                    except OSError:
                        continue
            except OSError:
                continue
        return latest, count

    def _archive_iteration(self, feature_id: str, edge: str, iteration: int, failed: bool = False):
        """Archive the project state for this iteration to ensure audit reproducibility."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        status = "FAILED" if failed else "OK"
        archive_name = f"run_{feature_id}_{edge.replace('→', '_').replace('↔', '_')}_iter{iteration}_{status}_{ts}"
        archive_dir = self.project_root / "runs" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy key directories (Markov Blanket)
        for d in ["code", "tests", "specification", ".ai-workspace"]:
            src = self.project_root / d
            if src.exists():
                # Avoid recursive copy
                shutil.copytree(src, archive_dir / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "runs"), dirs_exist_ok=True)
        
        # Update latest symlink
        latest = self.project_root / "runs" / "latest"
        latest.parent.mkdir(parents=True, exist_ok=True)
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        try:
            latest.symlink_to(archive_dir.name)
        except Exception:
            pass
            
        return archive_dir

    def detect_integrity_gaps(self) -> List[Dict[str, Any]]:
        """Find discrepancies between the Event Ledger (committed) and Filesystem (actual)."""
        events = self.store.load_all()
        last_committed_hashes = {}
        
        # Replay ledger to find the last committed hash for each artifact
        for ev in events:
            if ev.get("eventType") == "COMPLETE":
                for output in ev.get("outputs", []):
                    name = output.get("name")
                    facets = output.get("facets", {})
                    h = facets.get("sdlc:contentHash", {}).get("hash")
                    if name and h:
                        last_committed_hashes[name] = h
        
        gaps = []
        for rel_path, committed_hash in last_committed_hashes.items():
            full_path = self.project_root / rel_path
            if not full_path.exists():
                gaps.append({"path": rel_path, "type": "MISSING_ARTIFACT", "expected": committed_hash})
                continue
                
            actual_hash = self.store._hash_file(full_path)
            if actual_hash != committed_hash:
                gaps.append({
                    "path": rel_path, 
                    "type": "UNCOMMITTED_CHANGE", 
                    "expected": committed_hash, 
                    "actual": actual_hash
                })
        
        # Check for open transactions (START without COMPLETE/FAIL)
        starts = {ev["run"]["runId"]: ev for ev in events if ev.get("eventType") == "START"}
        for ev in events:
            if ev.get("eventType") in ("COMPLETE", "FAIL"):
                parent_id = ev.get("run", {}).get("facets", {}).get("parent_run_id", {}).get("runId")
                if parent_id:
                    starts.pop(parent_id, None)
                # Also pop direct runId
                starts.pop(ev["run"]["runId"], None)
        
        for run_id, ev in starts.items():
            gaps.append({"type": "OPEN_TRANSACTION", "run_id": run_id, "event": ev.get("event_type")})
            
        return gaps

    def iterate_edge(
        self,
        edge: str,
        feature_id: str,
        asset_path: Path,
        context: Dict[str, Any],
        iteration: int = 1,
        mode: str = "auto",
        checklist: List[Dict[str, Any]] = None,
        construct: bool = False
    ) -> IterationRecord:
        """Run one iteration on a single edge as a Unit of Work transaction."""
        
        # 0. Transaction BEGIN
        start_event = self.store.emit(
            event_type="iteration_started",
            project=context.get("project", "imp_gemini"),
            feature=feature_id,
            edge=edge,
            data={**context, "iteration": iteration, "mode": mode, "regime": "probabilistic" if mode == "prefect" else "deterministic"},
            eventType="START",
            inputs=[asset_path] if asset_path.exists() else []
        )
        transaction_id = start_event["run"]["runId"]

        # 1. Run Guardrails (Pre-flight)
        from .guardrails import GuardrailEngine
        guardrails = GuardrailEngine(self.constraints)
        gr_results = guardrails.validate_pre_flight(edge, context)
        
        if any(not r.passed for r in gr_results):
            report = IterationReport(
                asset_path=str(asset_path),
                delta=-1,
                converged=False,
                functor_results=[],
                guardrail_results=gr_results
            )
            self._archive_iteration(feature_id, edge, iteration, failed=True)
            self.store.emit(
                event_type="iteration_failed",
                project=context.get("project", "imp_gemini"),
                feature=feature_id,
                edge=edge,
                delta=-1,
                data={"reason": "pre-flight guardrail failure", "results": [r.passed for r in gr_results]},
                eventType="FAIL",
                parent_run_id=transaction_id
            )
            return IterationRecord(edge=edge, iteration=iteration, report=report)

        # 2. Construct phase (Stub for now)
        construct_result = None
        candidate = asset_path.read_text() if asset_path.exists() else ""
        
        if construct:
            # TODO: Implement actual construction logic
            construct_result = ConstructResult(artifact=candidate, reasoning="Construction skipped (stub).")
            candidate = construct_result.artifact or candidate

        # 3. Evaluate each check
        results = []
        checks = checklist if checklist else [{"evaluator": f.__class__.__name__.replace("Functor", "").lower()} for f in self.functor_map.values()]
        
        if mode == "prefect":
            # Run the entire edge iteration as a Prefect Flow (Markov Autonomous Vector)
            from .prefect import run_sdlc_workflow
            
            # Identify the primary probabilistic agent for this edge
            agent_functor = next((f for f in self.functor_map.values() if f.__class__.__name__ == "ProbabilisticFunctor"), None)
            if not agent_functor:
                # Fallback to 'agent' key or first functor
                agent_functor = self.functor_map.get("agent") or list(self.functor_map.values())[0]

            workflow_res = run_sdlc_workflow(
                edge=edge,
                feature_id=feature_id,
                asset_path=asset_path,
                context={**context, "checklist": checks, "parent_run_id": transaction_id},
                agent_class=agent_functor.__class__,
                config=self.constraints
            )
            # Map back from workflow result
            if workflow_res.get("status") == "success":
                from .models import FunctorResult, Outcome
                res_data = workflow_res.get("result_data", {})
                res = FunctorResult(
                    name=f"prefect_{edge}_agent",
                    outcome=Outcome.PASS if res_data.get("delta") == 0 else Outcome.FAIL,
                    delta=res_data.get("delta", 0),
                    reasoning=res_data.get("message", "Autonomous vector traversal complete."),
                    next_candidate=None
                )
                results.append(res)
            else:
                report = IterationReport(asset_path=str(asset_path), delta=-1, converged=False, functor_results=[])
                self._archive_iteration(feature_id, edge, iteration, failed=True)
                self.store.emit(
                    event_type="iteration_failed",
                    project=context.get("project", "imp_gemini"),
                    feature=feature_id,
                    edge=edge,
                    delta=-1,
                    data={"reason": "prefect workflow failed", "error": workflow_res.get("error")},
                    eventType="FAIL",
                    parent_run_id=transaction_id
                )
                return IterationRecord(edge=edge, iteration=iteration, report=report)
        else:
            for check in checks:
                eval_type = check.get("evaluator", "agent")
                if eval_type == "deterministic_shell": eval_type = "deterministic"
                if eval_type == "sub_agent_eval": eval_type = "agent"
                
                f = self.functor_map.get(eval_type)
                if not f:
                    continue
                    
                if mode == "headless" and f.__class__.__name__ == "HumanFunctor":
                    continue
                    
                check_context = {**context, **check, "constraints": self.constraints, "iteration_count": iteration, "mode": mode, "parent_run_id": transaction_id}
                res = f.evaluate(candidate, check_context)
                results.append(res)
                
                if res.next_candidate is not None:
                    candidate = res.next_candidate
        
        # Write back if changed
        if candidate and asset_path.exists() and asset_path.read_text() != candidate:
            asset_path.write_text(candidate)
        elif candidate and not asset_path.exists():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_text(candidate)

        total_delta = sum(r.delta for r in results)
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        
        # 4. Run Post-flight Guardrails
        post_gr_results = guardrails.validate_post_flight(edge, candidate)
        gr_results.extend(post_gr_results)
        
        report = IterationReport(
            asset_path=str(asset_path),
            delta=total_delta if all(r.passed for r in post_gr_results) else -1,
            converged=(total_delta == 0 and not spawn_req and all(r.passed for r in post_gr_results)),
            functor_results=results,
            guardrail_results=gr_results,
            spawn=spawn_req,
            construct_result=construct_result
        )
        
        # 5. Transaction COMMIT
        self._archive_iteration(feature_id, edge, iteration, failed=not report.converged)
        self.store.emit(
            event_type="iteration_completed",
            project=context.get("project", "imp_gemini"),
            feature=feature_id,
            edge=edge,
            delta=report.delta,
            data={
                "converged": report.converged, 
                "functor_results": [r.outcome.value for r in results],
                "guardrail_results": [r.passed for r in post_gr_results]
            },
            eventType="COMPLETE",
            outputs=[asset_path] if asset_path.exists() else [],
            parent_run_id=transaction_id
        )
        
        return IterationRecord(
            edge=edge, 
            iteration=iteration, 
            report=report, 
            construct_result=construct_result
        )

    def run_edge(
        self,
        edge: str,
        feature_id: str,
        asset_path: Path,
        context: Dict[str, Any],
        mode: str = "auto",
        checklist: List[Dict[str, Any]] = None,
        construct: bool = False,
        max_iterations: int = 10,
        stall_timeout: int = 300
    ) -> List[IterationRecord]:
        """Iterate on a single edge until convergence or budget exhaustion.
        Implements semantic stall detection via project fingerprinting.
        """
        base_iteration = context.get("iteration_count", 0)
        records = []
        
        last_mtime, last_count = self._get_project_fingerprint()
        last_activity = time.time()
        
        for i in range(1, max_iterations + 1):
            iter_num = base_iteration + i
            
            # Run one iteration
            record = self.iterate_edge(
                edge=edge,
                feature_id=feature_id,
                asset_path=asset_path,
                context=context,
                iteration=iter_num,
                mode=mode,
                checklist=checklist,
                construct=construct
            )
            records.append(record)
            
            if record.report.converged:
                break
                
            if record.report.spawn:
                break
                
            # Semantic Stall Detection
            cur_mtime, cur_count = self._get_project_fingerprint()
            if cur_mtime > last_mtime or cur_count != last_count:
                last_mtime = cur_mtime
                last_count = cur_count
                last_activity = time.time()
            elif time.time() - last_activity > stall_timeout:
                # Delta unchanged AND no project file changes = STALL
                break
                
        return records
