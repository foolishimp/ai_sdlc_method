# Validates: REQ-F-LINEAGE-001, REQ-F-LINEAGE-002, REQ-F-LINEAGE-003, REQ-F-LINEAGE-004
"""Tests for traceability parser extensions — 4-column lineage + telemetry scanner."""

from pathlib import Path

import pytest

from genesis_monitor.parsers.traceability import (
    TraceabilityReport,
    parse_traceability,
    spec_inventory,
    telemetry_scanner,
)
from genesis_monitor.projections.traceability import build_traceability_view


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def project_with_telemetry(tmp_path: Path) -> Path:
    """Project root with .py files containing req= telemetry tags."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text(
        '# Implements: REQ-F-AUTH-001\n'
        'import logging\n'
        'logger = logging.getLogger(__name__)\n'
        'def login():\n'
        '    logger.info("login", req="REQ-F-AUTH-001")\n'
        '    logger.info("token", req=\'REQ-F-AUTH-002\')\n'
    )
    (src / "other.py").write_text(
        'def foo():\n'
        '    pass\n'  # no telemetry tags
    )
    return tmp_path


@pytest.fixture
def project_with_requirements_md(tmp_path: Path) -> Path:
    """Project root with .ai-workspace/spec/REQUIREMENTS.md."""
    spec_dir = tmp_path / ".ai-workspace" / "spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n"
        "## 1. Auth\n\n"
        "### REQ-F-AUTH-001: Login\n\n"
        "The system MUST support login.\n\n"
        "### REQ-F-AUTH-002: Logout\n\n"
        "The system MUST support logout.\n\n"
        "### REQ-NFR-PERF-001: Latency\n\n"
        "P99 < 200ms.\n"
    )
    return tmp_path


@pytest.fixture
def project_with_fallback_requirements_md(tmp_path: Path) -> Path:
    """Project root with specification/REQUIREMENTS.md (fallback path)."""
    spec_dir = tmp_path / "specification"
    spec_dir.mkdir()
    (spec_dir / "REQUIREMENTS.md").write_text(
        "### REQ-F-FALLBACK-001: Fallback key\n\n"
    )
    return tmp_path


@pytest.fixture
def full_project(tmp_path: Path) -> Path:
    """Complete project with code, tests, telemetry, and spec."""
    # Spec
    spec_dir = tmp_path / ".ai-workspace" / "spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "REQUIREMENTS.md").write_text(
        "### REQ-F-AUTH-001: Login\n\n"
        "### REQ-F-AUTH-002: Logout\n\n"
        "### REQ-F-ORPHAN-999: This one exists only in spec\n\n"  # uncovered
    )
    # Code with Implements tags
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text(
        "# Implements: REQ-F-AUTH-001\n"
        'def login(): logger.info("x", req="REQ-F-AUTH-001")\n'
    )
    # Test with Validates tag
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_auth.py").write_text(
        "# Validates: REQ-F-AUTH-001\n"
        "def test_login(): pass\n"
    )
    # An orphan — in code but not in spec
    (src / "orphan_module.py").write_text(
        "# Implements: REQ-F-ORPHAN-CODE-001\n"
        "def foo(): pass\n"
    )
    return tmp_path


# ── spec_inventory() ─────────────────────────────────────────────


class TestSpecInventory:
    def test_reads_ai_workspace_spec_first(self, project_with_requirements_md: Path):
        keys = spec_inventory(project_with_requirements_md)
        assert "REQ-F-AUTH-001" in keys
        assert "REQ-F-AUTH-002" in keys
        assert "REQ-NFR-PERF-001" in keys

    def test_returns_set_of_strings(self, project_with_requirements_md: Path):
        keys = spec_inventory(project_with_requirements_md)
        assert isinstance(keys, set)

    def test_fallback_to_specification_dir(self, project_with_fallback_requirements_md: Path):
        keys = spec_inventory(project_with_fallback_requirements_md)
        assert "REQ-F-FALLBACK-001" in keys

    def test_prefers_ai_workspace_over_specification(self, tmp_path: Path):
        # Both paths exist — .ai-workspace/spec/ takes precedence
        spec_dir = tmp_path / ".ai-workspace" / "spec"
        spec_dir.mkdir(parents=True)
        (spec_dir / "REQUIREMENTS.md").write_text("### REQ-F-PRIMARY-001: Primary\n")
        fallback_dir = tmp_path / "specification"
        fallback_dir.mkdir()
        (fallback_dir / "REQUIREMENTS.md").write_text("### REQ-F-FALLBACK-001: Fallback\n")
        keys = spec_inventory(tmp_path)
        assert "REQ-F-PRIMARY-001" in keys
        assert "REQ-F-FALLBACK-001" not in keys

    def test_returns_empty_set_if_no_file(self, tmp_path: Path):
        keys = spec_inventory(tmp_path)
        assert keys == set()

    def test_ignores_non_heading_req_references(self, tmp_path: Path):
        spec_dir = tmp_path / ".ai-workspace" / "spec"
        spec_dir.mkdir(parents=True)
        (spec_dir / "REQUIREMENTS.md").write_text(
            "See REQ-F-AUTH-001 for details.\n"  # body reference, not heading
            "### REQ-F-AUTH-002: Official\n"
        )
        keys = spec_inventory(tmp_path)
        assert "REQ-F-AUTH-001" not in keys
        assert "REQ-F-AUTH-002" in keys

    def test_empty_file_returns_empty_set(self, tmp_path: Path):
        spec_dir = tmp_path / ".ai-workspace" / "spec"
        spec_dir.mkdir(parents=True)
        (spec_dir / "REQUIREMENTS.md").write_text("")
        keys = spec_inventory(tmp_path)
        assert keys == set()

    def test_handles_nfr_prefix(self, tmp_path: Path):
        spec_dir = tmp_path / ".ai-workspace" / "spec"
        spec_dir.mkdir(parents=True)
        (spec_dir / "REQUIREMENTS.md").write_text("### REQ-NFR-PERF-001: Perf\n")
        keys = spec_inventory(tmp_path)
        assert "REQ-NFR-PERF-001" in keys


# ── telemetry_scanner() ───────────────────────────────────────────


class TestTelemetryScanner:
    def test_finds_double_quoted_tags(self, project_with_telemetry: Path):
        result = telemetry_scanner(project_with_telemetry)
        assert "REQ-F-AUTH-001" in result

    def test_finds_single_quoted_tags(self, project_with_telemetry: Path):
        result = telemetry_scanner(project_with_telemetry)
        assert "REQ-F-AUTH-002" in result

    def test_returns_relative_file_paths(self, project_with_telemetry: Path):
        result = telemetry_scanner(project_with_telemetry)
        paths = result["REQ-F-AUTH-001"]
        assert all(not p.startswith("/") for p in paths)

    def test_no_entry_for_files_without_tags(self, project_with_telemetry: Path):
        result = telemetry_scanner(project_with_telemetry)
        # other.py has no req= tags — we shouldn't see it
        all_paths = [p for paths in result.values() for p in paths]
        assert not any("other.py" in p for p in all_paths)

    def test_returns_dict_type(self, project_with_telemetry: Path):
        result = telemetry_scanner(project_with_telemetry)
        assert isinstance(result, dict)

    def test_file_paths_are_sorted(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "z_file.py").write_text('logger.info(req="REQ-F-X-001")\n')
        (src / "a_file.py").write_text('logger.info(req="REQ-F-X-001")\n')
        result = telemetry_scanner(tmp_path)
        paths = result["REQ-F-X-001"]
        assert paths == sorted(paths)

    def test_no_duplicate_file_paths(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "dup.py").write_text(
            'logger.info(req="REQ-F-X-001")\n'
            'logger.info(req="REQ-F-X-001")\n'  # same key twice in same file
        )
        result = telemetry_scanner(tmp_path)
        paths = result["REQ-F-X-001"]
        assert len(paths) == len(set(paths))

    def test_empty_project_returns_empty_dict(self, tmp_path: Path):
        result = telemetry_scanner(tmp_path)
        assert result == {}

    def test_skips_non_py_files(self, tmp_path: Path):
        (tmp_path / "log.txt").write_text('req="REQ-F-X-001"\n')
        result = telemetry_scanner(tmp_path)
        assert result == {}

    def test_multiple_keys_per_file(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "multi.py").write_text(
            'logger.info(req="REQ-F-A-001")\n'
            'logger.info(req="REQ-F-B-001")\n'
        )
        result = telemetry_scanner(tmp_path)
        assert "REQ-F-A-001" in result
        assert "REQ-F-B-001" in result


# ── TraceabilityReport new fields ────────────────────────────────


class TestTraceabilityReportDefaults:
    def test_new_fields_have_empty_defaults(self):
        r = TraceabilityReport()
        assert r.telemetry_coverage == {}
        assert r.spec_defined_keys == set()
        assert r.orphan_keys == set()
        assert r.uncovered_keys == set()
        assert r.telemetry_files_scanned == 0


# ── parse_traceability() integration ─────────────────────────────


class TestParseTraceabilityIntegration:
    def test_populates_telemetry_coverage(self, full_project: Path):
        report = parse_traceability(full_project)
        assert "REQ-F-AUTH-001" in report.telemetry_coverage

    def test_populates_spec_defined_keys(self, full_project: Path):
        report = parse_traceability(full_project)
        assert "REQ-F-AUTH-001" in report.spec_defined_keys
        assert "REQ-F-AUTH-002" in report.spec_defined_keys

    def test_computes_orphan_keys(self, full_project: Path):
        # REQ-F-ORPHAN-CODE-001 is in code but not in spec
        report = parse_traceability(full_project)
        assert "REQ-F-ORPHAN-CODE-001" in report.orphan_keys

    def test_computes_uncovered_keys(self, full_project: Path):
        # REQ-F-ORPHAN-999 is in spec but has no code/test/telemetry coverage
        report = parse_traceability(full_project)
        assert "REQ-F-ORPHAN-999" in report.uncovered_keys

    def test_known_key_not_orphan(self, full_project: Path):
        report = parse_traceability(full_project)
        assert "REQ-F-AUTH-001" not in report.orphan_keys

    def test_covered_key_not_uncovered(self, full_project: Path):
        report = parse_traceability(full_project)
        assert "REQ-F-AUTH-001" not in report.uncovered_keys

    def test_no_spec_file_produces_empty_keys(self, tmp_path: Path):
        # No REQUIREMENTS.md → orphan/uncovered sets empty
        src = tmp_path / "src"
        src.mkdir()
        (src / "code.py").write_text("# Implements: REQ-F-X-001\n")
        report = parse_traceability(tmp_path)
        assert report.spec_defined_keys == set()
        assert report.orphan_keys == set()
        assert report.uncovered_keys == set()


# ── build_traceability_view() ─────────────────────────────────────


class TestBuildTraceabilityView:
    def test_empty_report_returns_zero_counts(self):
        view = build_traceability_view([], None)
        s = view["summary"]
        assert s["spec_count"] == 0
        assert s["telemetry_count"] == 0
        assert s["orphan_count"] == 0
        assert s["uncovered_count"] == 0

    def test_row_includes_new_fields(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        auth_row = next(r for r in view["req_rows"] if r["req_key"] == "REQ-F-AUTH-001")
        assert "spec_defined" in auth_row
        assert "telemetry_files" in auth_row
        assert "has_telemetry" in auth_row
        assert "is_orphan" in auth_row
        assert "is_uncovered" in auth_row

    def test_spec_defined_true_for_spec_key(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        auth_row = next(r for r in view["req_rows"] if r["req_key"] == "REQ-F-AUTH-001")
        assert auth_row["spec_defined"] is True

    def test_orphan_row_flagged(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        orphan_row = next(r for r in view["req_rows"] if r["req_key"] == "REQ-F-ORPHAN-CODE-001")
        assert orphan_row["is_orphan"] is True
        assert orphan_row["status"] == "orphan"

    def test_uncovered_row_flagged(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        gap_row = next(r for r in view["req_rows"] if r["req_key"] == "REQ-F-ORPHAN-999")
        assert gap_row["is_uncovered"] is True
        assert gap_row["status"] == "uncovered"

    def test_summary_spec_count(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        assert view["summary"]["spec_count"] == 3  # AUTH-001, AUTH-002, ORPHAN-999

    def test_summary_orphan_count(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        assert view["summary"]["orphan_count"] >= 1

    def test_summary_uncovered_count(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        assert view["summary"]["uncovered_count"] >= 1

    def test_spec_keys_included_in_rows(self, full_project: Path):
        # REQ-F-AUTH-002 is in spec but has no code/test/telemetry — still appears in rows
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        keys = [r["req_key"] for r in view["req_rows"]]
        assert "REQ-F-AUTH-002" in keys

    def test_telemetry_files_populated(self, full_project: Path):
        report = parse_traceability(full_project)
        view = build_traceability_view([], report)
        auth_row = next(r for r in view["req_rows"] if r["req_key"] == "REQ-F-AUTH-001")
        assert auth_row["has_telemetry"] is True
        assert len(auth_row["telemetry_files"]) >= 1

    def test_backward_compat_no_spec_file(self, tmp_path: Path):
        # Project with code tags but no REQUIREMENTS.md — should not raise
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("# Implements: REQ-F-X-001\n")
        report = parse_traceability(tmp_path)
        view = build_traceability_view([], report)
        assert view["summary"]["spec_count"] == 0
        assert view["summary"]["orphan_count"] == 0
        assert view["summary"]["uncovered_count"] == 0
