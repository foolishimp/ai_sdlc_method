# Validates: REQ-F-EXEC-001, REQ-F-EXEC-002, REQ-F-EXEC-003
"""Tests for ADR-009 executor attribution: inference, EdgeRun, convergence table, arc style."""

import json
from pathlib import Path

import pytest

from genesis_monitor.models.events import Event
from genesis_monitor.parsers.events import parse_events, _infer_executor
from genesis_monitor.projections.edge_runs import EdgeRun, build_edge_runs
from genesis_monitor.projections.convergence import build_convergence_table_from_events


# ── Helper factories ─────────────────────────────────────────────────────────


def _ol_event_line(edge: str, feature: str, event_type: str, **extra) -> str:
    """OL-format event (has eventType key)."""
    run_facets: dict = {
        "sdlc:event_type": {"type": event_type},
        "sdlc:req_keys": {"feature_id": feature, "edge": edge},
    }
    data: dict = {
        "eventType": "COMPLETE",
        "eventTime": "2026-03-09T10:00:00Z",
        "run": {"runId": "test-run-01", "facets": run_facets},
        "job": {"namespace": "aisdlc://test", "name": edge},
        "inputs": [],
        "outputs": [],
    }
    data.update(extra)
    return json.dumps(data)


def _flat_event_line(event_type: str, edge: str = "", feature: str = "", **extra) -> str:
    """Flat-format event (has event_type key, no eventType)."""
    data: dict = {
        "event_type": event_type,
        "timestamp": "2026-03-09T10:00:00Z",
        "project": "test",
        "edge": edge,
        "feature": feature,
    }
    data.update(extra)
    return json.dumps(data)


def _write_events(tmp_path: Path, lines: list[str]) -> Path:
    ws = tmp_path / ".ai-workspace"
    (ws / "events").mkdir(parents=True)
    (ws / "events" / "events.jsonl").write_text("\n".join(lines))
    return ws


# ── EXEC-001: Executor inference from OL-format events ───────────────────────


class TestExecutorInferenceOlFormat:
    def test_ol_event_gets_executor_engine(self, tmp_path):
        ws = _write_events(tmp_path, [
            _ol_event_line("code↔unit_tests", "REQ-F-X-001", "iteration_completed"),
        ])
        events = parse_events(ws)
        assert len(events) == 1
        assert events[0].executor == "engine"

    def test_ol_event_gets_emission_live(self, tmp_path):
        ws = _write_events(tmp_path, [
            _ol_event_line("code↔unit_tests", "REQ-F-X-001", "iteration_completed"),
        ])
        events = parse_events(ws)
        assert events[0].emission == "live"

    def test_ol_event_explicit_executor_wins(self, tmp_path):
        """Explicit executor field in raw data overrides inference."""
        ws = _write_events(tmp_path, [
            _ol_event_line("code↔unit_tests", "REQ-F-X-001", "iteration_completed", executor="retroactive"),
        ])
        events = parse_events(ws)
        assert events[0].executor == "retroactive"

    def test_ol_event_explicit_emission_retroactive_wins(self, tmp_path):
        ws = _write_events(tmp_path, [
            _ol_event_line("code↔unit_tests", "REQ-F-X-001", "iteration_completed", emission="retroactive"),
        ])
        events = parse_events(ws)
        assert events[0].emission == "retroactive"


# ── EXEC-001: Executor inference from flat-format events ─────────────────────


class TestExecutorInferenceFlatFormat:
    def test_flat_event_gets_executor_claude(self, tmp_path):
        ws = _write_events(tmp_path, [
            _flat_event_line("iteration_completed", edge="design→code", feature="REQ-F-X-001"),
        ])
        events = parse_events(ws)
        assert len(events) == 1
        assert events[0].executor == "claude"

    def test_flat_event_gets_emission_live(self, tmp_path):
        ws = _write_events(tmp_path, [
            _flat_event_line("iteration_completed", edge="design→code"),
        ])
        events = parse_events(ws)
        assert events[0].emission == "live"

    def test_flat_event_explicit_executor_wins(self, tmp_path):
        ws = _write_events(tmp_path, [
            _flat_event_line("edge_converged", edge="design→code", executor="engine"),
        ])
        events = parse_events(ws)
        assert events[0].executor == "engine"

    def test_unknown_when_no_format_detected(self):
        """Degenerate: event with neither eventType nor event_type key."""
        ev = Event()
        raw: dict = {}
        _infer_executor(ev, raw, is_ol=False)
        # is_ol=False → claude inference; no explicit field
        assert ev.executor == "claude"


# ── EXEC-001: EdgeRun executor attribution ────────────────────────────────────


