# Implements: REQ-F-DISPATCH-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Codex-native EDGE_RUNNER primitive for F_D -> F_P -> F_H loops."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any
import uuid

from .events import append_run_event
from .intents import resolve_named_intent_payload
from .paths import RuntimePaths, bootstrap_workspace
from .projections import default_feature_document, dump_yaml, load_feature


DEFAULT_BUDGET_USD = 1.00
COST_PER_FP_ITERATION = 0.15
MAX_FP_ITERATIONS = 3


@dataclass(frozen=True)
class DispatchTarget:
    """One edge dispatch selected by the intent observer."""

    intent_id: str
    feature_id: str
    edge: str
    intent_event: dict[str, Any] = field(default_factory=dict)
    feature_vector: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeRunResult:
    """Summary of one EDGE_RUNNER invocation."""

    run_id: str
    edge_started_run_id: str
    feature_id: str
    edge: str
    status: str
    delta: int
    iterations: int
    cost_usd: float
    failed_checks: list[str]
    fp_manifest_path: str
    events_emitted: list[str]
    iteration_start_run_id: str | None = None
    completed_run_id: str | None = None
    convergence_run_id: str | None = None
    intent_run_id: str | None = None


def _agents_dir(project_root: Path) -> Path:
    return project_root / ".ai-workspace" / "agents"


def _materialize_target_feature(paths: RuntimePaths, target: DispatchTarget) -> dict:
    feature_doc, feature_path = load_feature(paths, target.feature_id)
    if feature_doc is None:
        profile_name = str(target.feature_vector.get("profile", "standard"))
        feature_doc = default_feature_document(
            paths,
            feature_id=target.feature_id,
            profile_name=profile_name,
            title=target.feature_vector.get("title"),
        )
    feature_doc = {**feature_doc, **dict(target.feature_vector or {})}
    feature_doc["feature"] = target.feature_id
    feature_doc.setdefault("profile", "standard")
    dump_yaml(feature_path, feature_doc)
    return feature_doc


def _normalize_fd_result(result: object) -> tuple[int, list[str]]:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return int(result[0]), list(result[1])
        if len(result) == 1:
            return int(result[0]), []
    if isinstance(result, dict):
        failed_checks = result.get("failed_checks") or []
        return int(result.get("delta", len(failed_checks))), list(failed_checks)
    raise TypeError(f"Unsupported F_D evaluation result: {type(result)!r}")


def _run_fd_evaluation(
    target: DispatchTarget,
    project_root: Path,
    run_id: str,
    project: str,
    *,
    actor: str = "edge-runner",
    run_agent: bool = False,
    run_deterministic: bool = False,
) -> dict:
    """Execute the F_D evaluator pass for one feature-edge target."""

    del run_id, project
    from .commands import gen_iterate

    paths = bootstrap_workspace(project_root)
    feature_doc = _materialize_target_feature(paths, target)
    iterate = gen_iterate(
        project_root,
        feature=target.feature_id,
        edge=target.edge,
        profile=str(feature_doc.get("profile", "standard")),
        actor=actor,
        run_agent=run_agent,
        run_deterministic=run_deterministic,
        intent_id=target.intent_id,
    )
    failed_checks = [
        str(item.get("name", "unnamed_check"))
        for item in iterate.get("evaluator_summary", {}).get("details", [])
        if item.get("required") and item.get("result") == "fail"
    ]
    return {
        "delta": int(iterate["delta"]),
        "failed_checks": failed_checks,
        "status": iterate["status"],
        "iterate_result": iterate,
    }


