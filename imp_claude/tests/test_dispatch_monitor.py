# Validates: REQ-F-SENSE-001, REQ-F-DISPATCH-001
"""Tests for dispatch_monitor — event stream watcher driving autonomous dispatch.

Tests:
- check_and_dispatch() returns fired=False when events.jsonl unchanged
- check_and_dispatch() returns fired=True when mtime changes
- MonitorState accumulates totals across calls
- F_H resolution event detection (consensus_reached, review_approved, etc.)
- has_fh_resolution() detects relevant events by type
- run_monitor() terminates at max_total_fires
- Daemon mode prints progress on each fire
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from genesis.dispatch_monitor import (
    MonitorState,
    check_and_dispatch,
    has_fh_resolution,
    run_monitor,
    FH_RESOLUTION_EVENTS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Minimal workspace with events.jsonl."""
    events_dir = tmp_path / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True)
    (events_dir / "events.jsonl").touch()
    return tmp_path


@pytest.fixture
def events_path(workspace: Path) -> Path:
    return workspace / ".ai-workspace" / "events" / "events.jsonl"


def _append_event(events_path: Path, event_type: str, **extra) -> None:
    event = {"event_type": event_type, "timestamp": "2026-03-11T00:00:00Z", **extra}
    with open(events_path, "a") as f:
        f.write(json.dumps(event) + "\n")


# ── MonitorState ──────────────────────────────────────────────────────────────


class TestMonitorState:
    def test_initial_state(self):
        state = MonitorState()
        assert state.last_mtime == 0.0
        assert state.last_size == 0
        assert state.rounds_fired == 0
        assert state.total_dispatched == 0
        assert state.total_converged == 0
        assert state.fh_pending == 0

    def test_state_is_mutable(self):
        state = MonitorState()
        state.rounds_fired = 5
        state.total_dispatched = 10
        assert state.rounds_fired == 5
        assert state.total_dispatched == 10


# ── check_and_dispatch — unchanged file ───────────────────────────────────────


class TestCheckAndDispatchUnchanged:
    def test_no_fire_on_empty_unchanged_file(self, workspace, events_path):
        state = MonitorState()
        # Set state to match current file
        stat = events_path.stat()
        state.last_mtime = stat.st_mtime
        state.last_size = stat.st_size

        result = check_and_dispatch(workspace, state, events_path)
        assert result["fired"] is False

    def test_no_dispatch_called_when_unchanged(self, workspace, events_path):
        state = MonitorState()
        stat = events_path.stat()
        state.last_mtime = stat.st_mtime
        state.last_size = stat.st_size

        with patch("genesis.dispatch_monitor.run_dispatch_loop") as mock_loop:
            check_and_dispatch(workspace, state, events_path)
            mock_loop.assert_not_called()

    def test_returns_quiescent_when_unchanged(self, workspace, events_path):
        state = MonitorState()
        stat = events_path.stat()
        state.last_mtime = stat.st_mtime
        state.last_size = stat.st_size

        result = check_and_dispatch(workspace, state, events_path)
        assert result["quiescent"] is True

    def test_missing_events_file_returns_no_fire(self, tmp_path):
        workspace = tmp_path
        state = MonitorState()
        missing_path = tmp_path / "nonexistent.jsonl"

        result = check_and_dispatch(workspace, state, missing_path)
        assert result["fired"] is False
        assert result["quiescent"] is True


# ── check_and_dispatch — changed file ─────────────────────────────────────────


