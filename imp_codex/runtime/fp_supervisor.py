# Implements: REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Supervisor helpers for pending probabilistic (F_P) work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
import uuid

from .events import append_run_event
from .intents import resolve_named_intent_payload
from .paths import RuntimePaths
from .projections import load_feature, load_yaml

if TYPE_CHECKING:
    from .edge_runner import DispatchTarget


DEFAULT_RUNTIME_ROBUSTNESS = {
    "timeout_seconds": 300,
    "stall_seconds": 120,
    "max_retries": 2,
    "classify_missing_result_as": "stall",
}


@dataclass(frozen=True)
class FpSupervisorScanResult:
    """Summary of one pending F_P recovery scan."""

    scanned: int
    retries_scheduled: int
    escalations: int
    gap_events: int
    manifests: list[dict[str, Any]]


def _now(now: str | datetime | None = None) -> datetime:
    if isinstance(now, datetime):
        return now.astimezone(timezone.utc)
    if isinstance(now, str):
        value = now.replace("Z", "+00:00") if now.endswith("Z") else now
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def _ts(now: str | datetime | None = None) -> str:
    return _now(now).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _workspace_rel(paths: RuntimePaths, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(paths.project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _agents_dir(project_root: Path) -> Path:
    return project_root / ".ai-workspace" / "agents"


def fp_manifest_path(project_root: Path, run_id: str) -> Path:
    return _agents_dir(project_root) / f"fp_intent_{run_id}.json"


def fp_result_path(project_root: Path, run_id: str) -> Path:
    return _agents_dir(project_root) / f"fp_result_{run_id}.json"


def load_runtime_robustness(paths: RuntimePaths) -> dict[str, Any]:
    """Load supervisor thresholds from the workspace context."""

    config = dict(DEFAULT_RUNTIME_ROBUSTNESS)
    if paths.runtime_robustness_path.exists():
        file_data = load_yaml(paths.runtime_robustness_path).get("fp_supervisor", {})
        if isinstance(file_data, dict):
            config.update(file_data)
    config["timeout_seconds"] = int(config.get("timeout_seconds", DEFAULT_RUNTIME_ROBUSTNESS["timeout_seconds"]))
    config["stall_seconds"] = int(config.get("stall_seconds", DEFAULT_RUNTIME_ROBUSTNESS["stall_seconds"]))
    config["max_retries"] = int(config.get("max_retries", DEFAULT_RUNTIME_ROBUSTNESS["max_retries"]))
    config["classify_missing_result_as"] = str(
        config.get("classify_missing_result_as", DEFAULT_RUNTIME_ROBUSTNESS["classify_missing_result_as"])
    )
    return config


def input_manifest_for_target(
    paths: RuntimePaths,
    target: "DispatchTarget",
    iterate_result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Capture current artifact hashes for crash/session gap detection."""

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    if iterate_result is not None:
        feature_path = str(iterate_result.get("feature_path", "")).strip()
        if feature_path:
            candidate = Path(feature_path)
            if candidate.exists():
                resolved = candidate.resolve()
                seen.add(str(resolved))
                entries.append(
                    {
                        "path": _workspace_rel(paths, resolved),
                        "sha256": _sha256_file(resolved),
                        "bytes": resolved.stat().st_size,
                    }
                )
        for artifact in iterate_result.get("artifact_refs", []):
            candidate = paths.project_root / str(artifact.get("path", "")).strip()
            if not candidate.exists() or not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if str(resolved) in seen:
                continue
            seen.add(str(resolved))
            entries.append(
                {
                    "path": _workspace_rel(paths, resolved),
                    "sha256": _sha256_file(resolved),
                    "bytes": resolved.stat().st_size,
                }
            )

    _feature_doc, feature_path = load_feature(paths, target.feature_id)
    if feature_path.exists():
        resolved = feature_path.resolve()
        if str(resolved) not in seen:
            entries.append(
                {
                    "path": _workspace_rel(paths, resolved),
                    "sha256": _sha256_file(resolved),
                    "bytes": resolved.stat().st_size,
                }
            )
    return entries


def write_fp_manifest(
    paths: RuntimePaths,
    target: "DispatchTarget",
    run_id: str,
    iteration: int,
    budget_remaining_usd: float,
    failures: list[str],
    *,
    iterate_result: dict[str, Any] | None = None,
    retry_count: int = 0,
    previous_run_id: str | None = None,
    now: str | datetime | None = None,
) -> Path:
    """Write one pending F_P manifest with supervisor metadata."""

    _agents_dir(paths.project_root).mkdir(parents=True, exist_ok=True)
    path = fp_manifest_path(paths.project_root, run_id)
    robustness = load_runtime_robustness(paths)
    timestamp = _ts(now)
    manifest = {
        "run_id": run_id,
        "previous_run_id": previous_run_id,
        "intent_id": target.intent_id,
        "feature": target.feature_id,
        "edge": target.edge,
        "iteration": iteration,
        "failures": list(failures),
        "budget_remaining_usd": round(float(budget_remaining_usd), 4),
        "status": "pending",
        "result_path": str(fp_result_path(paths.project_root, run_id)),
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_progress_at": timestamp,
        "retry_count": int(retry_count),
        "max_retries": int(robustness["max_retries"]),
        "timeout_seconds": int(robustness["timeout_seconds"]),
        "stall_seconds": int(robustness["stall_seconds"]),
        "classify_missing_result_as": robustness["classify_missing_result_as"],
        "input_manifest": input_manifest_for_target(paths, target, iterate_result),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return path


def load_fp_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_fp_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def check_fp_result(project_root: Path, run_id: str) -> dict | None:
    path = fp_result_path(project_root, run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def classify_fp_result_failure(fp_result: dict | None) -> str | None:
    if fp_result is None:
        return None
    status = str(fp_result.get("status", "")).strip().lower()
    if status in {"timeout", "stall", "error"}:
        return status
    if status == "failed":
        return "error"
    if fp_result.get("terminal") is True and fp_result.get("converged") is False:
        return str(fp_result.get("failure_classification") or "error")
    return None


def classify_missing_result_failure(manifest: dict[str, Any], *, now: str | datetime | None = None) -> str | None:
    current = _now(now)
    created_at = _now(manifest.get("created_at"))
    last_progress = _now(manifest.get("last_progress_at") or manifest.get("created_at"))
    timeout_seconds = int(manifest.get("timeout_seconds", DEFAULT_RUNTIME_ROBUSTNESS["timeout_seconds"]))
    stall_seconds = int(manifest.get("stall_seconds", DEFAULT_RUNTIME_ROBUSTNESS["stall_seconds"]))

    if (current - created_at).total_seconds() >= timeout_seconds:
        return "timeout"
    if (current - last_progress).total_seconds() >= stall_seconds:
        return str(manifest.get("classify_missing_result_as", "stall"))
    return None


def detect_manifest_drift(paths: RuntimePaths, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    changed: list[dict[str, Any]] = []
    for entry in manifest.get("input_manifest", []):
        raw_path = str(entry.get("path", "")).strip()
        if not raw_path:
            continue
        candidate = paths.project_root / raw_path
        if not candidate.exists() or not candidate.is_file():
            changed.append({"path": raw_path, "reason": "missing"})
            continue
        current_hash = _sha256_file(candidate)
        if current_hash != entry.get("sha256"):
            changed.append(
                {
                    "path": raw_path,
                    "expected_sha256": entry.get("sha256"),
                    "actual_sha256": current_hash,
                }
            )
    return changed


def emit_gap_detected(
    paths: RuntimePaths,
    manifest: dict[str, Any],
    *,
    actor: str,
    now: str | datetime | None = None,
) -> dict | None:
    """Emit one gap_detected event when a pending F_P run drifted on disk."""

    changed = detect_manifest_drift(paths, manifest)
    if not changed:
        return None
    if manifest.get("gap_run_id"):
        return {"run": {"runId": manifest["gap_run_id"]}}
    event = append_run_event(
        paths.events_file,
        project_name=paths.project_root.name,
        semantic_type="gap_detected",
        actor=actor,
        feature=manifest.get("feature"),
        edge=manifest.get("edge"),
        payload={
            "run_id": manifest.get("run_id"),
            "feature": manifest.get("feature"),
            "edge": manifest.get("edge"),
            "signal_source": "fp_recovery",
            "trigger": "Pending F_P transaction drifted on disk before completion",
            "changed_paths": changed,
        },
        event_time=_ts(now),
    )
    manifest["gap_run_id"] = event["run"]["runId"]
    return event


def emit_fp_retry_failure(
    paths: RuntimePaths,
    manifest: dict[str, Any],
    *,
    classification: str,
    actor: str,
    now: str | datetime | None = None,
) -> dict:
    """Close the current open transaction as failed before retrying it."""

    return append_run_event(
        paths.events_file,
        project_name=paths.project_root.name,
        semantic_type="IterationFailed",
        actor=actor,
        feature=manifest.get("feature"),
        edge=manifest.get("edge"),
        payload={
            "run_id": manifest.get("run_id"),
            "feature": manifest.get("feature"),
            "edge": manifest.get("edge"),
            "intent_id": manifest.get("intent_id"),
            "failure_classification": classification,
            "retry_count": int(manifest.get("retry_count", 0)) + 1,
            "fp_manifest_ref": str(fp_manifest_path(paths.project_root, str(manifest.get("run_id")))),
        },
        run_id=str(manifest.get("run_id")),
        event_time=_ts(now),
    )


def open_retry_transaction(
    paths: RuntimePaths,
    manifest: dict[str, Any],
    *,
    actor: str,
    now: str | datetime | None = None,
) -> tuple[dict, Path]:
    """Open a new retry transaction after a failed F_P attempt."""

    from .edge_runner import DispatchTarget

    feature_doc, _feature_path = load_feature(paths, str(manifest.get("feature")))
    target = DispatchTarget(
        intent_id=str(manifest.get("intent_id")),
        feature_id=str(manifest.get("feature")),
        edge=str(manifest.get("edge")),
        feature_vector=feature_doc or {"feature": manifest.get("feature"), "profile": "standard", "trajectory": {}},
    )
    new_run_id = str(uuid.uuid4())
    started = append_run_event(
        paths.events_file,
        project_name=paths.project_root.name,
        semantic_type="edge_started",
        actor=actor,
        feature=target.feature_id,
        edge=target.edge,
        payload={
            "intent_id": target.intent_id,
            "feature": target.feature_id,
            "edge": target.edge,
            "status": "iterating",
            "dispatch_source": "fp_supervisor_retry",
            "retry_count": int(manifest.get("retry_count", 0)) + 1,
            "prior_run_id": manifest.get("run_id"),
        },
        run_id=new_run_id,
        event_time=_ts(now),
    )
    retry_manifest = write_fp_manifest(
        paths,
        target,
        new_run_id,
        int(manifest.get("iteration", 1)),
        float(manifest.get("budget_remaining_usd", 0.0)),
        list(manifest.get("failures", [])),
        retry_count=int(manifest.get("retry_count", 0)) + 1,
        previous_run_id=str(manifest.get("run_id")),
        now=now,
    )
    return started, retry_manifest


def route_terminal_fp_failure(
    paths: RuntimePaths,
    manifest: dict[str, Any],
    *,
    classification: str,
    actor: str,
    now: str | datetime | None = None,
) -> dict[str, Any]:
    """Escalate a terminal F_P failure into F_H."""

    from .commands import gen_consensus_open
    from .evaluators import load_edge_config

    edge_config = load_edge_config(paths, str(manifest.get("edge")))
    review = dict(edge_config.get("review") or {})
    mode = str(review.get("mode", "human")).strip().lower() or "human"
    feature_doc, feature_path = load_feature(paths, str(manifest.get("feature")))

    if mode == "consensus":
        roster = review.get("roster") or review.get("participants") or []
        if isinstance(roster, str):
            roster_value = roster
        else:
            roster_value = ",".join(str(item).strip() for item in roster if str(item).strip())
        consensus = gen_consensus_open(
            paths.project_root,
            artifact=_workspace_rel(paths, feature_path),
            roster=roster_value,
            quorum=str(review.get("quorum", "majority")),
            asset_version=str(review.get("asset_version", "v1")),
            min_duration_seconds=int(review.get("min_duration_seconds", 0)),
            review_closes_in=int(review.get("review_closes_in", 86400)),
            actor=actor,
            event_time=_ts(now),
        )
        return {
            "status": "consensus_requested",
            "fh_mode": "consensus",
            "review_id": consensus["review_id"],
            "cycle_id": consensus["cycle_id"],
            "consensus_requested_run_id": consensus["consensus_requested_run_id"],
            "intent_run_id": None,
        }

    intent_payload = resolve_named_intent_payload(
        paths,
        signal_source="fp_failure",
        feature=str(manifest.get("feature")),
        edge=str(manifest.get("edge")),
        affected_features=[str(manifest.get("feature"))],
        affected_req_keys=[str(manifest.get("feature"))],
    )
    intent = append_run_event(
        paths.events_file,
        project_name=paths.project_root.name,
        semantic_type="intent_raised",
        actor=actor,
        feature=str(manifest.get("feature")),
        edge=str(manifest.get("edge")),
        payload={
            "intent_id": intent_payload.get("intent_id", f"INT-FP-FAIL-{manifest.get('feature')}"),
            "feature": manifest.get("feature"),
            "edge": manifest.get("edge"),
            "signal_source": "fp_failure",
            "trigger": f"F_P supervisor exhausted retries after {classification}",
            "delta": len(manifest.get("failures", [])),
            "failed_checks": list(manifest.get("failures", [])),
            "failure_classification": classification,
            **intent_payload,
        },
        event_time=_ts(now),
    )
    return {
        "status": "fh_required",
        "fh_mode": "human",
        "review_id": None,
        "cycle_id": None,
        "consensus_requested_run_id": None,
        "intent_run_id": intent["run"]["runId"],
    }


def scan_pending_fp_runs(
    project_root: Path,
    *,
    actor: str = "fp-supervisor",
    now: str | datetime | None = None,
) -> FpSupervisorScanResult:
    """Recover stalled open F_P transactions and emit runtime-robustness telemetry."""

    paths = RuntimePaths(project_root)
    if not paths.workspace_root.exists():
        return FpSupervisorScanResult(0, 0, 0, 0, [])

    scanned = 0
    retries_scheduled = 0
    escalations = 0
    gap_events = 0
    manifests_summary: list[dict[str, Any]] = []
    timestamp = _ts(now)

    for manifest_path in sorted(_agents_dir(project_root).glob("fp_intent_*.json")):
        manifest = load_fp_manifest(manifest_path)
        if manifest.get("status") in {"failed", "abandoned", "completed"}:
            continue
        scanned += 1
        classification = None
        result = check_fp_result(project_root, str(manifest.get("run_id")))
        classification = classify_fp_result_failure(result)
        if classification is None:
            classification = classify_missing_result_failure(manifest, now=timestamp)
        if classification is None:
            manifests_summary.append(
                {
                    "run_id": manifest.get("run_id"),
                    "status": manifest.get("status"),
                    "action": "pending",
                }
            )
            continue

        gap_event = emit_gap_detected(paths, manifest, actor=actor, now=timestamp)
        if gap_event is not None:
            gap_events += 1

        retry_budget_remaining = int(manifest.get("max_retries", DEFAULT_RUNTIME_ROBUSTNESS["max_retries"])) - int(
            manifest.get("retry_count", 0)
        )
        if retry_budget_remaining > 0:
            failure_event = emit_fp_retry_failure(
                paths,
                manifest,
                classification=classification,
                actor=actor,
                now=timestamp,
            )
            if result is not None:
                fp_result_path(project_root, str(manifest.get("run_id"))).unlink(missing_ok=True)
            started, retry_manifest_path = open_retry_transaction(paths, manifest, actor=actor, now=timestamp)
            manifest["status"] = "failed"
            manifest["failure_classification"] = classification
            manifest["failure_run_id"] = failure_event["run"]["runId"]
            manifest["retry_started_run_id"] = started["run"]["runId"]
            manifest["updated_at"] = timestamp
            save_fp_manifest(manifest_path, manifest)
            retries_scheduled += 1
            manifests_summary.append(
                {
                    "run_id": manifest.get("run_id"),
                    "status": "retry_scheduled",
                    "classification": classification,
                    "failure_run_id": failure_event["run"]["runId"],
                    "retry_manifest_path": str(retry_manifest_path),
                }
            )
            continue

        terminal = append_run_event(
            paths.events_file,
            project_name=paths.project_root.name,
            semantic_type="IterationAbandoned",
            actor=actor,
            feature=str(manifest.get("feature")),
            edge=str(manifest.get("edge")),
            payload={
                "run_id": manifest.get("run_id"),
                "feature": manifest.get("feature"),
                "edge": manifest.get("edge"),
                "intent_id": manifest.get("intent_id"),
                "failure_classification": classification,
                "retry_count": int(manifest.get("retry_count", 0)),
                "fp_manifest_ref": str(manifest_path),
            },
            run_id=str(manifest.get("run_id")),
            event_time=timestamp,
        )
        escalation = route_terminal_fp_failure(paths, manifest, classification=classification, actor=actor, now=timestamp)
        manifest["status"] = "abandoned"
        manifest["failure_classification"] = classification
        manifest["terminal_run_id"] = terminal["run"]["runId"]
        manifest["updated_at"] = timestamp
        manifest.update({key: value for key, value in escalation.items() if value is not None})
        save_fp_manifest(manifest_path, manifest)
        escalations += 1
        manifests_summary.append(
            {
                "run_id": manifest.get("run_id"),
                "status": escalation["status"],
                "classification": classification,
                "terminal_run_id": terminal["run"]["runId"],
                "intent_run_id": escalation.get("intent_run_id"),
                "review_id": escalation.get("review_id"),
            }
        )

    return FpSupervisorScanResult(
        scanned=scanned,
        retries_scheduled=retries_scheduled,
        escalations=escalations,
        gap_events=gap_events,
        manifests=manifests_summary,
    )


__all__ = [
    "FpSupervisorScanResult",
    "check_fp_result",
    "classify_fp_result_failure",
    "classify_missing_result_failure",
    "fp_manifest_path",
    "fp_result_path",
    "input_manifest_for_target",
    "load_fp_manifest",
    "load_runtime_robustness",
    "scan_pending_fp_runs",
    "save_fp_manifest",
    "write_fp_manifest",
]