def _write_fp_manifest(
    target: DispatchTarget,
    project_root: Path,
    run_id: str,
    iteration: int,
    budget_remaining_usd: float,
    failures: list[str],
) -> Path:
    """Write the pending F_P work request for one edge run."""

    agents_dir = _agents_dir(project_root)
    agents_dir.mkdir(parents=True, exist_ok=True)
    path = agents_dir / f"fp_intent_{run_id}.json"
    result_path = agents_dir / f"fp_result_{run_id}.json"
    manifest = {
        "run_id": run_id,
        "intent_id": target.intent_id,
        "feature": target.feature_id,
        "edge": target.edge,
        "iteration": iteration,
        "failures": list(failures),
        "budget_remaining_usd": round(float(budget_remaining_usd), 4),
        "status": "pending",
        "result_path": str(result_path),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return path


def _check_fp_result(project_root: Path, run_id: str) -> dict | None:
    """Return the fold-back result if one exists for this run."""

    result_path = _agents_dir(project_root) / f"fp_result_{run_id}.json"
    if not result_path.exists():
        return None
    return json.loads(result_path.read_text())


def run_edge(
    target: DispatchTarget,
    project_root: Path,
    events_path: Path | None = None,
    *,
    project: str | None = None,
    actor: str = "edge-runner",
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_fp_iterations: int = MAX_FP_ITERATIONS,
    run_agent: bool = False,
    run_deterministic: bool = False,
) -> EdgeRunResult:
    """Run a bounded F_D -> F_P -> F_H loop for one dispatched edge."""

    paths = bootstrap_workspace(project_root, project_name=project)
    event_file = events_path or paths.events_file
    project_name = project or paths.project_root.name
    run_id = str(uuid.uuid4())
    events_emitted: list[str] = []
    total_cost = 0.0
    fp_iterations = 0

    started = append_run_event(
        event_file,
        project_name=project_name,
        semantic_type="edge_started",
        actor=actor,
        feature=target.feature_id,
        edge=target.edge,
        payload={
            "intent_id": target.intent_id,
            "feature": target.feature_id,
            "edge": target.edge,
            "status": "iterating",
            "dispatch_source": "edge_runner",
        },
        run_id=run_id,
    )
    events_emitted.append("EdgeStarted")

    iterations = 0
    failed_checks: list[str] = []
    manifest_path = ""
    iteration_start_run_id = None
    completed_run_id = None
    convergence_run_id = None
    while True:
        iterations += 1
        fd_result = _run_fd_evaluation(
            target,
            project_root,
            run_id,
            project_name,
            actor=actor,
            run_agent=run_agent,
            run_deterministic=run_deterministic,
        )
        delta, failed_checks = _normalize_fd_result(fd_result)
        iterate_result = fd_result.get("iterate_result") if isinstance(fd_result, dict) else None
        fd_status = fd_result.get("status") if isinstance(fd_result, dict) else None
        synthetic_events = iterate_result is None

        if synthetic_events:
            append_run_event(
                event_file,
                project_name=project_name,
                semantic_type="iteration_completed",
                actor=actor,
                feature=target.feature_id,
                edge=target.edge,
                payload={
                    "feature": target.feature_id,
                    "edge": target.edge,
                    "iteration": iterations,
                    "delta": delta,
                    "status": "converged" if delta == 0 else "iterating",
                    "intent_id": target.intent_id,
                    "run_id": run_id,
                    "failed_checks": failed_checks,
                },
                causation_id=started["run"]["runId"],
                correlation_id=run_id,
                parent_run_id=started["run"]["runId"],
            )
            events_emitted.append("IterationCompleted")
        else:
            iteration_start_run_id = iterate_result.get("start_run_id")
            completed_run_id = iterate_result.get("completed_run_id")
            convergence_run_id = iterate_result.get("convergence_run_id")
            events_emitted.extend(["IterationStarted", "IterationCompleted"])
            if convergence_run_id:
                events_emitted.append("ConvergenceAchieved")

        if fd_status == "pending_review":
            return EdgeRunResult(
                run_id=run_id,
                edge_started_run_id=started["run"]["runId"],
                feature_id=target.feature_id,
                edge=target.edge,
                status="pending_review",
                delta=delta,
                iterations=iterations,
                cost_usd=round(total_cost, 4),
                failed_checks=failed_checks,
                fp_manifest_path=manifest_path,
                events_emitted=events_emitted,
                iteration_start_run_id=iteration_start_run_id,
                completed_run_id=completed_run_id,
                convergence_run_id=convergence_run_id,
            )

        if (fd_status == "converged") or (fd_status is None and delta == 0):
            if synthetic_events:
                append_run_event(
                    event_file,
                    project_name=project_name,
                    semantic_type="edge_converged",
                    actor=actor,
                    feature=target.feature_id,
                    edge=target.edge,
                    payload={
                        "feature": target.feature_id,
                        "edge": target.edge,
                        "iteration": iterations,
                        "delta": 0,
                        "status": "converged",
                        "intent_id": target.intent_id,
                        "run_id": run_id,
                    },
                    correlation_id=run_id,
                    parent_run_id=started["run"]["runId"],
                )
                events_emitted.append("EdgeConverged")
            return EdgeRunResult(
                run_id=run_id,
                edge_started_run_id=started["run"]["runId"],
                feature_id=target.feature_id,
                edge=target.edge,
                status="converged",
                delta=0,
                iterations=iterations,
                cost_usd=round(total_cost, 4),
                failed_checks=[],
                fp_manifest_path="",
                events_emitted=events_emitted,
                iteration_start_run_id=iteration_start_run_id,
                completed_run_id=completed_run_id,
                convergence_run_id=convergence_run_id,
            )

        if fp_iterations >= max_fp_iterations or total_cost + COST_PER_FP_ITERATION > budget_usd:
            intent_payload = resolve_named_intent_payload(
                paths,
                signal_source="human_gate_required",
                feature=target.feature_id,
                edge=target.edge,
                affected_features=[target.feature_id],
                affected_req_keys=[target.feature_id],
            )
            intent_event = append_run_event(
                event_file,
                project_name=project_name,
                semantic_type="intent_raised",
                actor=actor,
                feature=target.feature_id,
                edge=target.edge,
                payload={
                    "intent_id": intent_payload.get("intent_id", f"INT-HUMAN-GATE-{target.feature_id}"),
                    "feature": target.feature_id,
                    "edge": target.edge,
                    "signal_source": "human_gate_required",
                    "trigger": "EDGE_RUNNER exhausted bounded F_P loop",
                    "delta": delta,
                    "failed_checks": failed_checks,
                    **intent_payload,
                },
                correlation_id=run_id,
                parent_run_id=started["run"]["runId"],
            )
            events_emitted.append("IntentRaised")
            return EdgeRunResult(
                run_id=run_id,
                edge_started_run_id=started["run"]["runId"],
                feature_id=target.feature_id,
                edge=target.edge,
                status="fh_required",
                delta=delta,
                iterations=iterations,
                cost_usd=round(total_cost, 4),
                failed_checks=failed_checks,
                fp_manifest_path=manifest_path,
                events_emitted=events_emitted,
                iteration_start_run_id=iteration_start_run_id,
                completed_run_id=completed_run_id,
                convergence_run_id=convergence_run_id,
                intent_run_id=intent_event["run"]["runId"],
            )

        fp_result = _check_fp_result(project_root, run_id)
        if fp_result is None:
            manifest = _write_fp_manifest(
                target,
                project_root,
                run_id,
                iterations,
                budget_usd - total_cost,
                failed_checks,
            )
            manifest_path = str(manifest)
            return EdgeRunResult(
                run_id=run_id,
                edge_started_run_id=started["run"]["runId"],
                feature_id=target.feature_id,
                edge=target.edge,
                status="fp_dispatched",
                delta=delta,
                iterations=iterations,
                cost_usd=round(total_cost, 4),
                failed_checks=failed_checks,
                fp_manifest_path=manifest_path,
                events_emitted=events_emitted,
                iteration_start_run_id=iteration_start_run_id,
                completed_run_id=completed_run_id,
                convergence_run_id=convergence_run_id,
            )

        total_cost += float(fp_result.get("cost_usd", COST_PER_FP_ITERATION))
        fp_iterations += 1


__all__ = [
    "COST_PER_FP_ITERATION",
    "DEFAULT_BUDGET_USD",
    "MAX_FP_ITERATIONS",
    "DispatchTarget",
    "EdgeRunResult",
    "_check_fp_result",
    "_run_fd_evaluation",
    "_write_fp_manifest",
    "run_edge",
]
