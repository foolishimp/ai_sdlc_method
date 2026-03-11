# Validates: REQ-F-CONSENSUS-001, REQ-F-CONS-001, REQ-F-CONS-002, REQ-F-CONS-003, REQ-F-CONS-005, REQ-F-CONS-008, REQ-F-CONS-009
"""Executable replay tests for the Codex consensus runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from imp_codex.runtime import (
    RuntimePaths,
    gen_comment,
    gen_consensus_close,
    gen_consensus_open,
    gen_consensus_recover,
    gen_consensus_status,
    gen_dispose,
    gen_vote,
)
from imp_codex.runtime.consensus import gating_comments, late_comments, vote_snapshot
from imp_codex.runtime.events import load_events


def _ts(minutes: int) -> str:
    base = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _write_review_artifact(project_root: Path, relative_path: str) -> str:
    artifact_path = project_root / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("# Review Artifact\n\nConsensus demo fixture.\n")
    return relative_path


def test_consensus_cycle_passes_after_disposition_and_closeout(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/adrs/ADR-001.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="gen-dev-observer,human:alice,human:bob",
        review_id="REVIEW-adr-001-1",
        min_participation_ratio=2 / 3,
        review_closes_in=3600,
        event_time=_ts(0),
    )

    assert opened["cycle_id"] == "CYCLE-001"
    assert opened["state"]["outcome"] == "deferred"
    review_doc = yaml.safe_load(Path(opened["review_path"]).read_text())
    assert review_doc["review_id"] == opened["review_id"]
    assert review_doc["cycle_id"] == "CYCLE-001"

    comment = gen_comment(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        content="Clarify the recovery behaviour before approval.",
        event_time=_ts(10),
    )
    assert comment["gating"] is True
    assert comment["state"]["gating_comments_remaining"] == ["COMMENT-001"]
    assert Path(comment["comment_path"]).exists()

    disposed = gen_dispose(
        project_root,
        review_id=opened["review_id"],
        comment_id=comment["comment_id"],
        disposition="resolved",
        rationale="Recovery section added to the ADR.",
        event_time=_ts(20),
    )
    assert disposed["state"]["gating_comments_remaining"] == []
    disposition_doc = yaml.safe_load(Path(disposed["disposition_path"]).read_text())
    assert disposition_doc["disposition"] == "resolved"

    alice_vote = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="approve",
        rationale="Recovery language is now explicit.",
        event_time=_ts(30),
    )
    bob_vote = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="bob",
        verdict="approve",
        rationale="Ready to merge.",
        event_time=_ts(40),
    )
    assert Path(alice_vote["vote_path"]).exists()
    assert Path(bob_vote["vote_path"]).exists()

    status = gen_consensus_status(
        project_root,
        review_id=opened["review_id"],
        now=_ts(61),
    )
    assert status["outcome"] == "passed"
    assert status["approve_votes"] == 2
    assert status["reject_votes"] == 0
    assert status["participation_ratio"] == pytest.approx(2 / 3)
    assert status["gating_comments_remaining"] == []

    closed = gen_consensus_close(
        project_root,
        review_id=opened["review_id"],
        event_time=_ts(61),
    )
    assert closed["emitted"] is True
    assert closed["outcome"] == "passed"
    outcome_doc = yaml.safe_load(Path(closed["outcome_path"]).read_text())
    assert outcome_doc["outcome"] == "passed"

    second_close = gen_consensus_close(
        project_root,
        review_id=opened["review_id"],
        event_time=_ts(62),
    )
    assert second_close["emitted"] is False
    assert second_close["terminal_run_id"] == closed["terminal_run_id"]

    replay = load_events(RuntimePaths(project_root).events_file)
    assert [event.semantic_type for event in replay] == [
        "ConsensusRequested",
        "CommentReceived",
        "CommentDispositioned",
        "VoteCast",
        "VoteCast",
        "ConsensusReached",
    ]

    late = gen_comment(
        project_root,
        review_id=opened["review_id"],
        participant="gen-dev-observer",
        content="Late context: relay review also looks good.",
        event_time=_ts(63),
    )
    assert late["gating"] is False
    assert late["state"]["current_cycle_open"] is False

    replay = load_events(RuntimePaths(project_root).events_file)
    assert len(gating_comments(replay, opened["review_id"], "CYCLE-001")) == 1
    assert len(late_comments(replay, opened["review_id"], "CYCLE-001")) == 1


def test_gating_vote_triggers_comment_event_and_written_review_trail(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/adrs/ADR-002.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-adr-002-1",
        review_closes_in=600,
        event_time=_ts(0),
    )

    voted = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="reject",
        rationale="Need rollback details before approval.",
        gating=True,
        event_time=_ts(5),
    )

    assert voted["comment_run_id"] is not None
    vote_doc = yaml.safe_load(Path(voted["vote_path"]).read_text())
    assert vote_doc["verdict"] == "reject"
    assert vote_doc["participant"] == "alice"

    comment_text = Path(voted["comment_path"]).read_text()
    assert "Need rollback details before approval." in comment_text
    assert "gating: true" in comment_text

    events = load_events(RuntimePaths(project_root).events_file)
    assert [event.semantic_type for event in events] == [
        "ConsensusRequested",
        "VoteCast",
        "CommentReceived",
    ]
    vote_payload = events[1].raw["run"]["facets"]["sdlc:payload"]
    comment_payload = events[2].raw["run"]["facets"]["sdlc:payload"]
    assert vote_payload["vote_ref"].endswith("votes/alice.yml")
    assert comment_payload["content_ref"].endswith("comments/COMMENT-001.md")


def test_consensus_tie_failure_can_reopen_and_pass_new_cycle(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "design/proposals/auth-scope.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-auth-scope-1",
        review_closes_in=1800,
        min_participation_ratio=1.0,
        event_time=_ts(0),
    )

    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="approve",
        rationale="Looks fine.",
        event_time=_ts(5),
    )
    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="reject",
        rationale="Actually, the rollback path is underspecified.",
        event_time=_ts(10),
    )
    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="bob",
        verdict="approve",
        rationale="Happy with the current draft.",
        event_time=_ts(15),
    )

    replay = load_events(RuntimePaths(project_root).events_file)
    snapshot = vote_snapshot(replay, opened["review_id"], "CYCLE-001")
    assert snapshot["alice"]["verdict"] == "reject"
    assert snapshot["bob"]["verdict"] == "approve"

    status = gen_consensus_status(
        project_root,
        review_id=opened["review_id"],
        now=_ts(31),
    )
    assert status["outcome"] == "failed"
    assert status["failure_reason"] == "tie"
    assert status["available_paths"] == ["re_open", "narrow_scope", "abandon"]

    closed = gen_consensus_close(
        project_root,
        review_id=opened["review_id"],
        event_time=_ts(31),
    )
    assert closed["emitted"] is True
    assert closed["outcome"] == "failed"

    recovered = gen_consensus_recover(
        project_root,
        review_id=opened["review_id"],
        path="re_open",
        rationale="Address tie with a revised draft.",
        review_closes_in=600,
        event_time=_ts(32),
    )
    assert recovered["review_reopened_run_id"] is not None
    assert recovered["state"]["review_id"] == opened["review_id"]
    assert recovered["state"]["cycle_id"] == "CYCLE-002"
    assert recovered["state"]["outcome"] == "deferred"

    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="approve",
        rationale="Rollback path is fixed now.",
        event_time=_ts(35),
    )
    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="bob",
        verdict="approve",
        rationale="Approved on reopen.",
        event_time=_ts(36),
    )

    reopened_status = gen_consensus_status(
        project_root,
        review_id=opened["review_id"],
        cycle_id="CYCLE-002",
        now=_ts(43),
    )
    assert reopened_status["outcome"] == "passed"
    assert reopened_status["approve_votes"] == 2

    reopened_close = gen_consensus_close(
        project_root,
        review_id=opened["review_id"],
        cycle_id="CYCLE-002",
        event_time=_ts(43),
    )
    assert reopened_close["emitted"] is True
    assert reopened_close["outcome"] == "passed"

    replay = load_events(RuntimePaths(project_root).events_file)
    assert [event.semantic_type for event in replay] == [
        "ConsensusRequested",
        "VoteCast",
        "VoteCast",
        "VoteCast",
        "ConsensusFailed",
        "RecoveryPathSelected",
        "ReviewReopened",
        "VoteCast",
        "VoteCast",
        "ConsensusReached",
    ]


def test_scope_change_disposition_emits_spec_modified(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/reviews/PROP-001.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice",
        review_id="REVIEW-prop-001-1",
        review_closes_in=900,
        event_time=_ts(0),
    )

    comment = gen_comment(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        content="This should be split into a smaller proposal.",
        event_time=_ts(1),
    )

    disposed = gen_dispose(
        project_root,
        review_id=opened["review_id"],
        comment_id=comment["comment_id"],
        disposition="scope_change",
        rationale="Proposal narrowed to auth-only scope.",
        event_time=_ts(2),
    )

    assert disposed["spec_modified_run_id"] is not None
    assert disposed["state"]["gating_comments_dispositioned"] == 1
    assert disposed["state"]["gating_comments_remaining"] == []

    replay = load_events(RuntimePaths(project_root).events_file)
    assert [event.semantic_type for event in replay] == [
        "ConsensusRequested",
        "CommentReceived",
        "CommentDispositioned",
        "SpecModified",
    ]
