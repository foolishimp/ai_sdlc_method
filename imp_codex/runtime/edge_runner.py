# Implements: REQ-F-DISPATCH-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Codex-native EDGE_RUNNER primitive for F_D -> F_P -> F_H loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import uuid

from .evaluators import load_edge_config
from .events import append_run_event
from .fp_supervisor import (
    check_fp_result as _check_fp_result,
    classify_fp_result_failure,
    fp_result_path,
    write_fp_manifest as _supervisor_write_fp_manifest,
)
from .fp_worker import run_fp_work
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
    fh_mode: str | None = None
    review_id: str | None = None
    cycle_id: str | None = None
    consensus_requested_run_id: str | None = None


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


def _schedule_fp_retry(
    paths: RuntimePaths,
    target: DispatchTarget,
    *,
    run_id: str,
    actor: str,
    classification: str,
    iteration: int,
    budget_remaining_usd: float,
    failures: list[str],
    iterate_result: dict[str, Any] | None,
    events_emitted: list[str],
) -> str:
    from .fp_supervisor import emit_fp_retry_failure, load_fp_manifest, open_retry_transaction, save_fp_manifest

    manifest_path = _write_fp_manifest(
        target,
        paths.project_root,
        run_id,
        iteration,
        budget_remaining_usd,
        failures,
        iterate_result=iterate_result,
    )
    manifest = load_fp_manifest(manifest_path)
    failure_event = emit_fp_retry_failure(
        paths,
        manifest,
        classification=classification,
        actor=actor,
    )
    fp_result_path(paths.project_root, run_id).unlink(missing_ok=True)
    started, retry_manifest = open_retry_transaction(paths, manifest, actor=actor)
    manifest["status"] = "failed"
    manifest["failure_classification"] = classification
    manifest["failure_run_id"] = failure_event["run"]["runId"]
    manifest["retry_started_run_id"] = started["run"]["runId"]
    save_fp_manifest(manifest_path, manifest)
    events_emitted.extend(["IterationFailed", "EdgeStarted"])
    return str(retry_manifest)


def _route_terminal_fp_failure(
    paths: RuntimePaths,
    target: DispatchTarget,
    *,
    run_id: str,
    actor: str,
    classification: str,
    iteration: int,
    budget_remaining_usd: float,
    failures: list[str],
    iterate_result: dict[str, Any] | None,
    events_emitted: list[str],
) -> dict[str, Any]:
    from .fp_supervisor import load_fp_manifest, route_terminal_fp_failure, save_fp_manifest

    manifest_path = _write_fp_manifest(
        target,
        paths.project_root,
        run_id,
        iteration,
        budget_remaining_usd,
        failures,
        iterate_result=iterate_result,
    )
    manifest = load_fp_manifest(manifest_path)
    terminal = append_run_event(
        paths.events_file,
        project_name=paths.project_root.name,
        semantic_type="IterationAbandoned",
        actor=actor,
        feature=target.feature_id,
        edge=target.edge,
        payload={
            "run_id": run_id,
            "feature": target.feature_id,
            "edge": target.edge,
            "intent_id": target.intent_id,
            "failure_classification": classification,
            "retry_count": int(manifest.get("retry_count", 0)),
            "fp_manifest_ref": str(manifest_path),
        },
        run_id=run_id,
    )
    escalation = route_terminal_fp_failure(paths, manifest, classification=classification, actor=actor)
    manifest["status"] = "abandoned"
    manifest["failure_classification"] = classification
    manifest["terminal_run_id"] = terminal["run"]["runId"]
    manifest.update({key: value for key, value in escalation.items() if value is not None})
    save_fp_manifest(manifest_path, manifest)
    events_emitted.append("IterationAbandoned")
    if escalation["status"] == "consensus_requested":
        events_emitted.append("ConsensusRequested")
    else:
        events_emitted.append("IntentRaised")
    return {
        "manifest_path": str(manifest_path),
        "terminal_run_id": terminal["run"]["runId"],
        **escalation,
    }


def _write_fp_manifest(
    target: DispatchTarget,
    project_root: Path,
    run_id: str,
    iteration: int,
    budget_remaining_usd: float,
    failures: list[str],
    *,
    iterate_result: dict[str, Any] | None = None,
) -> Path:
    """Write the pending F_P work request for one edge run."""
    return _supervisor_write_fp_manifest(
        RuntimePaths(project_root),
        target,
        run_id,
        iteration,
        budget_remaining_usd,
        failures,
        iterate_result=iterate_result,
    )


def _review_policy(paths: RuntimePaths, target: DispatchTarget) -> dict[str, Any]:
    """Resolve how this edge should route its F_H gate."""

    edge_config = load_edge_config(paths, target.edge)
    review = dict(edge_config.get("review") or {})
    mode = str(review.get("mode", "human")).strip().lower() or "human"
    roster = review.get("roster") or review.get("participants") or []
    if isinstance(roster, str):
        roster_entries = [entry.strip() for entry in roster.split(",") if entry.strip()]
    else:
        roster_entries = [str(entry).strip() for entry in roster if str(entry).strip()]
    return {
        "mode": mode,
        "roster": roster_entries,
        "quorum": str(review.get("quorum", "majority")),
        "asset_version": str(review.get("asset_version", "v1")),
        "min_duration_seconds": int(review.get("min_duration_seconds", 0)),
        "review_closes_in": int(review.get("review_closes_in", 86400)),
    }


