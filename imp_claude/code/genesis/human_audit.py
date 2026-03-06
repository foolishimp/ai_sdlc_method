# Implements: REQ-EVAL-003 (Human Accountability)
"""Human gate event emission and accountability audit trail.

Humans remain accountable for all decisions at F_H evaluation points.
AI (F_P) suggestions require human review at edges where a Human evaluator
is configured. This module:

  1. Emits structured human_gate_entered / human_decision events to events.jsonl
  2. Provides query functions for the accountability audit trail
  3. Detects edges that require F_H review from their evaluator config
  4. Records decisions with attribution — decisions attributed to humans, not AI

Event schema:
  human_gate_entered: {feature, edge, iteration, actor, trigger, suggestions}
  human_decision:     {feature, edge, iteration, actor, decision, reason, overrides_ai}

Attribution:
  actor field always identifies the human decision-maker.
  AI contributions are recorded in suggestions (advisory only).
  Override capability is always available (decision="override_approve" / "override_reject").
"""

from __future__ import annotations

import fcntl
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════
# DECISION TYPES
# ═══════════════════════════════════════════════════════════════════════

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
DECISION_OVERRIDE_APPROVE = "override_approve"  # overrides AI suggestion
DECISION_OVERRIDE_REJECT = "override_reject"    # overrides AI suggestion
DECISION_DEFER = "defer"                        # defer to next iteration

_VALID_DECISIONS = frozenset([
    DECISION_APPROVE,
    DECISION_REJECT,
    DECISION_OVERRIDE_APPROVE,
    DECISION_OVERRIDE_REJECT,
    DECISION_DEFER,
])


# ═══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class HumanGateEvent:
    """Record of a human gate being entered (before the decision)."""

    event_id: str
    feature: str
    edge: str
    iteration: int
    actor: str                       # identity of the human reviewer
    trigger: str                     # what caused the gate: "evaluator_required", "escalated", "manual"
    timestamp: str
    suggestions: list[dict[str, Any]] = field(default_factory=list)  # AI suggestions (advisory)
    project: str = ""


@dataclass
class HumanDecisionEvent:
    """Record of a human decision at a gate."""

    event_id: str
    gate_event_id: str               # links to the HumanGateEvent
    feature: str
    edge: str
    iteration: int
    actor: str                       # human who decided — NEVER "ai" or agent name
    decision: str                    # approve | reject | override_approve | override_reject | defer
    reason: str                      # human-authored justification
    timestamp: str
    overrides_ai: bool               # True when AI suggested differently
    project: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════
# EDGE CONFIG INSPECTION
# ═══════════════════════════════════════════════════════════════════════


def requires_human_review(edge_config: dict[str, Any]) -> bool:
    """Return True if this edge config contains at least one F_H (human) evaluator.

    Checks the `checklist` list for entries with type == "human".
    """
    checklist = edge_config.get("checklist", [])
    return any(
        isinstance(entry, dict) and entry.get("type", "").lower() == "human"
        for entry in checklist
    )