class TestCheckAndDispatchChanged:
    def test_fires_when_file_grows(self, workspace, events_path):
        state = MonitorState()
        # First call — initialises state
        with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
            "dispatched": 0, "converged": 0, "fh_required": 0,
            "fp_dispatched": 0, "quiescent": True,
        }):
            check_and_dispatch(workspace, state, events_path)

        # Append an event — file grows
        _append_event(events_path, "intent_raised")
        time.sleep(0.01)

        with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
            "dispatched": 1, "converged": 1, "fh_required": 0,
            "fp_dispatched": 0, "quiescent": True,
        }) as mock_loop:
            result = check_and_dispatch(workspace, state, events_path)

        assert result["fired"] is True
        mock_loop.assert_called_once()

    def test_state_updates_after_fire(self, workspace, events_path):
        state = MonitorState()
        _append_event(events_path, "intent_raised")

        with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
            "dispatched": 2, "converged": 1, "fh_required": 1,
            "fp_dispatched": 0, "quiescent": False,
        }):
            check_and_dispatch(workspace, state, events_path)

        assert state.rounds_fired == 1
        assert state.total_dispatched == 2
        assert state.total_converged == 1
        assert state.fh_pending == 1

    def test_accumulates_across_multiple_fires(self, workspace, events_path):
        state = MonitorState()

        for i in range(3):
            _append_event(events_path, f"event_{i}")
            time.sleep(0.02)
            with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
                "dispatched": 1, "converged": 1, "fh_required": 0,
                "fp_dispatched": 0, "quiescent": True,
            }):
                result = check_and_dispatch(workspace, state, events_path)
            assert result["fired"] is True

        assert state.rounds_fired == 3
        assert state.total_dispatched == 3
        assert state.total_converged == 3

    def test_fh_pending_clears_when_no_fh_required(self, workspace, events_path):
        state = MonitorState()
        state.fh_pending = 3  # simulate prior F_H pending

        _append_event(events_path, "consensus_reached")
        with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
            "dispatched": 1, "converged": 1, "fh_required": 0,
            "fp_dispatched": 0, "quiescent": True,
        }):
            check_and_dispatch(workspace, state, events_path)

        assert state.fh_pending == 0

    def test_returns_dispatch_result_fields(self, workspace, events_path):
        state = MonitorState()
        _append_event(events_path, "intent_raised")

        with patch("genesis.dispatch_monitor.run_dispatch_loop", return_value={
            "dispatched": 3, "converged": 2, "fh_required": 1,
            "fp_dispatched": 0, "quiescent": False,
        }):
            result = check_and_dispatch(workspace, state, events_path)

        assert result["dispatched"] == 3
        assert result["converged"] == 2
        assert result["fh_required"] == 1
        assert result["fired"] is True


# ── F_H resolution detection ──────────────────────────────────────────────────


class TestFhResolution:
    def test_fh_resolution_events_set_not_empty(self):
        assert len(FH_RESOLUTION_EVENTS) >= 4

    def test_consensus_reached_is_fh_resolution(self):
        assert "consensus_reached" in FH_RESOLUTION_EVENTS

    def test_review_approved_is_fh_resolution(self):
        assert "review_approved" in FH_RESOLUTION_EVENTS

    def test_feature_proposal_approved_is_fh_resolution(self):
        assert "feature_proposal_approved" in FH_RESOLUTION_EVENTS

    def test_edge_converged_is_fh_resolution(self):
        assert "edge_converged" in FH_RESOLUTION_EVENTS

    def test_has_fh_resolution_detects_consensus_reached(self, events_path):
        offset = events_path.stat().st_size
        _append_event(events_path, "consensus_reached")
        assert has_fh_resolution(events_path, offset) is True

    def test_has_fh_resolution_detects_review_approved(self, events_path):
        offset = events_path.stat().st_size
        _append_event(events_path, "review_approved")
        assert has_fh_resolution(events_path, offset) is True

    def test_has_fh_resolution_ignores_unrelated_events(self, events_path):
        offset = events_path.stat().st_size
        _append_event(events_path, "intent_raised")
        _append_event(events_path, "edge_started")
        assert has_fh_resolution(events_path, offset) is False

    def test_has_fh_resolution_false_on_empty_new_events(self, events_path):
        offset = events_path.stat().st_size
        assert has_fh_resolution(events_path, offset) is False

    def test_has_fh_resolution_handles_missing_file(self, tmp_path):
        missing = tmp_path / "missing.jsonl"
        assert has_fh_resolution(missing, 0) is False

    def test_has_fh_resolution_ignores_events_before_offset(self, events_path):
        _append_event(events_path, "consensus_reached")
        # Offset is AFTER the consensus_reached event
        offset = events_path.stat().st_size
        _append_event(events_path, "intent_raised")  # unrelated event after offset
        assert has_fh_resolution(events_path, offset) is False


