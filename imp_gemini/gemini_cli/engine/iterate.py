# Implements: REQ-CLI-003, REQ-CLI-005
"""
Universal Iteration Engine.
Executes the 'iterate' operation across any edge in the graph.
"""

from typing import Dict, Any, List, Protocol
from pathlib import Path

class Functor(Protocol):
    """Protocol for STL-style generic predicates (Evaluators)."""
    def evaluate(self, candidate: str, context: Dict) -> Dict[str, Any]:
        ...

class IterateEngine:
    """The Universal 'std::sort' of the SDLC."""
    
    def __init__(self, functors: List[Functor]):
        self.functors = functors

    def run(self, asset_path: Path, context: Dict, mode: str = "interactive") -> Dict[str, Any]:
        """
        Single application of iterate().
        Returns { 'next_candidate': str, 'delta': int, 'converged': bool }
        """
        # 1. Read current candidate
        candidate = asset_path.read_text() if asset_path.exists() else ""
        
        # 2. Run Generic Predicates (Evaluators)
        results = []
        for f in self.functors:
            # Skip human functors in headless mode
            if mode == "headless" and f.__class__.__name__ == "HumanFunctor":
                continue
            results.append(f.evaluate(candidate, context))
        
        # 3. Compute Delta and check for Spawn Requests
        total_delta = sum(r.get("delta", 0) for r in results if "delta" in r)
        spawn_request = next((r.get("spawn") for r in results if r.get("spawn")), None)
        
        return {
            "candidate": candidate,
            "delta": total_delta,
            "converged": total_delta == 0 and not spawn_request,
            "spawn": spawn_request,
            "reports": results
        }

    def validate_invariants(self, events: List[Dict]) -> List[str]:
        """
        Recursive Self-Validation: Check methodology invariants.
        Returns a list of violation messages.
        """
        violations = []
        
        # Invariant: Delta must not increase for the same feature/edge
        last_deltas = {}
        for ev in events:
            if ev.get("event_type") == "iteration_completed":
                key = (ev.get("feature"), ev.get("edge"))
                delta = ev.get("data", {}).get("delta")
                if key in last_deltas and delta > last_deltas[key]:
                    violations.append(f"INVARIANT_VIOLATION: Delta increased for {key}")
                last_deltas[key] = delta
                
        return violations