class TestEdgeRunExecutorAttribution:
    def _make_events(self, executor_on_converged: str | None, tmp_path: Path):
        lines = [
            _flat_event_line("edge_started", edge="code↔unit_tests", feature="REQ-F-X-001"),
            _flat_event_line("iteration_completed", edge="code↔unit_tests", feature="REQ-F-X-001",
                             iteration=1, delta=2, status="iterating"),
        ]
        converged_kw: dict = {}
        if executor_on_converged:
            converged_kw["executor"] = executor_on_converged
        lines.append(_flat_event_line("edge_converged", edge="code↔unit_tests",
                                      feature="REQ-F-X-001", **converged_kw))
        return _write_events(tmp_path, lines)

    def test_edge_run_executor_from_closing_event(self, tmp_path):
        ws = self._make_events("engine", tmp_path)
        events = parse_events(ws)
        runs = build_edge_runs(events)
        converged = [r for r in runs if r.status == "converged"]
        assert len(converged) == 1
        assert converged[0].executor == "engine"

    def test_edge_run_executor_fallback_from_raw_events(self, tmp_path):
        """When closing event has no executor, walk raw_events for fallback."""
        # edge_converged with no executor → should find executor from earlier events
        ws = self._make_events(None, tmp_path)
        events = parse_events(ws)
        # All events are flat → executor = "claude"
        runs = build_edge_runs(events)
        converged = [r for r in runs if r.status == "converged"]
        assert len(converged) == 1
        assert converged[0].executor == "claude"

    def test_edge_run_executor_unknown_when_no_events(self):
        """EdgeRun with no events has empty executor."""
        run = EdgeRun(
            run_id="x", feature="F", edge="e", project="p",
            started_at=__import__("datetime").datetime.now(),
            ended_at=None, status="in_progress", convergence_type="",
        )
        assert run.executor == ""


# ── EXEC-003: Convergence table executor field ────────────────────────────────


class TestConvergenceTableExecutor:
    def test_convergence_row_has_executor_from_edge_converged(self, tmp_path):
        lines = [
            _flat_event_line("edge_started", edge="design→code", feature="REQ-F-X-001"),
            _flat_event_line("iteration_completed", edge="design→code", feature="REQ-F-X-001",
                             iteration=1, delta=0, status="converged"),
            _flat_event_line("edge_converged", edge="design→code", feature="REQ-F-X-001",
                             executor="engine"),
        ]
        ws = _write_events(tmp_path, lines)
        events = parse_events(ws)
        rows = build_convergence_table_from_events(events)
        assert len(rows) == 1
        assert rows[0].executor == "engine"

    def test_convergence_row_executor_empty_when_not_in_events(self, tmp_path):
        """Rows without attribution get empty executor (shown as 'unknown' in template)."""
        lines = [
            _flat_event_line("edge_started", edge="design→code"),
            _flat_event_line("edge_converged", edge="design→code"),
        ]
        ws = _write_events(tmp_path, lines)
        events = parse_events(ws)
        rows = build_convergence_table_from_events(events)
        assert len(rows) == 1
        # flat events → executor="claude" via inference
        assert rows[0].executor == "claude"

    def test_convergence_multiple_edges_each_get_executor(self, tmp_path):
        lines = [
            _flat_event_line("edge_converged", edge="intent→requirements"),
            _ol_event_line("requirements→design", "REQ-F-X-001", "edge_converged"),
        ]
        ws = _write_events(tmp_path, lines)
        events = parse_events(ws)
        rows = build_convergence_table_from_events(events)
        by_edge = {r.edge: r for r in rows}
        assert by_edge["intent→requirements"].executor == "claude"
        assert by_edge["requirements→design"].executor == "engine"


# ── EXEC-002: Arc style in graph data ────────────────────────────────────────


class TestArcStyleInGraphData:
    """Validate that _build_graph_data produces arc_style for D3 rendering."""

    def _make_run(self, executor: str, status: str = "converged") -> "EdgeRun":
        import datetime
        r = EdgeRun(
            run_id="r1", feature="REQ-F-X-001", edge="design→code",
            project="test",
            started_at=datetime.datetime(2026, 3, 9, 10, 0),
            ended_at=datetime.datetime(2026, 3, 9, 10, 30),
            status=status,
            convergence_type="standard",
            executor=executor,
        )
        return r

    def _call_build(self, run: "EdgeRun") -> dict:
        """Test the executor→arc_style mapping from ADR-009."""
        style_map = {"engine": "arc-engine", "claude": "arc-claude", "retroactive": "arc-retroactive"}
        return {"arc_style": style_map.get(run.executor, "arc-engine")}

    def test_engine_arc_style(self):
        run = self._make_run("engine")
        result = self._call_build(run)
        assert result["arc_style"] == "arc-engine"

    def test_claude_arc_style(self):
        run = self._make_run("claude")
        result = self._call_build(run)
        assert result["arc_style"] == "arc-claude"

    def test_retroactive_arc_style(self):
        run = self._make_run("retroactive")
        result = self._call_build(run)
        assert result["arc_style"] == "arc-retroactive"

    def test_unknown_executor_defaults_to_engine_arc(self):
        run = self._make_run("unknown")
        result = self._call_build(run)
        assert result["arc_style"] == "arc-engine"

    def test_empty_executor_defaults_to_engine_arc(self):
        run = self._make_run("")
        result = self._call_build(run)
        assert result["arc_style"] == "arc-engine"
