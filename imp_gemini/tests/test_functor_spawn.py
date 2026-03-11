# Validates: REQ-LIFE-001, REQ-LIFE-002
"""Tests for F_D spawn module \u2014 detection, child creation, linkage, fold-back, time-box."""

import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from gemini_cli.engine.fd_spawn import (
    check_time_box,
    create_child_vector,
    detect_spawn_condition,
    emit_spawn_events,
    fold_back_child,
    link_parent_child,
    load_events,
)
from gemini_cli.engine.models import SpawnRequest


# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _make_iteration_event(feature, edge, delta, checks=None, iteration=1):
    """Build an iteration_completed event dict."""
    return {
        "event_type": "iteration_completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": "test",
        "feature": feature,
        "edge": edge,
        "delta": delta,
        "iteration": iteration,
        "checks": checks or [],
    }


def _write_events(workspace, events):
    """Write events to events.jsonl."""
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def _make_parent_vector(workspace, parent_id, edge_key="code_unit_tests"):
    """Create a minimal parent feature vector on disk."""
    features_dir = workspace / ".ai-workspace" / "features" / "active"
    features_dir.mkdir(parents=True, exist_ok=True)
    parent = {
        "feature": parent_id,
        "title": "Test Parent",
        "vector_type": "feature",
        "profile": "standard",
        "status": "in_progress",
        "children": [],
        "trajectory": {
            edge_key: {"status": "iterating"},
        },
    }
    parent_path = features_dir / f"{parent_id}.yml"
    with open(parent_path, "w") as f:
        yaml.dump(parent, f, default_flow_style=False, sort_keys=False)
    return parent_path


def _load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# SPAWN DETECTION
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


class TestDetectSpawnCondition:

    def test_no_spawn_when_delta_decreasing(self):
        """Decreasing deltas [5,4,3,2] \u2014 making progress, no spawn."""
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", d)
            for d in [5, 4, 3, 2]
        ]
        result = detect_spawn_condition(events, "REQ-F-001", "code\u2194unit_tests")
        assert result is None

    def test_spawn_when_delta_stuck(self):
        """Same delta [3,3,3] for 3 iterations \u2014 stuck, should spawn."""
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", 3)
            for _ in range(3)
        ]
        result = detect_spawn_condition(events, "REQ-F-001", "code\u2194unit_tests")
        assert result is not None
        assert isinstance(result, SpawnRequest)
        assert result.parent_feature == "REQ-F-001"
        assert result.triggered_at_edge == "code\u2194unit_tests"
        assert result.vector_type == "discovery"

    def test_no_spawn_when_converged(self):
        """Deltas [3,3,0] \u2014 last is 0, not stuck."""
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", d)
            for d in [3, 3, 0]
        ]
        result = detect_spawn_condition(events, "REQ-F-001", "code\u2194unit_tests")
        assert result is None

    def test_spawn_threshold_configurable(self):
        """With threshold=5, need 5 stuck iterations."""
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", 2)
            for _ in range(4)
        ]
        result = detect_spawn_condition(
            events, "REQ-F-001", "code\u2194unit_tests", threshold=5
        )
        assert result is None

        events.append(_make_iteration_event("REQ-F-001", "code\u2194unit_tests", 2))
        result = detect_spawn_condition(
            events, "REQ-F-001", "code\u2194unit_tests", threshold=5
        )
        assert result is not None

    def test_spawn_question_from_failing_checks(self):
        """Question should include failing check names."""
        checks = [
            {"name": "tests_pass", "outcome": "fail", "required": True},
            {"name": "lint_clean", "outcome": "pass", "required": True},
        ]
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", 1, checks)
            for _ in range(3)
        ]
        result = detect_spawn_condition(events, "REQ-F-001", "code\u2194unit_tests")
        assert "tests_pass" in result.question

    def test_spawn_type_defaults_to_discovery(self):
        """Default vector_type is discovery."""
        events = [
            _make_iteration_event("REQ-F-001", "code\u2194unit_tests", 1)
            for _ in range(3)
        ]
        result = detect_spawn_condition(events, "REQ-F-001", "code\u2194unit_tests")
        assert result.vector_type == "discovery"


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# CHILD VECTOR CREATION
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


