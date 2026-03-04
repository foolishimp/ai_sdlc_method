# Implements: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004, REQ-F-EDGE-001, REQ-EVAL-001, REQ-EVAL-002, REQ-F-EVAL-001, REQ-EVENT-002, REQ-EVENT-003, REQ-GRAPH-001, REQ-GRAPH-003
# Implements: REQ-EVENT-001, REQ-EVENT-004, REQ-F-EVENT-001, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003
import yaml
import re
import uuid
from typing import Dict, Any, List, Protocol, Optional
from pathlib import Path
from datetime import datetime, timezone
from .models import (
    IterationReport, 
    FunctorResult, 
    Outcome, 
    GuardrailResult, 
    EngineConfig, 
    IterationRecord, 
    ConstructResult
)
from .state import EventStore
from .config_loader import ConfigLoader
from .topology import GraphTopology

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

class IterateEngine:
    def __init__(self, functor_map: Dict[str, Functor] = None, constraints: Dict[str, Any] = None, project_root: Path = None):
        self.functor_map = functor_map or {}
        self.project_root = project_root or Path.cwd()
        # Find workspace root (parent of .ai-workspace)
        if (self.project_root / ".ai-workspace").exists():
            self.workspace_root = self.project_root / ".ai-workspace"
        elif self.project_root.name == ".ai-workspace":
            self.workspace_root = self.project_root
            self.project_root = self.workspace_root.parent
        else:
            self.workspace_root = self.project_root / ".ai-workspace"
        
        if constraints is None:
            loader = ConfigLoader(self.workspace_root)
            self.constraints = loader.constraints
        else:
            self.constraints = constraints
            
        self.store = EventStore(self.workspace_root)

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
        """Run one iteration on a single edge."""
        
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
        
        for check in checks:
            eval_type = check.get("evaluator", "agent")
            if eval_type == "deterministic_shell": eval_type = "deterministic"
            if eval_type == "sub_agent_eval": eval_type = "agent"
            
            f = self.functor_map.get(eval_type)
            if not f:
                continue
                
            # Skip human functors in headless mode
            if mode == "headless" and f.__class__.__name__ == "HumanFunctor":
                continue
                
            check_context = {**context, **check, "constraints": self.constraints, "iteration_count": iteration, "mode": mode}
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
        max_iterations: int = 10
    ) -> List[IterationRecord]:
        """Iterate on a single edge until convergence or budget exhaustion."""
        base_iteration = context.get("iteration_count", 0)
        records = []
        for i in range(1, max_iterations + 1):
            current_iteration = base_iteration + i
            
            # Emit IterationStarted
            self.emit_event("iteration_started", feature=feature_id, edge=edge, data={"iteration": current_iteration, "mode": mode})

            record = self.iterate_edge(
                edge=edge,
                feature_id=feature_id,
                asset_path=asset_path,
                context=context,
                iteration=current_iteration,
                mode=mode,
                checklist=checklist,
                construct=construct
            )
            records.append(record)
            
            # Emit event
            if record.report.spawn:
                # If recursion is requested, we treat it as an 'iteration_completed' with 'blocked' status
                status = "blocked"
                event = self.emit_event(
                    "iteration_completed", 
                    feature=feature_id, 
                    edge=edge, 
                    data={"status": status, "delta": record.report.delta, "iteration": current_iteration, "mode": mode}
                )
            elif any(not g.passed for g in record.report.guardrail_results):
                status = "failed"
                event = self.emit_event(
                    "iteration_failed", 
                    feature=feature_id, 
                    edge=edge, 
                    data={"reason": "Guardrail validation failed", "iteration": current_iteration, "mode": mode}
                )
            else:
                status = "converged" if record.report.converged else "iterating"
                event = self.emit_event(
                    "iteration_completed", 
                    feature=feature_id, 
                    edge=edge, 
                    data={"status": status, "delta": record.report.delta, "iteration": current_iteration, "mode": mode}
                )
            
            run_id = event.get("run", {}).get("runId", "unknown")
            
            # Update feature vector
            self.update_feature_vector(feature_id, edge, current_iteration, status, record.report.delta, str(asset_path), mode=mode, run_id=run_id)

            if record.report.spawn:
                # Saga Invariant: Trigger Compensation
                self.emit_event(
                    "compensation_triggered",
                    feature=feature_id,
                    edge=edge,
                    data={"reason": "RECURSION requested by evaluator", "spawn": record.report.spawn.__dict__}
                )
                break

            if record.report.converged:
                self.emit_event("edge_converged", feature=feature_id, edge=edge, data={"mode": mode, "delta": record.report.delta})
                break
                
        return records

    def run(
        self,
        feature_id: str,
        feature_type: str,
        asset_path: Path,
        context: Dict[str, Any] = None,
        mode: str = "auto",
        construct: bool = False,
        config: EngineConfig = None
    ) -> List[IterationRecord]:
        """Full graph traversal loop."""
        if context is None:
            context = {}
            
        # Load profile
        loader = ConfigLoader(self.workspace_root)
        profile_name = "standard" # Default
        # In a real implementation, we would select profile based on feature_type
        
        profile_path = self.workspace_root.parent / "gemini_cli" / "config" / "profiles" / f"{profile_name}.yml"
        if profile_path.exists():
            with open(profile_path, "r") as f:
                profile = yaml.safe_load(f)
        else:
            profile = {"graph": {"include": ["intent\u2192requirements", "requirements\u2192design", "design\u2192code", "code\u2194unit_tests"]}}

        topology = GraphTopology(self.workspace_root)
        all_records = []
        accumulated_context = context.copy()
        
        # Traverse edges defined in profile
        for edge in profile.get("graph", {}).get("include", []):
            print(f"\n>>> RUNNING EDGE: {edge}")
            
            # Resolve checklist for this edge
            edge_config_path = topology.get_edge_config_path(edge)
            edge_config = {}
            if edge_config_path and edge_config_path.exists():
                with open(edge_config_path, "r") as f:
                    edge_config = yaml.safe_load(f) or {}
            
            resolved_checklist = loader.resolve_checklist(edge_config)
            
            records = self.run_edge(
                edge=edge,
                feature_id=feature_id,
                asset_path=asset_path, # In a real implementation, asset_path might change per edge
                context=accumulated_context,
                mode=mode,
                checklist=resolved_checklist,
                construct=construct,
                max_iterations=config.max_iterations_per_edge if config else 10
            )
            all_records.extend(records)
            
            if not records or not records[-1].report.converged:
                print(f"Edge {edge} failed to converge. Stopping traversal.")
                break
                
            # Context Accumulation (REQ-F-FPC-003)
            if asset_path.exists():
                accumulated_context[f"{edge}_artifact"] = asset_path.read_text()

        return all_records

    # Legacy run for backward compatibility
    def old_run(self, asset_path: Path, context: Dict, mode: str = "interactive", checklist: List[Dict[str, Any]] = None) -> IterationReport:
        edge = context.get("edge", "")
        feature_id = context.get("feature_id", "unknown")
        iteration = context.get("iteration_count", 0) + 1
        record = self.iterate_edge(edge, feature_id, asset_path, context, iteration, mode, checklist)
        return record.report

    def emit_event(self, event_type: str, feature: str, edge: str, data: Dict[str, Any]):
        project_name = self.constraints.get("project", {}).get("name", "unknown")
        return self.store.emit(
            event_type=event_type,
            project=project_name,
            feature=feature,
            edge=edge,
            delta=data.get("delta"),
            data=data
        )

    def update_feature_vector(self, feature_id: str, edge: str, iteration: int, status: str, delta: int, asset_path: str = None, mode: str = None, run_id: str = None):
        fv_path = self.workspace_root / "features" / "active" / f"{feature_id}.yml"
        
        if fv_path.exists():
            with open(fv_path, "r") as f:
                data = yaml.safe_load(f)
        else:
            data = {
                "feature": feature_id,
                "status": "in_progress",
                "trajectory": {}
            }
        
        # Map edge to trajectory key
        parts = re.split(r"->|\u2192|\u2194", edge)
        traj_key = parts[-1].strip()
        
        data.setdefault("trajectory", {})[traj_key] = {
            "status": status,
            "delta": delta,
            "iteration": iteration,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "engine_run_id": run_id
        }
        if asset_path:
            data["trajectory"][traj_key]["asset"] = asset_path
            
        if status == "converged":
            data["trajectory"][traj_key]["converged_at"] = datetime.now(timezone.utc).isoformat()
            
            # Check if all core nodes in standard profile are converged
            required_edges = [
                "requirements", "feature_decomp", "design", "module_decomp", 
                "basis_proj", "code", "unit_tests"
            ]
            all_core_converged = True
            for req_edge in required_edges:
                edge_data = data["trajectory"].get(req_edge, {})
                if not isinstance(edge_data, dict) or edge_data.get("status") != "converged":
                    all_core_converged = False
                    break
            
            if all_core_converged:
                data["status"] = "converged"
            else:
                data["status"] = "in_progress" # Ensure it stays in progress

        fv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(fv_path, "w") as f:
            yaml.dump(data, f)

    def verify_protocol(self, start_time: datetime) -> List[str]:
        """Checks if the required events were emitted since start_time."""
        events = self.store.load_all()
        recent_events = []
        for e in events:
            ts_str = e.get("eventTime")
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= start_time:
                    recent_events.append(e)
        
        gaps = []
        has_iteration_event = False
        for e in recent_events:
            type_facet = e.get("run", {}).get("facets", {}).get("sdlc_event_type", {})
            if type_facet.get("type") == "iteration_completed":
                has_iteration_event = True
                break
            # Fallback for simple event format
            if e.get("event_type") == "iteration_completed":
                has_iteration_event = True
                break
                
        if not has_iteration_event:
            gaps.append("No event emitted.")
        
        if not recent_events:
            gaps.append("Feature vector state not updated.")
        
        return gaps

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
