
from typing import Dict, Any, List, Protocol, Optional
from pathlib import Path

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> Dict[str, Any]: ...

class CloudIterateEngine:
    """Universal algorithm running on Cloud Run."""
    def __init__(self, functors: List[Functor]):
        self.functors = functors

    def run(self, candidate: str, context: Dict, mode: str = "headless") -> Dict[str, Any]:
        results = []
        for f in self.functors:
            if mode == "headless" and f.__class__.__name__ == "HumanFunctor":
                continue
            results.append(f.evaluate(candidate, context))
        
        total_delta = sum(r.get("delta", 0) for r in results if "delta" in r)
        spawn_request = next((r.get("spawn") for r in results if r.get("spawn")), None)
        
        return {
            "delta": total_delta,
            "converged": total_delta == 0 and not spawn_request,
            "spawn": spawn_request,
            "reports": results
        }

    def validate_invariants(self, events: List[Dict]) -> List[str]:
        """Recursive Self-Validation: Check methodology invariants in the cloud stream."""
        violations = []
        last_deltas = {}
        for ev in events:
            if ev.get("event_type") == "iteration_completed":
                key = (ev.get("feature"), ev.get("edge"))
                delta = ev.get("delta")
                if key in last_deltas and delta > last_deltas[key]:
                    violations.append(f"INVARIANT_VIOLATION: Delta increased for {key}")
                last_deltas[key] = delta
        return violations
