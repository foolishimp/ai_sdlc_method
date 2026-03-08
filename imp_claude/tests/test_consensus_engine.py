# Validates: REQ-F-CONSENSUS-001, REQ-EVAL-001, REQ-EVAL-003
"""
Tests for consensus_engine.py — all five ADR-S-025 §Phase 4 quorum checks.

All tests are purely deterministic (F_D). No I/O, no agents, no events.jsonl.
Inject `now` for timing checks to avoid flakiness.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from imp_claude.code.genesis.consensus_engine import (
    AbstentionModel,
    Comment,
    FailureReason,
    QuorumResult,
    QuorumThreshold,
    ReviewConfig,
    Verdict,
    Vote,
    evaluate_quorum,
    project_review_state,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

BASE_TIME = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)
OPEN_TIME = BASE_TIME
CLOSE_TIME = BASE_TIME + timedelta(days=14)
AFTER_CLOSE = CLOSE_TIME + timedelta(hours=1)
MIN_DURATION = timedelta(days=14).total_seconds()


def make_config(
    roster=None,
    quorum=QuorumThreshold.MAJORITY,
    abstention_model=AbstentionModel.NEUTRAL,
    min_participation_ratio=0.5,
    published_at=None,
    review_closes_at=None,
    min_duration_seconds=None,
) -> ReviewConfig:
    return ReviewConfig(
        roster=roster or ["agent-a", "agent-b", "agent-c"],
        quorum=quorum,
        abstention_model=abstention_model,
        min_participation_ratio=min_participation_ratio,
        published_at=published_at or OPEN_TIME,
        review_closes_at=review_closes_at or CLOSE_TIME,
        min_duration_seconds=min_duration_seconds or MIN_DURATION,
    )


def make_vote(participant: str, verdict: Verdict, ts=None) -> Vote:
    return Vote(
        participant=participant,
        verdict=verdict,
        asset_version="v1",
        timestamp=ts or AFTER_CLOSE,
    )


def make_comment(participant: str, gating=True, disposition=None, ts=None) -> Comment:
    return Comment(
        participant=participant,
        timestamp=ts or OPEN_TIME + timedelta(days=1),
        content="test comment",
        gating=gating,
        disposition=disposition,
    )


# ── Check 1: min_duration_elapsed ─────────────────────────────────────────────

class TestMinDurationElapsed:
    def test_passes_after_min_duration(self):
        config = make_config()
        votes = [make_vote("agent-a", Verdict.APPROVE), make_vote("agent-b", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["min_duration_elapsed"] is True

    def test_fails_before_min_duration(self):
        config = make_config()
        votes = [make_vote("agent-a", Verdict.APPROVE), make_vote("agent-b", Verdict.APPROVE)]
        early = OPEN_TIME + timedelta(days=1)
        result = evaluate_quorum(config, votes, [], now=early)
        assert result.checks["min_duration_elapsed"] is False
        assert result.converged is False
        assert result.failure_reason == FailureReason.MIN_DURATION_NOT_ELAPSED

    def test_passes_exactly_at_min_duration(self):
        config = make_config(min_duration_seconds=3600)
        votes = [make_vote("agent-a", Verdict.APPROVE), make_vote("agent-b", Verdict.APPROVE)]
        exactly_at = OPEN_TIME + timedelta(seconds=3600)
        # Window must also be closed — set closes_at to match
        config2 = make_config(
            min_duration_seconds=3600,
            review_closes_at=exactly_at,
        )
        result = evaluate_quorum(config2, votes, [], now=exactly_at)
        assert result.checks["min_duration_elapsed"] is True


# ── Check 2: review_window_closed ─────────────────────────────────────────────

class TestReviewWindowClosed:
    def test_passes_after_close(self):
        config = make_config()
        votes = [make_vote("agent-a", Verdict.APPROVE), make_vote("agent-b", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["review_window_closed"] is True

    def test_fails_before_close(self):
        config = make_config()
        votes = [make_vote("agent-a", Verdict.APPROVE), make_vote("agent-b", Verdict.APPROVE)]
        before_close = CLOSE_TIME - timedelta(hours=1)
        result = evaluate_quorum(config, votes, [], now=before_close)
        assert result.checks["review_window_closed"] is False
        assert result.converged is False


# ── Check 3: participation_threshold_met ──────────────────────────────────────

class TestParticipationThreshold:
    def test_passes_with_full_participation(self):
        config = make_config(roster=["a", "b", "c"], min_participation_ratio=0.5)
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.REJECT),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["participation_threshold_met"] is True
        assert result.participation_ratio == 1.0

    def test_passes_at_floor(self):
        config = make_config(roster=["a", "b", "c"], min_participation_ratio=0.5)
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["participation_threshold_met"] is True

    def test_fails_below_floor(self):
        config = make_config(roster=["a", "b", "c"], min_participation_ratio=0.67)
        votes = [make_vote("a", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["participation_threshold_met"] is False
        assert result.failure_reason == FailureReason.PARTICIPATION_FLOOR_NOT_MET
        assert "re_open" in result.available_paths

    def test_abstain_counts_toward_participation(self):
        # 2 of 3 responded (1 approve + 1 abstain) = 0.66 — passes floor of 0.5
        config = make_config(roster=["a", "b", "c"], min_participation_ratio=0.5)
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.ABSTAIN)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["participation_threshold_met"] is True

    def test_non_response_does_not_count(self):
        # 1 of 3 voted = 33% < 67% floor
        config = make_config(roster=["a", "b", "c"], min_participation_ratio=0.67)
        votes = [make_vote("a", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.non_response_count == 2
        assert result.checks["participation_threshold_met"] is False


# ── Check 4: quorum_reached ───────────────────────────────────────────────────

class TestQuorumReached:
    def test_majority_passes(self):
        config = make_config(quorum=QuorumThreshold.MAJORITY)
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.REJECT),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is True
        assert result.approve_ratio == pytest.approx(2 / 3)

    def test_majority_fails_below_threshold(self):
        config = make_config(quorum=QuorumThreshold.MAJORITY)
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.REJECT),
            make_vote("c", Verdict.REJECT),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is False
        assert result.failure_reason == FailureReason.QUORUM_NOT_REACHED
        assert "narrow_scope" in result.available_paths

    def test_majority_tie_is_failure(self):
        config = make_config(roster=["a", "b"], quorum=QuorumThreshold.MAJORITY)
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.REJECT)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is False
        assert result.failure_reason == FailureReason.TIE

    def test_supermajority_passes_at_66pct(self):
        config = make_config(
            roster=["a", "b", "c"],
            quorum=QuorumThreshold.SUPERMAJORITY,
        )
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.REJECT),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is True

    def test_unanimity_with_counts_against_blocks_on_abstain(self):
        # Under COUNTS_AGAINST: ratio = approves / roster = 2/3 < 1.0 → fails unanimity
        config = make_config(
            quorum=QuorumThreshold.UNANIMITY,
            abstention_model=AbstentionModel.COUNTS_AGAINST,
        )
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.ABSTAIN),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is False

    def test_unanimity_neutral_passes_when_all_voters_approve(self):
        # Under NEUTRAL: ratio = approves / (approves + rejects) = 2/2 = 1.0 → passes
        # Abstention excluded from denominator per ADR-S-025 §Phase 4
        config = make_config(
            quorum=QuorumThreshold.UNANIMITY,
            abstention_model=AbstentionModel.NEUTRAL,
        )
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.ABSTAIN),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is True

    def test_unanimity_passes_all_approve(self):
        config = make_config(quorum=QuorumThreshold.UNANIMITY)
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.APPROVE),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["quorum_reached"] is True

    def test_neutral_abstention_excluded_from_denominator(self):
        config = make_config(
            quorum=QuorumThreshold.MAJORITY,
            abstention_model=AbstentionModel.NEUTRAL,
        )
        # 2 approve, 1 abstain — neutral: ratio = 2/(2+0) = 1.0
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.ABSTAIN),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.approve_ratio == pytest.approx(1.0)
        assert result.checks["quorum_reached"] is True

    def test_counts_against_abstention_reduces_ratio(self):
        config = make_config(
            roster=["a", "b", "c"],
            quorum=QuorumThreshold.MAJORITY,
            abstention_model=AbstentionModel.COUNTS_AGAINST,
        )
        # 2 approve, 1 abstain — counts_against: ratio = 2/3 = 0.67
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.ABSTAIN),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.approve_ratio == pytest.approx(2 / 3)


# ── Check 5: gating_comments_dispositioned ────────────────────────────────────

class TestGatingComments:
    def test_passes_with_no_gating_comments(self):
        config = make_config()
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.APPROVE)]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.checks["gating_comments_dispositioned"] is True
        assert result.gating_comments_total == 0

    def test_passes_all_gating_dispositioned(self):
        config = make_config()
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.APPROVE)]
        comments = [
            make_comment("a", gating=True, disposition="resolved"),
            make_comment("b", gating=True, disposition="rejected"),
        ]
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)
        assert result.checks["gating_comments_dispositioned"] is True
        assert result.gating_comments_dispositioned == 2

    def test_fails_undispositioned_gating_comment(self):
        config = make_config()
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.APPROVE)]
        comments = [make_comment("c", gating=True, disposition=None)]
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)
        assert result.checks["gating_comments_dispositioned"] is False
        assert result.failure_reason == FailureReason.GATING_COMMENTS_UNDISPOSITIONED

    def test_late_comment_not_gating(self):
        config = make_config()
        votes = [make_vote("a", Verdict.APPROVE), make_vote("b", Verdict.APPROVE)]
        # Late comment (after close) with no disposition — should NOT block
        late_ts = CLOSE_TIME + timedelta(hours=2)
        comments = [make_comment("c", gating=False, disposition=None, ts=late_ts)]
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)
        assert result.checks["gating_comments_dispositioned"] is True


# ── Full convergence scenarios ─────────────────────────────────────────────────

class TestFullConvergence:
    def test_consensus_reached_majority(self):
        config = make_config()
        votes = [
            make_vote("agent-a", Verdict.APPROVE),
            make_vote("agent-b", Verdict.APPROVE),
            make_vote("agent-c", Verdict.REJECT),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.converged is True
        assert result.failure_reason is None
        assert all(result.checks.values())

    def test_consensus_reached_unanimous(self):
        config = make_config(quorum=QuorumThreshold.UNANIMITY)
        votes = [
            make_vote("agent-a", Verdict.APPROVE),
            make_vote("agent-b", Verdict.APPROVE),
            make_vote("agent-c", Verdict.APPROVE),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.converged is True

    def test_consensus_failed_no_quorum(self):
        config = make_config()
        votes = [
            make_vote("agent-a", Verdict.REJECT),
            make_vote("agent-b", Verdict.REJECT),
            make_vote("agent-c", Verdict.APPROVE),
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.converged is False
        assert result.failure_reason == FailureReason.QUORUM_NOT_REACHED
        assert "narrow_scope" in result.available_paths
        assert "abandon" in result.available_paths

    def test_tallies_correct(self):
        config = make_config(roster=["a", "b", "c", "d"])
        votes = [
            make_vote("a", Verdict.APPROVE),
            make_vote("b", Verdict.APPROVE),
            make_vote("c", Verdict.ABSTAIN),
            # d = non_response
        ]
        result = evaluate_quorum(config, votes, [], now=AFTER_CLOSE)
        assert result.roster_size == 4
        assert result.approve_votes == 2
        assert result.reject_votes == 0
        assert result.abstain_votes == 1
        assert result.non_response_count == 1
        assert result.eligible_votes == 3


# ── Event projection ───────────────────────────────────────────────────────────

class TestProjectReviewState:
    def test_projects_votes_from_events(self):
        events = [
            {
                "event_type": "vote_cast",
                "review_id": "REVIEW-ADR-S-027",
                "timestamp": AFTER_CLOSE.isoformat(),
                "participant": "agent-a",
                "verdict": "approve",
                "asset_version": "v1",
                "rationale": "looks good",
            },
            {
                "event_type": "vote_cast",
                "review_id": "REVIEW-ADR-S-027",
                "timestamp": AFTER_CLOSE.isoformat(),
                "participant": "agent-b",
                "verdict": "reject",
                "asset_version": "v1",
            },
            {
                "event_type": "vote_cast",
                "review_id": "REVIEW-OTHER",  # different review — excluded
                "timestamp": AFTER_CLOSE.isoformat(),
                "participant": "agent-c",
                "verdict": "approve",
                "asset_version": "v1",
            },
        ]
        votes, comments = project_review_state(events, "REVIEW-ADR-S-027", CLOSE_TIME)
        assert len(votes) == 2
        assert votes[0].participant == "agent-a"
        assert votes[0].verdict == Verdict.APPROVE
        assert votes[1].verdict == Verdict.REJECT

    def test_projects_comments_with_gating_flag(self):
        before_close = (CLOSE_TIME - timedelta(days=1)).isoformat()
        after_close = (CLOSE_TIME + timedelta(hours=1)).isoformat()
        events = [
            {
                "event_type": "comment_received",
                "review_id": "REVIEW-ADR-S-027",
                "timestamp": before_close,
                "participant": "agent-a",
                "content": "I have a concern",
                "disposition": "resolved",
            },
            {
                "event_type": "comment_received",
                "review_id": "REVIEW-ADR-S-027",
                "timestamp": after_close,
                "participant": "agent-b",
                "content": "late comment",
            },
        ]
        votes, comments = project_review_state(events, "REVIEW-ADR-S-027", CLOSE_TIME)
        assert len(comments) == 2
        assert comments[0].gating is True
        assert comments[0].disposition == "resolved"
        assert comments[1].gating is False
        assert comments[1].disposition is None

    def test_filters_by_review_id(self):
        events = [
            {"event_type": "vote_cast", "review_id": "REVIEW-X", "timestamp": AFTER_CLOSE.isoformat(), "participant": "a", "verdict": "approve", "asset_version": "v1"},
            {"event_type": "vote_cast", "review_id": "REVIEW-Y", "timestamp": AFTER_CLOSE.isoformat(), "participant": "b", "verdict": "approve", "asset_version": "v1"},
        ]
        votes, _ = project_review_state(events, "REVIEW-X", CLOSE_TIME)
        assert len(votes) == 1
        assert votes[0].participant == "a"

    def test_end_to_end_project_then_evaluate(self):
        """Full pipeline: events → project → evaluate → consensus_reached."""
        events = [
            {"event_type": "vote_cast", "review_id": "REVIEW-ADR-S-027", "timestamp": AFTER_CLOSE.isoformat(), "participant": "agent-a", "verdict": "approve", "asset_version": "v1"},
            {"event_type": "vote_cast", "review_id": "REVIEW-ADR-S-027", "timestamp": AFTER_CLOSE.isoformat(), "participant": "agent-b", "verdict": "approve", "asset_version": "v1"},
            {"event_type": "vote_cast", "review_id": "REVIEW-ADR-S-027", "timestamp": AFTER_CLOSE.isoformat(), "participant": "agent-c", "verdict": "reject", "asset_version": "v1"},
        ]
        config = make_config()
        votes, comments = project_review_state(events, "REVIEW-ADR-S-027", CLOSE_TIME)
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)
        assert result.converged is True
        assert result.approve_votes == 2
        assert result.reject_votes == 1
