"""Tests for REQ-F-GAPENGINE-001: Gap Analysis Engine.

Covers spec key extraction, per-layer gap computation, health signal,
and the GET /api/projects/{project_id}/gaps endpoint.
"""

# Validates: REQ-F-GAP-001
# Validates: REQ-F-GAP-002
# Validates: REQ-F-GAP-003
# Validates: REQ-F-GAP-004
# Validates: REQ-F-API-003

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient

import genesis_nav.main as _main
from genesis_nav.analyzers.gap_analyzer import (
    analyze_gaps,
    compute_gap_layer,
    compute_health_signal,
    extract_code_req_keys,
    extract_spec_req_keys,
    extract_telemetry_req_keys,
    extract_test_req_keys,
)
from genesis_nav.main import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal Genesis workspace under tmp_path/proj."""
    project = tmp_path / "proj"
    events_dir = project / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True)
    (events_dir / "events.jsonl").write_text(
        '{"event_type":"project_initialized","timestamp":"2026-01-01T00:00:00Z"}\n'
    )
    return project


# ---------------------------------------------------------------------------
# TestGapAnalyzer — unit tests for the analyzer functions
# ---------------------------------------------------------------------------


class TestGapAnalyzer:
    """Tests for genesis_nav.analyzers.gap_analyzer."""

    # ---- extract_spec_req_keys ----

    def test_extract_spec_req_keys_finds_keys(self, tmp_path: Path) -> None:
        """Extracts REQ keys from REQUIREMENTS.md."""
        project = tmp_path / "proj"
        _write(
            project / "specification" / "requirements" / "REQUIREMENTS.md",
            "# Requirements\n\nREQ-F-AUTH-001: login\nREQ-F-AUTH-002: logout\nREQ-F-DATA-001: storage\n",
        )
        keys = extract_spec_req_keys(project)
        assert keys == {"REQ-F-AUTH-001", "REQ-F-AUTH-002", "REQ-F-DATA-001"}

    def test_extract_spec_req_keys_missing_file(self, tmp_path: Path) -> None:
        """Returns empty set when REQUIREMENTS.md does not exist."""
        keys = extract_spec_req_keys(tmp_path / "no-proj")
        assert keys == set()

    def test_extract_spec_req_keys_no_duplicates(self, tmp_path: Path) -> None:
        """Duplicate key occurrences collapse to a single entry."""
        project = tmp_path / "proj"
        _write(
            project / "specification" / "requirements" / "REQUIREMENTS.md",
            "REQ-F-AUTH-001 and REQ-F-AUTH-001 again\n",
        )
        keys = extract_spec_req_keys(project)
        assert len(keys) == 1

    # ---- extract_code_req_keys ----

    def test_extract_code_req_keys_finds_tagged_files(self, tmp_path: Path) -> None:
        """Finds # Implements: tags in source files."""
        project = tmp_path / "proj"
        _write(
            project / "src" / "auth.py",
            "# Implements: REQ-F-AUTH-001\ndef login(): pass\n",
        )
        result = extract_code_req_keys(project)
        assert "REQ-F-AUTH-001" in result
        assert any("auth.py" in f for f in result["REQ-F-AUTH-001"])

    def test_extract_code_req_keys_excludes_test_dirs(self, tmp_path: Path) -> None:
        """Does not scan files inside tests/ directories."""
        project = tmp_path / "proj"
        _write(
            project / "tests" / "test_auth.py",
            "# Implements: REQ-F-AUTH-001\n",
        )
        result = extract_code_req_keys(project)
        assert "REQ-F-AUTH-001" not in result

    def test_extract_code_req_keys_multiple_keys_one_file(self, tmp_path: Path) -> None:
        """Multiple Implements tags in one file are all captured."""
        project = tmp_path / "proj"
        _write(
            project / "src" / "multi.py",
            "# Implements: REQ-F-AUTH-001\n# Implements: REQ-F-DATA-001\n",
        )
        result = extract_code_req_keys(project)
        assert "REQ-F-AUTH-001" in result
        assert "REQ-F-DATA-001" in result

    def test_extract_code_req_keys_empty_project(self, tmp_path: Path) -> None:
        """Returns empty dict when no Implements tags exist."""
        result = extract_code_req_keys(tmp_path / "empty")
        assert result == {}

    # ---- extract_test_req_keys ----

    def test_extract_test_req_keys_finds_validates_in_test_dir(self, tmp_path: Path) -> None:
        """Finds # Validates: tags inside tests/ directory."""
        project = tmp_path / "proj"
        _write(
            project / "tests" / "test_auth.py",
            "# Validates: REQ-F-AUTH-001\ndef test_login(): pass\n",
        )
        result = extract_test_req_keys(project)
        assert "REQ-F-AUTH-001" in result

    def test_extract_test_req_keys_finds_test_prefix_file(self, tmp_path: Path) -> None:
        """Finds # Validates: in a file named test_*.py anywhere."""
        project = tmp_path / "proj"
        _write(
            project / "src" / "test_helpers.py",
            "# Validates: REQ-F-DATA-001\n",
        )
        result = extract_test_req_keys(project)
        assert "REQ-F-DATA-001" in result

    def test_extract_test_req_keys_ignores_source_files(self, tmp_path: Path) -> None:
        """Does not pick up # Validates: tags from non-test source files."""
        project = tmp_path / "proj"
        _write(
            project / "src" / "auth.py",
            "# Validates: REQ-F-AUTH-001\n",
        )
        result = extract_test_req_keys(project)
        assert "REQ-F-AUTH-001" not in result

    # ---- extract_telemetry_req_keys ----

    def test_extract_telemetry_req_keys_finds_req_param(self, tmp_path: Path) -> None:
        """Finds req="REQ-*" telemetry annotations in source files."""
        project = tmp_path / "proj"
        _write(
            project / "src" / "api.py",
            'logger.info("login", req="REQ-F-AUTH-001", latency_ms=12)\n',
        )
        result = extract_telemetry_req_keys(project)
        assert "REQ-F-AUTH-001" in result

    def test_extract_telemetry_req_keys_empty_when_no_tags(self, tmp_path: Path) -> None:
        """Returns empty dict when no telemetry annotations exist."""
        result = extract_telemetry_req_keys(tmp_path / "empty")
        assert result == {}

    # ---- compute_gap_layer ----

    def test_compute_gap_layer_full_coverage(self) -> None:
        """coverage_pct=100 and gap_count=0 when all spec keys are tagged."""
        spec = {"REQ-F-AUTH-001", "REQ-F-AUTH-002"}
        tagged = {"REQ-F-AUTH-001": ["a.py"], "REQ-F-AUTH-002": ["b.py"]}
        layer = compute_gap_layer(spec, tagged, "CODE_GAP")
        assert layer["gap_count"] == 0
        assert layer["coverage_pct"] == 100.0
        assert layer["gaps"] == []

    def test_compute_gap_layer_partial_coverage(self) -> None:
        """Untagged keys appear as gap items."""
        spec = {"REQ-F-AUTH-001", "REQ-F-AUTH-002", "REQ-F-DATA-001"}
        tagged = {"REQ-F-AUTH-001": ["a.py"]}
        layer = compute_gap_layer(spec, tagged, "CODE_GAP")
        assert layer["gap_count"] == 2
        assert layer["coverage_pct"] == pytest.approx(33.3, abs=0.2)
        gap_keys = {g["req_key"] for g in layer["gaps"]}
        assert gap_keys == {"REQ-F-AUTH-002", "REQ-F-DATA-001"}

    def test_compute_gap_layer_zero_coverage(self) -> None:
        """gap_count equals spec key count when nothing is tagged."""
        spec = {"REQ-F-AUTH-001", "REQ-F-AUTH-002"}
        layer = compute_gap_layer(spec, {}, "TEST_GAP")
        assert layer["gap_count"] == 2
        assert layer["coverage_pct"] == 0.0
        assert all(g["gap_type"] == "TEST_GAP" for g in layer["gaps"])

    def test_compute_gap_layer_empty_spec(self) -> None:
        """Empty spec keys → coverage 100%, zero gaps."""
        layer = compute_gap_layer(set(), {}, "CODE_GAP")
        assert layer["gap_count"] == 0
        assert layer["coverage_pct"] == 100.0

    # ---- compute_health_signal ----

    def test_health_signal_green(self) -> None:
        assert compute_health_signal(0, 0) == "GREEN"

    def test_health_signal_amber_boundary_low(self) -> None:
        assert compute_health_signal(1, 0) == "AMBER"

    def test_health_signal_amber_boundary_high(self) -> None:
        assert compute_health_signal(3, 2) == "AMBER"

    def test_health_signal_red(self) -> None:
        assert compute_health_signal(4, 3) == "RED"

    def test_health_signal_red_large(self) -> None:
        assert compute_health_signal(10, 10) == "RED"

    # ---- analyze_gaps (integration) ----

    def test_analyze_gaps_returns_correct_structure(self, tmp_path: Path) -> None:
        """analyze_gaps returns a dict with all required keys."""
        project = _make_project(tmp_path)
        result = analyze_gaps(project)
        assert "project_id" in result
        assert "computed_at" in result
        assert "health_signal" in result
        assert "layer_1" in result
        assert "layer_2" in result
        assert "layer_3" in result

    def test_analyze_gaps_no_spec_file(self, tmp_path: Path) -> None:
        """Without REQUIREMENTS.md all layers have 100% coverage (nothing to cover)."""
        project = _make_project(tmp_path)
        result = analyze_gaps(project)
        assert result["layer_1"]["coverage_pct"] == 100.0
        assert result["health_signal"] == "GREEN"

    def test_analyze_gaps_detects_code_gaps(self, tmp_path: Path) -> None:
        """Layer 1 reports gaps for untagged spec keys."""
        project = _make_project(tmp_path)
        _write(
            project / "specification" / "requirements" / "REQUIREMENTS.md",
            "REQ-F-AUTH-001\nREQ-F-AUTH-002\n",
        )
        # Only tag one of the two keys
        _write(project / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        result = analyze_gaps(project)
        assert result["layer_1"]["gap_count"] == 1
        assert result["layer_1"]["gaps"][0]["req_key"] == "REQ-F-AUTH-002"

    def test_analyze_gaps_detects_test_gaps(self, tmp_path: Path) -> None:
        """Layer 2 reports gaps for unvalidated spec keys."""
        project = _make_project(tmp_path)
        _write(
            project / "specification" / "requirements" / "REQUIREMENTS.md",
            "REQ-F-AUTH-001\n",
        )
        # No test file with Validates tag
        result = analyze_gaps(project)
        assert result["layer_2"]["gap_count"] == 1

    def test_analyze_gaps_health_red_when_many_gaps(self, tmp_path: Path) -> None:
        """health_signal is RED when combined layer1+layer2 gaps exceed 5."""
        project = _make_project(tmp_path)
        req_keys = "\n".join(f"REQ-F-TEST-{i:03d}" for i in range(1, 8))
        _write(
            project / "specification" / "requirements" / "REQUIREMENTS.md",
            req_keys + "\n",
        )
        result = analyze_gaps(project)
        assert result["health_signal"] == "RED"


# ---------------------------------------------------------------------------
# TestGapsEndpoint — HTTP tests for GET /api/projects/{id}/gaps
# ---------------------------------------------------------------------------


class TestGapsEndpoint:
    """Tests for GET /api/projects/{project_id}/gaps."""

    @pytest.fixture(autouse=True)
    def _app(self) -> None:
        self._client = TestClient(create_app())

    def _set_root(self, path: Path) -> None:
        _main._config["root_dir"] = str(path)

    def test_returns_200_for_existing_project(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """GET /api/projects/{id}/gaps returns 200."""
        root, make_project = tmp_workspace
        make_project("alpha")
        self._set_root(root)
        resp = self._client.get("/api/projects/alpha/gaps")
        assert resp.status_code == 200

    def test_response_has_gap_report_schema(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """Response contains all GapReport required fields."""
        root, make_project = tmp_workspace
        make_project("beta")
        self._set_root(root)
        data = self._client.get("/api/projects/beta/gaps").json()
        assert data["project_id"] == "beta"
        assert "computed_at" in data
        assert data["health_signal"] in ("GREEN", "AMBER", "RED")
        for layer_key in ("layer_1", "layer_2", "layer_3"):
            assert layer_key in data
            layer = data[layer_key]
            assert "gap_count" in layer
            assert "coverage_pct" in layer
            assert "gaps" in layer

    def test_returns_404_for_unknown_project(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """GET /api/projects/{id}/gaps returns 404 for unknown project_id."""
        root, _ = tmp_workspace
        self._set_root(root)
        resp = self._client.get("/api/projects/does-not-exist/gaps")
        assert resp.status_code == 404

    def test_green_health_for_empty_spec(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """Project with no REQUIREMENTS.md gets GREEN health (nothing to cover)."""
        root, make_project = tmp_workspace
        make_project("gamma")
        self._set_root(root)
        data = self._client.get("/api/projects/gamma/gaps").json()
        assert data["health_signal"] == "GREEN"
        assert data["layer_1"]["gap_count"] == 0

    def test_gap_items_have_correct_schema(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """Gap items in the response include req_key, gap_type, files, suggested_command."""
        root, make_project = tmp_workspace
        project = make_project("delta")
        (project / "specification" / "requirements").mkdir(parents=True)
        (project / "specification" / "requirements" / "REQUIREMENTS.md").write_text(
            "REQ-F-AUTH-001\n", encoding="utf-8"
        )
        self._set_root(root)
        data = self._client.get("/api/projects/delta/gaps").json()
        gaps = data["layer_1"]["gaps"]
        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["req_key"] == "REQ-F-AUTH-001"
        assert gap["gap_type"] == "CODE_GAP"
        assert isinstance(gap["files"], list)
        # suggested_command may be None
        assert "suggested_command" in gap

    def test_covered_key_not_in_gaps(
        self, tmp_workspace: tuple[Path, Callable]
    ) -> None:
        """A tagged REQ key does not appear in the gap list."""
        root, make_project = tmp_workspace
        project = make_project("epsilon")
        (project / "specification" / "requirements").mkdir(parents=True)
        (project / "specification" / "requirements" / "REQUIREMENTS.md").write_text(
            "REQ-F-AUTH-001\nREQ-F-AUTH-002\n", encoding="utf-8"
        )
        src = project / "src"
        src.mkdir(parents=True)
        (src / "auth.py").write_text("# Implements: REQ-F-AUTH-001\n", encoding="utf-8")
        self._set_root(root)
        data = self._client.get("/api/projects/epsilon/gaps").json()
        gap_keys = {g["req_key"] for g in data["layer_1"]["gaps"]}
        assert "REQ-F-AUTH-001" not in gap_keys
        assert "REQ-F-AUTH-002" in gap_keys
