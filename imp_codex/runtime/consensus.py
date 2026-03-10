"""Replay-safe CONSENSUS review projections for the Codex runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Iterable

from .events import NormalizedEvent, load_events


VALID_DISPOSITIONS = {"resolved", "rejected", "acknowledged", "scope_change"}
VALID_QUORUMS = {"majority", "supermajority", "unanimity"}
VALID_RECOVERY_PATHS = {"re_open", "narrow_scope", "abandon"}
VALID_VERDICTS = {"approve", "reject", "abstain"}

_CYCLE_ID_RE = re.compile(r"^CYCLE-(\d+)$")
_COMMENT_ID_RE = re.compile(r"^COMMENT-(\d+)$")
_REVIEW_ID_RE = re.compile(r"^REVIEW-(.+)-(\d+)$")


def parse_timestamp(value: str | None) -> datetime:
    """Parse an ISO timestamp into an aware UTC datetime."""

    if not value:
        return datetime.now(timezone.utc)
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def payload_for(event: NormalizedEvent) -> dict:
    """Return the normalized payload facet for one event."""

    facets = event.raw.get("run", {}).get("facets", {})
    payload = facets.get("sdlc:payload") or event.raw.get("data") or {}
    return dict(payload) if isinstance(payload, dict) else {}


def review_id_for(event: NormalizedEvent) -> str | None:
    payload = payload_for(event)
    return payload.get("review_id") or event.raw.get("review_id")


def cycle_id_for(event: NormalizedEvent) -> str | None:
    payload = payload_for(event)
    return payload.get("cycle_id") or event.raw.get("cycle_id")


def event_semantic_is(event: NormalizedEvent, *names: str) -> bool:
    return event.semantic_type in set(names)


def review_events(
    events: Iterable[NormalizedEvent],
    review_id: str,
    *,
    cycle_id: str | None = None,
    semantic_types: set[str] | None = None,
) -> list[NormalizedEvent]:
    """Filter an event stream down to one review, optionally one cycle."""

    filtered: list[NormalizedEvent] = []
    for event in events:
        if review_id_for(event) != review_id:
            continue
        if cycle_id is not None and cycle_id_for(event) != cycle_id:
            continue
        if semantic_types is not None and event.semantic_type not in semantic_types:
            continue
        filtered.append(event)
    return filtered


def roster_participants(cycle: dict) -> list[dict]:
    """Normalize participant roster entries to ``{id, type}`` records."""

    normalized: list[dict] = []
    for raw in cycle.get("participants") or cycle.get("roster") or []:
        if isinstance(raw, dict):
            participant_id = str(raw.get("id", "")).strip()
            if not participant_id:
                continue
            normalized.append(
                {
                    "id": participant_id,
                    "type": str(raw.get("type") or "human"),
                }
            )
        elif raw:
            normalized.append({"id": str(raw).strip(), "type": "human"})
    return normalized


def next_review_id(events: Iterable[NormalizedEvent], artifact: str) -> str:
    """Generate the next review ID for a given artifact path."""

    slug = Path(artifact).stem.lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]+", "-", slug).strip("-") or "asset"
    max_seq = 0
    for event in events:
        review_id = review_id_for(event)
        if not review_id:
            continue
        match = _REVIEW_ID_RE.fullmatch(review_id)
        if match and match.group(1) == slug:
            max_seq = max(max_seq, int(match.group(2)))
    return f"REVIEW-{slug}-{max_seq + 1}"


def next_cycle_id(events: Iterable[NormalizedEvent], review_id: str) -> str:
    max_seq = 0
    for event in review_events(events, review_id):
        cycle_id = cycle_id_for(event)
        if not cycle_id:
            continue
        match = _CYCLE_ID_RE.fullmatch(cycle_id)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f"CYCLE-{max_seq + 1:03d}"


def next_comment_id(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> str:
    max_seq = 0
    for event in review_events(events, review_id, cycle_id=cycle_id):
        if event.semantic_type != "CommentReceived":
            continue
        comment_id = payload_for(event).get("comment_id")
        if not comment_id:
            continue
        match = _COMMENT_ID_RE.fullmatch(str(comment_id))
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f"COMMENT-{max_seq + 1:03d}"


def terminal_event(
    events: Iterable[NormalizedEvent],
    review_id: str,
    cycle_id: str,
) -> NormalizedEvent | None:
    """Return the terminal event for one review cycle, if present."""

    candidates = review_events(
        events,
        review_id,
        cycle_id=cycle_id,
        semantic_types={"ConsensusReached", "ConsensusFailed"},
    )
    return candidates[-1] if candidates else None


def current_cycle(events: Iterable[NormalizedEvent], review_id: str) -> dict | None:
    """Return the latest known review cycle."""

    latest: dict | None = None
    for event in review_events(events, review_id):
        if event.semantic_type not in {"ConsensusRequested", "ReviewReopened"}:
            continue
        payload = payload_for(event)
        cycle_id = payload.get("cycle_id")
        if not cycle_id:
            continue
        latest = {
            "review_id": review_id,
            "cycle_id": cycle_id,
            "asset_id": payload.get("asset_id") or Path(str(payload.get("artifact", "asset"))).stem,
            "asset_version": payload.get("asset_version") or "v1",
            "artifact": payload.get("artifact", ""),
            "requested_by": payload.get("requested_by") or payload.get("reopened_by", ""),
            "published_at": payload.get("published_at") or event.event_time,
            "review_closes_at": payload.get("review_closes_at") or event.event_time,
            "min_duration_seconds": int(payload.get("min_duration_seconds") or 0),
            "participants": roster_participants(payload),
            "quorum_threshold": payload.get("quorum_threshold") or payload.get("quorum") or "majority",
            "abstention_model": payload.get("abstention_model") or "neutral",
            "min_participation_ratio": float(payload.get("min_participation_ratio") or 0.5),
            "prior_cycle_id": payload.get("prior_cycle_id"),
            "opened_event_time": event.event_time,
            "opened_run_id": event.raw.get("run", {}).get("runId"),
        }
    if latest is None:
        return None
    latest["terminal_event"] = terminal_event(events, review_id, latest["cycle_id"])
    latest["is_open"] = latest["terminal_event"] is None
    return latest


def session_state(
    events: Iterable[NormalizedEvent],
    review_id: str,
    cycle_id: str,
) -> list[NormalizedEvent]:
    return review_events(events, review_id, cycle_id=cycle_id)


def _project_comments(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> list[dict]:
    comments: list[dict] = []
    by_id: dict[str, dict] = {}
    for event in session_state(events, review_id, cycle_id):
        payload = payload_for(event)
        if event.semantic_type == "CommentReceived":
            comment_id = str(payload.get("comment_id", "")).strip()
            if not comment_id:
                continue
            record = {
                "comment_id": comment_id,
                "participant": str(payload.get("participant", "")).strip(),
                "timestamp": event.event_time,
                "content": payload.get("content", ""),
                "content_ref": payload.get("content_ref", ""),
                "asset_version": payload.get("asset_version") or "v1",
                "gating": bool(payload.get("gating")),
                "disposition": None,
                "disposition_rationale": "",
                "material_change": False,
            }
            comments.append(record)
            by_id[comment_id] = record
        elif event.semantic_type == "CommentDispositioned":
            comment_id = str(payload.get("comment_id", "")).strip()
            if not comment_id or comment_id not in by_id:
                continue
            by_id[comment_id]["disposition"] = payload.get("disposition")
            by_id[comment_id]["disposition_rationale"] = payload.get("rationale", "")
            by_id[comment_id]["material_change"] = bool(payload.get("material_change"))
    return comments


def gating_comments(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> list[dict]:
    return [comment for comment in _project_comments(events, review_id, cycle_id) if comment["gating"]]


def late_comments(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> list[dict]:
    return [comment for comment in _project_comments(events, review_id, cycle_id) if not comment["gating"]]


def disposition_state(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> dict:
    gating = gating_comments(events, review_id, cycle_id)
    dispositioned = [comment for comment in gating if comment["disposition"]]
    remaining = [comment["comment_id"] for comment in gating if not comment["disposition"]]
    return {
        "total_gating_comments": len(gating),
        "dispositioned_gating_comments": len(dispositioned),
        "remaining_comment_ids": remaining,
    }


def vote_snapshot(events: Iterable[NormalizedEvent], review_id: str, cycle_id: str) -> dict[str, dict]:
    """Return the current-cycle effective vote per participant."""

    snapshot: dict[str, dict] = {}
    for event in session_state(events, review_id, cycle_id):
        if event.semantic_type != "VoteCast":
            continue
        payload = payload_for(event)
        participant = str(payload.get("participant", "")).strip()
        verdict = str(payload.get("verdict", "")).strip()
        if not participant or verdict not in VALID_VERDICTS:
            continue
        snapshot[participant] = {
            "participant": participant,
            "timestamp": event.event_time,
            "asset_version": payload.get("asset_version") or "v1",
            "verdict": verdict,
            "rationale": payload.get("rationale", ""),
            "conditions": list(payload.get("conditions") or []),
            "run_id": event.raw.get("run", {}).get("runId"),
        }
    return snapshot


def _available_paths(failure_reason: str | None) -> list[str]:
    if failure_reason == "gating_comments_undispositioned":
        return ["re_open", "narrow_scope", "abandon"]
    if failure_reason == "window_closed_insufficient_votes":
        return ["re_open", "abandon"]
    if failure_reason == "participation_floor_not_met":
        return ["re_open", "abandon"]
    if failure_reason in {"tie", "quorum_not_reached"}:
        return ["re_open", "narrow_scope", "abandon"]
    return []


def quorum_state(
    events: Iterable[NormalizedEvent],
    review_id: str,
    cycle_id: str | None = None,
    *,
    now: str | datetime | None = None,
) -> dict:
    """Project one review cycle into a deterministic quorum state."""

    cycle = current_cycle(events, review_id)
    if cycle is None:
        raise ValueError(f"Review not found: {review_id}")
    if cycle_id is not None and cycle["cycle_id"] != cycle_id:
        session = session_state(events, review_id, cycle_id)
        if not session:
            raise ValueError(f"Cycle not found: {review_id} {cycle_id}")
        cycle = dict(cycle)
        for event in session:
            if event.semantic_type in {"ConsensusRequested", "ReviewReopened"}:
                cycle = current_cycle(session, review_id) or cycle
                break

    now_dt = parse_timestamp(now) if isinstance(now, str) else now or datetime.now(timezone.utc)
    published_at = parse_timestamp(cycle["published_at"])
    review_closes_at = parse_timestamp(cycle["review_closes_at"])
    min_duration_elapsed = now_dt >= published_at + timedelta(seconds=int(cycle["min_duration_seconds"]))
    window_closed = now_dt >= review_closes_at

    participants = roster_participants(cycle)
    roster_ids = [participant["id"] for participant in participants]
    roster_size = len(roster_ids)
    votes = vote_snapshot(events, review_id, cycle["cycle_id"])
    counted_votes = {pid: vote for pid, vote in votes.items() if pid in roster_ids}
    responded_ids = set(counted_votes)

    approve_votes = sum(1 for vote in counted_votes.values() if vote["verdict"] == "approve")
    reject_votes = sum(1 for vote in counted_votes.values() if vote["verdict"] == "reject")
    abstain_votes = sum(1 for vote in counted_votes.values() if vote["verdict"] == "abstain")
    eligible_votes = approve_votes + reject_votes + abstain_votes
    non_response_count = max(roster_size - len(responded_ids), 0)

    disposition = disposition_state(events, review_id, cycle["cycle_id"])
    gating_remaining = disposition["remaining_comment_ids"]

    participation_ratio = (eligible_votes / roster_size) if roster_size else 0.0
    if cycle["abstention_model"] == "counts_against":
        approve_denominator = roster_size
    else:
        approve_denominator = approve_votes + reject_votes
    approve_ratio = (approve_votes / approve_denominator) if approve_denominator else 0.0

    tie = approve_votes == reject_votes and approve_votes > 0
    threshold = cycle["quorum_threshold"]
    if threshold not in VALID_QUORUMS:
        raise ValueError(f"Unsupported quorum threshold: {threshold}")
    if threshold == "majority":
        quorum_reached = approve_ratio > 0.5
    elif threshold == "supermajority":
        quorum_reached = approve_ratio >= (2 / 3)
    else:
        quorum_reached = approve_ratio == 1.0 and reject_votes == 0 and approve_votes > 0

    participation_threshold_met = participation_ratio >= float(cycle["min_participation_ratio"])

    outcome = "deferred"
    failure_reason = None
    if cycle["terminal_event"] is not None:
        terminal_payload = payload_for(cycle["terminal_event"])
        outcome = "passed" if cycle["terminal_event"].semantic_type == "ConsensusReached" else "failed"
        failure_reason = terminal_payload.get("failure_reason")
    elif min_duration_elapsed and window_closed:
        if gating_remaining:
            outcome = "failed"
            failure_reason = "gating_comments_undispositioned"
        elif not participation_threshold_met:
            outcome = "failed"
            failure_reason = (
                "window_closed_insufficient_votes"
                if non_response_count > 0
                else "participation_floor_not_met"
            )
        elif threshold == "majority" and tie:
            outcome = "failed"
            failure_reason = "tie"
        elif quorum_reached:
            outcome = "passed"
        else:
            outcome = "failed"
            failure_reason = "quorum_not_reached"

    return {
        "review_id": cycle["review_id"],
        "cycle_id": cycle["cycle_id"],
        "asset_id": cycle["asset_id"],
        "asset_version": cycle["asset_version"],
        "artifact": cycle["artifact"],
        "participants": participants,
        "roster_size": roster_size,
        "quorum_threshold": threshold,
        "abstention_model": cycle["abstention_model"],
        "min_participation_ratio": float(cycle["min_participation_ratio"]),
        "published_at": cycle["published_at"],
        "review_closes_at": cycle["review_closes_at"],
        "min_duration_seconds": int(cycle["min_duration_seconds"]),
        "min_duration_elapsed": min_duration_elapsed,
        "window_closed": window_closed,
        "outcome": outcome,
        "failure_reason": failure_reason,
        "available_paths": _available_paths(failure_reason),
        "approve_votes": approve_votes,
        "reject_votes": reject_votes,
        "abstain_votes": abstain_votes,
        "eligible_votes": eligible_votes,
        "non_response_count": non_response_count,
        "approve_ratio": approve_ratio,
        "participation_ratio": participation_ratio,
        "participation_threshold_met": participation_threshold_met,
        "quorum_reached": quorum_reached,
        "gating_comments_total": disposition["total_gating_comments"],
        "gating_comments_dispositioned": disposition["dispositioned_gating_comments"],
        "gating_comments_remaining": gating_remaining,
        "vote_snapshot": counted_votes,
        "off_roster_votes": {
            participant: vote
            for participant, vote in votes.items()
            if participant not in roster_ids
        },
        "terminal_run_id": (
            cycle["terminal_event"].raw.get("run", {}).get("runId")
            if cycle["terminal_event"] is not None
            else None
        ),
        "current_cycle_open": cycle["terminal_event"] is None,
    }


def load_consensus_state(
    events_file: Path,
    review_id: str,
    *,
    cycle_id: str | None = None,
    now: str | datetime | None = None,
) -> dict:
    """Convenience wrapper for loading one review directly from disk."""

    events = load_events(events_file)
    return quorum_state(events, review_id, cycle_id, now=now)


__all__ = [
    "VALID_DISPOSITIONS",
    "VALID_QUORUMS",
    "VALID_RECOVERY_PATHS",
    "VALID_VERDICTS",
    "current_cycle",
    "cycle_id_for",
    "disposition_state",
    "format_timestamp",
    "gating_comments",
    "late_comments",
    "load_consensus_state",
    "next_comment_id",
    "next_cycle_id",
    "next_review_id",
    "parse_timestamp",
    "payload_for",
    "quorum_state",
    "review_events",
    "review_id_for",
    "roster_participants",
    "session_state",
    "terminal_event",
    "vote_snapshot",
]