class TestCreateChildVector:

    def _make_spawn_request(self):
        return SpawnRequest(
            question="Why are tests failing?",
            vector_type="discovery",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )

    def test_create_child_writes_yaml(self, tmp_path):
        """Child YAML file exists at correct path."""
        req = self._make_spawn_request()
        result = create_child_vector(tmp_path, req, "test_project")
        assert pathlib.Path(result.child_path).exists()
        child = _load_yaml(result.child_path)
        assert child["feature"] == result.child_id

    def test_child_has_parent_linkage(self, tmp_path):
        """Parent fields populated."""
        req = self._make_spawn_request()
        result = create_child_vector(tmp_path, req, "test_project")
        child = _load_yaml(result.child_path)
        assert child["parent"]["feature"] == "REQ-F-AUTH-001"
        assert child["parent"]["edge"] == "code\u2194unit_tests"
        assert "tests failing" in child["parent"]["reason"].lower()

    def test_child_has_time_box(self, tmp_path):
        """Time box enabled with duration from profile."""
        req = self._make_spawn_request()
        result = create_child_vector(tmp_path, req, "test_project")
        child = _load_yaml(result.child_path)
        assert child["time_box"]["enabled"] is True
        assert child["time_box"]["duration"] == "1 day"

    def test_child_id_sequential(self, tmp_path):
        """Second child gets SEQ=002."""
        req = self._make_spawn_request()
        r1 = create_child_vector(tmp_path, req, "test_project")
        r2 = create_child_vector(tmp_path, req, "test_project")
        assert r1.child_id.endswith("001")
        assert r2.child_id.endswith("002")

    def test_child_profile_from_type(self, tmp_path):
        """Profile derived from vector_type."""
        for vtype, expected_profile in [
            ("spike", "spike"),
            ("hotfix", "hotfix"),
            ("discovery", "minimal"),
        ]:
            req = SpawnRequest(
                question="test",
                vector_type=vtype,
                parent_feature="REQ-F-001",
                triggered_at_edge="code\u2194unit_tests",
            )
            result = create_child_vector(tmp_path, req, "test_project")
            assert result.profile == expected_profile


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# PARENT-CHILD LINKAGE
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


class TestLinkParentChild:

    def test_parent_children_list_updated(self, tmp_path):
        """Children list has new entry."""
        _make_parent_vector(tmp_path, "REQ-F-AUTH-001")
        req = SpawnRequest(
            question="test", vector_type="discovery",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )
        ok = link_parent_child(
            tmp_path, "REQ-F-AUTH-001", "REQ-F-DISCOVERY-001", "discovery", req
        )
        assert ok is True
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        assert len(parent["children"]) == 1
        assert parent["children"][0]["feature"] == "REQ-F-DISCOVERY-001"

    def test_parent_edge_blocked(self, tmp_path):
        """Trajectory edge status is 'blocked'."""
        _make_parent_vector(tmp_path, "REQ-F-AUTH-001")
        req = SpawnRequest(
            question="test", vector_type="discovery",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )
        link_parent_child(
            tmp_path, "REQ-F-AUTH-001", "REQ-F-DISCOVERY-001", "discovery", req
        )
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        assert parent["trajectory"]["code_unit_tests"]["status"] == "blocked"

    def test_parent_blocked_by_child(self, tmp_path):
        """blocked_by field set to child ID."""
        _make_parent_vector(tmp_path, "REQ-F-AUTH-001")
        req = SpawnRequest(
            question="test", vector_type="discovery",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )
        link_parent_child(
            tmp_path, "REQ-F-AUTH-001", "REQ-F-DISCOVERY-001", "discovery", req
        )
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        assert parent["trajectory"]["code_unit_tests"]["blocked_by"] == "REQ-F-DISCOVERY-001"

    def test_multiple_children(self, tmp_path):
        """Parent can have >1 child."""
        _make_parent_vector(tmp_path, "REQ-F-AUTH-001")
        for i, child_id in enumerate(["REQ-F-DISCOVERY-001", "REQ-F-SPIKE-001"]):
            req = SpawnRequest(
                question=f"test {i}", vector_type="discovery",
                parent_feature="REQ-F-AUTH-001",
                triggered_at_edge="code\u2194unit_tests",
            )
            link_parent_child(
                tmp_path, "REQ-F-AUTH-001", child_id, "discovery", req
            )
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        assert len(parent["children"]) == 2


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# FOLD-BACK
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