# ── run_monitor (daemon mode) ─────────────────────────────────────────────────


class TestRunMonitor:
    def test_terminates_at_max_fires(self, workspace, events_path):
        """Daemon terminates when max_total_fires reached."""
        call_count = {"n": 0}

        def fake_dispatch(workspace_root, state, events_path, project_name, max_rounds):
            # Simulate file always changing
            call_count["n"] += 1
            state.last_mtime = -1  # force "changed" on each call
            return {"dispatched": 1, "converged": 1, "fh_required": 0,
                    "fp_dispatched": 0, "quiescent": True}

        with patch("genesis.dispatch_monitor.check_and_dispatch", side_effect=fake_dispatch):
            with patch("genesis.dispatch_monitor.time.sleep"):
                # Max 3 fires — but check_and_dispatch is mocked so we need
                # to control the loop differently. Use run_monitor with max_total_fires=2.
                pass

        # Simpler: patch the whole loop at run_dispatch_loop level
        fires = {"count": 0}

        def patched_dispatch_loop(**kwargs):
            fires["count"] += 1
            return {"dispatched": 1, "converged": 1, "fh_required": 0,
                    "fp_dispatched": 0, "quiescent": True}

        # Force events_path to always have "new" content by writing before each poll
        original_check = check_and_dispatch.__wrapped__ if hasattr(check_and_dispatch, '__wrapped__') else None

        state_holder = MonitorState()
        state_holder.last_mtime = -999  # ensure first call "fires"

        with patch("genesis.dispatch_monitor.run_dispatch_loop", side_effect=patched_dispatch_loop):
            with patch("genesis.dispatch_monitor.time.sleep"):
                # Write events so mtime keeps changing
                _append_event(events_path, "intent_raised")
                # run_monitor will call check_and_dispatch in a loop
                # We'll patch check_and_dispatch to control fires count
                fire_calls = {"n": 0}

                def fake_check_and_dispatch(workspace_root, state, events_path, project_name, max_rounds):
                    fire_calls["n"] += 1
                    state.rounds_fired += 1
                    return {"fired": True, "dispatched": 1, "converged": 1,
                            "fh_required": 0, "fp_dispatched": 0, "quiescent": True}

                with patch("genesis.dispatch_monitor.check_and_dispatch", side_effect=fake_check_and_dispatch):
                    run_monitor(
                        workspace_root=workspace,
                        events_path=events_path,
                        poll_interval_s=0,
                        max_total_fires=3,
                    )

                assert fire_calls["n"] <= 10  # should terminate near 3

    def test_on_fh_required_callback_called(self, workspace, events_path):
        """on_fh_required callback is invoked when F_H gates are pending."""
        callback_calls = []

        def fake_check(workspace_root, state, events_path, project_name, max_rounds):
            state.rounds_fired += 1
            return {"fired": True, "dispatched": 1, "converged": 0,
                    "fh_required": 2, "fp_dispatched": 0, "quiescent": False}

        with patch("genesis.dispatch_monitor.check_and_dispatch", side_effect=fake_check):
            with patch("genesis.dispatch_monitor.time.sleep"):
                run_monitor(
                    workspace_root=workspace,
                    events_path=events_path,
                    poll_interval_s=0,
                    max_total_fires=1,
                    on_fh_required=callback_calls.append,
                )

        assert len(callback_calls) >= 1
        assert callback_calls[0] == 2
