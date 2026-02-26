from typing import Dict, Any, List, Protocol, Optional
from pathlib import Path
from .models import IterationReport, FunctorResult, Outcome

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

class IterateEngine:
    def __init__(self, functors: List[Functor], constraints: Dict[str, Any] = None):
        self.functors = functors
        self.constraints = constraints or {}

    def run(self, asset_path: Path, context: Dict, mode: str = "interactive") -> IterationReport:
        candidate = asset_path.read_text() if asset_path.exists() else ""
        results = []
        for f in self.functors:
            if mode == "headless" and f.__name__ == "HumanFunctor": continue
            results.append(f.evaluate(candidate, context))
        total_delta = sum(r.delta for r in results)
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        return IterationReport(asset_path=str(asset_path), delta=total_delta, converged=(total_delta == 0 and not spawn_req), functor_results=results, spawn=spawn_req)

    def validate_invariants(self, events: List[Dict]) -> List[str]:
        violations, last_deltas = [], {}
        for ev in events:
            if ev.get("event_type") == "iteration_completed":
                key, delta = (ev.get("feature"), ev.get("edge")), ev.get("delta")
                if delta is not None:
                    if key in last_deltas and delta > last_deltas[key]: violations.append(f"INVARIANT_VIOLATION: Delta increased for {key}")
                    last_deltas[key] = delta
        return violations
