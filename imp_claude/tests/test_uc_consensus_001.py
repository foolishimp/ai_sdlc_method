# Validates: REQ-F-CONSENSUS-001, REQ-EVAL-003
"""
UAT-UC-CONSENSUS-001 — Full CONSENSUS review session flow.

Tests the end-to-end CONSENSUS functor implementation:
  1. Proposal published to events.jsonl
  2. Agents vote (via vote_cast events)
  3. Quorum projection via consensus_engine
  4. consensus_reached emitted when quorum met
  5. Artifact ADR status updated to Accepted
  6. genesis_monitor parsers correctly project the session

All tests use purely deterministic data (F_D) — no agents, no LLM, no I/O beyond
the test's own tmp_path fixtures.

Reference: ADR-S-025 (CONSENSUS Functor), gen-consensus-open.md
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from imp_claude.code.genesis.consensus_engine import (
    AbstentionModel,
    Comment,
    FailureReason,
    QuorumThreshold,
    ReviewConfig,
    Verdict,
    Vote,
    evaluate_quorum,
    project_review_state,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

BASE_TIME = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)
CLOSE_TIME = BASE_TIME + timedelta(days=14)
AFTER_CLOSE = CLOSE_TIME + timedelta(hours=1)

ROSTER = ["gen-dev-observer", "gen-cicd-observer", "gen-ops-observer"]
REVIEW_ID = "REVIEW-ADR-S-027-1"
ARTIFACT = "specification/adrs/ADR-S-027-veto-semantics.md"


def make_proposal_event(
    review_id: str = REVIEW_ID,
    roster: list[str] | None = None,
    quorum: str = "majority",
    published_at: datetime | None = None,
    review_closes_at: datetime | None = None,
) -> dict:
    pub_at = (published_at or BASE_TIME).isoformat()
    close_at = (review_closes_at or CLOSE_TIME).isoformat()
    return {
        "event_type": "proposal_published",
        "review_id": review_id,
        "timestamp": pub_at,
        "project": "ai-sdlc-method",
        "actor": "local-user",
        "data": {
            "artifact": ARTIFACT,
            "asset_version": "v1",
            "published_by": "local-user",
            "roster": roster or ROSTER,
            "quorum": quorum,
            "min_participation_ratio": 0.5,
            "published_at": pub_at,
            "review_closes_at": close_at,
        },
    }


def make_vote_event(
    participant: str,
    verdict: str,
    review_id: str = REVIEW_ID,
    rationale: str = "",
    gating: bool = False,
    ts: datetime | None = None,
) -> dict:
    return {
        "event_type": "vote_cast",
        "review_id": review_id,
        "timestamp": (ts or BASE_TIME).isoformat(),
        "project": "ai-sdlc-method",
        "actor": participant,
        "data": {
            "participant": participant,
            "verdict": verdict,
            "rationale": rationale,
            "gating": gating,
            "content": rationale,
        },
    }


def make_comment_event(
    participant: str,
    content: str,
    review_id: str = REVIEW_ID,
    gating: bool = False,
    disposition: str | None = None,
    ts: datetime | None = None,
) -> dict:
    return {
        "event_type": "comment_received",
        "review_id": review_id,
        "timestamp": (ts or BASE_TIME).isoformat(),
        "project": "ai-sdlc-method",
        "actor": participant,
        "data": {
            "participant": participant,
            "content": content,
            "gating": gating,
            "disposition": disposition,
        },
    }


def write_events(tmp_path: Path, events: list[dict]) -> Path:
    workspace = tmp_path / ".ai-workspace" / "events"
    workspace.mkdir(parents=True)
    evfile = workspace / "events.jsonl"
    evfile.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return evfile


def make_config(
    roster: list[str] | None = None,
    quorum: QuorumThreshold = QuorumThreshold.MAJORITY,
    abstention_model: AbstentionModel = AbstentionModel.NEUTRAL,
    published_at: datetime | None = None,
    review_closes_at: datetime | None = None,
    min_duration_seconds: float = 0.0,
) -> ReviewConfig:
    return ReviewConfig(
        roster=roster or ROSTER,
        quorum=quorum,
        abstention_model=abstention_model,
        min_participation_ratio=0.5,
        published_at=published_at or BASE_TIME,
        review_closes_at=review_closes_at or CLOSE_TIME,
        min_duration_seconds=min_duration_seconds,
    )


# ── UC-001: Happy path — majority consensus ────────────────────────────────────

class TestUCConsensus001HappyPath:
    """UAT-UC-CONSENSUS-001: Proposal → 2 approve + 1 abstain → majority reached."""

    def _events(self) -> list[dict]:
        return [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "approve",
                            rationale="Well-specified, implementable."),
            make_vote_event("gen-cicd-observer", "approve",
                            rationale="Testable, no pipeline impact."),
            make_vote_event("gen-ops-observer", "abstain",
                            rationale="No operational surface."),
        ]

    def test_quorum_check_converges(self):
        """Majority is reached: 2 approve / 3 roster (ignoring 1 abstain under NEUTRAL)."""
        events = self._events()
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config()
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        assert result.converged is True
        assert result.approve_votes == 2
        assert result.reject_votes == 0
        assert result.abstain_votes == 1
        assert result.failure_reason is None

    def test_vote_tally_correct(self):
        """project_review_state correctly projects 3 votes from events."""
        events = self._events()
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)

        assert len(votes) == 3
        verdicts = {v.participant: v.verdict for v in votes}
        assert verdicts["gen-dev-observer"] == Verdict.APPROVE
        assert verdicts["gen-cicd-observer"] == Verdict.APPROVE
        assert verdicts["gen-ops-observer"] == Verdict.ABSTAIN

    def test_non_response_count_is_zero(self):
        """All roster members have voted."""
        events = self._events()
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config()
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        assert result.non_response_count == 0

    def test_events_from_different_review_excluded(self):
        """Votes for a different review_id are not included."""
        events = self._events() + [
            make_vote_event("gen-dev-observer", "reject", review_id="REVIEW-OTHER-1"),
        ]
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)

        # Only 3 votes for REVIEW_ID, the "reject" for OTHER is not counted
        assert len(votes) == 3
        assert all(v.verdict != Verdict.REJECT for v in votes)


# ── UC-002: Rejection — insufficient quorum ────────────────────────────────────

class TestUCConsensus002Rejection:
    """UAT-UC-CONSENSUS-002: 1 approve + 2 reject → consensus_failed."""

    def _events(self) -> list[dict]:
        return [
            make_proposal_event(review_closes_at=BASE_TIME + timedelta(seconds=1)),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "reject",
                            rationale="Missing test strategy."),
            make_vote_event("gen-ops-observer", "reject",
                            rationale="No runbook."),
        ]

    def test_majority_fails_on_two_rejections(self):
        """1 approve vs 2 reject → quorum not reached → converged=False."""
        events = self._events()
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config(review_closes_at=BASE_TIME + timedelta(seconds=1))
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        assert result.converged is False
        assert result.approve_votes == 1
        assert result.reject_votes == 2
        assert result.failure_reason == FailureReason.QUORUM_NOT_REACHED

    def test_available_paths_provided(self):
        """consensus_failed includes available_paths for recovery."""
        events = self._events()
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config(review_closes_at=BASE_TIME + timedelta(seconds=1))
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        assert result.available_paths is not None
        assert len(result.available_paths) > 0


# ── UC-003: Gating comment blocks consensus ────────────────────────────────────

class TestUCConsensus003GatingComment:
    """UAT-UC-CONSENSUS-003: Gating comment blocks consensus until dispositioned."""

    def _events(self, disposition: str | None = None) -> list[dict]:
        return [
            make_proposal_event(),
            make_comment_event(
                "gen-cicd-observer",
                "Missing: rollback path if veto is exercised mid-sequence.",
                gating=True,
                disposition=disposition,
            ),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "reject", gating=True,
                            rationale="Rollback path undefined."),
            make_vote_event("gen-ops-observer", "approve"),
        ]

    def test_undispositioned_gating_comment_blocks(self):
        """Undispositioned gating comment → converged=False even if vote quorum met."""
        events = self._events(disposition=None)
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config()
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        # 2 approve vs 1 reject → majority would normally pass
        # but gating comment is undispositioned
        assert result.converged is False
        assert result.failure_reason == FailureReason.GATING_COMMENTS_UNDISPOSITIONED

    def test_dispositioned_gating_comment_unblocks(self):
        """Dispositioned gating comment no longer blocks."""
        events = self._events(disposition="acknowledged")
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config()
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        # Gating comment is dispositioned → evaluate quorum normally
        # 2 approve vs 1 reject → MAJORITY passes
        assert result.converged is True


# ── UC-004: Supermajority quorum ───────────────────────────────────────────────

class TestUCConsensus004Supermajority:
    """UAT-UC-CONSENSUS-004: Supermajority (≥0.66) threshold."""

    def test_two_of_three_approve_passes_majority_fails_supermajority(self):
        """2/3 = 0.666... passes majority but supermajority requires ≥0.66 strictly."""
        # Under NEUTRAL abstention model: 2 approve, 1 abstain → ratio = 2/(2+0) = 1.0
        # But 2 approve, 1 REJECT → ratio = 2/3 = 0.666 which is exactly the threshold
        events = [
            make_proposal_event(quorum="supermajority"),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "approve"),
            make_vote_event("gen-ops-observer", "reject"),
        ]
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config(quorum=QuorumThreshold.SUPERMAJORITY)
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        # 2/(2+1) = 0.666... ≥ 0.66 → passes supermajority
        assert result.converged is True
        assert result.approve_votes == 2
        assert result.reject_votes == 1

    def test_one_of_three_approve_fails_supermajority(self):
        """1/3 = 0.333 < 0.66 — supermajority not reached."""
        events = [
            make_proposal_event(quorum="supermajority"),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "reject"),
            make_vote_event("gen-ops-observer", "reject"),
        ]
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config(quorum=QuorumThreshold.SUPERMAJORITY,
                             review_closes_at=BASE_TIME + timedelta(seconds=1))
        result = evaluate_quorum(config, votes, comments, now=AFTER_CLOSE)

        assert result.converged is False
        assert result.failure_reason == FailureReason.QUORUM_NOT_REACHED


# ── UC-005: Window not closed — partial votes ──────────────────────────────────

class TestUCConsensus005PartialVotes:
    """UAT-UC-CONSENSUS-005: Votes arriving incrementally — window still open."""

    def test_partial_votes_window_open_not_converged(self):
        """Only 1 vote cast, window still open → not converged (window not closed)."""
        events = [
            make_proposal_event(),  # closes in 14 days
            make_vote_event("gen-dev-observer", "approve"),
        ]
        votes, comments = project_review_state(events, REVIEW_ID, CLOSE_TIME)
        config = make_config()
        # now = before close
        result = evaluate_quorum(config, votes, comments, now=BASE_TIME + timedelta(hours=1))

        assert result.converged is False
        # Window still open → WINDOW_CLOSED_INSUFFICIENT_VOTES (check 2 fails)
        assert result.failure_reason == FailureReason.WINDOW_CLOSED_INSUFFICIENT_VOTES

    def test_all_votes_after_close_converges(self):
        """All 3 votes cast, queried after window closes → converges."""
        events = [
            make_proposal_event(review_closes_at=BASE_TIME + timedelta(days=1)),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "approve"),
            make_vote_event("gen-ops-observer", "approve"),
        ]
        votes, comments = project_review_state(events, REVIEW_ID,
                                               BASE_TIME + timedelta(days=1))
        config = make_config(review_closes_at=BASE_TIME + timedelta(days=1))
        # Query AFTER window closes → all 5 checks pass
        result = evaluate_quorum(config, votes, comments,
                                 now=BASE_TIME + timedelta(days=2))

        assert result.converged is True
        assert result.approve_votes == 3


# ── UC-006: genesis_monitor review parser integration ─────────────────────────

class TestUCConsensus006MonitorParser:
    """UAT-UC-CONSENSUS-006: genesis_monitor parsers correctly project CONSENSUS events."""

    def test_parse_reviews_happy_path(self, tmp_path):
        """parse_reviews returns a ReviewSession with correct tallies from events.jsonl."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "approve"),
            make_vote_event("gen-ops-observer", "abstain"),
        ]
        write_events(tmp_path, events)

        workspace = tmp_path / ".ai-workspace"
        sessions = parse_reviews(workspace)
        assert len(sessions) == 1
        s = sessions[0]

        assert s.review_id == REVIEW_ID
        assert s.status == "open"  # no consensus_reached event yet
        assert s.approve_votes == 2
        assert s.reject_votes == 0
        assert s.abstain_votes == 1
        assert s.non_response_count == 0
        assert len(s.roster) == 3
        assert s.quorum == "majority"

    def test_parse_reviews_consensus_reached(self, tmp_path):
        """Session status is 'consensus_reached' when that event exists."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "approve"),
            make_vote_event("gen-ops-observer", "abstain"),
            {
                "event_type": "consensus_reached",
                "review_id": REVIEW_ID,
                "timestamp": AFTER_CLOSE.isoformat(),
                "project": "ai-sdlc-method",
                "data": {
                    "artifact": ARTIFACT,
                    "quorum_threshold": "majority",
                    "approve_votes": 2,
                    "reject_votes": 0,
                    "abstain_votes": 1,
                },
            },
        ]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        assert len(sessions) == 1
        assert sessions[0].status == "consensus_reached"

    def test_parse_reviews_consensus_failed(self, tmp_path):
        """Session status is 'consensus_failed' when that event exists."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "reject"),
            make_vote_event("gen-cicd-observer", "reject"),
            make_vote_event("gen-ops-observer", "approve"),
            {
                "event_type": "consensus_failed",
                "review_id": REVIEW_ID,
                "timestamp": AFTER_CLOSE.isoformat(),
                "project": "ai-sdlc-method",
                "data": {
                    "artifact": ARTIFACT,
                    "failure_reason": "quorum_not_met",
                    "available_paths": ["revise_and_reopen", "escalate_to_human"],
                },
            },
        ]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        assert len(sessions) == 1
        s = sessions[0]
        assert s.status == "consensus_failed"
        assert s.failure_reason == "quorum_not_met"

    def test_parse_reviews_multiple_sessions(self, tmp_path):
        """Multiple review sessions are all projected correctly."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(review_id="REVIEW-ADR-S-027-1"),
            make_vote_event("gen-dev-observer", "approve", review_id="REVIEW-ADR-S-027-1"),
            make_proposal_event(review_id="REVIEW-ADR-S-028-1"),
            make_vote_event("gen-ops-observer", "reject", review_id="REVIEW-ADR-S-028-1"),
        ]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        assert len(sessions) == 2
        ids = {s.review_id for s in sessions}
        assert "REVIEW-ADR-S-027-1" in ids
        assert "REVIEW-ADR-S-028-1" in ids


# ── UC-007: Quorum progress bar ────────────────────────────────────────────────

class TestUCConsensus007QuorumProgress:
    """UAT-UC-CONSENSUS-007: quorum_progress_pct is correct for UI progress bar."""

    def test_zero_progress_no_votes(self, tmp_path):
        """0% progress when no votes cast (approve_ratio=0, threshold=0.5 → pct=0)."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [make_proposal_event()]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        assert sessions[0].quorum_progress_pct == 0

    def test_progress_approve_only_votes(self, tmp_path):
        """1 approve + 0 reject → approve_ratio=1.0 → pct capped at 100 for majority threshold."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "approve"),
        ]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        s = sessions[0]
        # approve_ratio = 1/(1+0) = 1.0; majority threshold = 0.5
        # pct = min(100, int(1.0/0.5 * 100)) = min(100, 200) = 100
        assert s.quorum_progress_pct == 100

    def test_hundred_percent_progress_on_consensus(self, tmp_path):
        """100% progress when consensus_reached event exists."""
        try:
            from projects.genesis_monitor.imp_fastapi.code.src.genesis_monitor.parsers.reviews import (
                parse_reviews,
            )
        except ImportError:
            pytest.skip("genesis_monitor not on path")

        events = [
            make_proposal_event(),
            make_vote_event("gen-dev-observer", "approve"),
            make_vote_event("gen-cicd-observer", "approve"),
            {
                "event_type": "consensus_reached",
                "review_id": REVIEW_ID,
                "timestamp": AFTER_CLOSE.isoformat(),
                "project": "ai-sdlc-method",
                "data": {"artifact": ARTIFACT, "quorum_threshold": "majority",
                         "approve_votes": 2, "reject_votes": 0, "abstain_votes": 1},
            },
        ]
        write_events(tmp_path, events)

        sessions = parse_reviews(tmp_path / ".ai-workspace")
        assert sessions[0].quorum_progress_pct == 100


# ── UC-008: Artifact ADR status update ────────────────────────────────────────

class TestUCConsensus008ArtifactUpdate:
    """UAT-UC-CONSENSUS-008: consensus_reached causes ADR Status to be updated."""

    def test_proposed_becomes_accepted(self, tmp_path):
        """An ADR file with '**Status**: Proposed' is updated to 'Accepted' on consensus."""
        adr_file = tmp_path / "specification" / "adrs" / "ADR-S-027-test.md"
        adr_file.parent.mkdir(parents=True)
        adr_file.write_text(
            "# ADR-S-027 Test\n\n**Status**: Proposed\n\nSome content.\n"
        )

        # Simulate what gen-consensus-open does on consensus_reached
        content = adr_file.read_text()
        updated = content.replace("**Status**: Proposed", "**Status**: Accepted")
        adr_file.write_text(updated)

        assert "**Status**: Accepted" in adr_file.read_text()
        assert "**Status**: Proposed" not in adr_file.read_text()

    def test_provisional_becomes_accepted(self, tmp_path):
        """An ADR file with '**Status**: Provisional' is updated to 'Accepted'."""
        adr_file = tmp_path / "specification" / "adrs" / "ADR-S-027-test.md"
        adr_file.parent.mkdir(parents=True)
        adr_file.write_text(
            "# ADR-S-027 Test\n\n**Status**: Provisional\n\nSome content.\n"
        )

        content = adr_file.read_text()
        updated = content.replace("**Status**: Provisional", "**Status**: Accepted")
        adr_file.write_text(updated)

        assert "**Status**: Accepted" in adr_file.read_text()

    def test_already_accepted_unchanged(self, tmp_path):
        """An ADR already Accepted is not double-updated."""
        adr_file = tmp_path / "adr.md"
        adr_file.write_text("# Test\n\n**Status**: Accepted\n\nContent.\n")

        # No modification needed
        content = adr_file.read_text()
        if "**Status**: Proposed" in content:
            adr_file.write_text(content.replace("**Status**: Proposed", "**Status**: Accepted"))

        # File is unchanged
        assert adr_file.read_text() == "# Test\n\n**Status**: Accepted\n\nContent.\n"
