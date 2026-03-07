# Implements: REQ-ITER-001, REQ-ROBUST-002
"""
Optional Prefect executor for long-running Gemini iterations.
This is a deployment mode, not a structural dependency of the engine.
"""

from typing import Dict, Any, List
from pathlib import Path
from ..stateless import run_iteration
from ..models import IterationRecord, IterationReport

try:
    from prefect import flow, task
except ImportError:
    # Prefect not installed - this executor will fail if called
    flow = lambda **kwargs: lambda func: func
    task = lambda **kwargs: lambda func: func

@task(name="stateless_iteration_pass")
def prefect_iteration_task(
    feature_id: str,
    edge: str,
    asset_path: Path,
    context: Dict[str, Any],
    functors: Dict[str, Any],
    store: Any,
    constraints: Dict[str, Any],
    iteration: int
) -> IterationReport:
    """Wrapper task for the stateless run_iteration function."""
    return run_iteration(
        feature_id=feature_id,
        edge=edge,
        asset_path=asset_path,
        context=context,
        functors=functors,
        store=store,
        constraints=constraints,
        iteration=iteration
    )

@flow(name="gemini_edge_traversal")
def run_with_prefect(
    edge: str,
    feature_id: str,
    asset_path: Path,
    context: Dict[str, Any],
    functors: Dict[str, Any],
    store: Any,
    constraints: Dict[str, Any],
    max_iterations: int = 10
) -> List[IterationRecord]:
    """Prefect flow that manages the loop over the stateless engine."""
    records = []
    base_iteration = context.get("iteration_count", 0)
    
    for i in range(1, max_iterations + 1):
        iter_num = base_iteration + i
        report = prefect_iteration_task(
            feature_id=feature_id,
            edge=edge,
            asset_path=asset_path,
            context=context,
            functors=functors,
            store=store,
            constraints=constraints,
            iteration=iter_num
        )
        
        record = IterationRecord(edge=edge, iteration=iter_num, report=report)
        records.append(record)
        
        if report.converged or report.spawn:
            break
            
    return records
