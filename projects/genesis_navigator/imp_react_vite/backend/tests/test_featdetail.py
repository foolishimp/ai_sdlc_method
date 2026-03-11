"""Tests for the feature detail endpoint.

Validates: REQ-F-FEATDETAIL-001
"""

# Validates: REQ-F-FEATDETAIL-001

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genesis_nav.main import _config, create_app

app = create_app()
client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_events(project_path: Path, events: list[dict]) -> None:
    events_dir = project_path / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    (events_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
    )


FULL_FEATURE_YAML = """\
feature:
  id: REQ-F-AUTH-001
  title: "User Authentication"
  status: converged
  priority: critical

satisfies:
  - REQ-F-AUTH-001
  - REQ-BR-001

trajectory:
  code_unit_tests:
    status: converged
    iteration: 2
    converged_at: "2026-03-12T10:00:00Z"

constraints:
  acceptance_criteria:
    - "Login endpoint returns JWT on valid credentials"
    - "Login endpoint returns 401 on invalid credentials"
    - "Token expiry is configurable"
"""

EVENTS = [
    {
        "event_type": "edge_started",
        "timestamp": "2026-03-12T09:00:00Z",
        "feature": "REQ-F-AUTH-001",
        "edge": "code↔unit_tests",
    },
    {
        "event_type": "iteration_completed",
        "timestamp": "2026-03-12T09:30:00Z",
        "feature": "REQ-F-AUTH-001",
        "edge": "code↔unit_tests",
        "delta": 2,
        "iteration": 1,
    },
    {
        "event_type": "iteration_completed",
        "timestamp": "2026-03-12T09:45:00Z",
        "feature": "REQ-F-AUTH-001",
        "edge": "code↔unit_tests",
        "delta": 0,
        "iteration": 2,
    },
    {
        "event_type": "edge_converged",
        "timestamp": "2026-03-12T10:00:00Z",
        "feature_id": "REQ-F-AUTH-001",
        "edge": "code↔unit_tests",
    },
]


# ---------------------------------------------------------------------------
# Test: basic endpoint availability
# ---------------------------------------------------------------------------

class TestFeatureDetailEndpointBasic:
    def test_404_unknown_project(self, tmp_path):
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/no-such-project/features/REQ-F-AUTH-001")
        assert resp.status_code == 404

    def test_404_unknown_feature(self, tmp_path):
        project = tmp_path / "myproject" / ".ai-workspace" / "events"
        project.mkdir(parents=True)
        (project / "events.jsonl").write_text(
            '{"event_type": "project_initialized", "timestamp": "2026-01-01T00:00:00Z"}\n'
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/myproject/features/REQ-F-NONEXISTENT-001")
        assert resp.status_code == 404
        assert "REQ-F-NONEXISTENT-001" in resp.json()["detail"]

    def test_200_with_valid_feature(self, tmp_path):
        project = tmp_path / "proj"
        _write_events(project, [])
        _write_feature(
            project / ".ai-workspace" / "features" / "active" / "REQ-F-AUTH-001.yml",
            FULL_FEATURE_YAML,
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-AUTH-001")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test: response shape
# ---------------------------------------------------------------------------

class TestFeatureDetailResponseShape:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        project = tmp_path / "proj"
        _write_events(project, EVENTS)
        _write_feature(
            project / ".ai-workspace" / "features" / "active" / "REQ-F-AUTH-001.yml",
            FULL_FEATURE_YAML,
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-AUTH-001")
        assert resp.status_code == 200
        self.data = resp.json()

    def test_has_feature_id(self):
        assert self.data["feature_id"] == "REQ-F-AUTH-001"

    def test_has_title(self):
        assert self.data["title"] == "User Authentication"

    def test_has_status(self):
        assert self.data["status"] == "converged"

    def test_has_hamiltonian(self):
        h = self.data["hamiltonian"]
        assert "H" in h
        assert "T" in h
        assert "V" in h
        assert "flat" in h

    def test_hamiltonian_t_counts_iterations(self):
        # 2 iteration_completed events for REQ-F-AUTH-001
        assert self.data["hamiltonian"]["T"] == 2

    def test_hamiltonian_v_zero_after_converge(self):
        # edge_converged follows → V should be 0
        assert self.data["hamiltonian"]["V"] == 0

    def test_has_trajectory(self):
        assert isinstance(self.data["trajectory"], list)

    def test_trajectory_edge_shape(self):
        edge = self.data["trajectory"][0]
        assert "edge" in edge
        assert "status" in edge
        assert "iteration" in edge

    def test_trajectory_converged_edge(self):
        edge = self.data["trajectory"][0]
        assert edge["status"] == "converged"
        assert edge["iteration"] == 2

    def test_has_satisfies(self):
        assert self.data["satisfies"] == ["REQ-F-AUTH-001", "REQ-BR-001"]

    def test_has_acceptance_criteria(self):
        ac = self.data["acceptance_criteria"]
        assert len(ac) == 3
        assert "JWT" in ac[0]

    def test_no_error(self):
        assert self.data["error"] is None


# ---------------------------------------------------------------------------
# Test: nested feature YAML format (standard Genesis format)
# ---------------------------------------------------------------------------

class TestFeatureDetailNestedYaml:
    def test_reads_satisfies_from_nested_yaml(self, tmp_path):
        project = tmp_path / "proj"
        _write_events(project, [])
        _write_feature(
            project / ".ai-workspace" / "features" / "active" / "REQ-F-SCAN-001.yml",
            """\
feature:
  id: REQ-F-SCAN-001
  title: "Workspace Scanner"
  status: converged

satisfies:
  - REQ-F-NAV-001
  - REQ-F-NAV-002

constraints:
  acceptance_criteria:
    - "Scans root directory"
    - "Prunes node_modules"
""",
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-SCAN-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["satisfies"] == ["REQ-F-NAV-001", "REQ-F-NAV-002"]
        assert len(data["acceptance_criteria"]) == 2

    def test_feature_with_no_satisfies_returns_empty_list(self, tmp_path):
        project = tmp_path / "proj"
        _write_events(project, [])
        _write_feature(
            project / ".ai-workspace" / "features" / "active" / "REQ-F-MIN-001.yml",
            "feature:\n  id: REQ-F-MIN-001\n  title: Minimal\n  status: pending\n",
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-MIN-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["satisfies"] == []
        assert data["acceptance_criteria"] == []


# ---------------------------------------------------------------------------
# Test: read-only — no filesystem writes (REQ-NFR-ARCH-002)
# ---------------------------------------------------------------------------

class TestFeatureDetailReadOnly:
    def test_no_writes_on_success(self, tmp_path, assert_no_writes):
        project = tmp_path / "proj"
        _write_events(project, [])
        _write_feature(
            project / ".ai-workspace" / "features" / "active" / "REQ-F-AUTH-001.yml",
            FULL_FEATURE_YAML,
        )
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-AUTH-001")
        assert resp.status_code == 200
        # assert_no_writes fixture asserts zero writes on teardown

    def test_no_writes_on_404(self, tmp_path, assert_no_writes):
        project = tmp_path / "proj" / ".ai-workspace" / "events"
        project.mkdir(parents=True)
        (project / "events.jsonl").write_text("")
        _config["root_dir"] = str(tmp_path)
        resp = client.get("/api/projects/proj/features/REQ-F-MISSING-001")
        assert resp.status_code == 404
        # assert_no_writes fixture asserts zero writes on teardown
