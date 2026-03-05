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
    
    def __init__(self, functors: Dict[str, Functor], project_root: Path, config_root: Path = None, store = None):
        self.functors = functors
        self.project_root = project_root
        self.workspace_root = project_root / ".ai-workspace"
        self.config_root = config_root or Path(__file__).parent.parent / "config"
        self.store = store

    def _get_project_fingerprint(self) -> tuple[float, int]:
        """Return (latest_mtime, total_file_count) for key project locations."""
        latest = 0.0
        count = 0
        sentinel_dirs = [
            self.project_root / "gemini_cloud",
            self.project_root / "tests",
            self.project_root / "specification",
            self.project_root / ".ai-workspace" / "events",
            self.project_root / ".ai-workspace" / "features",
        ]
        for d in sentinel_dirs:
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

    def get_liveness_signal(self, transport: str = "filesystem") -> tuple[float, int]:
        """Pluggable liveness signal (Finding #4)."""
        if transport == "filesystem":
            return self._get_project_fingerprint()
        # In cloud, this could check for Firestore heartbeat updates
        return time.time(), 0

    def _archive_iteration(self, feature_id: str, edge: str, iteration: int, failed: bool = False):
        """Archive project state for reproducibility."""
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
        return archive_dir

    def detect_integrity_gaps(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Find discrepancies between the Event Ledger (committed) and Filesystem (actual)."""
        last_committed_hashes = {}
        for ev in events:
            if ev.get("eventType") == "COMPLETE":
                for output in ev.get("outputs", []):
                    name = output.get("name")
                    facets = output.get("facets", {})
                    h = facets.get("sdlc:contentHash", {}).get("hash")
                    if name and h:
                        last_committed_hashes[name] = h
        
        gaps = []
        for rel_path, committed_hash in last_committed_hashes.items():
            full_path = self.project_root / rel_path
            if not full_path.exists():
                gaps.append({"path": rel_path, "type": "MISSING_ARTIFACT", "expected": committed_hash})
                continue
            if self.store:
                actual_hash = self.store._hash_file(full_path)
                if actual_hash != committed_hash:
                    gaps.append({"path": rel_path, "type": "UNCOMMITTED_CHANGE", "expected": committed_hash, "actual": actual_hash})
        
        # Check for open transactions
        starts = {ev["run"]["runId"]: ev for ev in events if ev.get("eventType") == "START"}
        for ev in events:
            if ev.get("eventType") in ("COMPLETE", "FAIL", "ABORT"):
                parent_id = ev.get("run", {}).get("facets", {}).get("parent_run_id", {}).get("runId")
                if parent_id: starts.pop(parent_id, None)
                starts.pop(ev["run"]["runId"], None)
        for run_id, ev in starts.items():
            gaps.append({"type": "OPEN_TRANSACTION", "run_id": run_id, "event": ev.get("event_type")})
        return gaps

    def run(self, asset_path: Path, feature: str, edge: str, context: Dict, mode: str = "interactive", iteration: int = 1, wall_timeout: int = 3600, stall_timeout: int = 300) -> IterationReport:
        edge_config = load_yaml(self.config_root / "edge_params" / f"{edge}.yml") if (self.config_root / "edge_params" / f"{edge}.yml").exists() else {"evaluators": ["agent"]}
        current_context = context.copy()
        current_context.update({"edge_config": edge_config})
        candidate = asset_path.read_text() if asset_path.exists() else f"# Next candidate for {feature} / {edge}"
        
        # Emit START
        transaction_id = None
        if self.store:
            start_ev = self.store.emit(event_type="iteration_started", feature=feature, edge=edge, eventType="START", inputs=[asset_path] if asset_path.exists() else [])
            transaction_id = start_ev["run"]["runId"]

        start_time = time.time(); last_mtime, last_count = self.get_liveness_signal()
        last_activity = time.time()

        results = []
        for eval_type in edge_config.get("evaluators", ["agent"]):
            functor_key = self._map_eval_to_functor(eval_type)
            functor = self.functors.get(functor_key)
            if not functor or (mode == "headless" and functor_key == "F_H"): continue
            
            # Wall-clock timeout check (Finding #1)
            if time.time() - start_time > wall_timeout: break
            
            res = functor.evaluate(candidate, current_context)
            results.append(res)
            
            # Stall Detection via pluggable signal (Finding #4)
            cur_mtime, cur_count = self.get_liveness_signal()
            if cur_mtime > last_mtime or cur_count != last_count:
                last_mtime, last_count = cur_mtime, cur_count; last_activity = time.time()
            elif time.time() - last_activity > stall_timeout: break

        total_delta = sum(r.delta for r in results)
        spawn_req = next((r.spawn for r in results if r.spawn), None)
        converged = (total_delta == 0 and not spawn_req)
        
        self._archive_iteration(feature, edge, iteration, failed=not converged)
        
        if self.store:
            self.store.emit(
                event_type="iteration_completed", feature=feature, edge=edge, delta=total_delta, 
                eventType="COMPLETE", outputs=[asset_path] if asset_path.exists() else [], parent_run_id=transaction_id
            )
        
        return IterationReport(asset_path=str(asset_path), delta=total_delta, converged=converged, functor_results=results, spawn=spawn_req)

    def _map_eval_to_functor(self, eval_type: str) -> str:
        return {"deterministic": "F_D", "agent": "F_P", "human": "F_H"}.get(eval_type, "F_P")
