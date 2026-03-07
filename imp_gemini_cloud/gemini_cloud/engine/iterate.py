from typing import Dict, Any, List, Protocol, Optional, Type, runtime_checkable
from pathlib import Path
import time
import shutil
from datetime import datetime, timezone
from .models import IterationReport, FunctorResult, Outcome, SpawnRequest
from .guardrails import GuardrailEngine, GuardrailResult
from gemini_cloud.internal.yaml_loader import load_yaml

@runtime_checkable
class Functor(Protocol):
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult: ...

@runtime_checkable
class ArchiveStore(Protocol):
    def archive_iteration(self, feature_id: str, edge: str, iteration: int, failed: bool = False) -> str: ...

@runtime_checkable
class LivenessSignal(Protocol):
    def get_signal(self) -> tuple[float, int]: ...

class FilesystemLiveness(LivenessSignal):
    def __init__(self, roots: List[Path]):
        self.roots = roots
    def get_signal(self) -> tuple[float, int]:
        latest = 0.0
        count = 0
        for d in self.roots:
            if not d.exists(): continue
            try:
                mt = d.stat().st_mtime
                if mt > latest: latest = mt
                for child in d.iterdir():
                    count += 1
                    try:
                        mt = child.stat().st_mtime
                        if mt > latest: latest = mt
                    except OSError: continue
            except OSError: continue
        return latest, count

class LocalArchiveStore(ArchiveStore):
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def archive_iteration(self, feature_id: str, edge: str, iteration: int, failed: bool = False) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        status = "FAILED" if failed else "OK"
        archive_name = f"run_{feature_id}_{edge.replace('→', '_').replace('↔', '_')}_iter{iteration}_{status}_{ts}"
        archive_dir = self.project_root / "runs" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        for d in ["gemini_cloud", "tests", "specification", ".ai-workspace"]:
            src = self.project_root / d
            if src.exists():
                shutil.copytree(src, archive_dir / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "runs"), dirs_exist_ok=True)
        latest = self.project_root / "runs" / "latest"
        latest.parent.mkdir(parents=True, exist_ok=True)
        if latest.exists() or latest.is_symlink(): latest.unlink()
        try: latest.symlink_to(archive_dir.name)
        except Exception: pass
        return str(archive_dir)

class CloudIterateEngine:
    """Stateless Cloud-native iteration engine (Reactor Pattern).
    Follows the Canonical Invocation Model: (State, Intent) -> State'
    """
    
    def __init__(
        self, 
        functors: Dict[str, Functor], 
        project_root: Path, 
        config_root: Path = None, 
        store = None,
        constraints: Dict[str, Any] = None,
        archiver: ArchiveStore = None,
        liveness: LivenessSignal = None
    ):
        self.functors = functors
        self.project_root = project_root
        self.workspace_root = project_root / ".ai-workspace"
        self.config_root = config_root or Path(__file__).parent.parent / "config"
        self.store = store
        self.constraints = constraints or {}
        self.guardrails = GuardrailEngine(self.constraints)
        self.archiver = archiver or LocalArchiveStore(project_root)
        self.liveness = liveness or FilesystemLiveness([
            project_root / "gemini_cloud",
            project_root / "tests",
            project_root / "specification",
            self.workspace_root / "events",
            self.workspace_root / "features",
        ])

    def run_once(self, asset_path: Path, feature: str, edge: str, context: Dict, mode: str = "interactive", iteration: int = 1) -> IterationReport:
        """Perform a single metabolic pass (Stateless)."""
        edge_config = load_yaml(self.config_root / "edge_params" / f"{edge}.yml") if (self.config_root / "edge_params" / f"{edge}.yml").exists() else {"evaluators": ["agent"]}
        current_context = {**context, "edge_config": edge_config, "constraints": self.constraints, "feature_id": feature, "edge": edge}
        
        # 1. START transaction
        transaction_id = None
        if self.store:
            start_ev = self.store.emit(event_type="iteration_started", feature=feature, edge=edge, eventType="START", inputs=[asset_path] if asset_path.exists() else [])
            transaction_id = start_ev["run"]["runId"]

        # 2. Pre-flight Guardrails
        gr_results = self.guardrails.validate_pre_flight(edge, current_context)
        if any(not r.passed for r in gr_results):
            report = IterationReport(asset_path=str(asset_path), delta=-1, converged=False, functor_results=[], guardrail_results=gr_results)
            self.archiver.archive_iteration(feature, edge, iteration, failed=True)
            if self.store:
                self.store.emit(event_type="iteration_failed", feature=feature, edge=edge, delta=-1, data={"reason": "pre-flight guardrail failure"}, eventType="FAIL", parent_run_id=transaction_id)
            return report

        # 3. Construct/Load
        candidate = asset_path.read_text() if asset_path.exists() else f"# Next candidate for {feature} / {edge}"
        
        # 4. Evaluate (Stateless Functors)
        results = []
        for eval_type in edge_config.get("evaluators", ["agent"]):
            functor_key = self._map_eval_to_functor(eval_type)
            functor = self.functors.get(functor_key)
            if not functor or (mode == "headless" and functor_key == "F_H"): continue
            
            res = functor.evaluate(candidate, current_context)
            results.append(res)
            if res.next_candidate is not None: candidate = res.next_candidate

        # 5. Post-flight Guardrails
        post_gr_results = self.guardrails.validate_post_flight(edge, candidate)
        gr_results.extend(post_gr_results)

        # 6. Compute Convergence
        total_delta = sum(r.delta for r in results) if all(r.passed for r in post_gr_results) else -1
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        converged = (total_delta == 0 and not spawn_req and all(r.passed for r in post_gr_results))
        
        # 7. Write Side-effects
        if candidate and asset_path.exists() and asset_path.read_text() != candidate:
            asset_path.write_text(candidate)
        elif candidate and not asset_path.exists():
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_text(candidate)

        self.archiver.archive_iteration(feature, edge, iteration, failed=not converged)
        
        # 8. COMPLETE transaction
        if self.store:
            self.store.emit(
                event_type="iteration_completed", feature=feature, edge=edge, delta=total_delta, 
                eventType="COMPLETE", outputs=[asset_path] if asset_path.exists() else [], parent_run_id=transaction_id,
                data={"iteration": iteration, "converged": converged, "functor_results": [r.outcome.value for r in results]}
            )
        
        return IterationReport(asset_path=str(asset_path), delta=total_delta, converged=converged, functor_results=results, guardrail_results=gr_results, spawn=spawn_req)

    def _map_eval_to_functor(self, eval_type: str) -> str:
        return {"deterministic": "F_D", "agent": "F_P", "human": "F_H"}.get(eval_type, "F_P")

