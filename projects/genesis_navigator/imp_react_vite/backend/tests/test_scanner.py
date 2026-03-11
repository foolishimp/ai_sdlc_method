# Validates: REQ-F-NAV-001
# Validates: REQ-F-API-001
# Validates: REQ-NFR-ARCH-002
# Validates: REQ-BR-001
# Validates: REQ-BR-002

"""Tests for the Workspace Scanner and FastAPI shell (REQ-F-SCANNER-001).

Structure
---------
TestWorkspaceScanner   — scan_workspace() logic
TestProjectIdentity    — derive_project_id() logic
TestProjectsEndpoint   — GET /api/projects via FastAPI TestClient
TestReadOnlyInvariant  — zero-write guarantee (REQ-NFR-ARCH-002)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import genesis_nav.main as _main
from genesis_nav.main import app
from genesis_nav.models.schemas import ProjectState, ProjectSummary
from genesis_nav.scanner.project_identity import derive_project_id
from genesis_nav.scanner.workspace_scanner import scan_workspace


# ---------------------------------------------------------------------------
# Helper — build the test client with a patched root dir
# ---------------------------------------------------------------------------


def _client_for(root: Path) -> TestClient:
    """Return a TestClient whose scanner root is *root*."""
    _main._config["root_dir"] = str(root)
    return TestClient(app)


# ===========================================================================
# TestWorkspaceScanner
# ===========================================================================


class TestWorkspaceScanner:
    """Unit tests for scan_workspace() — REQ-F-NAV-001."""

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_finds_single_genesis_project(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("alpha")

        # Act
        results = scan_workspace(root)

        # Assert
        assert len(results) == 1
        assert results[0].name == "alpha"

    def test_returns_project_summary_type(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("beta")

        # Act
        results = scan_workspace(root)

        # Assert
        assert isinstance(results[0], ProjectSummary)

    def test_path_field_is_absolute(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        p = make_project("gamma")

        # Act
        results = scan_workspace(root)

        # Assert
        assert Path(results[0].path).is_absolute()
        assert results[0].path == str(p)

    def test_multiple_projects_all_found(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj-a")
        make_project("proj-b")
        make_project("proj-c")

        # Act
        results = scan_workspace(root)
        names = {r.name for r in results}

        # Assert
        assert names == {"proj-a", "proj-b", "proj-c"}

    def test_empty_root_returns_empty_list(self, tmp_path):
        # Arrange — root with no children
        # Act
        results = scan_workspace(tmp_path)

        # Assert
        assert results == []

    def test_nested_project_found(self, tmp_workspace):
        # Arrange — project buried under a non-genesis dir
        root, make_project = tmp_workspace
        make_project("subdir/nested_proj")

        # Act
        results = scan_workspace(root)

        # Assert
        assert len(results) == 1
        assert results[0].name == "nested_proj"

    # ------------------------------------------------------------------
    # Pruning
    # ------------------------------------------------------------------

    def test_prunes_git_dir(self, tmp_workspace):
        # Arrange — genesis project inside .git → must not appear
        root, _ = tmp_workspace
        git_project = root / ".git" / "hidden"
        (git_project / ".ai-workspace" / "events").mkdir(parents=True)
        (git_project / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results == []

    def test_prunes_node_modules(self, tmp_workspace):
        # Arrange
        root, _ = tmp_workspace
        nm = root / "node_modules" / "pkg"
        (nm / ".ai-workspace" / "events").mkdir(parents=True)
        (nm / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results == []

    def test_prunes_pycache(self, tmp_workspace):
        # Arrange
        root, _ = tmp_workspace
        pc = root / "__pycache__" / "cached"
        (pc / ".ai-workspace" / "events").mkdir(parents=True)
        (pc / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results == []

    def test_prunes_venv(self, tmp_workspace):
        # Arrange
        root, _ = tmp_workspace
        venv = root / ".venv" / "lib"
        (venv / ".ai-workspace" / "events").mkdir(parents=True)
        (venv / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results == []

    def test_valid_project_alongside_pruned_dir_is_found(self, tmp_workspace):
        # Arrange — real project + a pruned sibling
        root, make_project = tmp_workspace
        make_project("real_proj")
        nm = root / "node_modules" / "pkg"
        (nm / ".ai-workspace" / "events").mkdir(parents=True)
        (nm / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert len(results) == 1
        assert results[0].name == "real_proj"

    # ------------------------------------------------------------------
    # Uninitialized workspace
    # ------------------------------------------------------------------

    def test_ai_workspace_without_events_jsonl_is_uninitialized(self, tmp_workspace):
        # Arrange — has .ai-workspace/ but no events/events.jsonl
        root, _ = tmp_workspace
        proj = root / "no_events_proj"
        (proj / ".ai-workspace").mkdir(parents=True)

        # Act
        results = scan_workspace(root)

        # Assert
        assert len(results) == 1
        assert results[0].state == ProjectState.UNINITIALIZED

    def test_uninitialized_project_has_zero_feature_counts(self, tmp_workspace):
        # Arrange
        root, _ = tmp_workspace
        proj = root / "empty_ws"
        (proj / ".ai-workspace").mkdir(parents=True)

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].active_feature_count == 0
        assert results[0].converged_feature_count == 0

    def test_uninitialized_project_last_event_at_is_none(self, tmp_workspace):
        # Arrange
        root, _ = tmp_workspace
        proj = root / "no_events"
        (proj / ".ai-workspace").mkdir(parents=True)

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].last_event_at is None

    # ------------------------------------------------------------------
    # State derivation (REQ-BR-002)
    # ------------------------------------------------------------------

    def test_state_quiescent_for_ordinary_events(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project(
            "proj",
            events=[{"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"}],
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].state == ProjectState.QUIESCENT

    def test_state_iterating_when_iteration_completed_iterating(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project(
            "proj",
            events=[
                {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"},
                {
                    "event_type": "iteration_completed",
                    "status": "iterating",
                    "timestamp": "2026-01-02T00:00:00Z",
                },
            ],
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].state == ProjectState.ITERATING

    def test_state_converged_when_last_event_is_edge_converged(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project(
            "proj",
            events=[
                {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"},
                {"event_type": "edge_converged", "timestamp": "2026-01-03T00:00:00Z"},
            ],
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].state == ProjectState.CONVERGED

    def test_state_derived_from_events_not_mtime(self, tmp_workspace):
        # Arrange — same mtime for two projects but different event states
        root, make_project = tmp_workspace
        make_project(
            "proj_converged",
            events=[
                {"event_type": "edge_converged", "timestamp": "2026-01-01T00:00:00Z"}
            ],
        )
        make_project(
            "proj_quiescent",
            events=[
                {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"}
            ],
        )

        # Act
        results = scan_workspace(root)
        by_name = {r.name: r for r in results}

        # Assert — states differ despite identical timestamps
        assert by_name["proj_converged"].state == ProjectState.CONVERGED
        assert by_name["proj_quiescent"].state == ProjectState.QUIESCENT

    def test_empty_events_jsonl_yields_quiescent(self, tmp_workspace):
        # Arrange — events.jsonl exists but is empty
        root, _ = tmp_workspace
        proj = root / "empty_events"
        events_dir = proj / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").write_text("")

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].state == ProjectState.QUIESCENT

    def test_malformed_json_lines_skipped(self, tmp_workspace):
        # Arrange — mix of valid and invalid lines
        root, _ = tmp_workspace
        proj = root / "bad_lines"
        events_dir = proj / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").write_text(
            'NOT JSON\n'
            '{"event_type":"project_initialized","timestamp":"2026-01-01T00:00:00Z"}\n'
            'ALSO BAD\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert — does not crash, falls back to quiescent
        assert len(results) == 1
        assert results[0].state == ProjectState.QUIESCENT

    # ------------------------------------------------------------------
    # Feature counts
    # ------------------------------------------------------------------

    def test_active_feature_count(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj", active_features=["feat_a.yml", "feat_b.yml"])

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].active_feature_count == 2

    def test_converged_feature_count(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj", completed_features=["done.yml"])

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].converged_feature_count == 1

    def test_only_yaml_files_counted_in_features(self, tmp_workspace):
        # Arrange — mix of yaml and non-yaml in active/
        root, make_project = tmp_workspace
        make_project("proj", active_features=["feat.yml", "feat2.yaml"])
        # Add a non-yaml file manually
        non_yaml = (
            root / "proj" / ".ai-workspace" / "features" / "active" / "README.md"
        )
        non_yaml.write_text("not counted")

        # Act
        results = scan_workspace(root)

        # Assert — README.md not counted
        assert results[0].active_feature_count == 2

    def test_missing_features_dir_yields_zero_count(self, tmp_workspace):
        # Arrange — no features/ subdirs at all
        root, make_project = tmp_workspace
        make_project("proj")

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].active_feature_count == 0
        assert results[0].converged_feature_count == 0

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    def test_last_event_at_is_latest_timestamp(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project(
            "proj",
            events=[
                {"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"},
                {"event_type": "edge_converged", "timestamp": "2026-06-15T12:30:00Z"},
            ],
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].last_event_at == "2026-06-15T12:30:00Z"

    def test_last_event_at_none_when_no_timestamps(self, tmp_workspace):
        # Arrange — events lack timestamp field
        root, make_project = tmp_workspace
        make_project(
            "proj",
            events=[{"event_type": "project_initialized"}],
        )

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].last_event_at is None

    # ------------------------------------------------------------------
    # scan_duration_ms
    # ------------------------------------------------------------------

    def test_scan_duration_ms_is_positive(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")

        # Act
        results = scan_workspace(root)

        # Assert
        assert results[0].scan_duration_ms >= 0.0

    # ------------------------------------------------------------------
    # Does not descend into project subdirs
    # ------------------------------------------------------------------

    def test_does_not_descend_into_project_subdirectories(self, tmp_workspace):
        # Arrange — parent project + child nested inside it
        root, make_project = tmp_workspace
        # Parent project
        parent = root / "parent"
        (parent / ".ai-workspace" / "events").mkdir(parents=True)
        (parent / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )
        # Child project inside parent
        child = parent / "child"
        (child / ".ai-workspace" / "events").mkdir(parents=True)
        (child / ".ai-workspace" / "events" / "events.jsonl").write_text(
            '{"event_type":"project_initialized"}\n'
        )

        # Act
        results = scan_workspace(root)

        # Assert — only the parent is discovered, not the nested child
        assert len(results) == 1
        assert results[0].name == "parent"


# ===========================================================================
# TestProjectIdentity
# ===========================================================================


class TestProjectIdentity:
    """Unit tests for derive_project_id() — REQ-BR-001."""

    def test_unique_name_returns_dirname(self, tmp_path):
        # Arrange
        project = tmp_path / "my_project"
        project.mkdir()
        seen: set[str] = set()

        # Act
        pid = derive_project_id(project, tmp_path, seen)

        # Assert
        assert pid == "my_project"

    def test_first_seen_name_added_to_seen_set(self, tmp_path):
        # Arrange
        project = tmp_path / "alpha"
        project.mkdir()
        seen: set[str] = set()

        # Act
        derive_project_id(project, tmp_path, seen)

        # Assert
        assert "alpha" in seen

    def test_duplicate_name_disambiguated_by_relative_path(self, tmp_path):
        # Arrange — two projects named "app" in different subdirs
        proj_a = tmp_path / "group_a" / "app"
        proj_b = tmp_path / "group_b" / "app"
        proj_a.mkdir(parents=True)
        proj_b.mkdir(parents=True)
        seen: set[str] = set()

        # Act
        id_a = derive_project_id(proj_a, tmp_path, seen)
        id_b = derive_project_id(proj_b, tmp_path, seen)

        # Assert
        assert id_a == "app"                      # first keeps simple name
        assert id_b != "app"                       # second is disambiguated
        assert "app" in id_b                       # relative path contains "app"
        assert id_a != id_b

    def test_disambiguated_id_is_relative_path_string(self, tmp_path):
        # Arrange
        proj_a = tmp_path / "x" / "foo"
        proj_b = tmp_path / "y" / "foo"
        proj_a.mkdir(parents=True)
        proj_b.mkdir(parents=True)
        seen: set[str] = set()

        # Act
        derive_project_id(proj_a, tmp_path, seen)
        id_b = derive_project_id(proj_b, tmp_path, seen)

        # Assert — disambiguated id is the relative path
        expected = str(proj_b.relative_to(tmp_path))
        assert id_b == expected

    def test_third_duplicate_also_disambiguated(self, tmp_path):
        # Arrange — three projects with the same name
        proj_a = tmp_path / "d1" / "same"
        proj_b = tmp_path / "d2" / "same"
        proj_c = tmp_path / "d3" / "same"
        for p in (proj_a, proj_b, proj_c):
            p.mkdir(parents=True)
        seen: set[str] = set()

        # Act
        id_a = derive_project_id(proj_a, tmp_path, seen)
        id_b = derive_project_id(proj_b, tmp_path, seen)
        id_c = derive_project_id(proj_c, tmp_path, seen)

        # Assert — all three are unique
        assert len({id_a, id_b, id_c}) == 3


# ===========================================================================
# TestProjectsEndpoint
# ===========================================================================


class TestProjectsEndpoint:
    """Integration tests for GET /api/projects — REQ-F-API-001."""

    def test_get_projects_returns_200(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)

        # Act
        response = client.get("/api/projects")

        # Assert
        assert response.status_code == 200

    def test_get_projects_returns_json_array(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)

        # Act
        body = client.get("/api/projects").json()

        # Assert
        assert isinstance(body, list)

    def test_get_projects_schema_fields_present(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()

        # Assert — all required fields present
        assert len(items) == 1
        item = items[0]
        for field in (
            "project_id",
            "name",
            "path",
            "state",
            "active_feature_count",
            "converged_feature_count",
            "last_event_at",
            "scan_duration_ms",
        ):
            assert field in item, f"Missing field: {field}"

    def test_get_projects_empty_root_returns_empty_list(self, tmp_path):
        # Arrange — no genesis projects in root
        client = _client_for(tmp_path)

        # Act
        body = client.get("/api/projects").json()

        # Assert
        assert body == []

    def test_get_projects_returns_correct_project_count(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("p1")
        make_project("p2")
        make_project("p3")
        client = _client_for(root)

        # Act
        body = client.get("/api/projects").json()

        # Assert
        assert len(body) == 3

    def test_get_projects_project_id_field(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("myproject")
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()

        # Assert
        assert items[0]["project_id"] == "myproject"

    def test_get_projects_name_field(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("named_proj")
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()

        # Assert
        assert items[0]["name"] == "named_proj"

    def test_get_projects_state_field_is_valid_enum(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)
        valid_states = {s.value for s in ProjectState}

        # Act
        items = client.get("/api/projects").json()

        # Assert
        assert items[0]["state"] in valid_states

    def test_get_projects_scan_duration_ms_non_negative(self, tmp_workspace):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()

        # Assert
        assert items[0]["scan_duration_ms"] >= 0.0

    def test_health_endpoint_returns_ok(self, tmp_path):
        # Arrange
        client = _client_for(tmp_path)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_get_projects_uninitialized_state_returned(self, tmp_workspace):
        # Arrange — .ai-workspace/ but no events.jsonl
        root, _ = tmp_workspace
        proj = root / "bare"
        (proj / ".ai-workspace").mkdir(parents=True)
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()

        # Assert
        assert len(items) == 1
        assert items[0]["state"] == ProjectState.UNINITIALIZED.value

    def test_get_projects_duplicate_names_disambiguated(self, tmp_workspace):
        # Arrange — two projects named "app" in different subdirs
        root, _ = tmp_workspace
        for subdir in ("team_a", "team_b"):
            proj = root / subdir / "app"
            (proj / ".ai-workspace" / "events").mkdir(parents=True)
            (proj / ".ai-workspace" / "events" / "events.jsonl").write_text(
                '{"event_type":"project_initialized"}\n'
            )
        client = _client_for(root)

        # Act
        items = client.get("/api/projects").json()
        ids = [item["project_id"] for item in items]

        # Assert — both discovered, ids are unique
        assert len(items) == 2
        assert len(set(ids)) == 2


# ===========================================================================
# TestReadOnlyInvariant
# ===========================================================================


class TestReadOnlyInvariant:
    """Verify zero filesystem writes (REQ-NFR-ARCH-002)."""

    def test_scan_workspace_no_writes(self, tmp_workspace, assert_no_writes):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")

        # Act — assert_no_writes fixture asserts after the test body
        _ = scan_workspace(root)

    def test_scan_workspace_multiple_projects_no_writes(
        self, tmp_workspace, assert_no_writes
    ):
        # Arrange
        root, make_project = tmp_workspace
        for name in ("a", "b", "c"):
            make_project(name)

        # Act
        _ = scan_workspace(root)

    def test_api_endpoint_no_writes(self, tmp_workspace, assert_no_writes):
        # Arrange
        root, make_project = tmp_workspace
        make_project("proj")
        client = _client_for(root)

        # Act
        client.get("/api/projects")

    def test_api_endpoint_empty_root_no_writes(self, tmp_path, assert_no_writes):
        # Arrange
        client = _client_for(tmp_path)

        # Act
        client.get("/api/projects")

    def test_uninitialized_workspace_no_writes(self, tmp_workspace, assert_no_writes):
        # Arrange — workspace without events.jsonl
        root, _ = tmp_workspace
        proj = root / "bare"
        (proj / ".ai-workspace").mkdir(parents=True)

        # Act
        _ = scan_workspace(root)