class TestFoldBack:

    def _setup_parent_child(self, workspace):
        """Create linked parent + child on disk."""
        _make_parent_vector(workspace, "REQ-F-AUTH-001")
        req = SpawnRequest(
            question="test", vector_type="discovery",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )
        result = create_child_vector(workspace, req, "test_project")
        link_parent_child(
            workspace, "REQ-F-AUTH-001", result.child_id, "discovery", req
        )
        # Mark child as converged
        child_path = pathlib.Path(result.child_path)
        child = _load_yaml(child_path)
        child["status"] = "converged"
        with open(child_path, "w") as f:
            yaml.dump(child, f, default_flow_style=False, sort_keys=False)
        return result.child_id

    def test_fold_back_writes_payload(self, tmp_path):
        """Payload file exists in fold-back/."""
        child_id = self._setup_parent_child(tmp_path)
        result = fold_back_child(
            tmp_path, "REQ-F-AUTH-001", child_id, "test_project",
            payload_summary="Tests now pass."
        )
        assert pathlib.Path(result.payload_path).exists()

    def test_fold_back_updates_parent_children(self, tmp_path):
        """fold_back_status=folded_back in parent's children entry."""
        child_id = self._setup_parent_child(tmp_path)
        fold_back_child(
            tmp_path, "REQ-F-AUTH-001", child_id, "test_project"
        )
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        child_entry = parent["children"][0]
        assert child_entry["fold_back_status"] == "folded_back"

    def test_fold_back_unblocks_parent(self, tmp_path):
        """Edge status back to 'iterating'."""
        child_id = self._setup_parent_child(tmp_path)
        result = fold_back_child(
            tmp_path, "REQ-F-AUTH-001", child_id, "test_project"
        )
        assert result.parent_unblocked is True
        parent = _load_yaml(
            tmp_path / ".ai-workspace/features/active/REQ-F-AUTH-001.yml"
        )
        assert parent["trajectory"]["code_unit_tests"]["status"] == "iterating"
        assert "blocked_by" not in parent["trajectory"]["code_unit_tests"]

    def test_fold_back_emits_event(self, tmp_path):
        """spawn_folded_back in events.jsonl."""
        child_id = self._setup_parent_child(tmp_path)
        fold_back_child(
            tmp_path, "REQ-F-AUTH-001", child_id, "test_project"
        )
        events = load_events(tmp_path)
        fold_events = [e for e in events if e["event_type"] == "spawn_folded_back"]
        assert len(fold_events) == 1
        assert fold_events[0]["child_feature"] == child_id

    def test_fold_back_on_time_box_expired(self, tmp_path):
        """Works with expired status too."""
        _make_parent_vector(tmp_path, "REQ-F-AUTH-001")
        req = SpawnRequest(
            question="test", vector_type="spike",
            parent_feature="REQ-F-AUTH-001",
            triggered_at_edge="code\u2194unit_tests",
        )
        result = create_child_vector(tmp_path, req, "test_project")
        link_parent_child(
            tmp_path, "REQ-F-AUTH-001", result.child_id, "spike", req
        )
        # Mark child as time_box_expired
        child_path = pathlib.Path(result.child_path)
        child = _load_yaml(child_path)
        child["status"] = "time_box_expired"
        with open(child_path, "w") as f:
            yaml.dump(child, f, default_flow_style=False, sort_keys=False)

        fb = fold_back_child(
            tmp_path, "REQ-F-AUTH-001", result.child_id, "test_project"
        )
        assert fb.parent_unblocked is True


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TIME BOX
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


class TestTimeBox:

    def test_time_box_active(self):
        """Within duration returns 'active'."""
        now = datetime.now(timezone.utc)
        fv = {
            "time_box": {
                "enabled": True,
                "duration": "1 week",
                "started": now.isoformat(),
            }
        }
        assert check_time_box(fv) == "active"

    def test_time_box_expired(self):
        """Past duration returns 'expired'."""
        long_ago = datetime.now(timezone.utc) - timedelta(days=30)
        fv = {
            "time_box": {
                "enabled": True,
                "duration": "1 day",
                "started": long_ago.isoformat(),
            }
        }
        assert check_time_box(fv) == "expired"

    def test_time_box_disabled(self):
        """enabled=false returns 'disabled'."""
        fv = {"time_box": {"enabled": False}}
        assert check_time_box(fv) == "disabled"
