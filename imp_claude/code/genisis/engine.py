# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-EVAL-002 (Evaluator Composition), REQ-F-FPC-003 (Context Accumulation), REQ-F-FPC-004 (Engine Construct Integration), REQ-NFR-FPC-001 (4 Calls Per Traversal), REQ-NFR-FPC-002 (Backward Compatible Default), REQ-BR-FPC-001 (Construct Before Evaluate), REQ-ROBUST-007 (Failure Event Emission)
"""Deterministic engine — owns the graph traversal loop.

F_D controls: routing, emission, delta computation, convergence decisions.
F_P is called: for agent evaluation via Claude Code CLI.
F_P is called: for artifact construction via Claude Code CLI (ADR-020).
F_H is called: for human evaluation (future — currently skips).

The LLM cannot skip emission. The deterministic code calls it, takes its
answer, records everything, then decides what to do next.

Design principle (ADR-019): iterate_edge() is pure evaluation — it computes
delta and emits events. Lifecycle decisions (spawn, fold-back) belong to the
orchestrator (run_edge, run, or CLI).

Design principle (ADR-020): When construct=True, iterate_edge() calls
fp_construct.run_construct() BEFORE evaluation. The constructed artifact
replaces the input for evaluation. Batched F_P evaluations from the construct
response are merged with F_D check results.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config_loader import load_yaml, resolve_checklist
from .fd_emit import emit_event, make_event
from .fd_evaluate import run_check as fd_run_check
from .fd_route import select_next_edge, select_profile
from .fp_construct import batched_check_results, run_construct
from .fp_evaluate import run_check as fp_run_check
from .models import (
    CheckOutcome,
    CheckResult,
    ConstructResult,
    EvaluationResult,
)


@dataclass
class EngineConfig:
    """Configuration for the engine."""

    project_name: str
    workspace_path: Path
    edge_params_dir: Path
    profiles_dir: Path
    constraints: dict
    graph_topology: dict
    model: str = "sonnet"
    max_iterations_per_edge: int = 10
    claude_timeout: int = 120
    deterministic_only: bool = False
    fd_timeout: int = 120
    stall_timeout: int = 60
    sanitize_env: bool = True


@dataclass
class IterationRecord:
    """Record of one iteration — what happened, what was decided."""

    edge: str
    iteration: int
    evaluation: EvaluationResult
    event_emitted: bool = True
    construct_result: Optional[ConstructResult] = None


def iterate_edge(
    edge: str,
    edge_config: dict,
    config: EngineConfig,
    feature_id: str,
    asset_content: str,
    context: str = "",
    iteration: int = 1,
    construct: bool = False,
    output_path: Path | None = None,
) -> IterationRecord:
    """Run one iteration on a single edge.

    This is the core loop body. F_D owns every step:
    1. (Optional) F_P: Construct artifact via Claude Code CLI
    2. Resolve checklist ($variables)
    3. Evaluate each check (dispatch by type: F_D subprocess or F_P Claude Code)
       - When construct=True, batched F_P evaluations replace per-check agent calls
    4. Compute delta (deterministic)
    5. Emit event (deterministic — ALWAYS fires)
    6. Return the record

    When construct=True (ADR-020):
    - Calls fp_construct.run_construct() BEFORE evaluation
    - Writes constructed artifact to output_path (if provided)
    - Uses batched F_P evaluations from construct response
    - Falls back to per-check fp_evaluate for unmatched agent checks
    """
    construct_result = None
    events_path = config.workspace_path / ".ai-workspace" / "events" / "events.jsonl"

    # 1. F_P: Construct artifact (when enabled)
    if construct:
        construct_result = run_construct(
            edge=edge,
            asset_content=asset_content,
            context=context,
            edge_config=edge_config,
            constraints=config.constraints,
            model=config.model,
            timeout=config.claude_timeout,
            claude_cmd="claude",
        )

        # Emit fp_failure event on construct failure (REQ-ROBUST-007)
        if not construct_result.artifact and construct_result.source_findings:
            classification = "UNKNOWN"
            for finding in construct_result.source_findings:
                classification = finding.get("classification", "UNKNOWN")
                break
            emit_event(
                events_path,
                make_event(
                    "fp_failure",
                    config.project_name,
                    feature=feature_id,
                    edge=edge,
                    iteration=iteration,
                    classification=classification,
                    duration_ms=construct_result.duration_ms,
                    retries=construct_result.retries,
                    phase="construct",
                ),
            )

        # Write constructed artifact to filesystem (REQ-BR-FPC-001)
        if construct_result.artifact and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(construct_result.artifact)

        # Use constructed artifact for evaluation instead of input
        if construct_result.artifact:
            asset_content = construct_result.artifact

    # 2. F_D: Resolve checklist
    checks = resolve_checklist(edge_config, config.constraints)

    # Build batched evaluation lookup (from construct response)
    batched_results = {}
    if construct_result and construct_result.evaluations:
        agent_checks = [c for c in checks if c.check_type == "agent"]
        batched = batched_check_results(construct_result, agent_checks)
        for check, result in zip(agent_checks, batched):
            if result is not None:
                batched_results[check.name] = result

    # 3. Evaluate each check — dispatch by type
    results: list[CheckResult] = []
    escalations: list[str] = []

    for check in checks:
        if check.check_type == "deterministic":
            cr = fd_run_check(check, config.workspace_path, timeout=config.fd_timeout)
        elif check.check_type == "agent":
            # Use batched result from construct if available
            if check.name in batched_results:
                cr = batched_results[check.name]
            elif config.deterministic_only:
                cr = CheckResult(
                    name=check.name,
                    outcome=CheckOutcome.SKIP,
                    required=check.required,
                    check_type=check.check_type,
                    functional_unit=check.functional_unit,
                    message="Skipped: deterministic-only mode",
                )
            else:
                cr = fp_run_check(
                    check,
                    asset_content=asset_content,
                    context=context,
                    model=config.model,
                    timeout=config.claude_timeout,
                )
        elif check.check_type == "human":
            cr = CheckResult(
                name=check.name,
                outcome=CheckOutcome.SKIP,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message="Skipped: human check (interactive mode not available)",
            )
        else:
            cr = CheckResult(
                name=check.name,
                outcome=CheckOutcome.SKIP,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Skipped: unknown check type '{check.check_type}'",
            )

        results.append(cr)

        # Emit evaluator_detail event for failing checks (REQ-ROBUST-007)
        if cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR):
            emit_event(
                events_path,
                make_event(
                    "evaluator_detail",
                    config.project_name,
                    feature=feature_id,
                    edge=edge,
                    iteration=iteration,
                    check_name=cr.name,
                    check_type=cr.check_type,
                    outcome=cr.outcome.value,
                    required=cr.required,
                    message=cr.message[:500] if cr.message else "",
                ),
            )

        # η detection
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR):
            if cr.check_type == "deterministic":
                escalations.append(f"η_D→P: {cr.name} — deterministic failure")
            elif cr.check_type == "agent":
                escalations.append(f"η_P→H: {cr.name} — agent evaluation failed")

    # 4. F_D: Compute delta — DETERMINISTIC
    delta = sum(
        1
        for cr in results
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )
    converged = delta == 0

    evaluation = EvaluationResult(
        edge=edge,
        checks=results,
        delta=delta,
        converged=converged,
        escalations=escalations,
    )

    # 5. F_D: Emit event — THIS ALWAYS FIRES
    check_summary = [
        {
            "name": cr.name,
            "type": cr.check_type,
            "outcome": cr.outcome.value,
            "required": cr.required,
        }
        for cr in results
    ]

    passed = sum(1 for cr in results if cr.outcome == CheckOutcome.PASS)
    failed = sum(
        1 for cr in results if cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )
    skipped = sum(1 for cr in results if cr.outcome == CheckOutcome.SKIP)

    event_data = dict(
        feature=feature_id,
        edge=edge,
        iteration=iteration,
        delta=delta,
        status="converged" if converged else "iterating",
        evaluators={
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(results),
            "details": check_summary,
        },
        checks=check_summary,
        escalations=escalations,
    )

    if construct_result:
        event_data["construct"] = {
            "model": construct_result.model,
            "duration_ms": construct_result.duration_ms,
            "retries": construct_result.retries,
            "traceability": construct_result.traceability,
            "source_findings": construct_result.source_findings,
        }

    emit_event(
        events_path,
        make_event("iteration_completed", config.project_name, **event_data),
    )

    if converged:
        emit_event(
            events_path,
            make_event(
                "edge_converged",
                config.project_name,
                feature=feature_id,
                edge=edge,
                iteration=iteration,
            ),
        )

    # 6. Return the record — spawn decisions are orchestrator responsibility (ADR-019)
    return IterationRecord(
        edge=edge,
        iteration=iteration,
        evaluation=evaluation,
        construct_result=construct_result,
    )


def run_edge(
    edge: str,
    config: EngineConfig,
    feature_id: str,
    profile: dict,
    asset_content: str,
    context: str = "",
    construct: bool = False,
    output_path: Path | None = None,
) -> list[IterationRecord]:
    """Iterate on a single edge until convergence or budget exhaustion."""
    edge_config_path = config.edge_params_dir / f"{_edge_to_filename(edge)}.yml"
    edge_key = edge.replace("→", "_").replace("↔", "_").replace(" ", "")

    if not edge_config_path.exists():
        edge_config_path = config.edge_params_dir / f"{edge_key}.yml"

    if not edge_config_path.exists():
        events_path = (
            config.workspace_path / ".ai-workspace" / "events" / "events.jsonl"
        )
        emit_event(
            events_path,
            make_event(
                "iteration_completed",
                config.project_name,
                feature=feature_id,
                edge=edge,
                iteration=0,
                delta=-1,
                status="error",
                error=f"No edge config found for '{edge}'",
            ),
        )
        return []

    edge_config = load_yaml(edge_config_path)
    records = []

    for i in range(1, config.max_iterations_per_edge + 1):
        record = iterate_edge(
            edge=edge,
            edge_config=edge_config,
            config=config,
            feature_id=feature_id,
            asset_content=asset_content,
            context=context,
            iteration=i,
            construct=construct,
            output_path=output_path,
        )
        records.append(record)

        # If construct produced an artifact, use it for subsequent iterations
        if record.construct_result and record.construct_result.artifact:
            asset_content = record.construct_result.artifact

        if record.evaluation.converged:
            break

        # Spawn detection at orchestrator level (not inside iterate_edge)
        from .fd_spawn import (
            detect_spawn_condition,
            create_child_vector,
            link_parent_child,
            emit_spawn_events,
            load_events as load_spawn_events,
        )

        spawn_request = detect_spawn_condition(
            load_spawn_events(config.workspace_path), feature_id, edge, threshold=3
        )
        if spawn_request:
            spawn_result = create_child_vector(
                config.workspace_path, spawn_request, config.project_name
            )
            link_parent_child(
                config.workspace_path,
                feature_id,
                spawn_result.child_id,
                spawn_request.vector_type,
                spawn_request,
            )
            emit_spawn_events(
                config.workspace_path,
                config.project_name,
                spawn_request,
                spawn_result,
            )
            record.evaluation.spawn_requested = spawn_result.child_id
            break  # Parent is now blocked — stop iterating

    return records


def run(
    feature_id: str,
    feature_type: str,
    config: EngineConfig,
    asset_content: str,
    context: str = "",
    construct: bool = False,
    output_dir: Path | None = None,
) -> list[IterationRecord]:
    """Full graph traversal — deterministic loop, Claude Code for evaluation.

    Routes through edges in profile order, iterating each until convergence.
    When construct=True, threads context between edges: each converged edge's
    artifact is appended to the context for the next edge (REQ-F-FPC-003).
    """
    profile_name = select_profile(feature_type, config.profiles_dir)
    profile = load_yaml(config.profiles_dir / f"{profile_name}.yml")

    feature_trajectory = {
        "feature_id": feature_id,
        "trajectory": {},
    }

    all_records = []
    accumulated_context = context

    route = select_next_edge(feature_trajectory, config.graph_topology, profile)

    while route.selected_edge:
        edge = route.selected_edge

        # Determine output path for this edge's artifact
        output_path = None
        if construct and output_dir:
            edge_filename = edge.replace("→", "_").replace("↔", "_").replace(" ", "")
            output_path = output_dir / f"{feature_id}_{edge_filename}.md"

        records = run_edge(
            edge=edge,
            config=config,
            feature_id=feature_id,
            profile=profile,
            asset_content=asset_content,
            context=accumulated_context,
            construct=construct,
            output_path=output_path,
        )
        all_records.extend(records)

        edge_key = edge.replace("→", "_").replace("↔", "_").replace(" ", "")
        if records and records[-1].evaluation.converged:
            feature_trajectory["trajectory"][edge_key] = {"status": "converged"}

            # Thread constructed artifact as context for next edge (REQ-F-FPC-003)
            if construct and records[-1].construct_result:
                last_artifact = records[-1].construct_result.artifact
                if last_artifact:
                    accumulated_context += (
                        f"\n\n--- {edge} artifact ---\n{last_artifact}"
                    )

        elif records and records[-1].evaluation.spawn_requested:
            feature_trajectory["trajectory"][edge_key] = {
                "status": "blocked",
                "blocked_by": records[-1].evaluation.spawn_requested,
            }
            break
        else:
            feature_trajectory["trajectory"][edge_key] = {"status": "iterating"}
            break

        route = select_next_edge(feature_trajectory, config.graph_topology, profile)

    return all_records


def _edge_to_filename(edge: str) -> str:
    """Convert edge name to config filename."""
    edge_map = {
        "code↔unit_tests": "tdd",
        "design→test_cases": "design_tests",
        "design→uat_tests": "bdd",
    }
    if edge in edge_map:
        return edge_map[edge]
    return edge.replace("→", "_").replace("↔", "_").replace(" ", "")
