# Validates: REQ-F-DISPATCH-001
"""Tests for IntentObserver — find_unhandled_intents, resolve_dispatch_targets,
get_pending_dispatches.

Covers:
- find_unhandled_intents: empty log, only intent_raised, handled/unhandled
- resolve_dispatch_targets: scope resolution, edge selection, missing vectors
- get_pending_dispatches: integration
- Edge selection from trajectory: first non-converged, skip converged, all converged
- Scope resolution: affected_features=["all"] vs specific list
"""

import json
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genesis.intent_observer import (
    DispatchTarget,
    _get_affected_features,
    _get_intent_id,
    _normalize,
    _select_edge,
    find_unhandled_intents,
    get_pending_dispatches,
    resolve_dispatch_targets,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_intent_raised(intent_id: str, affected_features: list[str] | None = None) -> dict:
    """Create a flat intent_raised event."""
    ev = {
        "event_type": "intent_raised",
        "timestamp": "2026-03-11T00:00:00Z",
        "project": "test_project",
        "intent_id": intent_id,
        "signal_source": "test",
        "affected_features": affected_features or [],
    }
    return ev


def _make_edge_started(feature: str, edge: str, intent_id: str | None = None) -> dict:
    """Create a flat edge_started event."""
    ev = {
        "event_type": "edge_started",
        "timestamp": "2026-03-11T00:01:00Z",
        "project": "test_project",
        "feature": feature,
        "edge": edge,
    }
    if intent_id:
        ev["intent_id"] = intent_id
    return ev


def _write_events(events_path: pathlib.Path, events: list[dict]) -> None:
    """Write events to events.jsonl."""
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _write_feature_vector(workspace: pathlib.Path, feature_id: str, data: dict) -> None:
    """Write a feature vector YAML."""
    active_dir = workspace / ".ai-workspace" / "features" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    path = active_dir / f"{feature_id}.yml"
    path.write_text(yaml.dump(data))


def _minimal_feature_vector(feature_id: str, profile: str = "standard", trajectory: dict | None = None) -> dict:
    """Create a minimal feature vector."""
    return {
        "feature": feature_id,
        "title": f"Test feature {feature_id}",
        "profile": profile,
        "status": "iterating",
        "trajectory": trajectory or {},
    }


# ── Tests: find_unhandled_intents ──────────────────────────────────────────────


class TestFindUnhandledIntents:
    """Tests for find_unhandled_intents()."""

    def test_empty_log_returns_empty(self, tmp_path):
        """Empty events.jsonl → no unhandled intents."""
        events_path = tmp_path / "events.jsonl"
        events_path.write_text("")
        result = find_unhandled_intents(events_path)
        assert result == []

    def test_nonexistent_log_returns_empty(self, tmp_path):
        """Missing events.jsonl → no unhandled intents."""
        events_path = tmp_path / "events.jsonl"
        result = find_unhandled_intents(events_path)
        assert result == []

    def test_single_intent_with_no_edge_started(self, tmp_path):
        """Single intent_raised with no edge_started → unhandled."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
        ])
        result = find_unhandled_intents(events_path)
        assert len(result) == 1
        assert result[0]["intent_id"] == "INT-001"

    def test_intent_with_matching_edge_started_is_handled(self, tmp_path):
        """intent_raised + edge_started with matching intent_id → handled."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_edge_started("REQ-F-TEST-001", "code↔unit_tests", intent_id="INT-001"),
        ])
        result = find_unhandled_intents(events_path)
        assert result == []

    def test_intent_with_different_edge_started_intent_id_is_unhandled(self, tmp_path):
        """edge_started with different intent_id → original intent still unhandled."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_edge_started("REQ-F-TEST-001", "code↔unit_tests", intent_id="INT-002"),
        ])
        result = find_unhandled_intents(events_path)
        assert len(result) == 1
        assert result[0]["intent_id"] == "INT-001"

    def test_edge_started_without_intent_id_does_not_handle_any_intent(self, tmp_path):
        """edge_started without intent_id → doesn't count as handling any intent."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_edge_started("REQ-F-TEST-001", "code↔unit_tests"),  # no intent_id
        ])
        result = find_unhandled_intents(events_path)
        assert len(result) == 1

    def test_multiple_intents_some_handled(self, tmp_path):
        """Two intents, one handled, one not."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_intent_raised("INT-002", ["REQ-F-TEST-002"]),
            _make_edge_started("REQ-F-TEST-001", "code↔unit_tests", intent_id="INT-001"),
        ])
        result = find_unhandled_intents(events_path)
        assert len(result) == 1
        assert result[0]["intent_id"] == "INT-002"

    def test_intent_without_intent_id_is_skipped(self, tmp_path):
        """intent_raised without intent_id → skipped (cannot track idempotency)."""
        events_path = tmp_path / "events.jsonl"
        ev = {
            "event_type": "intent_raised",
            "timestamp": "2026-03-11T00:00:00Z",
            "project": "test_project",
            "signal_source": "test",
            # no intent_id
        }
        _write_events(events_path, [ev])
        result = find_unhandled_intents(events_path)
        assert result == []

    def test_ol_format_intent_raised(self, tmp_path):
        """OL-format intent_raised event is normalised and detected."""
        events_path = tmp_path / "events.jsonl"
        ol_event = {
            "eventType": "OTHER",
            "eventTime": "2026-03-11T00:00:00Z",
            "run": {
                "runId": "abc-123",
                "facets": {
                    "sdlc:event_type": {
                        "_producer": "test",
                        "_schemaURL": "test",
                        "type": "intent_raised",
                    },
                    "sdlc:payload": {
                        "_producer": "test",
                        "_schemaURL": "test",
                        "intent_id": "INT-OL-001",
                        "affected_features": ["REQ-F-TEST-001"],
                    },
                },
            },
            "job": {"namespace": "aisdlc://test_project", "name": "INTENT_ENGINE"},
            "inputs": [],
            "outputs": [],
            "producer": "test",
            "schemaURL": "test",
        }
        _write_events(events_path, [ol_event])
        result = find_unhandled_intents(events_path)
        assert len(result) == 1

    def test_non_intent_events_ignored(self, tmp_path):
        """Other event types don't appear as unhandled intents."""
        events_path = tmp_path / "events.jsonl"
        _write_events(events_path, [
            {"event_type": "edge_converged", "feature": "F1", "edge": "code↔unit_tests"},
            {"event_type": "iteration_completed", "feature": "F1", "delta": 0},
        ])
        result = find_unhandled_intents(events_path)
        assert result == []

    def test_malformed_json_lines_tolerated(self, tmp_path):
        """Malformed JSON lines are skipped gracefully."""
        events_path = tmp_path / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            json.dumps(_make_intent_raised("INT-001")) + "\n"
            "not valid json\n"
            + json.dumps(_make_intent_raised("INT-002")) + "\n"
        )
        result = find_unhandled_intents(events_path)
        assert len(result) == 2


