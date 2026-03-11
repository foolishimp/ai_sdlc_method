# Implements: REQ-EVAL-003 (Human Accountability)
"""Human gate event emission and accountability audit trail.
"""

from __future__ import annotations

import fcntl
import json
import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .ol_event import normalize_event

# \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
# DECISION TYPES
# \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
DECISION_OVERRIDE_APPROVE = "override_approve"
DECISION_OVERRIDE_REJECT = "override_reject"
DECISION_DEFER = "defer"

_VALID_DECISIONS = frozenset(
    [
        DECISION_APPROVE,
        DECISION_REJECT,
        DECISION_OVERRIDE_APPROVE,
        DECISION_OVERRIDE_REJECT,
        DECISION_DEFER,
    ]
)

@dataclass
class HumanGateEvent:
    event_id: str
    feature: str
    edge: str
    iteration: int
    actor: str
    trigger: str
    timestamp: str
    suggestions: list[dict[str, Any]] = field(default_factory=list)
    project: str = ""

@dataclass
class HumanDecisionEvent:
    event_id: str
    gate_event_id: str
    feature: str
    edge: str
    iteration: int
    actor: str
    decision: str
    reason: str
    timestamp: str
    overrides_ai: bool
    project: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

def _append_event(events_path: Path, event: dict[str, Any]) -> None:
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
    if decision not in _VALID_DECISIONS:
        raise ValueError(f"Invalid decision {decision!r}")

    _ai_markers = ("agent", "llm", "claude", "gemini", "gpt", "openai", "anthropic", "codex", "bot", "worker", "evaluator")
    actor_lower = actor.lower()
    if any(marker in actor_lower for marker in _ai_markers):
        raise ValueError(f"actor {actor!r} appears to be an AI identity. Human decisions must be attributed to humans.")

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

def load_events(events_path: Path) -> list[dict[str, Any]]:
    if not events_path.exists():
        return []
    events = []
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(normalize_event(json.loads(line)))
                except:
                    continue
    return events

def get_human_gates(events: list[dict[str, Any]], feature: Optional[str] = None, edge: Optional[str] = None) -> list[dict[str, Any]]:
    gates = [e for e in events if e.get("event_type") == "human_gate_entered"]
    if feature:
        gates = [g for g in gates if g.get("feature") == feature]
    if edge:
        gates = [g for g in gates if g.get("edge") == edge]
    return gates

def get_human_decisions(events: list[dict[str, Any]], feature: Optional[str] = None, edge: Optional[str] = None, actor: Optional[str] = None) -> list[dict[str, Any]]:
    decisions = [e for e in events if e.get("event_type") == "human_decision"]
    if feature:
        decisions = [d for d in decisions if d.get("feature") == feature]
    if edge:
        decisions = [d for d in decisions if d.get("edge") == edge]
    if actor:
        decisions = [d for d in decisions if d.get("actor") == actor]
    return decisions

def get_pending_gates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates = get_human_gates(events)
    decisions = get_human_decisions(events)
    decided_gate_ids = {d.get("gate_event_id") for d in decisions if d.get("gate_event_id")}
    return [g for g in gates if g.get("event_id") not in decided_gate_ids]

def get_override_decisions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = get_human_decisions(events)
    return [d for d in decisions if d.get("overrides_ai") or d.get("decision") in (DECISION_OVERRIDE_APPROVE, DECISION_OVERRIDE_REJECT)]

def audit_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    gates = get_human_gates(events)
    decisions = get_human_decisions(events)
    pending = get_pending_gates(events)
    overrides = get_override_decisions(events)
    
    actors = sorted(list({d.get("actor") for d in decisions if d.get("actor")}))
    
    by_decision = {}
    for d in decisions:
        dec = d.get("decision")
        by_decision[dec] = by_decision.get(dec, 0) + 1
        
    return {
        "gates_entered": len(gates),
        "decisions_made": len(decisions),
        "pending_gates": len(pending),
        "override_count": len(overrides),
        "actors": actors,
        "by_decision": by_decision
    }

def requires_human_review(config: dict[str, Any]) -> bool:
    checklist = config.get("checklist", [])
    for entry in checklist:
        if entry.get("type", "").lower() == "human":
            return True
    return False

def get_human_evaluators(config: dict[str, Any]) -> list[dict[str, Any]]:
    checklist = config.get("checklist", [])
    return [e for e in checklist if e.get("type", "").lower() == "human"]