def get_human_evaluators(edge_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all human evaluator entries from an edge config's checklist."""
    return [
        entry
        for entry in edge_config.get("checklist", [])
        if isinstance(entry, dict) and entry.get("type", "").lower() == "human"
    ]


# ═══════════════════════════════════════════════════════════════════════
# EVENT EMISSION
# ═══════════════════════════════════════════════════════════════════════


def _append_event(events_path: Path, event: dict[str, Any]) -> None:
    """Append one JSON line to events.jsonl (atomic write with file lock)."""
    events_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
    with open(events_path, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def emit_human_gate_entered(
    events_path: Path,
    feature: str,
    edge: str,
    project: str,
    actor: str,
    iteration: int = 1,
    trigger: str = "evaluator_required",
    suggestions: Optional[list[dict[str, Any]]] = None,
) -> str:
    """Emit a human_gate_entered event and return the event_id.

    Args:
        events_path: Path to events.jsonl
        feature:     Feature ID (e.g. REQ-F-AUTH-001)
        edge:        Edge name (e.g. "design→code")
        project:     Project name
        actor:       Identity of the human reviewer entering the gate
        iteration:   Iteration count at gate entry
        trigger:     What caused the gate: "evaluator_required" | "escalated" | "manual"
        suggestions: AI-generated suggestions (advisory, not decisions)

    Returns:
        event_id (str uuid4) for linking to the subsequent human_decision event
    """
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    event: dict[str, Any] = {
        "event_type": "human_gate_entered",
        "event_id": event_id,
        "timestamp": now,
        "project": project,
        "feature": feature,
        "edge": edge,
        "iteration": iteration,
        "actor": actor,
        "trigger": trigger,
        "suggestions": suggestions or [],
    }
    _append_event(events_path, event)
    return event_id


def emit_human_decision(
    events_path: Path,
    feature: str,
    edge: str,
    project: str,
    actor: str,
    decision: str,
    reason: str,
    gate_event_id: str,
    iteration: int = 1,
    overrides_ai: bool = False,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    """Emit a human_decision event and return the event_id.

    Args:
        events_path:   Path to events.jsonl
        feature:       Feature ID
        edge:          Edge name
        project:       Project name
        actor:         Human decision-maker identity (NEVER an AI agent name)
        decision:      One of: approve | reject | override_approve | override_reject | defer
        reason:        Human-authored justification (non-empty)
        gate_event_id: event_id from the matching human_gate_entered event
        iteration:     Iteration count at decision time
        overrides_ai:  True when AI suggested a different outcome
        extra:         Additional context (comments, linked issues, etc.)

    Returns:
        event_id (str uuid4)

    Raises:
        ValueError: if decision is not a recognised value
        ValueError: if actor looks like an AI identity (contains "agent", "llm", "claude" etc.)
    """
    if decision not in _VALID_DECISIONS:
        raise ValueError(
            f"Invalid decision {decision!r}. Must be one of: {sorted(_VALID_DECISIONS)}"
        )

    # Attribution guard — reject AI-sounding actor names for accountability
    _ai_markers = ("agent", "llm", "claude", "gemini", "gpt", "openai", "anthropic", "codex")
    actor_lower = actor.lower()
    if any(marker in actor_lower for marker in _ai_markers):
        raise ValueError(
            f"actor {actor!r} appears to be an AI identity. "
            f"Human decisions must be attributed to human actors. "
            f"Use a human name, username, or role (e.g. 'jim', 'tech-lead', 'reviewer-1')."
        )

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    event: dict[str, Any] = {
        "event_type": "human_decision",
        "event_id": event_id,
        "timestamp": now,
        "project": project,
        "feature": feature,
        "edge": edge,
        "iteration": iteration,
        "actor": actor,
        "decision": decision,
        "reason": reason,
        "gate_event_id": gate_event_id,
        "overrides_ai": overrides_ai,
        "extra": extra or {},
    }
    _append_event(events_path, event)
    return event_id


# ═══════════════════════════════════════════════════════════════════════
# AUDIT TRAIL QUERIES
# ═══════════════════════════════════════════════════════════════════════


def load_events(events_path: Path) -> list[dict[str, Any]]:
    """Load all events from events.jsonl, skipping malformed lines."""
    if not events_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def get_human_gates(
    events: list[dict[str, Any]],
    feature: Optional[str] = None,
    edge: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return all human_gate_entered events, optionally filtered by feature/edge."""
    return [
        ev for ev in events
        if ev.get("event_type") == "human_gate_entered"
        and (feature is None or ev.get("feature") == feature)
        and (edge is None or ev.get("edge") == edge)
    ]


def get_human_decisions(
    events: list[dict[str, Any]],
    feature: Optional[str] = None,
    edge: Optional[str] = None,
    actor: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return all human_decision events, optionally filtered by feature/edge/actor."""
    return [
        ev for ev in events
        if ev.get("event_type") == "human_decision"
        and (feature is None or ev.get("feature") == feature)
        and (edge is None or ev.get("edge") == edge)
        and (actor is None or ev.get("actor") == actor)
    ]


def get_pending_gates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return human_gate_entered events that have no matching human_decision.

    These are gates that have been entered but not yet decided.
    """
    decided_gate_ids: set[str] = {
        ev.get("gate_event_id", "")
        for ev in events
        if ev.get("event_type") == "human_decision"
    }
    return [
        ev for ev in events
        if ev.get("event_type") == "human_gate_entered"
        and ev.get("event_id", "") not in decided_gate_ids
    ]


def get_override_decisions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return all human decisions that overrode an AI suggestion."""
    return [
        ev for ev in events
        if ev.get("event_type") == "human_decision"
        and ev.get("overrides_ai", False)
    ]


def audit_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute an accountability audit summary from the event log.

    Returns:
        gates_entered:    total human gates entered
        decisions_made:   total human decisions recorded
        pending_gates:    gates with no decision yet
        override_count:   decisions that overrode AI suggestions
        actors:           set of human actors who have made decisions
        by_decision:      breakdown of decisions by type
    """
    gates = get_human_gates(events)
    decisions = get_human_decisions(events)
    pending = get_pending_gates(events)
    overrides = get_override_decisions(events)

    by_decision: dict[str, int] = {}
    actors: set[str] = set()
    for dec in decisions:
        d = dec.get("decision", "unknown")
        by_decision[d] = by_decision.get(d, 0) + 1
        actors.add(dec.get("actor", "unknown"))

    return {
        "gates_entered": len(gates),
        "decisions_made": len(decisions),
        "pending_gates": len(pending),
        "override_count": len(overrides),
        "actors": sorted(actors),
        "by_decision": by_decision,
    }
