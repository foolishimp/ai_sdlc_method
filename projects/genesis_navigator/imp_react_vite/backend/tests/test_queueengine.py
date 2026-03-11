"""Tests for REQ-F-QUEUEENGINE-001: Decision Queue Engine.

Covers STUCK detection, BLOCKED detection, gap cluster aggregation,
empty queue (healthy) path, ranking order, and the
GET /api/projects/{project_id}/queue endpoint.
"""

# Validates: REQ-F-QUEUE-001
# Validates: REQ-F-QUEUE-002
# Validates: REQ-F-QUEUE-003
# Validates: REQ-F-API-004

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

import genesis_nav.main as _main
from genesis_nav.analyzers.queue_builder import (
    build_item_detail,
    build_queue_items,
    command_for_item,
)
from genesis_nav.main import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMPTY_GAPS: dict = {"layer_1": {"gaps": []}, "layer_2": {"gaps": []}}


def _iter_ev(feature_id: str, delta: int, edge: str = "design→code") -> dict:
    return {
        "event_type": "iteration_completed",
        "feature_id": feature_id,
        "edge": edge,
        "delta": delta,
    }


def _edge_started(feature_id: str, edge: str = "design→code") -> dict:
    return {"event_type": "edge_started", "feature_id": feature_id, "edge": edge}


def _edge_converged(feature_id: str, edge: str = "design→code") -> dict:
    return {"event_type": "edge_converged", "feature_id": feature_id, "edge": edge}


def _feature(fid: str, status: str = "in_progress") -> dict:
    return {"feature_id": fid, "status": status}


# ---------------------------------------------------------------------------
# TestQueueBuilder — unit tests for queue_builder functions
# ---------------------------------------------------------------------------


