# Validates: REQ-F-CONSENSUS-001, REQ-F-CONS-001, REQ-F-CONS-002, REQ-F-CONS-003
"""End-to-end consensus scenarios for the Codex runtime."""

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
    gen_consensus_status,
    gen_dispose,
    gen_vote,
)
from imp_codex.runtime.events import load_events


def _ts(minutes: int) -> str:
    base = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _write_review_artifact(project_root: Path, relative_path: str) -> str:
    artifact_path = project_root / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("# Consensus Artifact\n\nE2E consensus scenario.\n")
    return relative_path


@pytest.mark.e2e
def test_e2e_consensus_pass_loop_writes_review_trail(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/adrs/ADR-E2E-001.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-adr-e2e-001-1",
        review_closes_in=900,
        min_participation_ratio=1.0,
        event_time=_ts(0),
    )
    comment = gen_comment(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        content="Please make the rollback path explicit.",
        event_time=_ts(2),
    )
    disposed = gen_dispose(
        project_root,
        review_id=opened["review_id"],
        comment_id=comment["comment_id"],
        disposition="resolved",
        rationale="Rollback section added.",
        event_time=_ts(4),
    )
    alice_vote = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="approve",
        rationale="Looks good now.",
        event_time=_ts(6),
    )
    bob_vote = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="bob",
        verdict="approve",
        rationale="Approved.",
        event_time=_ts(7),
    )
    status = gen_consensus_status(project_root, review_id=opened["review_id"], now=_ts(20))
    closed = gen_consensus_close(project_root, review_id=opened["review_id"], event_time=_ts(20))

    assert status["outcome"] == "passed"
    assert closed["outcome"] == "passed"
    assert Path(opened["review_path"]).exists()
    assert Path(comment["comment_path"]).exists()
    assert Path(disposed["disposition_path"]).exists()
    assert Path(alice_vote["vote_path"]).exists()
    assert Path(bob_vote["vote_path"]).exists()
    assert Path(closed["outcome_path"]).exists()

    review_doc = yaml.safe_load(Path(opened["review_path"]).read_text())
    outcome_doc = yaml.safe_load(Path(closed["outcome_path"]).read_text())
    assert review_doc["artifact"] == artifact
    assert outcome_doc["outcome"] == "passed"

    events = load_events(RuntimePaths(project_root).events_file)
    assert [event.semantic_type for event in events] == [
        "ConsensusRequested",
        "CommentReceived",
        "CommentDispositioned",
        "VoteCast",
        "VoteCast",
        "ConsensusReached",
    ]


@pytest.mark.e2e
def test_e2e_consensus_gating_vote_triggers_comment_write(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/reviews/PROP-E2E-002.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-prop-e2e-002-1",
        review_closes_in=900,
        event_time=_ts(0),
    )
    vote = gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="reject",
        rationale="Need narrower scope before approval.",
        gating=True,
        event_time=_ts(3),
    )

    assert vote["comment_run_id"] is not None
    assert Path(vote["vote_path"]).exists()
    assert Path(vote["comment_path"]).exists()

    vote_doc = yaml.safe_load(Path(vote["vote_path"]).read_text())
    comment_text = Path(vote["comment_path"]).read_text()
    assert vote_doc["verdict"] == "reject"
    assert "Need narrower scope before approval." in comment_text

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
