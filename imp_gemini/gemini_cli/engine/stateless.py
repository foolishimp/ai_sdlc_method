# Implements: REQ-ITER-001, REQ-ITER-002, REQ-EVENT-001, REQ-EVENT-003
# Implements: REQ-ROBUST-001, REQ-ROBUST-002, REQ-ROBUST-007, REQ-F-ROBUST-001
"""
Pure stateless iteration logic for the Gemini Core.
Has zero knowledge of orchestration, loops, or persistence.
It reads State and Intent, then performs a single metabolic transformation.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import IterationReport, FunctorResult, Outcome, ConstructResult
from .guardrails import GuardrailEngine

from .ol_event import emit_ol_event, make_ol_event, iteration_started, iteration_completed

def run_iteration(
    feature_id: str,
    edge: str,
    asset_path: Path,
    context: Dict[str, Any],
    functors: Dict[str, Any],
    store: Any,
    constraints: Dict[str, Any],
    iteration: int = 1,
    construct: bool = False,
    checklist: List[Dict[str, Any]] = None
) -> IterationReport:
    """Perform a single stateless iteration."""
    events_path = store.workspace_root / "events" / "events.jsonl"
    project_name = constraints.get("project_id") or "imp_gemini"
    edge_run_id = context.get("edge_run_id")
    edge_correlation_id = context.get("edge_correlation_id")

    # 1. START transaction
    inputs = []
    if asset_path.exists():
        try:
            rel_path = str(asset_path.relative_to(store.workspace_root.parent))
        except ValueError:
            rel_path = asset_path.name
        inputs = [{"path": rel_path, "hash": store._hash_file(asset_path)}]

    iter_run_id = emit_ol_event(
        events_path,
        iteration_started(
            project=project_name,
            instance_id=feature_id,
            actor="genesis-engine",
            edge=edge,
            causation_id=edge_run_id,
            correlation_id=edge_correlation_id,
            payload={
                "feature": feature_id, 
                "edge": edge, 
                "iteration": iteration,
                "sdlc_manifest": {"inputs": inputs} # Backward compat or extra facet
            },
            inputs=[str(asset_path)] if asset_path.exists() else []
        )
    )

    # 2. Pre-flight Guardrails
    guardrails = GuardrailEngine(constraints)
    gr_results = guardrails.validate_pre_flight(edge, context)
    
    if any(not r.passed for r in gr_results):
        report = IterationReport(
            asset_path=str(asset_path),
            delta=-1,
            converged=False,
            functor_results=[],
            guardrail_results=gr_results
        )
        emit_ol_event(
            events_path,
            make_ol_event(
                "IterationFailed",
                edge,
                project_name,
                feature_id,
                "genesis-engine",
                causation_id=iter_run_id,
                correlation_id=edge_correlation_id,
                payload={"reason": "pre-flight guardrail failure", "feature": feature_id, "edge": edge}
            )
        )
        return report

    # 3. Construct (F_P)
    candidate = asset_path.read_text() if asset_path.exists() else ""
    construct_result = None
    if construct:
        # In the stateless model, construction is just another functor call
        # but one that is allowed to mutate the asset string.
        construct_result = ConstructResult(artifact=candidate, reasoning="Construction skipped (stub).")
        candidate = construct_result.artifact or candidate

    # 4. Evaluate
    results = []
    checks = checklist or [{"evaluator": f.__class__.__name__.replace("Functor", "").lower()} for f in functors.values()]
    
    for check in checks:
        eval_type = check.get("evaluator", "agent")
        f = functors.get(eval_type)
        if not f: continue
        
        res = f.evaluate(candidate, {
            **context, 
            **check, 
            "constraints": constraints,
            "iteration": iteration,
            "parent_run_id": iter_run_id
        })
        results.append(res)
        if res.next_candidate is not None:
            candidate = res.next_candidate

    # 5. Write Side-effects (Filesystem is the current state)
    if candidate and asset_path.exists() and asset_path.read_text() != candidate:
        asset_path.write_text(candidate)
    elif candidate and not asset_path.exists():
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(candidate)

    # 6. Post-flight Guardrails
    post_gr_results = guardrails.validate_post_flight(edge, candidate)
    gr_results.extend(post_gr_results)

    # 7. Compute Delta and Convergence
    total_delta = sum(r.delta for r in results)
    spawn_req = next((r.spawn for r in results if r.spawn), None)
    
    # Invalidation: Guardrail failure forces delta -1
    if any(not r.passed for r in post_gr_results):
        total_delta = 1

    converged = (total_delta == 0 and not spawn_req and all(r.passed for r in post_gr_results))

    # 8. COMPLETE transaction
    outputs = []
    if asset_path.exists():
        try:
            rel_path = str(asset_path.relative_to(store.workspace_root.parent))
        except ValueError:
            rel_path = asset_path.name
        outputs = [{"path": rel_path, "hash": store._hash_file(asset_path)}]

    status = "converged" if converged else "iterating"
    if spawn_req: status = "blocked"

    emit_ol_event(
        events_path,
        iteration_completed(
            project=project_name,
            instance_id=feature_id,
            actor="genesis-engine",
            edge=edge,
            delta=total_delta,
            causation_id=iter_run_id,
            correlation_id=edge_correlation_id,
            payload={
                "iteration": iteration,
                "converged": converged,
                "status": status,
                "feature": feature_id,
                "edge": edge,
                "delta": total_delta,
                "sdlc_manifest": {"outputs": outputs}
            },
            outputs=[str(asset_path)] if asset_path.exists() else []
        )
    )

    return IterationReport(
        asset_path=str(asset_path),
        delta=total_delta,
        converged=converged,
        functor_results=results,
        guardrail_results=gr_results,
        spawn=spawn_req,
        construct_result=construct_result
    )
