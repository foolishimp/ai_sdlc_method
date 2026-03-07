# Implements: REQ-ITER-001, REQ-ITER-002, REQ-EVENT-001, REQ-EVENT-003
"""
Pure stateless iteration logic for the Gemini Core.
Has zero knowledge of orchestration (Prefect, loops, or persistence).
It reads State and Intent, then performs a single metabolic transformation.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import IterationReport, FunctorResult, Outcome, ConstructResult
from .guardrails import GuardrailEngine

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
    """Perform a single stateless iteration.
    
    This is the core 'Metabolism' of the system.
    """
    # 1. START transaction
    start_event = store.emit(
        event_type="iteration_started",
        feature=feature_id,
        edge=edge,
        data={**context, "iteration": iteration},
        eventType="START",
        inputs=[asset_path] if asset_path.exists() else []
    )
    transaction_id = start_event["run"]["runId"]

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
        store.emit(
            event_type="iteration_failed",
            feature=feature_id,
            edge=edge,
            delta=-1,
            data={"reason": "pre-flight guardrail failure"},
            eventType="FAIL",
            parent_run_id=transaction_id
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
            "parent_run_id": transaction_id
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
    store.emit(
        event_type="iteration_completed",
        feature=feature_id,
        edge=edge,
        delta=total_delta,
        data={
            "iteration": iteration,
            "converged": converged,
            "functor_results": [r.outcome.value for r in results]
        },
        eventType="COMPLETE",
        outputs=[asset_path] if asset_path.exists() else [],
        parent_run_id=transaction_id
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
