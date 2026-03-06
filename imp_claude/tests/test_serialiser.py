# Validates: REQ-COORD-002 (Feature Assignment via Events), REQ-COORD-004, REQ-COORD-005
"""Tests for ADR-013 Serialiser — multi-agent edge claim resolution."""

import json
import time
from pathlib import Path

import pytest

from genesis.serialiser import (
    detect_stale_claims,
    get_active_claims,
    process_inbox,
    read_inbox_events,
    stage_claim,
    stage_release,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Minimal workspace with events and inbox dirs."""
    (tmp_path / ".ai-workspace" / "events" / "inbox").mkdir(parents=True)
    return tmp_path


def _write_events(workspace: Path, events: list[dict]) -> None:
    events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
    with open(events_file, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _read_events(workspace: Path) -> list[dict]:
    events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    return [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]


# ── get_active_claims ─────────────────────────────────────────────────────────


class TestGetActiveClaims:
    def test_edge_started_creates_claim(self) -> None:
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code", "agent_id": "agent-1"},
        ]
        claims = get_active_claims(events)
        assert claims[("REQ-F-A", "design→code")] == "agent-1"

    def test_edge_converged_releases_claim(self) -> None:
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code", "agent_id": "agent-1"},
            {"event_type": "edge_converged", "feature": "REQ-F-A", "edge": "design→code", "agent_id": "agent-1"},
        ]
        claims = get_active_claims(events)
        assert ("REQ-F-A", "design→code") not in claims

    def test_edge_released_releases_claim(self) -> None:
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code", "agent_id": "agent-1"},
            {"event_type": "edge_released", "feature": "REQ-F-A", "edge": "design→code"},
        ]
        claims = get_active_claims(events)
        assert ("REQ-F-A", "design→code") not in claims

    def test_multiple_features_tracked_independently(self) -> None:
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code", "agent_id": "agent-1"},
            {"event_type": "edge_started", "feature": "REQ-F-B", "edge": "code↔unit_tests", "agent_id": "agent-2"},
        ]
        claims = get_active_claims(events)
        assert claims[("REQ-F-A", "design→code")] == "agent-1"
        assert claims[("REQ-F-B", "code↔unit_tests")] == "agent-2"

    def test_empty_events_returns_empty_claims(self) -> None:
        assert get_active_claims([]) == {}


# ── detect_stale_claims ───────────────────────────────────────────────────────


class TestDetectStaleClaims:
    def test_detects_stale_after_timeout(self) -> None:
        old_ts = "2026-01-01T00:00:00Z"
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code",
             "agent_id": "agent-1", "timestamp": old_ts},
        ]
        # now is way in the future
        now = time.time()
        stale = detect_stale_claims(events, timeout_seconds=60, now=now)
        assert len(stale) == 1
        assert stale[0]["agent_id"] == "agent-1"
        assert stale[0]["feature"] == "REQ-F-A"
        assert stale[0]["seconds_idle"] > 0

    def test_fresh_claim_not_stale(self) -> None:
        fresh_ts = "2026-03-07T12:00:00Z"
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code",
             "agent_id": "agent-1", "timestamp": fresh_ts},
        ]
        fresh_now = 1741348800.0  # 2026-03-07T12:00:00Z epoch
        stale = detect_stale_claims(events, timeout_seconds=3600, now=fresh_now + 60)
        assert stale == []

    def test_empty_events_no_stale(self) -> None:
        stale = detect_stale_claims([], timeout_seconds=60, now=time.time())
        assert stale == []


# ── stage_claim / stage_release ───────────────────────────────────────────────


class TestStageClaim:
    def test_stage_claim_creates_inbox_file(self, workspace: Path) -> None:
        path = stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["event_type"] == "edge_claim"
        assert data["feature"] == "REQ-F-A"
        assert data["edge"] == "design→code"
        assert data["agent_id"] == "agent-1"

    def test_stage_release_creates_inbox_file(self, workspace: Path) -> None:
        path = stage_release(workspace, "agent-1", "REQ-F-A", "design→code")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["event_type"] == "edge_released"
        assert data["agent_id"] == "agent-1"

    def test_inbox_file_in_agent_subdir(self, workspace: Path) -> None:
        path = stage_claim(workspace, "my-agent", "REQ-F-B", "code↔unit_tests")
        assert path.parent.name == "my-agent"


# ── read_inbox_events ─────────────────────────────────────────────────────────


class TestReadInboxEvents:
    def test_reads_events_in_agent_then_seq_order(self, workspace: Path) -> None:
        # Two agents: agent-a and agent-b (alphabetical)
        stage_claim(workspace, "agent-b", "REQ-F-B", "design→code")
        time.sleep(0.01)
        stage_claim(workspace, "agent-a", "REQ-F-A", "design→code")

        inbox_dir = workspace / ".ai-workspace" / "events" / "inbox"
        items = read_inbox_events(inbox_dir)

        # agent-a sorts before agent-b
        assert len(items) == 2
        assert items[0][0] == "agent-a"
        assert items[1][0] == "agent-b"

    def test_empty_inbox_returns_empty(self, workspace: Path) -> None:
        inbox_dir = workspace / ".ai-workspace" / "events" / "inbox"
        assert read_inbox_events(inbox_dir) == []


# ── process_inbox ─────────────────────────────────────────────────────────────


class TestProcessInbox:
    def test_first_claim_granted(self, workspace: Path) -> None:
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")

        counts = process_inbox(workspace, project="test-proj")

        assert counts["granted"] == 1
        assert counts["rejected"] == 0

        events = _read_events(workspace)
        granted = [e for e in events if e.get("event_type") == "edge_started"]
        assert len(granted) == 1
        assert granted[0]["agent_id"] == "agent-1"

    def test_second_claim_for_same_edge_rejected(self, workspace: Path) -> None:
        # First agent claims and gets granted
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        process_inbox(workspace, project="test-proj")

        # Second agent tries to claim same edge
        stage_claim(workspace, "agent-2", "REQ-F-A", "design→code")
        counts = process_inbox(workspace, project="test-proj")

        assert counts["rejected"] == 1
        events = _read_events(workspace)
        rejected = [e for e in events if e.get("event_type") == "claim_rejected"]
        assert len(rejected) == 1
        assert rejected[0]["agent_id"] == "agent-2"
        assert "agent-1" in rejected[0]["data"]["held_by"]

    def test_release_frees_claim_for_next_agent(self, workspace: Path) -> None:
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        process_inbox(workspace, project="test-proj")

        stage_release(workspace, "agent-1", "REQ-F-A", "design→code")
        process_inbox(workspace, project="test-proj")

        # Now agent-2 can claim
        stage_claim(workspace, "agent-2", "REQ-F-A", "design→code")
        counts = process_inbox(workspace, project="test-proj")

        assert counts["granted"] == 1

    def test_different_features_all_granted(self, workspace: Path) -> None:
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        stage_claim(workspace, "agent-2", "REQ-F-B", "code↔unit_tests")

        counts = process_inbox(workspace, project="test-proj")

        assert counts["granted"] == 2
        assert counts["rejected"] == 0

    def test_inbox_files_deleted_after_processing(self, workspace: Path) -> None:
        claim_file = stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        assert claim_file.exists()

        process_inbox(workspace, project="test-proj")

        assert not claim_file.exists()

    def test_stale_claim_emits_claim_expired(self, workspace: Path) -> None:
        # Write an edge_started event with a very old timestamp
        old_ts = "2020-01-01T00:00:00Z"
        _write_events(workspace, [
            {"event_type": "edge_started", "feature": "REQ-F-X", "edge": "design→code",
             "agent_id": "stale-agent", "timestamp": old_ts, "project": "test-proj"},
        ])

        counts = process_inbox(workspace, project="test-proj", timeout_seconds=1)

        assert counts["expired"] == 1
        events = _read_events(workspace)
        expired = [e for e in events if e.get("event_type") == "claim_expired"]
        assert len(expired) == 1
        assert expired[0]["agent_id"] == "stale-agent"

    def test_empty_inbox_returns_zero_counts(self, workspace: Path) -> None:
        counts = process_inbox(workspace, project="test-proj")
        assert counts == {"granted": 0, "rejected": 0, "forwarded": 0, "expired": 0, "errors": 0}

    def test_same_agent_claiming_same_edge_is_idempotent(self, workspace: Path) -> None:
        """Agent re-claiming its own edge should be granted (re-affirmation)."""
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        process_inbox(workspace, project="test-proj")

        # Same agent claims again
        stage_claim(workspace, "agent-1", "REQ-F-A", "design→code")
        counts = process_inbox(workspace, project="test-proj")

        # Should be granted (agent already holds the claim)
        assert counts["granted"] == 1
        assert counts["rejected"] == 0
