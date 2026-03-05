from typing import Dict, Any, List, Protocol, Optional, Type
from pathlib import Path
import time
import shutil
from datetime import datetime, timezone
from .models import IterationReport, FunctorResult, Outcome, SpawnRequest
from gemini_cloud.internal.yaml_loader import load_yaml

class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

class CloudIterateEngine:
    """Cloud-native iteration engine following the Canonical Invocation Model.
    Implements Markov Blanket pattern via project fingerprinting and run archival.
    """
    
    def __init__(self, functors: Dict[str, Functor], project_root: Path, config_root: Path = None):
        self.functors = functors  # e.g., {"F_D": DeterministicFunctor(), "F_P": VertexFunctor(), "F_H": HumanFunctor()}
        self.project_root = project_root
        self.workspace_root = project_root / ".ai-workspace"
        self.config_root = config_root or Path(__file__).parent.parent / "config"

    def _get_project_fingerprint(self) -> tuple[float, int]:
        """Return (latest_mtime, total_file_count) for key project locations.
        Implementation of the Markov Blanket boundary check.
        """
        latest = 0.0
        count = 0
        # For Cloud implementation, we still check the local checkout/mirror
        sentinel_dirs = [
            self.project_root / "gemini_cloud", # Cloud source dir
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
        # Cloud runs archived locally for now, in real impl could sync to GCS
        archive_dir = self.project_root / "runs" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy key directories (Markov Blanket)
        for d in ["gemini_cloud", "tests", "specification", ".ai-workspace"]:
            src = self.project_root / d
            if src.exists():
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

    def _load_edge_config(self, edge: str) -> Dict[str, Any]:
        edge_config_path = self.config_root / "edge_params" / f"{edge}.yml"
        if not edge_config_path.exists():
            return {"evaluators": ["agent"]}
        return load_yaml(edge_config_path)

    def run(self, asset_path: Path, feature: str, edge: str, context: Dict, mode: str = "interactive", iteration: int = 1) -> IterationReport:
        # 1. Load Config
        edge_config = self._load_edge_config(edge)
        evaluator_types = edge_config.get("evaluators", ["agent"])
        
        # 2. Load Context
        current_context = context.copy()
        current_context.update({"edge_config": edge_config})

        # 3. Construct Candidate
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
                res_p = self.functors["F_P"].evaluate(candidate, current_context)
                results.append(res_p)
            
            if res.outcome == Outcome.FAIL and functor_key == "F_P" and mode == "interactive" and "F_H" in self.functors:
                res_h = self.functors["F_H"].evaluate(candidate, current_context)
                results.append(res_h)

        # 5. Convergence Check
        total_delta = sum(r.delta for r in results)
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        converged = (total_delta == 0 and not spawn_req)
        
        report = IterationReport(
            asset_path=str(asset_path),
            delta=total_delta,
            converged=converged,
            functor_results=results,
            spawn=spawn_req
        )
        
        # 6. Archive Run
        self._archive_iteration(feature, edge, iteration, failed=not converged)
        
        return report

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
