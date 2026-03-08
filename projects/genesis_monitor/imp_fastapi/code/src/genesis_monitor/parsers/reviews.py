# Implements: REQ-F-CONSENSUS-001
"""Parse CONSENSUS review sessions from events.jsonl filtered by review_id.

Session state = events where event.review_id == X (ADR-S-025 observer binding).
No session files. The event log IS the session.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ReviewComment:
    participant: str
    timestamp: datetime
    content: str
    gating: bool
    disposition: str | None = None


@dataclass
class ReviewVote:
    participant: str
    verdict: str          # approve | reject | abstain
    timestamp: datetime
    rationale: str = ""
    conditions: list[str] = field(default_factory=list)


@dataclass
class ReviewSession:
    review_id: str
    artifact: str
    published_by: str
    published_at: datetime
    roster: list[str]
    quorum: str           # majority | supermajority | unanimity
    min_participation_ratio: float
    review_closes_at: datetime | None

    votes: list[ReviewVote] = field(default_factory=list)
    comments: list[ReviewComment] = field(default_factory=list)

    # Derived state
    status: str = "open"              # open | consensus_reached | consensus_failed
    failure_reason: str | None = None
    approve_votes: int = 0
    reject_votes: int = 0
    abstain_votes: int = 0
    non_response_count: int = 0
    approve_ratio: float = 0.0
    participation_ratio: float = 0.0
    gating_comments_total: int = 0
    gating_comments_dispositioned: int = 0
    quorum_progress_pct: int = 0      # 0-100 for progress bar


def parse_reviews(workspace: Path) -> list[ReviewSession]:
    """Project review sessions from events.jsonl.

    Returns sessions sorted by published_at descending (newest first).
    """
    events_path = workspace / "events" / "events.jsonl"
    if not events_path.exists():
        return []

    raw_events: list[dict] = []
    try:
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw_events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []

    # Group all CONSENSUS events by review_id
    sessions_map: dict[str, dict] = {}   # review_id → publication event data
    events_by_review: dict[str, list[dict]] = {}

    for ev in raw_events:
        review_id = ev.get("review_id") or ev.get("data", {}).get("review_id")
        if not review_id:
            continue
        etype = ev.get("event_type", "")
        events_by_review.setdefault(review_id, []).append(ev)

        if etype == "proposal_published":
            sessions_map[review_id] = ev

    sessions: list[ReviewSession] = []
    for review_id, pub_ev in sessions_map.items():
        session = _build_session(review_id, pub_ev, events_by_review.get(review_id, []))
        if session:
            sessions.append(session)

    sessions.sort(key=lambda s: s.published_at, reverse=True)
    return sessions


def _build_session(
    review_id: str,
    pub_ev: dict,
    all_events: list[dict],
) -> ReviewSession | None:
    data = pub_ev.get("data", pub_ev)

    published_at = _parse_ts(pub_ev.get("timestamp", ""))
    if not published_at:
        return None

    closes_str = data.get("review_closes_at", "")
    review_closes_at = _parse_ts(closes_str) if closes_str else None

    roster = data.get("roster", [])
    if isinstance(roster, list) and roster and isinstance(roster[0], dict):
        roster = [r.get("id", "") for r in roster]

    session = ReviewSession(
        review_id=review_id,
        artifact=data.get("artifact", data.get("asset_id", "")),
        published_by=data.get("published_by", pub_ev.get("actor", "unknown")),
        published_at=published_at,
        roster=roster,
        quorum=data.get("quorum", {}).get("threshold", "majority") if isinstance(data.get("quorum"), dict) else data.get("quorum", "majority"),
        min_participation_ratio=float(data.get("min_participation_ratio", 0.5)),
        review_closes_at=review_closes_at,
    )

    # Replay events to build votes, comments, terminal state
    for ev in all_events:
        etype = ev.get("event_type", "")
        ev_data = ev.get("data", ev)
        ts = _parse_ts(ev.get("timestamp", ""))

        if etype == "vote_cast" and ts:
            session.votes.append(ReviewVote(
                participant=ev_data.get("participant", ""),
                verdict=ev_data.get("verdict", "abstain"),
                timestamp=ts,
                rationale=ev_data.get("rationale", ""),
                conditions=ev_data.get("conditions", []),
            ))

        elif etype == "comment_received" and ts:
            gating = ts <= review_closes_at if review_closes_at else True
            session.comments.append(ReviewComment(
                participant=ev_data.get("participant", ""),
                timestamp=ts,
                content=ev_data.get("content", ""),
                gating=gating,
                disposition=ev_data.get("disposition"),
            ))

        elif etype == "consensus_reached":
            session.status = "consensus_reached"

        elif etype == "consensus_failed":
            session.status = "consensus_failed"
            session.failure_reason = ev_data.get("failure_reason")

    # Compute derived tallies
    _compute_tallies(session)
    return session


def _compute_tallies(session: ReviewSession) -> None:
    roster_size = len(session.roster) or 1
    approves = [v for v in session.votes if v.verdict == "approve"]
    rejects = [v for v in session.votes if v.verdict == "reject"]
    abstains = [v for v in session.votes if v.verdict == "abstain"]

    session.approve_votes = len(approves)
    session.reject_votes = len(rejects)
    session.abstain_votes = len(abstains)

    responded = {v.participant for v in session.votes}
    session.non_response_count = sum(1 for p in session.roster if p not in responded)

    eligible = len(session.votes)
    session.participation_ratio = eligible / roster_size

    denominator = session.approve_votes + session.reject_votes
    session.approve_ratio = session.approve_votes / denominator if denominator > 0 else 0.0

    gating = [c for c in session.comments if c.gating]
    session.gating_comments_total = len(gating)
    session.gating_comments_dispositioned = sum(1 for c in gating if c.disposition)

    # Progress bar: how close to quorum?
    threshold_map = {"majority": 0.5, "supermajority": 0.66, "unanimity": 1.0}
    threshold = threshold_map.get(session.quorum, 0.5)
    if threshold > 0:
        pct = min(100, int((session.approve_ratio / threshold) * 100))
    else:
        pct = 0
    session.quorum_progress_pct = pct


def _parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
