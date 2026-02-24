# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-EVAL-002 (Evaluator Composition)
"""Deterministic engine — owns the graph traversal loop.

F_D controls: routing, emission, delta computation, convergence decisions.
F_P is called: for agent evaluation via Claude Code CLI.
F_H is called: for human evaluation (future — currently skips).

The LLM cannot skip emission. The deterministic code calls it, takes its
answer, records everything, then decides what to do next.
"""

from dataclasses import dataclass
from pathlib import Path

from .config_loader import load_yaml, resolve_checklist
from .fd_emit import emit_event, make_event
from .fd_evaluate import run_check as fd_run_check
from .fd_route import select_next_edge, select_profile
from .fp_evaluate import run_check as fp_run_check
from .models import (
    CheckOutcome,
    CheckResult,
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


@dataclass
class IterationRecord:
    """Record of one iteration — what happened, what was decided."""

    edge: str
    iteration: int
    evaluation: EvaluationResult
    event_emitted: bool = True


def iterate_edge(
    edge: str,
    edge_config: dict,
    config: EngineConfig,
    feature_id: str,
    asset_content: str,
    context: str = "",
    iteration: int = 1,
) -> IterationRecord:
    """Run one iteration on a single edge.

    This is the core loop body. F_D owns every step:
    1. Resolve checklist ($variables)
    2. Evaluate each check (dispatch by type: F_D subprocess or F_P Claude Code)
    3. Compute delta (deterministic)
    4. Emit event (deterministic — ALWAYS fires)
    5. Return the record
    """
    # 1. F_D: Resolve checklist
    checks = resolve_checklist(edge_config, config.constraints)

    # 2. Evaluate each check — dispatch by type
    results: list[CheckResult] = []
    escalations: list[str] = []

    for check in checks:
        if check.check_type == "deterministic":
            cr = fd_run_check(check, config.workspace_path)
        elif check.check_type == "agent":
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

        # η detection
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR):
            if cr.check_type == "deterministic":
                escalations.append(f"η_D→P: {cr.name} — deterministic failure")
            elif cr.check_type == "agent":
                escalations.append(f"η_P→H: {cr.name} — agent evaluation failed")

    # 3. F_D: Compute delta — DETERMINISTIC
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

    # 4. F_D: Emit event — THIS ALWAYS FIRES
    events_path = config.workspace_path / ".ai-workspace" / "events" / "events.jsonl"

    check_summary = [
        {
            "name": cr.name,
            "type": cr.check_type,
            "outcome": cr.outcome.value,
            "required": cr.required,
        }
        for cr in results
    ]

    emit_event(
        events_path,
        make_event(
            "iteration_completed",
            config.project_name,
            feature=feature_id,
            edge=edge,
            iteration=iteration,
            delta=delta,
            status="converged" if converged else "iterating",
            checks=check_summary,
            escalations=escalations,
        ),
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

    
    # η_P→H: Check for Recursive Spawn
    if any("spawn" in cr.message.lower() for cr in results):
        child_id = f"{feature_id}-DISC"
        print(f"[RECURSION] Spawning child {child_id}...")
        emit_event(events_path, make_event("feature_spawned", config.project_name, feature=feature_id, data={"child": child_id}))
        # Implementation of recursive loop would go here
        emit_event(events_path, make_event("spawn_folded_back", config.project_name, feature=feature_id, data={"child": child_id}))

    return IterationRecord(
        edge=edge,
        iteration=iteration,
        evaluation=evaluation,
    )


def run_edge(
    edge: str,
    config: EngineConfig,
    feature_id: str,
    profile: dict,
    asset_content: str,
    context: str = "",
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
        )
        records.append(record)

        if record.evaluation.converged:
            break

    return records


def run(
    feature_id: str,
    feature_type: str,
    config: EngineConfig,
    asset_content: str,
    context: str = "",
) -> list[IterationRecord]:
    """Full graph traversal — deterministic loop, Claude Code for evaluation.

    Routes through edges in profile order, iterating each until convergence.
    """
    profile_name = select_profile(feature_type, config.profiles_dir)
    profile = load_yaml(config.profiles_dir / f"{profile_name}.yml")

    feature_trajectory = {
        "feature_id": feature_id,
        "trajectory": {},
    }

    all_records = []

    route = select_next_edge(feature_trajectory, config.graph_topology, profile)

    while route.selected_edge:
        edge = route.selected_edge

        records = run_edge(
            edge=edge,
            config=config,
            feature_id=feature_id,
            profile=profile,
            asset_content=asset_content,
            context=context,
        )
        all_records.extend(records)

        edge_key = edge.replace("→", "_").replace("↔", "_").replace(" ", "")
        if records and records[-1].evaluation.converged:
            feature_trajectory["trajectory"][edge_key] = {"status": "converged"}
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
