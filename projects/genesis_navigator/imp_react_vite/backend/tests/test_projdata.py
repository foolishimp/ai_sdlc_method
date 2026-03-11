"""Tests for REQ-F-PROJDATA-001: Project Data Reader + Detail API.

Covers event reader, feature reader, state computation, Hamiltonian metrics,
and the GET /api/projects/{project_id} endpoint.
"""

# Validates: REQ-F-STAT-001
# Validates: REQ-F-STAT-002
# Validates: REQ-F-STAT-003
# Validates: REQ-F-STAT-004
# Validates: REQ-F-API-002
# Validates: REQ-NFR-PERF-002

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

import genesis_nav.main as _main
from genesis_nav.main import create_app
from genesis_nav.readers.event_reader import last_event_timestamp, read_events
from genesis_nav.readers.feature_reader import read_features
from genesis_nav.readers.state_computer import (
    compute_hamiltonian,
    compute_project_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_feature_yaml(directory: Path, filename: str, content: str) -> None:
    """Write a YAML feature file into an existing features sub-directory."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(content, encoding="utf-8")


def _active_dir(project: Path) -> Path:
    return project / ".ai-workspace" / "features" / "active"


def _completed_dir(project: Path) -> Path:
    return project / ".ai-workspace" / "features" / "completed"


# ---------------------------------------------------------------------------
# TestEventReader
# ---------------------------------------------------------------------------


class TestEventReader:
    """Tests for genesis_nav.readers.event_reader."""

    def test_read_valid_events(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_events returns all valid JSONL lines as dicts."""
        root, make_project = tmp_workspace
        events = [
            {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"},
            {"event_type": "edge_started", "feature_id": "F1", "edge": "design→code"},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 3},
        ]
        project = make_project("alpha", events=events)
        result = read_events(project)
        assert len(result) == 3
        assert result[0]["event_type"] == "project_initialized"
        assert result[2]["delta"] == 3

    def test_skip_malformed_lines(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_events silently skips malformed JSON lines."""
        root, make_project = tmp_workspace
        project = make_project("beta", events=[{"event_type": "project_initialized"}])
        events_file = project / ".ai-workspace" / "events" / "events.jsonl"
        # Append a malformed line
        with events_file.open("a") as fh:
            fh.write("not valid json\n")
            fh.write(json.dumps({"event_type": "edge_started"}) + "\n")
        result = read_events(project)
        assert len(result) == 2
        assert all(isinstance(e, dict) for e in result)

    def test_empty_events_file(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_events returns [] for an empty events.jsonl."""
        root, make_project = tmp_workspace
        project = make_project("gamma")
        events_file = project / ".ai-workspace" / "events" / "events.jsonl"
        events_file.write_text("", encoding="utf-8")
        result = read_events(project)
        assert result == []

    def test_missing_events_file_returns_empty(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_events returns [] when events.jsonl does not exist."""
        root, _ = tmp_workspace
        non_genesis = root / "no-workspace"
        non_genesis.mkdir()
        result = read_events(non_genesis)
        assert result == []

    def test_last_event_timestamp_found(self) -> None:
        """last_event_timestamp returns the timestamp of the last event that has one."""
        events = [
            {"event_type": "a", "timestamp": "2026-01-01T00:00:00Z"},
            {"event_type": "b"},
            {"event_type": "c", "timestamp": "2026-06-01T12:00:00Z"},
        ]
        assert last_event_timestamp(events) == "2026-06-01T12:00:00Z"

    def test_last_event_timestamp_none(self) -> None:
        """last_event_timestamp returns None when no event has a timestamp."""
        events = [{"event_type": "a"}, {"event_type": "b"}]
        assert last_event_timestamp(events) is None

    def test_last_event_timestamp_empty_list(self) -> None:
        """last_event_timestamp returns None for empty list."""
        assert last_event_timestamp([]) is None


# ---------------------------------------------------------------------------
# TestFeatureReader
# ---------------------------------------------------------------------------


class TestFeatureReader:
    """Tests for genesis_nav.readers.feature_reader."""

    def test_read_active_features(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features returns features from the active directory."""
        root, make_project = tmp_workspace
        project = make_project("proj1")
        _write_feature_yaml(
            _active_dir(project),
            "REQ-F-AUTH-001.yml",
            "feature_id: REQ-F-AUTH-001\ntitle: Authentication\nstatus: in_progress\n",
        )
        features = read_features(project)
        assert len(features) == 1
        assert features[0]["feature_id"] == "REQ-F-AUTH-001"
        assert features[0]["status"] == "in_progress"

    def test_read_completed_features(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features returns features from the completed directory."""
        root, make_project = tmp_workspace
        project = make_project("proj2")
        _write_feature_yaml(
            _completed_dir(project),
            "REQ-F-SCAN-001.yml",
            "feature_id: REQ-F-SCAN-001\ntitle: Scanner\nstatus: converged\n",
        )
        features = read_features(project)
        assert len(features) == 1
        assert features[0]["status"] == "converged"

    def test_reads_active_and_completed(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features concatenates active and completed features."""
        root, make_project = tmp_workspace
        project = make_project("proj3")
        _write_feature_yaml(
            _active_dir(project),
            "active1.yml",
            "feature_id: A1\nstatus: in_progress\n",
        )
        _write_feature_yaml(
            _completed_dir(project),
            "done1.yml",
            "feature_id: D1\nstatus: converged\n",
        )
        features = read_features(project)
        assert len(features) == 2
        ids = {f["feature_id"] for f in features}
        assert ids == {"A1", "D1"}

    def test_skip_malformed_yaml_returns_error_status(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """read_features returns error-status dict for malformed YAML."""
        root, make_project = tmp_workspace
        project = make_project("proj4")
        _write_feature_yaml(
            _active_dir(project),
            "bad.yml",
            "key: [unclosed bracket\n",
        )
        features = read_features(project)
        assert len(features) == 1
        assert features[0]["status"] == "error"
        assert "error" in features[0]
        assert features[0]["feature_id"] == "bad"

    def test_empty_directories_returns_empty(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features returns [] when no feature directories exist."""
        root, make_project = tmp_workspace
        project = make_project("proj5")
        features = read_features(project)
        assert features == []

    def test_feature_id_defaults_to_stem(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features injects feature_id from filename stem when absent."""
        root, make_project = tmp_workspace
        project = make_project("proj6")
        _write_feature_yaml(
            _active_dir(project),
            "my-feature.yml",
            "title: No ID field\nstatus: in_progress\n",
        )
        features = read_features(project)
        assert features[0]["feature_id"] == "my-feature"

    def test_non_yaml_files_ignored(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """read_features ignores non-.yml/.yaml files."""
        root, make_project = tmp_workspace
        project = make_project("proj7")
        active = _active_dir(project)
        active.mkdir(parents=True, exist_ok=True)
        (active / "README.md").write_text("# not yaml", encoding="utf-8")
        _write_feature_yaml(active, "f.yml", "feature_id: F\nstatus: in_progress\n")
        features = read_features(project)
        assert len(features) == 1
        assert features[0]["feature_id"] == "F"


# ---------------------------------------------------------------------------
# TestStateComputer
# ---------------------------------------------------------------------------


class TestStateComputer:
    """Tests for compute_project_state."""

    def test_empty_features_is_uninitialized(self) -> None:
        """Empty feature list → 'uninitialized'."""
        assert compute_project_state([]) == "uninitialized"

    def test_iterating_state(self) -> None:
        """Any in_progress or iterating feature → ITERATING."""
        features = [{"feature_id": "F1", "status": "in_progress"}]
        assert compute_project_state(features) == "ITERATING"

    def test_iterating_status_keyword(self) -> None:
        """status='iterating' also triggers ITERATING."""
        features = [{"feature_id": "F1", "status": "iterating"}]
        assert compute_project_state(features) == "ITERATING"

    def test_converged_state(self) -> None:
        """All required features converged → CONVERGED."""
        features = [
            {"feature_id": "F1", "status": "converged"},
            {"feature_id": "F2", "status": "converged"},
        ]
        assert compute_project_state(features) == "CONVERGED"

    def test_converged_excludes_abandoned(self) -> None:
        """Abandoned features are excluded from required set for CONVERGED."""
        features = [
            {"feature_id": "F1", "status": "converged"},
            {"feature_id": "F2", "status": "abandoned"},
        ]
        assert compute_project_state(features) == "CONVERGED"

    def test_converged_excludes_blocked_deferred(self) -> None:
        """blocked_deferred features are excluded from required set."""
        features = [
            {"feature_id": "F1", "status": "converged"},
            {"feature_id": "F2", "status": "blocked_deferred"},
        ]
        assert compute_project_state(features) == "CONVERGED"

    def test_quiescent_blocked_without_disposition(self) -> None:
        """Blocked feature without disposition → QUIESCENT."""
        features = [
            {"feature_id": "F1", "status": "blocked"},
        ]
        assert compute_project_state(features) == "QUIESCENT"

    def test_bounded_all_blocked_have_disposition(self) -> None:
        """All blocked features have disposition → BOUNDED."""
        features = [
            {"feature_id": "F1", "status": "blocked", "disposition": "deferred to v2"},
        ]
        assert compute_project_state(features) == "BOUNDED"

    def test_quiescent_mixed_blocked(self) -> None:
        """Mixed blocked (some with, some without disposition) → QUIESCENT."""
        features = [
            {"feature_id": "F1", "status": "blocked", "disposition": "deferred"},
            {"feature_id": "F2", "status": "blocked"},
        ]
        assert compute_project_state(features) == "QUIESCENT"

    def test_iterating_beats_blocked(self) -> None:
        """ITERATING takes priority over blocked features."""
        features = [
            {"feature_id": "F1", "status": "in_progress"},
            {"feature_id": "F2", "status": "blocked"},
        ]
        assert compute_project_state(features) == "ITERATING"

    def test_default_quiescent_no_blocked(self) -> None:
        """No iterating, not converged, no blocked → QUIESCENT."""
        features = [{"feature_id": "F1", "status": "unknown"}]
        assert compute_project_state(features) == "QUIESCENT"


# ---------------------------------------------------------------------------
# TestHamiltonian
# ---------------------------------------------------------------------------


class TestHamiltonian:
    """Tests for compute_hamiltonian."""

    def test_no_events_returns_zeros(self) -> None:
        """No iteration events → H=0, T=0, V=0, flat=False."""
        result = compute_hamiltonian([], "F1")
        assert result == {"H": 0, "T": 0, "V": 0, "flat": False}

    def test_single_iteration(self) -> None:
        """Single iteration_completed → T=1, V=delta, H=T+V."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 5},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["T"] == 1
        assert result["V"] == 5
        assert result["H"] == 6
        assert result["flat"] is False

    def test_v_zero_when_edge_converged_follows(self) -> None:
        """V=0 when edge_converged follows the last iteration_completed."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 3},
            {"event_type": "edge_converged", "feature_id": "F1"},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["V"] == 0
        assert result["T"] == 1
        assert result["H"] == 1

    def test_ignores_other_feature_events(self) -> None:
        """Events from other features are not counted."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "OTHER", "delta": 10},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 2},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["T"] == 1
        assert result["V"] == 2

    def test_flat_detection_true(self) -> None:
        """flat=True when last 3 V values are identical."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 4},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 4},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 4},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["flat"] is True
        assert result["T"] == 3

    def test_flat_detection_false_varying_delta(self) -> None:
        """flat=False when last 3 V values differ."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 5},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 3},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 1},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["flat"] is False

    def test_flat_false_fewer_than_three_iterations(self) -> None:
        """flat=False when fewer than 3 iterations exist."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 2},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 2},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["flat"] is False

    def test_multiple_iterations_accumulate_t(self) -> None:
        """T counts all iteration_completed events."""
        events = [
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 3},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 2},
            {"event_type": "iteration_completed", "feature_id": "F1", "delta": 1},
        ]
        result = compute_hamiltonian(events, "F1")
        assert result["T"] == 3
        assert result["V"] == 1  # last delta
        assert result["H"] == 4


# ---------------------------------------------------------------------------
# TestProjectDetailEndpoint
# ---------------------------------------------------------------------------


class TestProjectDetailEndpoint:
    """Tests for GET /api/projects/{project_id}."""

    @pytest.fixture(autouse=True)
    def _app(self) -> TestClient:
        """Create a fresh TestClient for each test."""
        self._client = TestClient(create_app())

    def _set_root(self, path: Path) -> None:
        _main._config["root_dir"] = str(path)

    def test_returns_200_for_existing_project(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """GET /api/projects/{id} returns 200 for a known project."""
        root, make_project = tmp_workspace
        make_project("alpha")
        self._set_root(root)
        resp = self._client.get("/api/projects/alpha")
        assert resp.status_code == 200

    def test_response_has_correct_schema_fields(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Response contains all ProjectDetail required fields."""
        root, make_project = tmp_workspace
        make_project("beta")
        self._set_root(root)
        data = self._client.get("/api/projects/beta").json()
        assert data["project_id"] == "beta"
        assert data["name"] == "beta"
        assert "state" in data
        assert "features" in data
        assert "total_edges" in data
        assert "converged_edges" in data

    def test_returns_404_for_unknown_project(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """GET /api/projects/{id} returns 404 when project_id is not found."""
        root, _ = tmp_workspace
        self._set_root(root)
        resp = self._client.get("/api/projects/does-not-exist")
        assert resp.status_code == 404

    def test_features_included_in_response(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Response features list reflects workspace feature vectors."""
        root, make_project = tmp_workspace
        project = make_project("gamma")
        _write_feature_yaml(
            _active_dir(project),
            "F1.yml",
            "feature_id: F1\ntitle: My Feature\nstatus: in_progress\n",
        )
        self._set_root(root)
        data = self._client.get("/api/projects/gamma").json()
        assert len(data["features"]) == 1
        feat = data["features"][0]
        assert feat["feature_id"] == "F1"
        assert feat["title"] == "My Feature"
        assert feat["status"] == "in_progress"

    def test_edge_counts_computed(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """total_edges and converged_edges reflect trajectory data."""
        root, make_project = tmp_workspace
        events = [
            {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"},
            {"event_type": "edge_started", "feature_id": "F1", "edge": "design→code"},
            {
                "event_type": "iteration_completed",
                "feature_id": "F1",
                "edge": "design→code",
                "delta": 2,
            },
            {"event_type": "edge_converged", "feature_id": "F1", "edge": "design→code"},
            {"event_type": "edge_started", "feature_id": "F1", "edge": "code→tests"},
            {
                "event_type": "iteration_completed",
                "feature_id": "F1",
                "edge": "code→tests",
                "delta": 1,
            },
        ]
        project = make_project("delta", events=events)
        _write_feature_yaml(
            _active_dir(project),
            "F1.yml",
            "feature_id: F1\ntitle: Test Feature\nstatus: in_progress\n",
        )
        self._set_root(root)
        data = self._client.get("/api/projects/delta").json()
        assert data["total_edges"] == 2
        assert data["converged_edges"] == 1

    def test_state_derived_from_features(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Project state matches computed state from feature vectors."""
        root, make_project = tmp_workspace
        project = make_project("epsilon")
        _write_feature_yaml(
            _completed_dir(project),
            "F1.yml",
            "feature_id: F1\ntitle: Done\nstatus: converged\n",
        )
        self._set_root(root)
        data = self._client.get("/api/projects/epsilon").json()
        assert data["state"] == "CONVERGED"

    def test_empty_features_state_uninitialized(self, tmp_workspace: tuple[Path, Callable]) -> None:
        """Project with no feature files returns state='uninitialized'."""
        root, make_project = tmp_workspace
        make_project("zeta")
        self._set_root(root)
        data = self._client.get("/api/projects/zeta").json()
        assert data["state"] == "uninitialized"
        assert data["features"] == []
        assert data["total_edges"] == 0
        assert data["converged_edges"] == 0
