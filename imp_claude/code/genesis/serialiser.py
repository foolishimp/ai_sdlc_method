# Implements: REQ-COORD-002 (Feature Assignment via Events), REQ-COORD-004 (Markov-Aligned Parallelism)
# Implements: REQ-COORD-005 (Role-Based Evaluator Authority)
"""ADR-013 Serialiser — single-writer arbiter for multi-agent edge claims.

Reads agent inboxes in deterministic order, resolves claims against the
canonical event log, and writes results (edge_started | claim_rejected |
claim_expired) to events.jsonl.

In single-agent mode the agent emits edge_started directly — no inbox,
no claim step. Both modes satisfy the invariant: events.jsonl has exactly
one writer at a time.

Inbox layout:
    .ai-workspace/events/inbox/<agent_id>/<seq>.json

Each inbox file is a single JSON event dict with event_type one of:
    edge_claim   — agent proposes to work on feature+edge
    edge_released — agent voluntarily releases a claim
"""

from __future__ import annotations

import fcntl
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .role_authority import (
    check_role_authority,
    convergence_action,
    emit_convergence_escalated,
    load_role_config,
    normalise_edge,
)


# ═══════════════════════════════════════════════════════════════════════
# CLAIM RESOLUTION
# ═══════════════════════════════════════════════════════════════════════

