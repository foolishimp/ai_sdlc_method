# Validates: REQ-F-ELIN-001, REQ-F-ELIN-002, REQ-F-ELIN-003, REQ-F-ELIN-004, REQ-F-ELIN-005
"""Tests for EventIndex and EdgeRun — ADR-004 scalable index.

Covers:
  - build_edge_runs(): grouping OL and flat events into EdgeRun objects
  - EventIndex: build, all query methods, incremental append, summary stats
  - _parse_flat(): flat-format event parsing
  - New routes: /timeline, /feature/{id}, /artifact, /run-detail fragment
"""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest
from event_factory import make_ol2_event
from fastapi import FastAPI
from fastapi.testclient import TestClient

from genesis_monitor.index import EventIndex
from genesis_monitor.models.events import Event
from genesis_monitor.parsers.events import _parse_flat, parse_events
from genesis_monitor.projections.edge_runs import EdgeRun, build_edge_runs
from genesis_monitor.registry import ProjectRegistry
from genesis_monitor.server.app import create_app
from genesis_monitor.server.broadcaster import SSEBroadcaster


# ── Helpers ─────────────────────────────────────────────────────────────────

def _ts(iso: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _event(event_type: str, timestamp: str, project: str = "proj",
           feature: str = "REQ-F-001", edge: str = "code↔unit_tests",
           **data) -> Event:
    """Create a minimal Event object for testing."""
    return Event(
        timestamp=_ts(timestamp),
        event_type=event_type,
        project=project,
        data={"feature": feature, "edge": edge, **data},
    )


def _iter_event(timestamp: str, iteration: int, delta: int | None,
                status: str = "iterating", evaluators_passed: int = 5,
                evaluators_failed: int = 0, evaluators_skipped: int = 2,
                feature: str = "REQ-F-001", edge: str = "code↔unit_tests") -> Event:
    """Create an iteration_completed Event."""
    return Event(
        timestamp=_ts(timestamp),
        event_type="iteration_completed",
        project="proj",
        data={
            "feature": feature,
            "edge": edge,
            "iteration": iteration,
            "delta": delta,
            "status": status,
            "evaluators": {
                "passed": evaluators_passed,
                "failed": evaluators_failed,
                "skipped": evaluators_skipped,
                "total": evaluators_passed + evaluators_failed + evaluators_skipped,
            },
        },
    )


# ── build_edge_runs ──────────────────────────────────────────────────────────

class TestBuildEdgeRuns:
    """Tests for the event → EdgeRun grouping algorithm."""

    def test_single_converged_run(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z"),
            _event("edge_converged", "2026-03-01T10:05:00Z"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "converged"
        assert runs[0].feature == "REQ-F-001"
        assert runs[0].edge == "code↔unit_tests"

    def test_run_with_iterations(self):
        events = [
            _event("edge_started", "2026-03-01T10:00:00Z"),
            _iter_event("2026-03-01T10:01:00Z", iteration=1, delta=3),
            _iter_event("2026-03-01T10:02:00Z", iteration=2, delta=1),
            _iter_event("2026-03-01T10:03:00Z", iteration=3, delta=0, status="converged"),
            _event("edge_converged", "2026-03-01T10:03:00Z"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        run = runs[0]
        assert run.iteration_count == 3
        assert run.final_delta == 0
        assert run.status == "converged"

    def test_open_run_is_in_progress(self):
        events = [
            _event("edge_started", "2026-03-01T10:00:00Z"),
            _iter_event("2026-03-01T10:01:00Z", iteration=1, delta=2),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "in_progress"
        assert runs[0].ended_at is None

    def test_two_sequential_runs_same_edge(self):
        """Two edge_started events for the same (feature, edge) → two separate runs."""
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z"),
            _event("edge_converged", "2026-03-01T10:05:00Z"),
            _event("edge_started",   "2026-03-01T11:00:00Z"),
            _event("edge_converged", "2026-03-01T11:10:00Z"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 2
        assert all(r.status == "converged" for r in runs)
        assert runs[0].started_at < runs[1].started_at

    def test_two_features_independent(self):
        """Runs for different features are grouped separately."""
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001"),
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-002"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-002"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 2
        features = {r.feature for r in runs}
        assert features == {"REQ-F-001", "REQ-F-002"}

    def test_iteration_without_edge_started_synthesises_run(self):
        """iteration_completed without a preceding edge_started creates a synthetic run."""
        events = [
            _iter_event("2026-03-01T10:01:00Z", iteration=1, delta=2),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "in_progress"
        assert runs[0].iteration_count == 1

    def test_failed_run(self):
        events = [
            _event("edge_started",  "2026-03-01T10:00:00Z"),
            _event("command_error", "2026-03-01T10:02:00Z"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "failed"

    def test_aborted_run(self):
        events = [
            _event("edge_started",       "2026-03-01T10:00:00Z"),
            _event("transaction_aborted","2026-03-01T10:02:00Z"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "aborted"

    def test_empty_events(self):
        assert build_edge_runs([]) == []

    def test_events_without_feature_or_edge_skipped(self):
        events = [Event(timestamp=_ts("2026-03-01T10:00:00Z"), event_type="edge_started",
                        project="proj", data={})]
        runs = build_edge_runs(events)
        assert len(runs) == 0

    def test_duration_computed(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z"),
            _event("edge_converged", "2026-03-01T10:05:00Z"),
        ]
        runs = build_edge_runs(events)
        assert runs[0].duration_seconds == pytest.approx(300.0)

    def test_duration_none_for_open_run(self):
        events = [_event("edge_started", "2026-03-01T10:00:00Z")]
        runs = build_edge_runs(events)
        assert runs[0].duration_seconds is None

    def test_convergence_type_propagated(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z"),
            _event("edge_converged", "2026-03-01T10:05:00Z",
                   **{"data": {"convergence_type": "time_box_expired"}}),
        ]
        runs = build_edge_runs(events)
        assert runs[0].convergence_type == "time_box_expired"

    def test_events_sorted_chronologically(self):
        """Runs are output in chronological order regardless of input order."""
        events = [
            _event("edge_started",   "2026-03-01T12:00:00Z", feature="REQ-F-002"),
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T12:05:00Z", feature="REQ-F-002"),
        ]
        runs = build_edge_runs(events)
        assert runs[0].feature == "REQ-F-001"
        assert runs[1].feature == "REQ-F-002"

    def test_auto_close_on_converged_status_in_iteration(self):
        """iteration_completed with status='converged' closes the run automatically."""
        events = [
            _event("edge_started", "2026-03-01T10:00:00Z"),
            _iter_event("2026-03-01T10:02:00Z", iteration=1, delta=0, status="converged"),
        ]
        runs = build_edge_runs(events)
        assert len(runs) == 1
        assert runs[0].status == "converged"


# ── EventIndex ───────────────────────────────────────────────────────────────

class TestEventIndexBuild:
    """Tests for EventIndex.build() and secondary index construction."""

    def _make_events(self) -> list[Event]:
        return [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001", edge="req→design"),
            _iter_event("2026-03-01T10:01:00Z", 1, 2, feature="REQ-F-001", edge="req→design"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_started",   "2026-03-01T11:00:00Z", feature="REQ-F-001", edge="code↔unit_tests"),
            _iter_event("2026-03-01T11:01:00Z", 1, 3, feature="REQ-F-001", edge="code↔unit_tests"),
            _event("edge_started",   "2026-03-01T12:00:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
            _event("edge_converged", "2026-03-01T12:30:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
        ]

    def test_total_runs(self):
        idx = EventIndex.build(self._make_events())
        assert idx.total_runs == 3

    def test_event_count(self):
        events = self._make_events()
        idx = EventIndex.build(events)
        assert idx.event_count == len(events)

    def test_converged_count(self):
        idx = EventIndex.build(self._make_events())
        assert idx.converged_count == 2

    def test_in_progress_count(self):
        idx = EventIndex.build(self._make_events())
        assert idx.in_progress_count == 1

    def test_failed_count_zero(self):
        idx = EventIndex.build(self._make_events())
        assert idx.failed_count == 0

    def test_features_list(self):
        idx = EventIndex.build(self._make_events())
        assert idx.features == ["REQ-F-001", "REQ-F-002"]

    def test_edges_list(self):
        idx = EventIndex.build(self._make_events())
        assert "code↔unit_tests" in idx.edges
        assert "req→design" in idx.edges

    def test_empty_events(self):
        idx = EventIndex.build([])
        assert idx.total_runs == 0
        assert idx.event_count == 0


class TestEventIndexTimeline:
    """Tests for EventIndex.timeline() and timeline_fuzzy()."""

    @pytest.fixture
    def idx(self) -> EventIndex:
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_started",   "2026-03-01T11:00:00Z", feature="REQ-F-001", edge="code↔unit_tests"),
            _event("edge_started",   "2026-03-01T12:00:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
            _event("edge_converged", "2026-03-01T12:30:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
        ]
        return EventIndex.build(events)

    def test_no_filter_returns_all(self, idx):
        assert len(idx.timeline()) == 3

    def test_filter_by_feature(self, idx):
        runs = idx.timeline(feature="REQ-F-001")
        assert len(runs) == 2
        assert all(r.feature == "REQ-F-001" for r in runs)

    def test_filter_by_edge(self, idx):
        runs = idx.timeline(edge="code↔unit_tests")
        assert len(runs) == 2

    def test_filter_by_status_converged(self, idx):
        runs = idx.timeline(status="converged")
        assert len(runs) == 2
        assert all(r.status == "converged" for r in runs)

    def test_filter_by_status_in_progress(self, idx):
        runs = idx.timeline(status="in_progress")
        assert len(runs) == 1

    def test_filter_feature_and_edge(self, idx):
        runs = idx.timeline(feature="REQ-F-001", edge="req→design")
        assert len(runs) == 1
        assert runs[0].edge == "req→design"

    def test_result_is_sorted_chronologically(self, idx):
        runs = idx.timeline()
        for i in range(len(runs) - 1):
            assert runs[i].started_at <= runs[i + 1].started_at

    def test_since_filter(self, idx):
        since = _ts("2026-03-01T11:30:00Z")
        runs = idx.timeline(since=since)
        assert all(r.started_at >= since for r in runs)

    def test_until_filter(self, idx):
        until = _ts("2026-03-01T10:30:00Z")
        runs = idx.timeline(until=until)
        assert all(r.started_at <= until for r in runs)

    def test_fuzzy_feature_substring(self, idx):
        runs = idx.timeline_fuzzy(feature="REQ-F")
        assert len(runs) == 3  # all features match

    def test_fuzzy_edge_substring(self, idx):
        runs = idx.timeline_fuzzy(edge="code")
        assert len(runs) == 2


class TestEventIndexFeatureRuns:
    def test_feature_runs_returns_ordered(self):
        events = [
            _event("edge_started",   "2026-03-01T11:00:00Z", feature="REQ-F-001", edge="code↔unit_tests"),
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_converged", "2026-03-01T11:30:00Z", feature="REQ-F-001", edge="code↔unit_tests"),
        ]
        idx = EventIndex.build(events)
        runs = idx.feature_runs("REQ-F-001")
        assert len(runs) == 2
        assert runs[0].edge == "req→design"
        assert runs[1].edge == "code↔unit_tests"

    def test_feature_runs_unknown_feature_returns_empty(self):
        idx = EventIndex.build([])
        assert idx.feature_runs("REQ-F-NONEXISTENT") == []


class TestEventIndexRunDetail:
    def test_run_detail_o1_lookup(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z"),
            _event("edge_converged", "2026-03-01T10:05:00Z"),
        ]
        idx = EventIndex.build(events)
        run = idx.timeline()[0]
        found = idx.run_detail(run.run_id)
        assert found is not None
        assert found.run_id == run.run_id

    def test_run_detail_unknown_id_returns_none(self):
        idx = EventIndex.build([])
        assert idx.run_detail("nonexistent-run-id") is None


class TestEventIndexDays:
    def test_groups_by_calendar_day(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001"),
            _event("edge_started",   "2026-03-02T10:00:00Z", feature="REQ-F-002"),
            _event("edge_converged", "2026-03-02T10:05:00Z", feature="REQ-F-002"),
        ]
        idx = EventIndex.build(events)
        days = idx.days()
        assert len(days) == 2
        dates = [d for d, _ in days]
        assert "2026-03-01" in dates
        assert "2026-03-02" in dates

    def test_days_sorted_ascending(self):
        events = [
            _event("edge_started",   "2026-03-02T10:00:00Z", feature="REQ-F-002"),
            _event("edge_converged", "2026-03-02T10:05:00Z", feature="REQ-F-002"),
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001"),
        ]
        idx = EventIndex.build(events)
        days = idx.days()
        assert days[0][0] < days[1][0]

    def test_days_with_runs_subset(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001", edge="req→design"),
            _event("edge_started",   "2026-03-01T11:00:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
            _event("edge_converged", "2026-03-01T11:05:00Z", feature="REQ-F-002", edge="code↔unit_tests"),
        ]
        idx = EventIndex.build(events)
        subset = idx.timeline(feature="REQ-F-001")
        days = idx.days(subset)
        assert len(days) == 1
        assert len(days[0][1]) == 1


class TestEventIndexAppend:
    def test_append_adds_new_run(self):
        events = [
            _event("edge_started",   "2026-03-01T10:00:00Z", feature="REQ-F-001"),
            _event("edge_converged", "2026-03-01T10:05:00Z", feature="REQ-F-001"),
        ]
        idx = EventIndex.build(events)
        assert idx.total_runs == 1

        new_events = [
            _event("edge_started",   "2026-03-01T11:00:00Z", feature="REQ-F-002"),
            _event("edge_converged", "2026-03-01T11:05:00Z", feature="REQ-F-002"),
        ]
        idx.append(new_events)
        assert idx.total_runs == 2
        assert "REQ-F-002" in idx.features

    def test_append_closes_open_run(self):
        """Appending edge_converged closes a previously open run."""
        events = [
            _event("edge_started", "2026-03-01T10:00:00Z"),
        ]
        idx = EventIndex.build(events)
        assert idx.in_progress_count == 1

        new_events = [_event("edge_converged", "2026-03-01T10:05:00Z")]
        idx.append(new_events)
        assert idx.converged_count == 1
        assert idx.in_progress_count == 0

    def test_append_updates_event_count(self):
        events = [_event("edge_started", "2026-03-01T10:00:00Z")]
        idx = EventIndex.build(events)
        assert idx.event_count == 1

        idx.append([_event("edge_converged", "2026-03-01T10:05:00Z")])
        assert idx.event_count == 2


# ── _parse_flat ──────────────────────────────────────────────────────────────

class TestParseFlatEvents:
    """Tests for _parse_flat() — flat-format event parsing."""

    def _flat(self, event_type: str, timestamp: str = "2026-03-01T10:00:00Z",
              project: str = "imp_gemini", **extra) -> dict:
        return {"event_type": event_type, "timestamp": timestamp, "project": project, **extra}

    def test_basic_event_type(self):
        ev = _parse_flat(self._flat("intent_raised"))
        assert ev.event_type == "intent_raised"
        assert ev.project == "imp_gemini"

    def test_timestamp_parsed(self):
        ev = _parse_flat(self._flat("intent_raised", timestamp="2026-03-08T14:30:00Z"))
        assert ev.timestamp.year == 2026
        assert ev.timestamp.month == 3
        assert ev.timestamp.day == 8

    def test_unknown_event_type_returns_base_event(self):
        ev = _parse_flat(self._flat("some_future_event_type"))
        assert isinstance(ev, Event)
        assert ev.event_type == "some_future_event_type"

    def test_iteration_completed_flat_fields(self):
        ev = _parse_flat(self._flat(
            "iteration_completed",
            feature="REQ-F-001",
            edge="code↔unit_tests",
            delta=2,
            iteration=3,
        ))
        assert ev.event_type == "iteration_completed"
        # feature and edge stored in data dict
        assert ev.data.get("feature") == "REQ-F-001"
        assert ev.data.get("delta") == 2

    def test_data_preserved(self):
        ev = _parse_flat(self._flat("intent_raised", intent_id="INT-001", severity="high"))
        assert ev.data.get("intent_id") == "INT-001"
        assert ev.data.get("severity") == "high"


class TestParseFlatIntegration:
    """Integration test: events.jsonl with mixed OL + flat events."""

    def test_both_formats_parsed(self, tmp_path):
        ws = tmp_path / "project" / ".ai-workspace" / "events"
        ws.mkdir(parents=True)
        events = [
            # OL format
            make_ol2_event("edge_started", timestamp="2026-03-01T10:00:00Z",
                           project="test", feature="REQ-F-001", edge="code↔unit_tests"),
            # flat format
            {"event_type": "intent_raised", "timestamp": "2026-03-01T10:01:00Z",
             "project": "test", "intent_id": "INT-001"},
            # OL format converge
            make_ol2_event("edge_converged", timestamp="2026-03-01T10:05:00Z",
                           project="test", feature="REQ-F-001", edge="code↔unit_tests"),
        ]
        (ws / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
        parsed = parse_events(ws.parent)
        # OL events + flat event
        assert len(parsed) == 3
        types = {e.event_type for e in parsed}
        assert "edge_started" in types
        assert "intent_raised" in types
        assert "edge_converged" in types

    def test_ol_camelcase_normalised(self, tmp_path):
        """CamelCase sdlc:event_type values are normalised to snake_case."""
        ws = tmp_path / "project" / ".ai-workspace" / "events"
        ws.mkdir(parents=True)
        # engine now emits CamelCase: "IterationCompleted", "EdgeStarted", etc.
        import uuid as _uuid
        ev = {
            "eventType": "OTHER",
            "eventTime": "2026-03-01T10:01:00Z",
            "run": {
                "runId": str(_uuid.uuid4()),
                "facets": {
                    "sdlc:event_type": {"type": "IterationCompleted", "_producer": "x", "_schemaURL": "x"},
                }
            },
            "job": {"namespace": "aisdlc://test", "name": "code↔unit_tests"},
            "_metadata": {"project": "test"},
        }
        (ws / "events.jsonl").write_text(json.dumps(ev))
        parsed = parse_events(ws.parent)
        assert len(parsed) == 1
        assert parsed[0].event_type == "iteration_completed"


# ── Routes ───────────────────────────────────────────────────────────────────

@pytest.fixture
def client_with_events(tmp_workspace: Path) -> TestClient:
    """TestClient with a project that has OL events to build the index from."""
    ws = tmp_workspace / ".ai-workspace" / "events"
    ws.mkdir(parents=True, exist_ok=True)
    # Write enough events for the timeline and feature lineage to render
    events = [
        make_ol2_event("edge_started",   "2026-03-01T10:00:00Z",
                       feature="REQ-F-001", edge="code↔unit_tests"),
        make_ol2_event("edge_converged", "2026-03-01T10:05:00Z",
                       feature="REQ-F-001", edge="code↔unit_tests"),
        make_ol2_event("edge_started",   "2026-03-01T11:00:00Z",
                       feature="REQ-F-002", edge="req→design"),
    ]
    (ws / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))

    reg = ProjectRegistry()
    reg.add_project(tmp_workspace)

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    bc = SSEBroadcaster()
    app = create_app(
        watch_dirs=[tmp_workspace.parent],
        _registry=reg,
        _broadcaster=bc,
        _lifespan=noop_lifespan,
    )
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


class TestTimelineRoute:
    """Tests for GET /project/{id}/timeline."""

    def test_returns_200_html(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_contains_run_rows(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline")
        # runs are rendered as .run-row divs
        assert "run-row" in resp.text

    def test_contains_stats(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline")
        assert "Converged" in resp.text
        assert "In Progress" in resp.text

    def test_feature_filter_param(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline?feature=REQ-F-001")
        assert resp.status_code == 200
        assert "REQ-F-001" in resp.text

    def test_status_filter_param(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline?status=converged")
        assert resp.status_code == 200

    def test_filter_bar_rendered(self, client_with_events):
        resp = client_with_events.get("/project/test-project/timeline")
        assert "filter-bar" in resp.text

    def test_unknown_project_returns_404(self, client_with_events):
        resp = client_with_events.get("/project/no-such-project/timeline")
        assert resp.status_code == 404


class TestTimelineRunsFragment:
    def test_returns_html(self, client_with_events):
        resp = client_with_events.get("/fragments/project/test-project/timeline-runs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


class TestRunDetailFragment:
    def test_known_run_id_is_linked_in_timeline(self, client_with_events):
        # run_id is embedded in hx-get=/fragments/.../run-detail/{run_id} in timeline HTML
        resp = client_with_events.get("/project/test-project/timeline")
        assert resp.status_code == 200
        assert "run-detail" in resp.text

    def test_unknown_run_id_returns_not_found_msg(self, client_with_events):
        resp = client_with_events.get(
            "/fragments/project/test-project/run-detail/no-such-run-id"
        )
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


class TestFeatureLineageRoute:
    def test_returns_200(self, client_with_events):
        resp = client_with_events.get("/project/test-project/feature/REQ-F-001")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_feature_id_in_page(self, client_with_events):
        resp = client_with_events.get("/project/test-project/feature/REQ-F-001")
        assert "REQ-F-001" in resp.text

    def test_edge_history_section_present(self, client_with_events):
        resp = client_with_events.get("/project/test-project/feature/REQ-F-001")
        assert "Edge Traversal History" in resp.text

    def test_unknown_feature_shows_no_events_msg(self, client_with_events):
        resp = client_with_events.get("/project/test-project/feature/REQ-F-NONEXISTENT")
        assert resp.status_code == 200
        assert "No edge traversal" in resp.text

    def test_unknown_project_returns_404(self, client_with_events):
        resp = client_with_events.get("/project/no-such-project/feature/REQ-F-001")
        assert resp.status_code == 404


class TestArtifactRoute:
    def test_returns_200_for_existing_file(self, client_with_events, tmp_workspace: Path):
        # Write a real file in the project directory
        test_file = tmp_workspace / "test_artifact.py"
        test_file.write_text("# Implements: REQ-F-001\ndef hello(): pass\n")
        resp = client_with_events.get(
            f"/project/test-project/artifact?path={test_file}"
        )
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_shows_file_content(self, client_with_events, tmp_workspace: Path):
        test_file = tmp_workspace / "test_artifact.py"
        test_file.write_text("def hello(): pass\n")
        resp = client_with_events.get(
            f"/project/test-project/artifact?path={test_file}"
        )
        assert "hello" in resp.text

    def test_missing_file_shows_error(self, client_with_events):
        resp = client_with_events.get(
            "/project/test-project/artifact?path=/nonexistent/path/file.py"
        )
        assert resp.status_code == 200
        assert "not found" in resp.text.lower() or "error" in resp.text.lower()

    def test_no_path_param_returns_400(self, client_with_events):
        resp = client_with_events.get("/project/test-project/artifact")
        assert resp.status_code == 400


class TestProjectPageHasTimelineLink:
    def test_timeline_button_on_project_page(self, client_with_events):
        resp = client_with_events.get("/project/test-project")
        assert resp.status_code == 200
        assert "timeline" in resp.text.lower()
        assert "Edge Traversal Timeline" in resp.text