# ── Tests: _select_edge ────────────────────────────────────────────────────────


class TestSelectEdge:
    """Tests for _select_edge() — edge selection from trajectory."""

    def test_empty_trajectory_returns_first_standard_edge(self):
        """Empty trajectory → first edge in standard profile."""
        fv = {"profile": "standard", "trajectory": {}}
        edge = _select_edge(fv)
        assert edge == "intent→requirements"

    def test_converged_edges_are_skipped(self):
        """Converged edges are skipped; returns next non-converged."""
        fv = {
            "profile": "standard",
            "trajectory": {
                "intent_requirements": {"status": "converged"},
                "requirements_feature_decomposition": {"status": "converged"},
            },
        }
        edge = _select_edge(fv)
        # Both intent→req and req→feat_decomp are converged; next is feature_decomp→design_rec
        assert edge == "feature_decomposition→design_recommendations"

    def test_iterating_edge_is_selected(self):
        """Edge with status 'iterating' is returned as the target."""
        fv = {
            "profile": "standard",
            "trajectory": {
                "intent_requirements": {"status": "converged"},
                "requirements_feature_decomposition": {"status": "iterating"},
            },
        }
        edge = _select_edge(fv)
        assert edge == "requirements→feature_decomposition"

    def test_all_converged_returns_none(self):
        """All profile edges converged → returns None."""
        from genesis.intent_observer import PROFILE_EDGE_ORDERS
        standard = PROFILE_EDGE_ORDERS["standard"]
        traj = {}
        for e in standard:
            key = e.replace("→", "_").replace("↔", "_").replace(" ", "")
            traj[key] = {"status": "converged"}
        fv = {"profile": "standard", "trajectory": traj}
        edge = _select_edge(fv)
        assert edge is None

    def test_hotfix_profile_uses_short_edge_list(self):
        """Hotfix profile only checks code↔unit_tests."""
        fv = {"profile": "hotfix", "trajectory": {}}
        edge = _select_edge(fv)
        assert edge == "code↔unit_tests"

    def test_unknown_profile_falls_back_to_standard(self):
        """Unknown profile uses standard edge order."""
        fv = {"profile": "unknown_profile", "trajectory": {}}
        edge = _select_edge(fv)
        assert edge == "intent→requirements"

    def test_none_trajectory_returns_first_edge(self):
        """None trajectory is treated as empty."""
        fv = {"profile": "standard", "trajectory": None}
        edge = _select_edge(fv)
        assert edge == "intent→requirements"

    def test_poc_profile_edges(self):
        """PoC profile uses a shorter edge list."""
        fv = {"profile": "poc", "trajectory": {
            "intent_requirements": {"status": "converged"},
        }}
        edge = _select_edge(fv)
        assert edge == "requirements→feature_decomposition"