CLAIM_TIMEOUT_SECONDS = 3600  # 1 hour — stale after this


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_event(events_path: Path, event: dict[str, Any]) -> None:
    """Append a single event to events.jsonl (single-writer, fcntl-locked)."""
    events_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, separators=(",", ":")) + "\n"
    with open(events_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def get_active_claims(events: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    """Derive active claim map: (feature, edge) → agent_id.

    Replays the event log to find feature+edge pairs that are claimed
    (edge_started) but not yet released (edge_converged | edge_released).

    Returns:
        Dict mapping (feature, edge) → holding agent_id.
    """
    claimed: dict[tuple[str, str], str] = {}

    for ev in events:
        et = ev.get("event_type", "")
        feature = ev.get("feature", "")
        edge = ev.get("edge", "")
        if not feature or not edge:
            continue
        key = (feature, edge)

        if et == "edge_started":
            agent_id = ev.get("agent_id", ev.get("data", {}).get("agent_id", "primary"))
            claimed[key] = agent_id
        elif et in ("edge_converged", "edge_released"):
            claimed.pop(key, None)

    return claimed


def get_last_event_time(
    events: list[dict[str, Any]], agent_id: str
) -> Optional[float]:
    """Return the unix timestamp of the most recent event from agent_id, or None."""
    last: Optional[float] = None
    for ev in events:
        ev_agent = ev.get("agent_id", ev.get("data", {}).get("agent_id", ""))
        if ev_agent != agent_id:
            continue
        ts = ev.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                epoch = dt.timestamp()
                if last is None or epoch > last:
                    last = epoch
            except (ValueError, AttributeError):
                pass
    return last


def detect_stale_claims(
    events: list[dict[str, Any]],
    timeout_seconds: int = CLAIM_TIMEOUT_SECONDS,
    now: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Find active claims where the holding agent has been idle too long.

    Returns list of dicts: {feature, edge, agent_id, seconds_idle}.
    """
    if now is None:
        now = time.time()

    active = get_active_claims(events)
    stale: list[dict[str, Any]] = []

    for (feature, edge), agent_id in active.items():
        last_ts = get_last_event_time(events, agent_id)
        if last_ts is None:
            continue
        seconds_idle = now - last_ts
        if seconds_idle > timeout_seconds:
            stale.append(
                {
                    "feature": feature,
                    "edge": edge,
                    "agent_id": agent_id,
                    "seconds_idle": int(seconds_idle),
                }
            )

    return stale


# ═══════════════════════════════════════════════════════════════════════
# INBOX PROCESSING
# ═══════════════════════════════════════════════════════════════════════


def read_inbox_events(inbox_dir: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Read all pending events from inbox/<agent_id>/ subdirectories.

    Returns list of (agent_id, file_path, event_dict) tuples, sorted
    deterministically: lexicographic agent_id order, then sequence number
    within each agent's inbox.
    """
    if not inbox_dir.exists():
        return []

    items: list[tuple[str, Path, dict[str, Any]]] = []
    for agent_dir in sorted(inbox_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent_id = agent_dir.name
        for event_file in sorted(agent_dir.glob("*.json")):
            try:
                data = json.loads(event_file.read_text())
                items.append((agent_id, event_file, data))
            except (json.JSONDecodeError, OSError):
                pass

    return items


def process_inbox(
    workspace: Path,
    project: str,
    instance_id: str = "serialiser",
    timeout_seconds: int = CLAIM_TIMEOUT_SECONDS,
    roles_config: Optional[dict[str, Any]] = None,
) -> dict[str, int]:
    """Process all pending inbox events and write results to events.jsonl.

    Resolution logic:
    - edge_claim: if (feature, edge) is unclaimed AND role has authority
                    → emit edge_started (granted)
                  if already claimed by another agent → emit claim_rejected
                  if role lacks authority → emit convergence_escalated, count as escalated
    - edge_released: emit edge_released to events.jsonl, update claim map
    - Other event types: forwarded verbatim to events.jsonl

    After processing claims, check for stale claims and emit claim_expired
    for each one that has timed out.

    Returns counts: {granted, rejected, forwarded, expired, errors, escalated}.
    """
    if roles_config is None:
        try:
            roles_config = load_role_config()
        except FileNotFoundError:
            roles_config = {}

    ws_dir = workspace / ".ai-workspace" if (workspace / ".ai-workspace").exists() else workspace
    events_path = ws_dir / "events" / "events.jsonl"
    inbox_dir = ws_dir / "events" / "inbox"

    # Load current event log for claim resolution
    existing_events: list[dict[str, Any]] = []
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    existing_events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    active_claims = get_active_claims(existing_events)
    inbox_items = read_inbox_events(inbox_dir)

    counts: dict[str, int] = {
        "granted": 0,
        "rejected": 0,
        "forwarded": 0,
        "expired": 0,
        "errors": 0,
        "escalated": 0,
    }

    for agent_id, event_file, ev in inbox_items:
        et = ev.get("event_type", "")
        feature = ev.get("feature", "") or ev.get("data", {}).get("feature", "")
        edge = ev.get("edge", "") or ev.get("data", {}).get("edge", "")

        try:
            if et == "edge_claim" and feature and edge:
                key = (feature, edge)
                held_by = active_claims.get(key)

                if held_by is None or held_by == agent_id:
                    # Role authority check (REQ-COORD-005)
                    agent_role = ev.get("agent_role", "full_stack")
                    if not check_role_authority(agent_role, edge, roles_config):
                        action = convergence_action(agent_role, edge, roles_config)
                        emit_convergence_escalated(
                            events_path=events_path,
                            project=project,
                            agent_id=agent_id,
                            agent_role=agent_role,
                            feature=feature,
                            edge=edge,
                            reason=f"role '{agent_role}' not authorised to converge '{edge}'",
                            action=action,
                        )
                        counts["escalated"] += 1
                        # "warn" still grants; "escalate"/"reject" block
                        if action != "warn":
                            event_file.unlink(missing_ok=True)
                            continue

                    # Grant: emit edge_started
                    granted_event = {
                        "event_type": "edge_started",
                        "timestamp": _now_iso(),
                        "project": project,
                        "feature": feature,
                        "edge": edge,
                        "agent_id": agent_id,
                        "instance_id": instance_id,
                        "data": {"granted_to": agent_id, "source": "serialiser"},
                    }
                    _append_event(events_path, granted_event)
                    active_claims[key] = agent_id
                    existing_events.append(granted_event)
                    counts["granted"] += 1
                else:
                    # Reject: emit claim_rejected
                    rejected_event = {
                        "event_type": "claim_rejected",
                        "timestamp": _now_iso(),
                        "project": project,
                        "feature": feature,
                        "edge": edge,
                        "agent_id": agent_id,
                        "data": {
                            "reason": f"already claimed by {held_by}",
                            "held_by": held_by,
                        },
                    }
                    _append_event(events_path, rejected_event)
                    existing_events.append(rejected_event)
                    counts["rejected"] += 1

            elif et == "edge_released" and feature and edge:
                forwarded = dict(ev)
                forwarded["timestamp"] = _now_iso()
                forwarded["project"] = project
                forwarded["agent_id"] = agent_id
                _append_event(events_path, forwarded)
                active_claims.pop((feature, edge), None)
                existing_events.append(forwarded)
                counts["forwarded"] += 1

            else:
                # Forward verbatim (other event types)
                forwarded = dict(ev)
                if "project" not in forwarded:
                    forwarded["project"] = project
                if "timestamp" not in forwarded:
                    forwarded["timestamp"] = _now_iso()
                _append_event(events_path, forwarded)
                existing_events.append(forwarded)
                counts["forwarded"] += 1

            # Delete processed inbox file
            event_file.unlink(missing_ok=True)

        except Exception:
            counts["errors"] += 1

    # Check for stale claims
    stale = detect_stale_claims(existing_events, timeout_seconds=timeout_seconds)
    for s in stale:
        expired_event = {
            "event_type": "claim_expired",
            "timestamp": _now_iso(),
            "project": project,
            "feature": s["feature"],
            "edge": s["edge"],
            "agent_id": s["agent_id"],
            "data": {
                "seconds_idle": s["seconds_idle"],
                "source": "serialiser",
            },
        }
        _append_event(events_path, expired_event)
        counts["expired"] += 1

    return counts


# ═══════════════════════════════════════════════════════════════════════
# INBOX STAGING (write side)
# ═══════════════════════════════════════════════════════════════════════


def stage_claim(
    workspace: Path,
    agent_id: str,
    feature: str,
    edge: str,
    agent_role: str = "full_stack",
) -> Path:
    """Write an edge_claim event to the agent's inbox directory.

    Returns the path of the staged file. The serialiser reads and resolves
    claims from inbox/ in lexicographic agent_id + sequence order.
    """
    ws_dir = workspace / ".ai-workspace" if (workspace / ".ai-workspace").exists() else workspace
    inbox_agent_dir = ws_dir / "events" / "inbox" / agent_id
    inbox_agent_dir.mkdir(parents=True, exist_ok=True)

    # Use a timestamp-based sequence for lexicographic ordering
    seq = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    event_file = inbox_agent_dir / f"{seq}_edge_claim.json"

    claim_event = {
        "event_type": "edge_claim",
        "timestamp": _now_iso(),
        "feature": feature,
        "edge": edge,
        "agent_id": agent_id,
        "agent_role": agent_role,
    }
    event_file.write_text(json.dumps(claim_event, separators=(",", ":")))
    return event_file


def stage_release(
    workspace: Path,
    agent_id: str,
    feature: str,
    edge: str,
    reason: str = "iteration_complete",
) -> Path:
    """Write an edge_released event to the agent's inbox directory."""
    ws_dir = workspace / ".ai-workspace" if (workspace / ".ai-workspace").exists() else workspace
    inbox_agent_dir = ws_dir / "events" / "inbox" / agent_id
    inbox_agent_dir.mkdir(parents=True, exist_ok=True)

    seq = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    event_file = inbox_agent_dir / f"{seq}_edge_released.json"

    release_event = {
        "event_type": "edge_released",
        "timestamp": _now_iso(),
        "feature": feature,
        "edge": edge,
        "agent_id": agent_id,
        "reason": reason,
    }
    event_file.write_text(json.dumps(release_event, separators=(",", ":")))
    return event_file
