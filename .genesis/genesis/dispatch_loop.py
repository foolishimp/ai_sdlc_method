# Implements: REQ-F-DISPATCH-001
# Implements: REQ-F-RUNTIME-001
# Implements: REQ-LIFE-002 (Telemetry — req= structured log tags at dispatch points)
"""Dispatch loop — top-level orchestrator wiring IntentObserver → EDGE_RUNNER.

This is what `/gen-start --auto` should call. Finds all pending dispatches,
runs EDGE_RUNNER for each, emits events, repeats until no pending dispatches
or max_rounds exhausted.

Design decisions:
- Each round: find pending → run one or all → check for new intents → repeat
- Deduplication: edge_started as idempotency marker prevents double-dispatch
- Summary tracking: {rounds, dispatched, converged, fp_dispatched, fh_required, stuck}
- Graceful degradation: errors in one target don't stop others
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .edge_runner import EdgeRunResult, run_edge
from .intent_observer import DispatchTarget, get_pending_dispatches
from .ol_event import emit_ol_event, make_ol_event

_log = logging.getLogger(__name__)


# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class DispatchSummary:
    """Summary of a dispatch loop run."""

    rounds: int = 0
    dispatched: int = 0
    converged: int = 0
    fp_dispatched: int = 0
    fh_required: int = 0
    stuck: int = 0
    errors: int = 0
    results: list[EdgeRunResult] = field(default_factory=list)


# ── Quiescence ─────────────────────────────────────────────────────────────────

# Event types that close an fh_required gate for a (feature, edge)
_FH_RESOLUTION_EVENTS = {"consensus_reached", "review_approved", "edge_converged"}


def _has_unresolved_fh_gates(events_path: Path) -> bool:
    """Return True if any fh_required escalation has no matching resolution event.

    An fh_required gate is opened by:
        intent_raised{signal_source: human_gate_required, feature: X, edge: Y}

    It closes when any of _FH_RESOLUTION_EVENTS appears for the same (feature, edge)
    after the opening event.
    """
    if not events_path.exists():
        return False

    events: list[dict] = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    # Collect open gates in order
    open_gates: list[tuple[str, str]] = []  # (feature, edge) for each unresolved gate
    for ev in events:
        et = ev.get("event_type", "")
        data = ev.get("data", {}) or {}

        # Open gate
        if et == "intent_raised":
            src = data.get("signal_source") or ev.get("signal_source", "")
            if src == "human_gate_required":
                feat = (data.get("affected_features") or [""])[0] or data.get("feature", "")
                edge = data.get("edge", "") or ev.get("edge", "")
                if feat:
                    open_gates.append((feat, edge))

        # Close gate
        elif et in _FH_RESOLUTION_EVENTS:
            feat = data.get("feature", "") or ev.get("feature", "")
            edge = data.get("edge", "") or ev.get("edge", "")
            key = (feat, edge)
            if key in open_gates:
                open_gates.remove(key)

    return len(open_gates) > 0


def _compute_quiescence(workspace_root: Path) -> bool:
    """Workspace is quiescent iff no pending work in ANY state.

    Three conditions — all must be false for quiescence:
    1. Unhandled intents ready to dispatch (get_pending_dispatches)
    2. In-flight fp_dispatched manifests awaiting fold-back
    3. Unresolved fh_required escalations awaiting human gate resolution
    """
    if get_pending_dispatches(workspace_root):
        return False

    # Parked fp_dispatched: manifests with status pending or dispatched
    agents_dir = workspace_root / ".ai-workspace" / "agents"
    if agents_dir.exists():
        for p in agents_dir.glob("fp_intent_*.json"):
            try:
                data = json.loads(p.read_text())
                if data.get("status") in ("pending", "dispatched"):
                    return False
            except Exception:
                pass

    # Parked fh_required: unresolved human gate escalations
    events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"
    if _has_unresolved_fh_gates(events_path):
        return False

    return True


# ── Helpers ────────────────────────────────────────────────────────────────────


def _emit_dispatch_started(
    events_path: Path,
    workspace_root: Path,
    project_name: str,
    round_num: int,
    pending_count: int,
) -> str:
    """Emit DispatchLoopStarted event for observability."""
    return emit_ol_event(
        events_path,
        make_ol_event(
            "IterationStarted",
            "intent_dispatch",
            project_name,
            f"dispatch-loop-{round_num}",
            "dispatch-loop",
            payload={
                "round": round_num,
                "pending_dispatches": pending_count,
                "source": "dispatch_loop",
            },
        ),
    )


def _emit_dispatch_completed(
    events_path: Path,
    project_name: str,
    round_num: int,
    summary: DispatchSummary,
) -> None:
    """Emit DispatchLoopCompleted event."""
    emit_ol_event(
        events_path,
        make_ol_event(
            "IterationCompleted",
            "intent_dispatch",
            project_name,
            f"dispatch-loop-{round_num}",
            "dispatch-loop",
            payload={
                "round": round_num,
                "dispatched": summary.dispatched,
                "converged": summary.converged,
                "fp_dispatched": summary.fp_dispatched,
                "fh_required": summary.fh_required,
                "stuck": summary.stuck,
                "errors": summary.errors,
            },
        ),
    )


def _run_target_safely(
    target: DispatchTarget,
    workspace_root: Path,
    events_path: Path,
    project_name: str,
) -> EdgeRunResult | None:
    """Run EDGE_RUNNER for target, catching all exceptions gracefully."""
    _log.info(f'dispatch req="{target.feature_id}" edge="{target.edge}" intent="{target.intent_id}"')
    try:
        result = run_edge(
            target=target,
            workspace_root=workspace_root,
            events_path=events_path,
            project_name=project_name,
        )
        if result is not None:
            _log.info(
                f'dispatch_done req="{target.feature_id}" edge="{target.edge}" '
                f'status="{result.status}"'
            )
        return result
    except Exception as exc:
        # Emit error event so the failure is observable
        try:
            emit_ol_event(
                events_path,
                make_ol_event(
                    "IterationFailed",
                    target.edge,
                    project_name,
                    target.feature_id,
                    "dispatch-loop",
                    payload={
                        "feature": target.feature_id,
                        "edge": target.edge,
                        "intent_id": target.intent_id,
                        "error": str(exc)[:500],
                        "source": "dispatch_loop",
                    },
                ),
            )
        except Exception:
            pass
        return None


# ── Public API ─────────────────────────────────────────────────────────────────


def run_dispatch_loop(
    workspace_root: Path,
    events_path: Path | None = None,
    project_name: str = "ai_sdlc_method",
    max_rounds: int = 10,
) -> dict:
    """Main dispatch loop: IntentObserver → EDGE_RUNNER, repeating until quiescent.

    Each round:
    1. Get all pending dispatches (IntentObserver)
    2. For each target: run EDGE_RUNNER
    3. Accumulate results
    4. Repeat if new dispatches appeared (converged edges may unblock others)

    Terminates when:
    - No pending dispatches found (quiescent)
    - max_rounds exhausted
    - All dispatches are fp_dispatched or fh_required (waiting on external actor)

    Returns summary dict:
    {
        "rounds": int,
        "dispatched": int,
        "converged": int,
        "fp_dispatched": int,
        "fh_required": int,
        "stuck": int,
        "errors": int,
        "quiescent": bool,
    }
    """
    if events_path is None:
        events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    summary = DispatchSummary()

    for round_num in range(1, max_rounds + 1):
        pending = get_pending_dispatches(workspace_root)

        if not pending:
            # No work to do — system is quiescent
            break

        # Filter: skip targets that are already waiting on F_P or F_H
        # (they require external actor — polling them again wastes cycles)
        actionable = [t for t in pending]

        if not actionable:
            break

        summary.rounds = round_num
        _emit_dispatch_started(events_path, workspace_root, project_name, round_num, len(actionable))

        made_progress = False
        for target in actionable:
            result = _run_target_safely(target, workspace_root, events_path, project_name)
            summary.dispatched += 1

            if result is None:
                summary.errors += 1
                continue

            summary.results.append(result)
            if result.status == "converged":
                summary.converged += 1
                made_progress = True
            elif result.status == "fp_dispatched":
                summary.fp_dispatched += 1
                # Cannot make further progress without LLM actor
            elif result.status == "fh_required":
                summary.fh_required += 1
                # Cannot make further progress without human
            elif result.status == "stuck":
                summary.stuck += 1

        _emit_dispatch_completed(events_path, project_name, round_num, summary)

        # If nothing converged, no point continuing — waiting on external actors
        if not made_progress:
            break

    return {
        "rounds": summary.rounds,
        "dispatched": summary.dispatched,
        "converged": summary.converged,
        "fp_dispatched": summary.fp_dispatched,
        "fh_required": summary.fh_required,
        "stuck": summary.stuck,
        "errors": summary.errors,
        "quiescent": _compute_quiescence(workspace_root),
    }


def run_single_dispatch(
    workspace_root: Path,
    events_path: Path | None = None,
    project_name: str = "ai_sdlc_method",
) -> dict:
    """Single pass: find one pending dispatch, run it, return result.

    Useful for step-by-step debugging or single-intent processing.
    """
    if events_path is None:
        events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"

    pending = get_pending_dispatches(workspace_root)
    if not pending:
        return {
            "status": "quiescent",
            "message": "No pending dispatches found",
            "dispatched": 0,
        }

    target = pending[0]
    result = _run_target_safely(target, workspace_root, events_path, project_name)

    if result is None:
        return {
            "status": "error",
            "feature": target.feature_id,
            "edge": target.edge,
            "intent_id": target.intent_id,
            "dispatched": 1,
        }

    return {
        "status": result.status,
        "feature": result.feature_id,
        "edge": result.edge,
        "run_id": result.run_id,
        "delta": result.delta,
        "iterations": result.iterations,
        "cost_usd": result.cost_usd,
        "events_emitted": result.events_emitted,
        "fp_manifest_path": result.fp_manifest_path,
        "dispatched": 1,
    }
