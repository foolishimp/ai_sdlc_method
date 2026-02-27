# Validates: REQ-ROBUST-003 (Crash Recovery), REQ-ROBUST-007 (Failure Events), REQ-ROBUST-008 (Session Gap Detection)
"""Tests for session gap detection and failure event emission."""

import json

import pytest

from genesis.workspace_state import detect_abandoned_iterations, load_events


# ── detect_abandoned_iterations tests ────────────────────────────────


class TestDetectAbandonedIterations:
    """Validates: REQ-ROBUST-003, REQ-ROBUST-008."""

    def test_no_events_no_gaps(self):
        """Empty event log produces no abandoned iterations."""
        assert detect_abandoned_iterations([]) == []

    def test_edge_started_then_converged_no_gap(self):
        """A started edge followed by convergence is not abandoned."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t1"},
            {"event_type": "edge_converged", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t2"},
        ]
        assert detect_abandoned_iterations(events) == []

    def test_edge_started_then_iteration_completed_no_gap(self):
        """A started edge followed by iteration_completed is not abandoned."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t1"},
            {"event_type": "iteration_completed", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t2"},
        ]
        assert detect_abandoned_iterations(events) == []

    def test_edge_started_no_completion_detected(self):
        """An edge_started with no completion is detected as abandoned."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "2026-02-27T10:00:00Z"},
        ]
        result = detect_abandoned_iterations(events)
        assert len(result) == 1
        assert result[0]["feature"] == "REQ-F-001"
        assert result[0]["edge"] == "design→code"
        assert result[0]["last_event_timestamp"] == "2026-02-27T10:00:00Z"

    def test_multiple_abandoned_edges(self):
        """Multiple incomplete edges are all detected."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t1"},
            {"event_type": "edge_started", "feature": "REQ-F-002", "edge": "code↔unit_tests", "timestamp": "t2"},
        ]
        result = detect_abandoned_iterations(events)
        assert len(result) == 2

    def test_mixed_completed_and_abandoned(self):
        """Only incomplete edges are flagged; completed ones are not."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t1"},
            {"event_type": "edge_converged", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t2"},
            {"event_type": "edge_started", "feature": "REQ-F-002", "edge": "code↔unit_tests", "timestamp": "t3"},
        ]
        result = detect_abandoned_iterations(events)
        assert len(result) == 1
        assert result[0]["feature"] == "REQ-F-002"

    def test_idempotent_with_existing_abandoned_event(self):
        """Already-emitted iteration_abandoned events are not re-detected."""
        events = [
            {"event_type": "edge_started", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t1"},
            {"event_type": "iteration_abandoned", "feature": "REQ-F-001", "edge": "design→code", "timestamp": "t2"},
        ]
        result = detect_abandoned_iterations(events)
        assert len(result) == 0

    def test_events_without_feature_or_edge_ignored(self):
        """Events missing feature or edge fields are silently skipped."""
        events = [
            {"event_type": "edge_started", "timestamp": "t1"},
            {"event_type": "edge_started", "feature": "REQ-F-001", "timestamp": "t2"},
        ]
        result = detect_abandoned_iterations(events)
        assert len(result) == 0


# ── Failure event structure tests ────────────────────────────────────


class TestFpFailureEventStructure:
    """Validates: REQ-ROBUST-007 — failure events have correct schema."""

    def test_fp_failure_event_from_engine(self, tmp_path):
        """Engine emits fp_failure event on construct failure."""
        from genesis.fd_emit import emit_event, make_event

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True)

        emit_event(
            events_path,
            make_event(
                "fp_failure",
                "test_project",
                feature="REQ-F-001",
                edge="design→code",
                iteration=1,
                classification="TIMEOUT",
                duration_ms=120000,
                retries=2,
                phase="construct",
            ),
        )

        events = load_events(tmp_path)
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "fp_failure"
        assert ev["project"] == "test_project"
        assert ev["feature"] == "REQ-F-001"
        assert ev["edge"] == "design→code"
        assert ev["classification"] == "TIMEOUT"
        assert ev["duration_ms"] == 120000
        assert ev["retries"] == 2

    def test_evaluator_detail_event_structure(self, tmp_path):
        """Engine emits evaluator_detail event on check failure."""
        from genesis.fd_emit import emit_event, make_event

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True)

        emit_event(
            events_path,
            make_event(
                "evaluator_detail",
                "test_project",
                feature="REQ-F-001",
                edge="code↔unit_tests",
                iteration=3,
                check_name="tests_pass",
                check_type="deterministic",
                outcome="fail",
                required=True,
                message="2 tests failed",
            ),
        )

        events = load_events(tmp_path)
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "evaluator_detail"
        assert ev["check_name"] == "tests_pass"
        assert ev["check_type"] == "deterministic"
        assert ev["outcome"] == "fail"
        assert ev["required"] is True

    def test_iteration_abandoned_event_structure(self, tmp_path):
        """Abandoned iteration event has required fields."""
        from genesis.fd_emit import emit_event, make_event

        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True)

        emit_event(
            events_path,
            make_event(
                "iteration_abandoned",
                "test_project",
                feature="REQ-F-001",
                edge="design→code",
                last_event_timestamp="2026-02-27T10:00:00Z",
            ),
        )

        events = load_events(tmp_path)
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "iteration_abandoned"
        assert ev["feature"] == "REQ-F-001"
        assert ev["edge"] == "design→code"
        assert ev["last_event_timestamp"] == "2026-02-27T10:00:00Z"


# ── Integration: _check_session_gaps ─────────────────────────────────


class TestCheckSessionGaps:
    """Validates: REQ-ROBUST-008 — startup gap detection integration."""

    def test_gap_detected_and_event_emitted(self, tmp_path):
        """_check_session_gaps emits iteration_abandoned for incomplete edges."""
        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_file = events_dir / "events.jsonl"
        events_file.write_text(
            json.dumps({
                "event_type": "edge_started",
                "timestamp": "2026-02-27T10:00:00Z",
                "project": "test",
                "feature": "REQ-F-001",
                "edge": "design→code",
            }) + "\n"
        )

        from genesis.__main__ import _check_session_gaps

        _check_session_gaps(tmp_path, "test")

        events = load_events(tmp_path)
        abandoned = [e for e in events if e["event_type"] == "iteration_abandoned"]
        assert len(abandoned) == 1
        assert abandoned[0]["feature"] == "REQ-F-001"

    def test_no_gaps_no_events(self, tmp_path):
        """When no gaps exist, no events are emitted."""
        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_file = events_dir / "events.jsonl"
        events_file.write_text(
            json.dumps({
                "event_type": "edge_started",
                "timestamp": "2026-02-27T10:00:00Z",
                "project": "test",
                "feature": "REQ-F-001",
                "edge": "design→code",
            }) + "\n"
            + json.dumps({
                "event_type": "edge_converged",
                "timestamp": "2026-02-27T10:05:00Z",
                "project": "test",
                "feature": "REQ-F-001",
                "edge": "design→code",
            }) + "\n"
        )

        from genesis.__main__ import _check_session_gaps

        _check_session_gaps(tmp_path, "test")

        events = load_events(tmp_path)
        abandoned = [e for e in events if e["event_type"] == "iteration_abandoned"]
        assert len(abandoned) == 0
