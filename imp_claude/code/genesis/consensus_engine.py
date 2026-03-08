# Implements: REQ-F-CONSENSUS-001 (CONSENSUS Functor Implementation)
# Implements: REQ-EVAL-001 (Three Evaluator Types — F_H multi-party)
# Implements: REQ-EVAL-003 (Human Accountability — roster, quorum, attribution)
"""
CONSENSUS engine — pure quorum logic for multi-stakeholder evaluation.

Implements ADR-S-025 §Phase 4 (Quorum Evaluation) — five deterministic checks,
all F_D. No I/O. Takes a review state dict, returns a QuorumResult.

Review state is derived from events.jsonl filtered by review_id:
    session_state(review_id) = [e for e in events if e.get("review_id") == review_id]

This module never reads files — callers project the event log and pass state in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ── Types ─────────────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class AbstentionModel(str, Enum):
    NEUTRAL = "neutral"          # abstentions excluded from denominator
    COUNTS_AGAINST = "counts_against"  # abstentions reduce approve ratio


class QuorumThreshold(str, Enum):
    MAJORITY = "majority"        # approve_ratio > 0.5
    SUPERMAJORITY = "supermajority"  # approve_ratio >= 0.66
    UNANIMITY = "unanimity"      # approve_ratio == 1.0


class FailureReason(str, Enum):
    QUORUM_NOT_REACHED = "quorum_not_reached"
    TIE = "tie"
    PARTICIPATION_FLOOR_NOT_MET = "participation_floor_not_met"
    WINDOW_CLOSED_INSUFFICIENT_VOTES = "window_closed_insufficient_votes"
    MIN_DURATION_NOT_ELAPSED = "min_duration_not_elapsed"
    GATING_COMMENTS_UNDISPOSITIONED = "gating_comments_undispositioned"


@dataclass
class Vote:
    participant: str
    verdict: Verdict
    asset_version: str
    timestamp: datetime
    rationale: str = ""
    conditions: list[str] = field(default_factory=list)


@dataclass
class Comment:
    participant: str
    timestamp: datetime
    content: str
    gating: bool          # True if timestamp <= review_closes_at
    disposition: Optional[str] = None   # resolved|rejected|acknowledged|scope_change


@dataclass
class ReviewConfig:
    roster: list[str]                    # participant IDs
    quorum: QuorumThreshold
    abstention_model: AbstentionModel
    min_participation_ratio: float       # floor: fraction of roster who must respond
    published_at: datetime
    review_closes_at: datetime           # must satisfy >= published_at + min_duration
    min_duration_seconds: float          # lower-bound constraint (ADR-S-025 §5.3)


@dataclass
class QuorumResult:
    """Output of evaluate_quorum() — always deterministic."""
    converged: bool
    failure_reason: Optional[FailureReason]

    # Tallies
    roster_size: int
    approve_votes: int
    reject_votes: int
    abstain_votes: int
    non_response_count: int
    eligible_votes: int          # votes_received + abstain_count
    approve_ratio: float
    participation_ratio: float

    # Gating comment state
    gating_comments_total: int
    gating_comments_dispositioned: int

    # Which of the 5 checks passed
    checks: dict[str, bool] = field(default_factory=dict)

    # Available recovery paths when not converged
    available_paths: list[str] = field(default_factory=list)


# ── Five deterministic checks (ADR-S-025 §Phase 4) ────────────────────────────

def _check_min_duration_elapsed(config: ReviewConfig, now: datetime) -> bool:
    """Check 1: lower-bound time constraint — minimum deliberation window."""
    elapsed = (now - config.published_at).total_seconds()
    return elapsed >= config.min_duration_seconds


def _check_review_window_closed(config: ReviewConfig, now: datetime) -> bool:
    """Check 2: upper-bound time constraint — review window has closed."""
    return now >= config.review_closes_at


def _check_participation_threshold(
    config: ReviewConfig,
    votes: list[Vote],
    abstains: list[Vote],
) -> tuple[bool, float]:
    """Check 3: participation floor — enough roster members responded."""
    eligible = len(votes) + len(abstains)
    roster_size = len(config.roster)
    ratio = eligible / roster_size if roster_size > 0 else 0.0
    return ratio >= config.min_participation_ratio, ratio


def _check_quorum_reached(
    config: ReviewConfig,
    approves: list[Vote],
    rejects: list[Vote],
    abstains: list[Vote],
) -> tuple[bool, float, Optional[FailureReason]]:
    """Check 4: quorum arithmetic (ADR-S-025 §Phase 4 approve ratio formula)."""
    approve_count = len(approves)
    reject_count = len(rejects)
    abstain_count = len(abstains)

    roster_size = len(config.roster)
    if config.abstention_model == AbstentionModel.NEUTRAL:
        denominator = approve_count + reject_count
        ratio = approve_count / denominator if denominator > 0 else 0.0
    else:  # COUNTS_AGAINST
        ratio = approve_count / roster_size if roster_size > 0 else 0.0

    # Threshold evaluation
    if config.quorum == QuorumThreshold.MAJORITY:
        if ratio == 0.5:
            return False, ratio, FailureReason.TIE
        passed = ratio > 0.5
    elif config.quorum == QuorumThreshold.SUPERMAJORITY:
        passed = ratio >= 0.66
    else:  # UNANIMITY
        passed = ratio == 1.0

    failure = None if passed else FailureReason.QUORUM_NOT_REACHED
    return passed, ratio, failure


def _check_gating_comments(comments: list[Comment]) -> tuple[bool, int, int]:
    """Check 5: all gating comments must be dispositioned."""
    gating = [c for c in comments if c.gating]
    dispositioned = [c for c in gating if c.disposition is not None]
    passed = len(gating) == len(dispositioned)
    return passed, len(gating), len(dispositioned)


# ── Main evaluator ─────────────────────────────────────────────────────────────

def evaluate_quorum(
    config: ReviewConfig,
    votes: list[Vote],
    comments: list[Comment],
    now: Optional[datetime] = None,
) -> QuorumResult:
    """
    Run all five ADR-S-025 quorum checks and return a QuorumResult.

    This is the F_D evaluator for CONSENSUS — fully deterministic, no I/O.

    Args:
        config:   Review configuration (roster, quorum rule, timing)
        votes:    All votes cast (approve/reject/abstain)
        comments: All comments received (gating and late)
        now:      Evaluation timestamp (default: UTC now). Injected for testability.

    Returns:
        QuorumResult with converged=True when all 5 checks pass.
    """
    now = now or datetime.now(timezone.utc)

    approves = [v for v in votes if v.verdict == Verdict.APPROVE]
    rejects = [v for v in votes if v.verdict == Verdict.REJECT]
    abstains = [v for v in votes if v.verdict == Verdict.ABSTAIN]

    # Participants who neither voted nor abstained
    responded_ids = {v.participant for v in votes}
    non_response_count = sum(1 for p in config.roster if p not in responded_ids)

    # Run checks
    c1 = _check_min_duration_elapsed(config, now)
    c2 = _check_review_window_closed(config, now)
    c3_passed, participation_ratio = _check_participation_threshold(config, approves + rejects, abstains)
    c4_passed, approve_ratio, quorum_failure = _check_quorum_reached(config, approves, rejects, abstains)
    c5_passed, gating_total, gating_dispositioned = _check_gating_comments(comments)

    checks = {
        "min_duration_elapsed": c1,
        "review_window_closed": c2,
        "participation_threshold_met": c3_passed,
        "quorum_reached": c4_passed,
        "gating_comments_dispositioned": c5_passed,
    }

    converged = all(checks.values())

    # Determine failure reason (first failing check wins)
    failure_reason: Optional[FailureReason] = None
    available_paths: list[str] = []

    if not converged:
        if not c1:
            failure_reason = FailureReason.MIN_DURATION_NOT_ELAPSED
            available_paths = ["wait"]
        elif not c2:
            failure_reason = FailureReason.WINDOW_CLOSED_INSUFFICIENT_VOTES
            available_paths = ["wait"]
        elif not c3_passed:
            failure_reason = FailureReason.PARTICIPATION_FLOOR_NOT_MET
            available_paths = ["re_open", "abandon"]
        elif not c4_passed:
            failure_reason = quorum_failure or FailureReason.QUORUM_NOT_REACHED
            available_paths = ["re_open", "narrow_scope", "abandon"]
        elif not c5_passed:
            failure_reason = FailureReason.GATING_COMMENTS_UNDISPOSITIONED
            available_paths = ["disposition_comments"]

    return QuorumResult(
        converged=converged,
        failure_reason=failure_reason,
        roster_size=len(config.roster),  # noqa: E501
        approve_votes=len(approves),
        reject_votes=len(rejects),
        abstain_votes=len(abstains),
        non_response_count=non_response_count,
        eligible_votes=len(approves) + len(rejects) + len(abstains),
        approve_ratio=approve_ratio,
        participation_ratio=participation_ratio,
        gating_comments_total=gating_total,
        gating_comments_dispositioned=gating_dispositioned,
        checks=checks,
        available_paths=available_paths,
    )


# ── Event projection helpers ───────────────────────────────────────────────────

def project_review_state(
    events: list[dict],
    review_id: str,
    review_closes_at: datetime,
) -> tuple[list[Vote], list[Comment]]:
    """
    Project votes and comments from events.jsonl for a given review_id.

    This is the rehydration contract (ADR-S-025 observer binding):
        session_state(review_id) = events where event.review_id == review_id

    Args:
        events:          All events from events.jsonl (already parsed)
        review_id:       The review session key
        review_closes_at: Determines gating status of each comment

    Returns:
        (votes, comments) — inputs to evaluate_quorum()
    """
    scoped = [e for e in events if e.get("review_id") == review_id]

    votes: list[Vote] = []
    comments: list[Comment] = []

    for e in scoped:
        etype = e.get("event_type", "")
        data = e.get("data", e)  # flat or nested

        if etype == "vote_cast":
            ts = _parse_ts(e.get("timestamp", ""))
            if ts:
                votes.append(Vote(
                    participant=data.get("participant", ""),
                    verdict=Verdict(data.get("verdict", "abstain")),
                    asset_version=data.get("asset_version", ""),
                    timestamp=ts,
                    rationale=data.get("rationale", ""),
                    conditions=data.get("conditions", []),
                ))

        elif etype == "comment_received":
            ts = _parse_ts(e.get("timestamp", ""))
            if ts:
                gating = ts <= review_closes_at
                comments.append(Comment(
                    participant=data.get("participant", ""),
                    timestamp=ts,
                    content=data.get("content", ""),
                    gating=gating,
                    disposition=data.get("disposition"),
                ))

    return votes, comments


def _parse_ts(ts_str: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp string to datetime (UTC)."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
