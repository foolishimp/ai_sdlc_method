# Implements: REQ-F-DISPATCH-001
"""EDGE_RUNNER — composes F_D → F_P → F_H for a single feature+edge traversal.

This is the effector half of the homeostatic dispatch loop. Given a
DispatchTarget from IntentObserver, EDGE_RUNNER:

1. Emits edge_started (with intent_id — idempotency marker for IntentObserver)
2. Runs F_D evaluation (via engine iterate_edge, deterministic_only=True)
3. If delta=0: emits edge_converged, returns "converged"
4. If delta>0 and F_P iterations < max_fp_iterations: writes fp_intent manifest
   (fold-back protocol), returns "fp_dispatched"
5. If F_P exhausted or budget exceeded: emits intent_raised with
   signal_source="human_gate_required", returns "fh_required"
6. If max_iterations exhausted with no convergence: returns "stuck"

Design decisions (ADR-S-032):
- F_D runs pure deterministic evaluation (deterministic_only=True in engine)
- F_P uses the fold-back protocol: write manifest, check for result next iteration
- F_H boundary is preserved: EDGE_RUNNER cannot resolve human gates autonomously
- Budget tracking is approximate (USD cap on F_P attempt count)
- Run IDs: uuid4 per edge_runner invocation
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .intent_observer import DispatchTarget
from .ol_event import emit_ol_event, make_ol_event


# ── Config constants ───────────────────────────────────────────────────────────

DEFAULT_BUDGET_USD = 0.50
MAX_FP_ITERATIONS = 3
COST_PER_FP_ITERATION = 0.15  # approximate cost per F_P call


@dataclass
class EdgeRunResult:
    """Result of executing EDGE_RUNNER for one dispatch target."""

    run_id: str
    feature_id: str
    edge: str
    status: str  # "converged" | "fp_dispatched" | "fh_required" | "stuck"
    delta: int
    iterations: int
    cost_usd: float
    events_emitted: list[str] = field(default_factory=list)
    fp_manifest_path: str = ""
    error: str = ""


# ── F_D evaluation ─────────────────────────────────────────────────────────────


def _run_fd_evaluation(
    target: DispatchTarget,
    workspace_root: Path,
    edge_run_id: str,
    project_name: str,
) -> tuple[int, list[str]]:
    """Run F_D deterministic evaluation for the given feature+edge.

    Returns (delta, list_of_failed_check_names).
    Falls back to delta=1 on import error (engine not available in test context).
    """
    try:
        import sys
        # Ensure genesis package is importable
        genesis_parent = Path(__file__).parent.parent
        if str(genesis_parent) not in sys.path:
            sys.path.insert(0, str(genesis_parent))

        from .config_loader import load_yaml
        from .engine import EngineConfig, iterate_edge as engine_iterate_edge

        # Load edge config
        edge_params_dir = (
            workspace_root
            / "imp_claude"
            / "code"
            / ".claude-plugin"
            / "plugins"
            / "genesis"
            / "config"
            / "edge_params"
        )

        # Load graph topology for EngineConfig
        topology_path = (
            workspace_root
            / "imp_claude"
            / "code"
            / ".claude-plugin"
            / "plugins"
            / "genesis"
            / "config"
            / "graph_topology.yml"
        )
        graph_topology = load_yaml(topology_path) if topology_path.exists() else {}

        profiles_dir = edge_params_dir.parent / "profiles"

        config = EngineConfig(
            project_name=project_name,
            workspace_path=workspace_root,
            edge_params_dir=edge_params_dir,
            profiles_dir=profiles_dir,
            constraints=target.feature_vector.get("constraints", {}),
            graph_topology=graph_topology,
            max_iterations_per_edge=1,
            deterministic_only=True,
        )

        # Resolve edge config filename
        edge_key = target.edge.replace("→", "_").replace("↔", "_").replace(" ", "")
        edge_config_path = edge_params_dir / f"{edge_key}.yml"
        if not edge_config_path.exists():
            # Try edge_map lookup
            edge_map = {
                "code↔unit_tests": "tdd",
                "design→test_cases": "design_tests",
                "design→uat_tests": "bdd",
            }
            fname = edge_map.get(target.edge, edge_key)
            edge_config_path = edge_params_dir / f"{fname}.yml"

        if not edge_config_path.exists():
            # No edge config — cannot evaluate, treat as delta=1
            return 1, [f"no_edge_config:{target.edge}"]

        edge_config = load_yaml(edge_config_path)

        record = engine_iterate_edge(
            edge=target.edge,
            edge_config=edge_config,
            config=config,
            feature_id=target.feature_id,
            asset_content="",
            iteration=1,
            construct=False,
            edge_run_id=edge_run_id,
            edge_correlation_id=edge_run_id,
        )

        failures = [
            cr.name
            for cr in record.evaluation.checks
            if cr.required and cr.outcome.value in ("fail", "error")
        ]
        return record.evaluation.delta, failures

    except Exception as exc:
        # Engine not available or config error — treat as delta=1
        return 1, [f"engine_error:{exc}"]


# ── F_P manifest ───────────────────────────────────────────────────────────────


def _write_fp_manifest(
    target: DispatchTarget,
    workspace_root: Path,
    run_id: str,
    iteration: int,
    budget_usd: float,
    failures: list[str],
) -> Path:
    """Write fp_intent manifest for the fold-back protocol.

    The LLM actor (invoked via gen-iterate MCP) reads this manifest, does the
    construction work, and writes the fold-back result to fp_result_{run_id}.json.
    """
    agents_dir = workspace_root / ".ai-workspace" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "edge": target.edge,
        "feature": target.feature_id,
        "intent_id": target.intent_id,
        "iteration": iteration,
        "grain": "iteration",
        "budget_usd": budget_usd,
        "max_depth": 3,
        "failures": failures,
        "constraints": target.feature_vector.get("constraints", {}),
        "result_path": str(agents_dir / f"fp_result_{run_id}.json"),
        "status": "pending",
        "source": "edge_runner",
    }
    intent_path = agents_dir / f"fp_intent_{run_id}.json"
    intent_path.write_text(json.dumps(manifest, indent=2))
    return intent_path


def _check_fp_result(workspace_root: Path, run_id: str) -> dict[str, Any] | None:
    """Check if a fold-back result exists for the given run_id."""
    result_path = workspace_root / ".ai-workspace" / "agents" / f"fp_result_{run_id}.json"
    if result_path.exists():
        try:
            return json.loads(result_path.read_text())
        except Exception:
            return None
    return None


# ── Event helpers ──────────────────────────────────────────────────────────────


def _emit(
    events_path: Path,
    event_type: str,
    target: DispatchTarget,
    project: str,
    run_id: str,
    causation_id: str | None,
    payload: dict[str, Any],
) -> str:
    """Emit a single OL event and return its run_id."""
    return emit_ol_event(
        events_path,
        make_ol_event(
            event_type,
            target.edge,
            project,
            target.feature_id,
            "edge-runner",
            causation_id=causation_id,
            correlation_id=run_id,
            payload=payload,
        ),
    )


# ── Main EDGE_RUNNER ───────────────────────────────────────────────────────────


def run_edge(
    target: DispatchTarget,
    workspace_root: Path,
    events_path: Path,
    project_name: str = "ai_sdlc_method",
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_fp_iterations: int = MAX_FP_ITERATIONS,
) -> EdgeRunResult:
    """Execute EDGE_RUNNER for a single dispatch target.

    Phase 1: F_D gate
    Phase 2: F_P fold-back (up to max_fp_iterations)
    Phase 3: F_H escalation (if F_P exhausted)

    Returns EdgeRunResult with final status.
    """
    run_id = str(uuid.uuid4())
    events_emitted: list[str] = []
    cost_usd = 0.0
    fp_iteration = 0
    failures: list[str] = []

    # Emit edge_started (carries intent_id — IntentObserver idempotency marker)
    edge_started_id = _emit(
        events_path,
        "EdgeStarted",
        target,
        project_name,
        run_id,
        None,
        {
            "feature": target.feature_id,
            "edge": target.edge,
            "intent_id": target.intent_id,
            "source": "edge_runner",
        },
    )
    events_emitted.append("EdgeStarted")

    # ── Phase 1: F_D evaluation ────────────────────────────────────────────────
    delta, failures = _run_fd_evaluation(target, workspace_root, edge_started_id, project_name)

    # Emit IterationCompleted for the F_D pass
    _emit(
        events_path,
        "IterationCompleted",
        target,
        project_name,
        run_id,
        edge_started_id,
        {
            "feature": target.feature_id,
            "edge": target.edge,
            "iteration": 1,
            "delta": delta,
            "status": "converged" if delta == 0 else "iterating",
            "phase": "F_D",
            "failures": failures[:10],  # cap for event size
        },
    )
    events_emitted.append("IterationCompleted")

    if delta == 0:
        # Converged at F_D — done
        _emit(
            events_path,
            "EdgeConverged",
            target,
            project_name,
            run_id,
            edge_started_id,
            {
                "feature": target.feature_id,
                "edge": target.edge,
                "iteration": 1,
                "phase": "F_D",
                "delta": 0,
            },
        )
        events_emitted.append("EdgeConverged")
        return EdgeRunResult(
            run_id=run_id,
            feature_id=target.feature_id,
            edge=target.edge,
            status="converged",
            delta=0,
            iterations=1,
            cost_usd=cost_usd,
            events_emitted=events_emitted,
        )

    # ── Phase 2: F_P fold-back ─────────────────────────────────────────────────
    fp_manifest_path = ""
    while fp_iteration < max_fp_iterations:
        if cost_usd >= budget_usd:
            break

        fp_iteration += 1
        cost_usd += COST_PER_FP_ITERATION

        # Write fp_intent manifest
        fp_run_id = f"{run_id}-fp{fp_iteration}"
        manifest_path = _write_fp_manifest(
            target, workspace_root, fp_run_id, fp_iteration, budget_usd, failures
        )
        fp_manifest_path = str(manifest_path)

        # Check for existing fold-back result (prior run in same session)
        fp_result = _check_fp_result(workspace_root, fp_run_id)
        if fp_result is None:
            # No result yet — manifest written, actor needs to be invoked
            _emit(
                events_path,
                "IterationCompleted",
                target,
                project_name,
                run_id,
                edge_started_id,
                {
                    "feature": target.feature_id,
                    "edge": target.edge,
                    "iteration": 1 + fp_iteration,
                    "delta": delta,
                    "status": "fp_pending",
                    "phase": "F_P",
                    "fp_run_id": fp_run_id,
                    "fp_manifest_path": str(manifest_path),
                },
            )
            events_emitted.append("IterationCompleted")
            return EdgeRunResult(
                run_id=run_id,
                feature_id=target.feature_id,
                edge=target.edge,
                status="fp_dispatched",
                delta=delta,
                iterations=1 + fp_iteration,
                cost_usd=cost_usd,
                events_emitted=events_emitted,
                fp_manifest_path=fp_manifest_path,
            )

        # Fold-back result available — re-evaluate F_D
        delta, failures = _run_fd_evaluation(target, workspace_root, edge_started_id, project_name)
        _emit(
            events_path,
            "IterationCompleted",
            target,
            project_name,
            run_id,
            edge_started_id,
            {
                "feature": target.feature_id,
                "edge": target.edge,
                "iteration": 1 + fp_iteration,
                "delta": delta,
                "status": "converged" if delta == 0 else "iterating",
                "phase": "F_P_result",
                "fp_run_id": fp_run_id,
                "fp_cost_usd": fp_result.get("cost_usd", 0.0),
            },
        )
        events_emitted.append("IterationCompleted")
        cost_usd += fp_result.get("cost_usd", 0.0)

        if delta == 0:
            _emit(
                events_path,
                "EdgeConverged",
                target,
                project_name,
                run_id,
                edge_started_id,
                {
                    "feature": target.feature_id,
                    "edge": target.edge,
                    "iteration": 1 + fp_iteration,
                    "phase": "F_P",
                    "delta": 0,
                },
            )
            events_emitted.append("EdgeConverged")
            return EdgeRunResult(
                run_id=run_id,
                feature_id=target.feature_id,
                edge=target.edge,
                status="converged",
                delta=0,
                iterations=1 + fp_iteration,
                cost_usd=cost_usd,
                events_emitted=events_emitted,
                fp_manifest_path=fp_manifest_path,
            )

    # ── Phase 3: F_H escalation ────────────────────────────────────────────────
    # F_P exhausted (or budget exceeded) — escalate to human gate
    _emit(
        events_path,
        "IterationCompleted",
        target,
        project_name,
        run_id,
        edge_started_id,
        {
            "feature": target.feature_id,
            "edge": target.edge,
            "iteration": 1 + fp_iteration,
            "delta": delta,
            "status": "fh_required",
            "phase": "F_H",
            "fp_iterations_exhausted": fp_iteration,
            "budget_usd": budget_usd,
            "cost_usd": cost_usd,
        },
    )
    events_emitted.append("IterationCompleted")

    # Emit intent_raised for human escalation
    _emit(
        events_path,
        "IterationCompleted",  # Use intent_raised-like payload but within iteration chain
        target,
        project_name,
        run_id,
        edge_started_id,
        {
            "feature": target.feature_id,
            "edge": target.edge,
            "intent_id": target.intent_id,
            "signal_source": "human_gate_required",
            "delta": delta,
            "failures": failures[:10],
            "fp_iterations_attempted": fp_iteration,
            "reason": (
                f"F_P exhausted after {fp_iteration} iterations. "
                f"Delta={delta}. Human review required."
            ),
        },
    )
    events_emitted.append("FH_escalation")

    # Emit a proper intent_raised event for the human gate
    emit_ol_event(
        events_path,
        make_ol_event(
            "intent_raised",
            target.edge,
            project_name,
            target.feature_id,
            "edge-runner",
            correlation_id=run_id,
            payload={
                "intent_id": f"{target.intent_id}:fh:{run_id[:8]}",
                "signal_source": "human_gate_required",
                "parent_intent_id": target.intent_id,
                "feature": target.feature_id,
                "edge": target.edge,
                "delta": delta,
                "failures": failures[:10],
                "fp_iterations_attempted": fp_iteration,
                "affected_features": [target.feature_id],
            },
        ),
    )
    events_emitted.append("intent_raised:fh")

    status = "fh_required" if fp_iteration > 0 else "stuck"
    return EdgeRunResult(
        run_id=run_id,
        feature_id=target.feature_id,
        edge=target.edge,
        status=status,
        delta=delta,
        iterations=1 + fp_iteration,
        cost_usd=cost_usd,
        events_emitted=events_emitted,
        fp_manifest_path=fp_manifest_path,
    )
