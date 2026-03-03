from typing import Dict, Any, List, Protocol, Optional, Type
from pathlib import Path
from datetime import datetime
from .models import IterationReport, FunctorResult, Outcome, SpawnRequest
from gemini_cloud.internal.yaml_loader import load_yaml

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

class CloudIterateEngine:
    def __init__(self, functors: Dict[str, Functor], config_root: Path = None):
        self.functors = functors  # e.g., {"F_D": DeterministicFunctor(), "F_P": VertexFunctor(), "F_H": HumanFunctor()}
        self.config_root = config_root or Path(__file__).parent.parent / "config"

    def _load_edge_config(self, edge: str) -> Dict[str, Any]:
        edge_config_path = self.config_root / "edge_params" / f"{edge}.yml"
        return load_yaml(edge_config_path)

    def run(self, asset_path: Path, feature: str, edge: str, context: Dict, mode: str = "interactive") -> IterationReport:
        # 1. Load Config
        edge_config = self._load_edge_config(edge)
        evaluator_types = edge_config.get("evaluators", ["agent"]) # default to agent (F_P)
        
        # 2. Load Context (Mock for now)
        # In a real implementation, this would load from GCS/Firestore/Vertex Search
        current_context = context.copy()
        current_context.update({"edge_config": edge_config})

        # 3. Construct Candidate
        # For now, we assume the candidate exists on disk or we generate a placeholder
        candidate = asset_path.read_text() if asset_path.exists() else f"# Next candidate for {feature} / {edge}\nImplements: REQ-001"
        
        # 4. Evaluator Chain
        results = []
        for eval_type in evaluator_types:
            functor_key = self._map_eval_to_functor(eval_type)
            functor = self.functors.get(functor_key)
            
            if not functor:
                continue
                
            if mode == "headless" and functor_key == "F_H":
                continue
                
            res = functor.evaluate(candidate, current_context)
            results.append(res)
            
            # Escalation Logic (eta_D->P, eta_P->H)
            if res.outcome == Outcome.FAIL and functor_key == "F_D" and "F_P" in self.functors:
                # Escalation from D to P
                res_p = self.functors["F_P"].evaluate(candidate, current_context)
                results.append(res_p)
                if res_p.outcome == Outcome.PASS:
                    # P resolved the ambiguity D had
                    pass
            
            if res.outcome == Outcome.FAIL and functor_key == "F_P" and mode == "interactive" and "F_H" in self.functors:
                # Escalation from P to H
                res_h = self.functors["F_H"].evaluate(candidate, current_context)
                results.append(res_h)

        # 5. Convergence Check
        total_delta = sum(r.delta for r in results)
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        
        # Determine if we converged
        converged = (total_delta == 0 and not spawn_req)
        
        return IterationReport(
            asset_path=str(asset_path),
            delta=total_delta,
            converged=converged,
            functor_results=results,
            spawn=spawn_req
        )

    def _map_eval_to_functor(self, eval_type: str) -> str:
        mapping = {
            "deterministic": "F_D",
            "agent": "F_P",
            "human": "F_H"
        }
        return mapping.get(eval_type, "F_P")

    def validate_invariants(self, events: List[Dict]) -> List[str]:
        violations, last_deltas = [], {}
        for ev in events:
            if ev.get("event_type") == "iteration_completed":
                key = (ev.get("feature"), ev.get("edge"))
                delta = ev.get("delta")
                if delta is not None:
                    if key in last_deltas and delta > last_deltas[key]:
                        violations.append(f"INVARIANT_VIOLATION: Delta increased for {key}")
                    last_deltas[key] = delta
        return violations