def _review_artifact(paths: RuntimePaths, target: DispatchTarget, iterate_result: dict[str, Any] | None) -> str:
    """Choose the most relevant artifact path for F_H review."""

    if iterate_result is not None:
        for artifact in iterate_result.get("artifact_refs", []):
            candidate = str(artifact.get("path", "")).strip()
            if candidate:
                return candidate
        feature_path = str(iterate_result.get("feature_path", "")).strip()
        if feature_path:
            return feature_path

    _materialize_target_feature(paths, target)
    _feature_doc, feature_path = load_feature(paths, target.feature_id)
    try:
        return str(feature_path.relative_to(paths.project_root))
    except ValueError:
        return str(feature_path)


def _open_consensus_review(
    paths: RuntimePaths,
    target: DispatchTarget,
    iterate_result: dict[str, Any] | None,
    *,
    actor: str,
) -> dict:
    """Open a consensus review for this edge when its F_H policy requires it."""

    from .commands import gen_consensus_open

    policy = _review_policy(paths, target)
    roster = policy["roster"]
    if not roster:
        raise ValueError(f"Consensus review policy for {target.edge} requires a non-empty roster")

    return gen_consensus_open(
        paths.project_root,
        artifact=_review_artifact(paths, target, iterate_result),
        roster=",".join(roster),
        quorum=policy["quorum"],
        asset_version=policy["asset_version"],
        min_duration_seconds=policy["min_duration_seconds"],
        review_closes_in=policy["review_closes_in"],
        actor=actor,
    )


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
            review_policy = _review_policy(paths, target)
            if review_policy["mode"] == "consensus":
                consensus = _open_consensus_review(
                    paths,
                    target,
                    iterate_result if isinstance(iterate_result, dict) else None,
                    actor=actor,
                )
                events_emitted.append("ConsensusRequested")
                return EdgeRunResult(
                    run_id=run_id,
                    edge_started_run_id=started["run"]["runId"],
                    feature_id=target.feature_id,
                    edge=target.edge,
                    status="consensus_requested",
                    delta=delta,
                    iterations=iterations,
                    cost_usd=round(total_cost, 4),
                    failed_checks=failed_checks,
                    fp_manifest_path=manifest_path,
                    events_emitted=events_emitted,
                    iteration_start_run_id=iteration_start_run_id,
                    completed_run_id=completed_run_id,
                    convergence_run_id=convergence_run_id,
                    fh_mode="consensus",
                    review_id=consensus["review_id"],
                    cycle_id=consensus["cycle_id"],
                    consensus_requested_run_id=consensus["consensus_requested_run_id"],
                )
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
                fh_mode="human",
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
            review_policy = _review_policy(paths, target)
            if review_policy["mode"] == "consensus":
                consensus = _open_consensus_review(paths, target, None, actor=actor)
                events_emitted.append("ConsensusRequested")
                return EdgeRunResult(
                    run_id=run_id,
                    edge_started_run_id=started["run"]["runId"],
                    feature_id=target.feature_id,
                    edge=target.edge,
                    status="consensus_requested",
                    delta=delta,
                    iterations=iterations,
                    cost_usd=round(total_cost, 4),
                    failed_checks=failed_checks,
                    fp_manifest_path=manifest_path,
                    events_emitted=events_emitted,
                    iteration_start_run_id=iteration_start_run_id,
                    completed_run_id=completed_run_id,
                    convergence_run_id=convergence_run_id,
                    fh_mode="consensus",
                    review_id=consensus["review_id"],
                    cycle_id=consensus["cycle_id"],
                    consensus_requested_run_id=consensus["consensus_requested_run_id"],
                )
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
                fh_mode="human",
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
                iterate_result=iterate_result if isinstance(iterate_result, dict) else None,
            )
            manifest_path = str(manifest)
            if not run_agent:
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
            run_fp_work(project_root, run_id=run_id, actor=actor)
            fp_result = _check_fp_result(project_root, run_id)
            if fp_result is None:
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

        failure_classification = classify_fp_result_failure(fp_result)
        if failure_classification is not None:
            if fp_iterations + 1 < max_fp_iterations:
                manifest_path = _schedule_fp_retry(
                    paths,
                    target,
                    run_id=run_id,
                    actor=actor,
                    classification=failure_classification,
                    iteration=iterations,
                    budget_remaining_usd=budget_usd - total_cost,
                    failures=failed_checks,
                    iterate_result=iterate_result if isinstance(iterate_result, dict) else None,
                    events_emitted=events_emitted,
                )
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

            escalation = _route_terminal_fp_failure(
                paths,
                target,
                run_id=run_id,
                actor=actor,
                classification=failure_classification,
                iteration=iterations,
                budget_remaining_usd=budget_usd - total_cost,
                failures=failed_checks,
                iterate_result=iterate_result if isinstance(iterate_result, dict) else None,
                events_emitted=events_emitted,
            )
            return EdgeRunResult(
                run_id=run_id,
                edge_started_run_id=started["run"]["runId"],
                feature_id=target.feature_id,
                edge=target.edge,
                status=escalation["status"],
                delta=delta,
                iterations=iterations,
                cost_usd=round(total_cost, 4),
                failed_checks=failed_checks,
                fp_manifest_path=escalation["manifest_path"],
                events_emitted=events_emitted,
                iteration_start_run_id=iteration_start_run_id,
                completed_run_id=completed_run_id,
                convergence_run_id=convergence_run_id,
                intent_run_id=escalation.get("intent_run_id"),
                fh_mode=escalation.get("fh_mode"),
                review_id=escalation.get("review_id"),
                cycle_id=escalation.get("cycle_id"),
                consensus_requested_run_id=escalation.get("consensus_requested_run_id"),
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