class TestQueueBuilder:
    """Tests for genesis_nav.analyzers.queue_builder."""

    # ---- command_for_item ----

    def test_command_stuck(self) -> None:
        cmd = command_for_item("STUCK", "REQ-F-AUTH-001", "design→code", [])
        assert "/gen-iterate" in cmd
        assert "REQ-F-AUTH-001" in cmd
        assert "design→code" in cmd

    def test_command_blocked(self) -> None:
        cmd = command_for_item("BLOCKED", "REQ-F-AUTH-001", "code→tests", [])
        assert "/gen-iterate" in cmd

    def test_command_gap_cluster(self) -> None:
        cmd = command_for_item("GAP_CLUSTER", None, None, ["REQ-F-AUTH-001"])
        assert cmd == "/gen-gaps"

    def test_command_in_progress(self) -> None:
        cmd = command_for_item("IN_PROGRESS", "REQ-F-DATA-001", "design→code", [])
        assert "/gen-iterate" in cmd
        assert "REQ-F-DATA-001" in cmd

    def test_command_feature_no_edge(self) -> None:
        """Falls back to --feature only when edge is None."""
        cmd = command_for_item("STUCK", "REQ-F-AUTH-001", None, [])
        assert "/gen-iterate" in cmd
        assert "REQ-F-AUTH-001" in cmd

    # ---- build_item_detail ----

    def test_stuck_detail_has_iteration_history(self) -> None:
        """STUCK detail carries the last 3 deltas in iteration_history."""
        events = [
            _iter_ev("F1", 5),
            _iter_ev("F1", 5),
            _iter_ev("F1", 5),
        ]
        detail = build_item_detail("STUCK", _feature("F1"), events, [])
        assert detail["iteration_history"] == [5, 5, 5]
        assert detail["delta"] == 5

    def test_gap_cluster_detail_has_gap_keys(self) -> None:
        """GAP_CLUSTER detail carries gap_keys list."""
        keys = ["REQ-F-AUTH-001", "REQ-F-AUTH-002"]
        detail = build_item_detail("GAP_CLUSTER", {}, [], keys)
        assert detail["gap_keys"] == keys
        assert detail["delta"] is None

    def test_blocked_detail_has_reason(self) -> None:
        """BLOCKED detail has a non-empty reason."""
        detail = build_item_detail("BLOCKED", _feature("F1", "blocked"), [], [])
        assert detail["reason"]

    def test_in_progress_detail_current_delta(self) -> None:
        """IN_PROGRESS detail delta reflects the latest iteration delta."""
        events = [_iter_ev("F1", 3), _iter_ev("F1", 2)]
        detail = build_item_detail("IN_PROGRESS", _feature("F1"), events, [])
        assert detail["delta"] == 2

    # ---- build_queue_items — STUCK detection ----

    def test_stuck_detected_when_last_three_same(self) -> None:
        """Feature with 3 identical deltas is classified STUCK."""
        features = [_feature("F1")]
        events = [_iter_ev("F1", 4), _iter_ev("F1", 4), _iter_ev("F1", 4)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        types = [i["type"] for i in items]
        assert "STUCK" in types

    def test_stuck_not_detected_fewer_than_three(self) -> None:
        """Fewer than 3 iterations → not STUCK."""
        features = [_feature("F1")]
        events = [_iter_ev("F1", 4), _iter_ev("F1", 4)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        assert all(i["type"] != "STUCK" for i in items)

    def test_stuck_not_detected_varying_deltas(self) -> None:
        """Varying deltas → not STUCK even with 3+ iterations."""
        features = [_feature("F1")]
        events = [_iter_ev("F1", 5), _iter_ev("F1", 3), _iter_ev("F1", 1)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        assert all(i["type"] != "STUCK" for i in items)

    def test_stuck_item_has_critical_severity(self) -> None:
        """STUCK items carry 'critical' severity."""
        features = [_feature("F1")]
        events = [_iter_ev("F1", 2), _iter_ev("F1", 2), _iter_ev("F1", 2)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        stuck = next(i for i in items if i["type"] == "STUCK")
        assert stuck["severity"] == "critical"

    def test_stuck_converged_feature_not_stuck(self) -> None:
        """A converged feature with 3 identical deltas is NOT stuck."""
        features = [_feature("F1", "converged")]
        events = [_iter_ev("F1", 0), _iter_ev("F1", 0), _iter_ev("F1", 0)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        assert all(i["type"] != "STUCK" for i in items)

    # ---- build_queue_items — BLOCKED detection ----

    def test_blocked_feature_creates_blocked_item(self) -> None:
        """Feature with status='blocked' creates a BLOCKED queue item."""
        features = [_feature("F2", "blocked")]
        items = build_queue_items(features, [], _EMPTY_GAPS)
        types = [i["type"] for i in items]
        assert "BLOCKED" in types

    def test_blocked_item_severity_is_high(self) -> None:
        """BLOCKED items carry 'high' severity."""
        features = [_feature("F2", "blocked")]
        items = build_queue_items(features, [], _EMPTY_GAPS)
        blocked = next(i for i in items if i["type"] == "BLOCKED")
        assert blocked["severity"] == "high"

    def test_blocked_item_includes_feature_id(self) -> None:
        """BLOCKED item references the correct feature_id."""
        features = [_feature("REQ-F-MYFEATURE-001", "blocked")]
        items = build_queue_items(features, [], _EMPTY_GAPS)
        blocked = next(i for i in items if i["type"] == "BLOCKED")
        assert blocked["feature_id"] == "REQ-F-MYFEATURE-001"

    # ---- build_queue_items — GAP_CLUSTER ----

    def test_gap_cluster_groups_by_prefix(self) -> None:
        """Multiple gaps sharing a prefix collapse into one cluster."""
        gaps = {
            "layer_1": {
                "gaps": [
                    {"req_key": "REQ-F-AUTH-001"},
                    {"req_key": "REQ-F-AUTH-002"},
                ]
            },
            "layer_2": {"gaps": []},
        }
        items = build_queue_items([], [], gaps)
        cluster_items = [i for i in items if i["type"] == "GAP_CLUSTER"]
        assert len(cluster_items) == 1
        assert cluster_items[0]["detail"]["gap_keys"] == [
            "REQ-F-AUTH-001",
            "REQ-F-AUTH-002",
        ]

    def test_gap_cluster_different_prefixes_separate(self) -> None:
        """Gaps with different prefixes produce separate cluster items."""
        gaps = {
            "layer_1": {
                "gaps": [
                    {"req_key": "REQ-F-AUTH-001"},
                    {"req_key": "REQ-F-DATA-001"},
                ]
            },
            "layer_2": {"gaps": []},
        }
        items = build_queue_items([], [], gaps)
        cluster_items = [i for i in items if i["type"] == "GAP_CLUSTER"]
        assert len(cluster_items) == 2

    def test_gap_cluster_severity_is_medium(self) -> None:
        """GAP_CLUSTER items carry 'medium' severity."""
        gaps = {
            "layer_1": {"gaps": [{"req_key": "REQ-F-AUTH-001"}]},
            "layer_2": {"gaps": []},
        }
        items = build_queue_items([], [], gaps)
        cluster = next(i for i in items if i["type"] == "GAP_CLUSTER")
        assert cluster["severity"] == "medium"

    def test_gap_cluster_command_is_gen_gaps(self) -> None:
        """GAP_CLUSTER items always suggest /gen-gaps."""
        gaps = {
            "layer_1": {"gaps": [{"req_key": "REQ-F-AUTH-001"}]},
            "layer_2": {"gaps": []},
        }
        items = build_queue_items([], [], gaps)
        cluster = next(i for i in items if i["type"] == "GAP_CLUSTER")
        assert cluster["command"] == "/gen-gaps"

    # ---- build_queue_items — IN_PROGRESS ----

    def test_in_progress_iterating_feature(self) -> None:
        """An iterating feature (not stuck/blocked) gets an IN_PROGRESS item."""
        features = [_feature("F1", "in_progress")]
        events = [_iter_ev("F1", 3), _iter_ev("F1", 2)]  # not stuck
        items = build_queue_items(features, events, _EMPTY_GAPS)
        types = [i["type"] for i in items]
        assert "IN_PROGRESS" in types

    def test_in_progress_severity_is_low(self) -> None:
        """IN_PROGRESS items carry 'low' severity."""
        features = [_feature("F1", "in_progress")]
        events = [_iter_ev("F1", 3), _iter_ev("F1", 2)]
        items = build_queue_items(features, events, _EMPTY_GAPS)
        ip = next(i for i in items if i["type"] == "IN_PROGRESS")
        assert ip["severity"] == "low"

    def test_converged_feature_not_in_progress(self) -> None:
        """Converged features are excluded from the queue."""
        features = [_feature("F1", "converged")]
        items = build_queue_items(features, [], _EMPTY_GAPS)
        assert all(i["type"] != "IN_PROGRESS" for i in items)

    # ---- build_queue_items — empty queue ----

    def test_empty_queue_returns_healthy_item(self) -> None:
        """No issues → single healthy item returned."""
        items = build_queue_items([], [], _EMPTY_GAPS)
        assert len(items) == 1
        assert items[0]["type"] == "healthy"
        assert items[0]["severity"] == "info"
        assert items[0]["command"] == ""

    def test_converged_project_returns_healthy(self) -> None:
        """Fully converged project with no gaps → healthy."""
        features = [_feature("F1", "converged"), _feature("F2", "converged")]
        items = build_queue_items(features, [], _EMPTY_GAPS)
        assert len(items) == 1
        assert items[0]["type"] == "healthy"

    # ---- build_queue_items — ranking order ----

    def test_stuck_before_blocked_before_gap_before_in_progress(self) -> None:
        """Items are sorted: critical > high > medium > low."""
        features = [
            _feature("F1", "in_progress"),  # will be IN_PROGRESS (not stuck)
            _feature("F2", "blocked"),
            _feature("F3"),  # will be STUCK
        ]
        # Make F1 vary deltas so it's not stuck
        # Make F3 stuck with 3 identical deltas
        events = [
            _iter_ev("F1", 5),
            _iter_ev("F1", 3),
            _iter_ev("F1", 1),
            _iter_ev("F3", 7),
            _iter_ev("F3", 7),
            _iter_ev("F3", 7),
        ]
        gaps = {
            "layer_1": {"gaps": [{"req_key": "REQ-F-GAP-001"}]},
            "layer_2": {"gaps": []},
        }
        items = build_queue_items(features, events, gaps)
        types = [i["type"] for i in items]
        severities = [i["severity"] for i in items]
        # STUCK (critical) must come first
        assert types[0] == "STUCK"
        # BLOCKED (high) second
        assert "BLOCKED" in types
        blocked_idx = types.index("BLOCKED")
        stuck_idx = types.index("STUCK")
        assert stuck_idx < blocked_idx
        # GAP_CLUSTER (medium) before IN_PROGRESS (low)
        if "GAP_CLUSTER" in types and "IN_PROGRESS" in types:
            assert types.index("GAP_CLUSTER") < types.index("IN_PROGRESS")


# ---------------------------------------------------------------------------
# TestQueueEndpoint — HTTP tests for GET /api/projects/{id}/queue
# ---------------------------------------------------------------------------


class TestQueueEndpoint:
    """Tests for GET /api/projects/{project_id}/queue."""

    @pytest.fixture(autouse=True)
    def _app(self) -> None:
        self._client = TestClient(create_app())

    def _set_root(self, path: Path) -> None:
        _main._config["root_dir"] = str(path)

    def test_returns_200_for_existing_project(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """GET /api/projects/{id}/queue returns 200."""
        root, make_project = tmp_workspace
        make_project("alpha")
        self._set_root(root)
        resp = self._client.get("/api/projects/alpha/queue")
        assert resp.status_code == 200

    def test_response_is_list(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Response is a JSON array."""
        root, make_project = tmp_workspace
        make_project("beta")
        self._set_root(root)
        data = self._client.get("/api/projects/beta/queue").json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_healthy_item_for_empty_project(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """Project with no features and no gaps returns a healthy item."""
        root, make_project = tmp_workspace
        make_project("gamma")
        self._set_root(root)
        data = self._client.get("/api/projects/gamma/queue").json()
        assert data[0]["type"] == "healthy"
        assert data[0]["severity"] == "info"

    def test_queue_item_schema(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Each queue item has the required fields."""
        root, make_project = tmp_workspace
        make_project("delta")
        self._set_root(root)
        data = self._client.get("/api/projects/delta/queue").json()
        item = data[0]
        assert "type" in item
        assert "severity" in item
        assert "description" in item
        assert "command" in item
        assert "detail" in item
        detail = item["detail"]
        assert "reason" in detail
        assert "delta" in detail
        assert "failing_checks" in detail
        assert "expected_outcome" in detail
        assert "gap_keys" in detail
        assert "iteration_history" in detail

    def test_returns_404_for_unknown_project(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """GET /api/projects/{id}/queue returns 404 for unknown project_id."""
        root, _ = tmp_workspace
        self._set_root(root)
        resp = self._client.get("/api/projects/no-such-project/queue")
        assert resp.status_code == 404
