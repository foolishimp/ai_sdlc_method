# Implements: REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Codex-native F_P worker for fold-back manifests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .evaluators import run_agent_checks
from .fp_supervisor import (
    check_fp_result,
    classify_fp_result_failure,
    fp_manifest_path,
    fp_result_path,
    load_fp_manifest,
    save_fp_manifest,
)
from .paths import RuntimePaths
from .projections import load_project_constraints


@dataclass(frozen=True)
class FpWorkResult:
    """Summary of one processed F_P manifest."""

    run_id: str
    feature: str
    edge: str
    status: str
    converged: bool
    delta: int
    cost_usd: float
    result_path: str
    artifacts: list[dict[str, Any]]
    message: str
    provider: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _workspace_rel(paths: RuntimePaths, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(paths.project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_invocation_path(paths: RuntimePaths) -> Path | None:
    config = dict(load_project_constraints(paths).get("agent_invocation", {}))
    configured = config.get("file")
    if not configured:
        return None
    candidate = Path(str(configured))
    if candidate.is_absolute():
        return candidate
    return (paths.project_root / candidate).resolve()


def _load_fp_contract(paths: RuntimePaths) -> dict:
    invocation_path = _resolve_invocation_path(paths)
    if invocation_path is None or not invocation_path.exists():
        return {}
    text = invocation_path.read_text()
    if invocation_path.suffix.lower() == ".json":
        parsed = json.loads(text)
    else:
        parsed = yaml.safe_load(text)
    return parsed if isinstance(parsed, dict) else {}


def _match_fp_record(rows: list[dict], *, run_id: str, feature: str, edge: str) -> dict | None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("run_id") == run_id:
            return row
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("feature") == feature and row.get("edge") == edge:
            return row
    return None


def _write_artifacts(paths: RuntimePaths, artifacts: list[dict]) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for artifact in artifacts:
        raw_path = str(artifact.get("path", "")).strip()
        if not raw_path:
            continue
        candidate = (paths.project_root / raw_path).resolve()
        try:
            candidate.relative_to(paths.project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Artifact path escapes project root: {raw_path}") from exc
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if "content" in artifact:
            candidate.write_text(str(artifact.get("content", "")))
        elif "yaml" in artifact:
            candidate.write_text(yaml.safe_dump(artifact["yaml"], sort_keys=False))
        else:
            raise ValueError(f"Artifact contract for {raw_path} requires 'content' or 'yaml'")
        written.append(
            {
                "path": _workspace_rel(paths, candidate),
                "sha256": _sha256_file(candidate),
                "bytes": candidate.stat().st_size,
            }
        )
    return written


def _write_fp_result(paths: RuntimePaths, manifest: dict, result: dict[str, Any]) -> Path:
    path = fp_result_path(paths.project_root, str(manifest["run_id"]))
    path.write_text(json.dumps(result, indent=2, sort_keys=True))
    manifest_path = fp_manifest_path(paths.project_root, str(manifest["run_id"]))
    latest = load_fp_manifest(manifest_path)
    latest["updated_at"] = _ts()
    latest["last_progress_at"] = latest["updated_at"]
    latest["result_run_status"] = str(result.get("status", "completed"))
    latest["result_path"] = str(path)
    if classify_fp_result_failure(result) is None:
        latest["status"] = "completed"
    save_fp_manifest(manifest_path, latest)
    return path


def _heuristic_fp_result(paths: RuntimePaths, manifest: dict) -> dict[str, Any]:
    checks = run_agent_checks(paths, str(manifest["edge"]), feature=str(manifest["feature"]))
    failed_checks = [
        str(item.get("name", "unnamed_check"))
        for item in checks
        if item.get("required") and item.get("result") == "fail"
    ]
    delta = len(failed_checks)
    return {
        "status": "completed",
        "provider": "heuristic",
        "message": "Heuristic F_P evaluation completed",
        "converged": delta == 0,
        "delta": delta,
        "cost_usd": 0.15,
        "checks": checks,
        "artifacts": [],
        "spawns": [],
    }


def run_fp_work(
    project_root: Path,
    *,
    run_id: str,
    actor: str = "fp-worker",
) -> FpWorkResult:
    """Consume one F_P manifest and write a structured fold-back result."""

    del actor
    paths = RuntimePaths(project_root)
    manifest = load_fp_manifest(fp_manifest_path(paths.project_root, run_id))
    existing = check_fp_result(paths.project_root, run_id)
    if existing is not None:
        return FpWorkResult(
            run_id=run_id,
            feature=str(manifest["feature"]),
            edge=str(manifest["edge"]),
            status=str(existing.get("status", "completed")),
            converged=bool(existing.get("converged")),
            delta=int(existing.get("delta", 1)),
            cost_usd=float(existing.get("cost_usd", 0.0)),
            result_path=str(fp_result_path(paths.project_root, run_id)),
            artifacts=list(existing.get("artifacts", [])),
            message=str(existing.get("message", "existing fp result reused")),
            provider=str(existing.get("provider", "existing")),
        )

    constraints = load_project_constraints(paths)
    invocation = dict(constraints.get("agent_invocation", {}))
    mode = str(invocation.get("mode", "heuristic")).strip().lower() or "heuristic"
    provider = mode

    if mode == "file":
        contract = _load_fp_contract(paths)
        row = _match_fp_record(
            list(contract.get("fp_results") or []),
            run_id=run_id,
            feature=str(manifest["feature"]),
            edge=str(manifest["edge"]),
        )
        if row is None:
            row = {
                "status": "error",
                "message": "No fp_results entry matched manifest",
                "cost_usd": 0.0,
                "converged": False,
                "delta": len(manifest.get("failures", [])),
                "artifacts": [],
            }
            provider = "file_missing"
        artifacts = _write_artifacts(paths, list(row.get("artifacts") or []))
        result = {
            "status": str(row.get("status", "completed")),
            "provider": provider,
            "message": str(row.get("message", "External F_P result applied")),
            "converged": bool(row.get("converged", False)),
            "delta": int(row.get("delta", len(manifest.get("failures", [])))),
            "cost_usd": float(row.get("cost_usd", 0.15)),
            "checks": list(row.get("checks") or []),
            "artifacts": artifacts,
            "spawns": list(row.get("spawns") or []),
        }
    else:
        result = _heuristic_fp_result(paths, manifest)
        artifacts = list(result.get("artifacts", []))

    result_path = _write_fp_result(paths, manifest, result)
    return FpWorkResult(
        run_id=run_id,
        feature=str(manifest["feature"]),
        edge=str(manifest["edge"]),
        status=str(result["status"]),
        converged=bool(result["converged"]),
        delta=int(result["delta"]),
        cost_usd=float(result["cost_usd"]),
        result_path=str(result_path),
        artifacts=artifacts,
        message=str(result["message"]),
        provider=str(result["provider"]),
    )


def run_pending_fp_work(
    project_root: Path,
    *,
    actor: str = "fp-worker",
) -> list[FpWorkResult]:
    """Process all pending manifests that do not already have a result file."""

    del actor
    paths = RuntimePaths(project_root)
    results: list[FpWorkResult] = []
    agents_dir = paths.workspace_root / "agents"
    if not agents_dir.exists():
        return results
    for manifest_path in sorted(agents_dir.glob("fp_intent_*.json")):
        manifest = load_fp_manifest(manifest_path)
        if manifest.get("status") != "pending":
            continue
        results.append(run_fp_work(paths.project_root, run_id=str(manifest["run_id"]), actor=actor))
    return results


__all__ = ["FpWorkResult", "run_fp_work", "run_pending_fp_work"]
