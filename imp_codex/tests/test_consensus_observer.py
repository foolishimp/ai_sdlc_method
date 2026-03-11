# Validates: REQ-F-CONSENSUS-001, REQ-F-CDX-006
"""Replay-driven observer tests for the Codex consensus saga."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from imp_codex.runtime import (
    RuntimePaths,
    gen_comment,
    gen_consensus_open,
    gen_dispose,
    gen_vote,
    run_consensus_observer,
)
from imp_codex.runtime.events import load_events


def _ts(minutes: int) -> str:
    base = datetime(2026, 3, 12, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _write_review_artifact(project_root: Path, relative_path: str) -> str:
    artifact_path = project_root / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("# Observer Fixture\n\nConsensus observer test artifact.\n")
    return relative_path


def test_consensus_observer_writes_and_clears_pending_disposition_action(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "specification/adrs/ADR-010.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-adr-010-1",
        review_closes_in=3600,
        event_time=_ts(0),
    )
    comment = gen_comment(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        content="Please clarify the rollback handling.",
        event_time=_ts(5),
    )

    observed = run_consensus_observer(
        project_root,
        review_id=opened["review_id"],
        now=_ts(6),
    )

    assert observed.processed_reviews == 1
    assert observed.actions_written >= 2
    review_summary = observed.reviews[0]
    assert review_summary["pending_actions"][0]["kind"] == "pending_disposition"

    action_path = Path(review_summary["pending_actions"][0]["path"])
    assert action_path.exists()
    action_doc = yaml.safe_load(action_path.read_text())
    assert action_doc["comment_id"] == comment["comment_id"]
    assert action_doc["trigger_reason"] == "pending_disposition"

    state_doc = yaml.safe_load(Path(review_summary["state_path"]).read_text())
    assert state_doc["gating_comments_remaining"] == [comment["comment_id"]]

    gen_dispose(
        project_root,
        review_id=opened["review_id"],
        comment_id=comment["comment_id"],
        disposition="resolved",
        rationale="Rollback section added.",
        event_time=_ts(10),
    )

    observed_again = run_consensus_observer(
        project_root,
        review_id=opened["review_id"],
        now=_ts(11),
    )

    assert observed_again.processed_reviews == 1
    assert observed_again.reviews[0]["pending_actions"] == []
    assert action_path.exists() is False

    cleared_state = yaml.safe_load(Path(observed_again.reviews[0]["state_path"]).read_text())
    assert cleared_state["gating_comments_remaining"] == []


def test_consensus_observer_emits_closeout_when_projection_is_terminal(tmp_path):
    project_root = tmp_path / "demo"
    artifact = _write_review_artifact(project_root, "design/proposals/closeout-demo.md")

    opened = gen_consensus_open(
        project_root,
        artifact=artifact,
        roster="alice,bob",
        review_id="REVIEW-closeout-demo-1",
        review_closes_in=1800,
        min_participation_ratio=1.0,
        event_time=_ts(0),
    )
    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="alice",
        verdict="approve",
        rationale="Ready.",
        event_time=_ts(5),
    )
    gen_vote(
        project_root,
        review_id=opened["review_id"],
        participant="bob",
        verdict="approve",
        rationale="Looks good.",
        event_time=_ts(10),
    )

    observed = run_consensus_observer(
        project_root,
        review_id=opened["review_id"],
        now=_ts(31),
    )

    assert observed.processed_reviews == 1
    assert observed.closeouts_emitted == 1
    review_summary = observed.reviews[0]
    assert review_summary["outcome"] == "passed"
    assert review_summary["terminal_run_id"] is not None

    state_doc = yaml.safe_load(Path(review_summary["state_path"]).read_text())
    assert state_doc["outcome"] == "passed"
    assert state_doc["terminal_run_id"] == review_summary["terminal_run_id"]

    semantic_types = [event.semantic_type for event in load_events(RuntimePaths(project_root).events_file)]
    assert semantic_types == [
        "ConsensusRequested",
        "VoteCast",
        "VoteCast",
        "ConsensusReached",
    ]

    observed_again = run_consensus_observer(
        project_root,
        review_id=opened["review_id"],
        now=_ts(32),
    )
    assert observed_again.closeouts_emitted == 0