# ── Tests: resolve_dispatch_targets ────────────────────────────────────────────


class TestResolveDispatchTargets:
    """Tests for resolve_dispatch_targets()."""

    def test_single_feature_with_active_vector(self, tmp_path):
        """Intent with one affected feature → one DispatchTarget."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        intent = _make_intent_raised("INT-001", ["REQ-F-TEST-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert len(targets) == 1
        assert targets[0].feature_id == "REQ-F-TEST-001"
        assert targets[0].intent_id == "INT-001"

    def test_feature_without_active_vector_is_skipped(self, tmp_path):
        """Affected feature with no active vector → skipped."""
        workspace = tmp_path
        intent = _make_intent_raised("INT-001", ["REQ-F-MISSING-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert targets == []

    def test_all_scope_resolves_all_active_features(self, tmp_path):
        """affected_features=["all"] → all active feature vectors."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-A-001", _minimal_feature_vector("REQ-F-A-001"))
        _write_feature_vector(workspace, "REQ-F-B-001", _minimal_feature_vector("REQ-F-B-001"))
        intent = _make_intent_raised("INT-001", ["all"])
        targets = resolve_dispatch_targets(intent, workspace)
        feature_ids = {t.feature_id for t in targets}
        assert "REQ-F-A-001" in feature_ids
        assert "REQ-F-B-001" in feature_ids

    def test_fully_converged_feature_is_skipped(self, tmp_path):
        """Feature with all edges converged → skipped."""
        from genesis.intent_observer import PROFILE_EDGE_ORDERS
        workspace = tmp_path
        standard = PROFILE_EDGE_ORDERS["standard"]
        traj = {}
        for e in standard:
            key = e.replace("→", "_").replace("↔", "_").replace(" ", "")
            traj[key] = {"status": "converged"}
        fv = _minimal_feature_vector("REQ-F-DONE-001", trajectory=traj)
        _write_feature_vector(workspace, "REQ-F-DONE-001", fv)
        intent = _make_intent_raised("INT-001", ["REQ-F-DONE-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert targets == []

    def test_no_intent_id_returns_empty(self, tmp_path):
        """Intent event without intent_id → empty targets."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        intent = {
            "event_type": "intent_raised",
            "project": "test",
            "affected_features": ["REQ-F-TEST-001"],
            # no intent_id
        }
        targets = resolve_dispatch_targets(intent, workspace)
        assert targets == []

    def test_empty_affected_features_returns_empty(self, tmp_path):
        """Intent with empty affected_features → empty targets."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        intent = _make_intent_raised("INT-001", [])
        targets = resolve_dispatch_targets(intent, workspace)
        assert targets == []

    def test_target_carries_intent_event(self, tmp_path):
        """DispatchTarget carries the full intent event."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        intent = _make_intent_raised("INT-001", ["REQ-F-TEST-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert len(targets) == 1
        assert targets[0].intent_event["intent_id"] == "INT-001"

    def test_target_carries_feature_vector(self, tmp_path):
        """DispatchTarget carries the loaded feature vector."""
        workspace = tmp_path
        fv = _minimal_feature_vector("REQ-F-TEST-001")
        _write_feature_vector(workspace, "REQ-F-TEST-001", fv)
        intent = _make_intent_raised("INT-001", ["REQ-F-TEST-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert len(targets) == 1
        assert targets[0].feature_vector["feature"] == "REQ-F-TEST-001"

    def test_edge_selection_in_target(self, tmp_path):
        """Selected edge reflects trajectory state."""
        workspace = tmp_path
        fv = _minimal_feature_vector("REQ-F-TEST-001", trajectory={
            "intent_requirements": {"status": "converged"},
        })
        _write_feature_vector(workspace, "REQ-F-TEST-001", fv)
        intent = _make_intent_raised("INT-001", ["REQ-F-TEST-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert len(targets) == 1
        # intent→requirements is converged; next should be requirements→feature_decomposition
        assert targets[0].edge == "requirements→feature_decomposition"

    def test_multiple_features_in_affected_list(self, tmp_path):
        """Multiple affected features → one target per non-converged feature."""
        workspace = tmp_path
        _write_feature_vector(workspace, "REQ-F-A-001", _minimal_feature_vector("REQ-F-A-001"))
        _write_feature_vector(workspace, "REQ-F-B-001", _minimal_feature_vector("REQ-F-B-001"))
        intent = _make_intent_raised("INT-001", ["REQ-F-A-001", "REQ-F-B-001"])
        targets = resolve_dispatch_targets(intent, workspace)
        assert len(targets) == 2


# ── Tests: get_pending_dispatches ──────────────────────────────────────────────


class TestGetPendingDispatches:
    """Integration tests for get_pending_dispatches()."""

    def test_no_events_returns_empty(self, tmp_path):
        """Workspace with no events → no pending dispatches."""
        result = get_pending_dispatches(tmp_path)
        assert result == []

    def test_unhandled_intent_with_active_vector(self, tmp_path):
        """Unhandled intent + active feature vector → pending dispatch."""
        workspace = tmp_path
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
        ])
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        result = get_pending_dispatches(workspace)
        assert len(result) == 1
        assert result[0].intent_id == "INT-001"
        assert result[0].feature_id == "REQ-F-TEST-001"

    def test_handled_intent_not_returned(self, tmp_path):
        """Handled intent (edge_started emitted) → not in pending."""
        workspace = tmp_path
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_edge_started("REQ-F-TEST-001", "code↔unit_tests", intent_id="INT-001"),
        ])
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        result = get_pending_dispatches(workspace)
        assert result == []

    def test_deduplication_across_intents(self, tmp_path):
        """Two intents targeting same feature+edge → deduplicated to one target."""
        workspace = tmp_path
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        _write_events(events_path, [
            _make_intent_raised("INT-001", ["REQ-F-TEST-001"]),
            _make_intent_raised("INT-002", ["REQ-F-TEST-001"]),
        ])
        _write_feature_vector(workspace, "REQ-F-TEST-001", _minimal_feature_vector("REQ-F-TEST-001"))
        result = get_pending_dispatches(workspace)
        # Same feature+edge from both intents — first one wins (dedup by feature_id+edge)
        feature_edge_pairs = [(t.feature_id, t.edge) for t in result]
        assert len(set(feature_edge_pairs)) == len(feature_edge_pairs)  # no duplicates
