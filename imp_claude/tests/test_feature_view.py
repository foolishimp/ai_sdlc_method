# Validates: REQ-TOOL-009 (Feature Views)
"""Tests for feature_view.py — cross-artifact REQ key tracer."""

from pathlib import Path

import pytest

from genesis.feature_view import (
    ArtifactMatch,
    FeatureView,
    build_all_feature_views,
    build_feature_view,
    coverage_report,
    scan_for_req_key,
    _classify_line_tag,
    _infer_stage,
    EXPECTED_STAGES,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── _classify_line_tag ────────────────────────────────────────────────────────


class TestClassifyLineTag:
    def test_implements_tag(self) -> None:
        tags = _classify_line_tag("# Implements: REQ-F-AUTH-001")
        assert "implements" in tags

    def test_validates_tag(self) -> None:
        tags = _classify_line_tag("# Validates: REQ-F-AUTH-001")
        assert "validates" in tags

    def test_telemetry_tag_double_quote(self) -> None:
        tags = _classify_line_tag('logger.info("login", req="REQ-F-AUTH-001")')
        assert "telemetry" in tags

    def test_telemetry_tag_single_quote(self) -> None:
        tags = _classify_line_tag("log.info(req='REQ-F-AUTH-001')")
        assert "telemetry" in tags

    def test_gherkin_tag(self) -> None:
        tags = _classify_line_tag("  @REQ-F-AUTH-001")
        assert "gherkin_tag" in tags

    def test_bare_mention(self) -> None:
        tags = _classify_line_tag("See REQ-F-AUTH-001 for details.")
        assert "bare" in tags

    def test_multiple_tags_on_one_line(self) -> None:
        # Unlikely but possible
        tags = _classify_line_tag("# Implements: REQ-F-AUTH-001 # Validates: REQ-F-AUTH-001")
        assert "implements" in tags
        assert "validates" in tags


# ── _infer_stage ──────────────────────────────────────────────────────────────


class TestInferStage:
    def test_spec_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "specification" / "requirements.md"
        assert _infer_stage(f, tmp_path) == "spec"

    def test_design_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "imp_claude" / "design" / "DESIGN.md"
        assert _infer_stage(f, tmp_path) == "design"

    def test_tests_dir(self, tmp_path: Path) -> None:
        f = tmp_path / "tests" / "test_auth.py"
        assert _infer_stage(f, tmp_path) == "tests"

    def test_feature_file_is_uat(self, tmp_path: Path) -> None:
        f = tmp_path / "tests" / "uat" / "auth.feature"
        assert _infer_stage(f, tmp_path) == "uat"

    def test_code_by_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "auth.py"
        assert _infer_stage(f, tmp_path) == "code"


# ── scan_for_req_key ──────────────────────────────────────────────────────────


class TestScanForReqKey:
    def test_finds_implements_in_py_file(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\ndef login(): pass\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 1
        assert "implements" in matches[0].tag_types

    def test_finds_validates_in_test_file(self, tmp_path: Path) -> None:
        write(tmp_path / "tests" / "test_auth.py", "# Validates: REQ-F-AUTH-001\ndef test_login(): pass\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 1
        assert "validates" in matches[0].tag_types

    def test_finds_bare_mention_in_md(self, tmp_path: Path) -> None:
        write(tmp_path / "spec.md", "# Requirements\nREQ-F-AUTH-001: User auth\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 1

    def test_no_false_positives_different_key(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "api.py", "# Implements: REQ-F-API-001\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 0

    def test_multiple_files_multiple_matches(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        write(tmp_path / "tests" / "test_auth.py", "# Validates: REQ-F-AUTH-001\n")
        write(tmp_path / "spec" / "requirements.md", "REQ-F-AUTH-001 defined here\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 3

    def test_correct_line_numbers(self, tmp_path: Path) -> None:
        write(tmp_path / "auth.py", "line1\nline2\n# Implements: REQ-F-AUTH-001\nline4\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 1
        assert 3 in matches[0].line_numbers

    def test_skips_pycache_and_git(self, tmp_path: Path) -> None:
        write(tmp_path / "__pycache__" / "auth.pyc", "REQ-F-AUTH-001")
        write(tmp_path / ".git" / "COMMIT_EDITMSG", "REQ-F-AUTH-001")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert len(matches) == 0

    def test_handles_empty_directory(self, tmp_path: Path) -> None:
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path)
        assert matches == []

    def test_relative_paths_from_project_root(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        matches = scan_for_req_key("REQ-F-AUTH-001", tmp_path, project_root=tmp_path)
        assert not matches[0].rel_path.startswith("/")  # relative, not absolute


# ── build_feature_view ────────────────────────────────────────────────────────


class TestBuildFeatureView:
    def test_empty_project_all_stages_missing(self, tmp_path: Path) -> None:
        view = build_feature_view("REQ-F-AUTH-001", tmp_path)
        assert view.req_key == "REQ-F-AUTH-001"
        assert view.coverage == 0
        assert sorted(view.missing_stages) == sorted(EXPECTED_STAGES)

    def test_coverage_counts_unique_stages(self, tmp_path: Path) -> None:
        write(tmp_path / "specification" / "req.md", "REQ-F-AUTH-001 defined\n")
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        write(tmp_path / "tests" / "test_auth.py", "# Validates: REQ-F-AUTH-001\n")
        view = build_feature_view("REQ-F-AUTH-001", tmp_path)
        assert view.coverage >= 2

    def test_summary_format(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        view = build_feature_view("REQ-F-AUTH-001", tmp_path)
        summary = view.summary()
        assert "REQ-F-AUTH-001" in summary
        assert "/" in summary

    def test_custom_expected_stages(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        view = build_feature_view("REQ-F-AUTH-001", tmp_path, expected_stages=["code"])
        # Only "code" expected → if found → 1/1
        assert view.total_stages == 1

    def test_coverage_pct_calculation(self, tmp_path: Path) -> None:
        # 2 stages present out of 5 expected → 40%
        write(tmp_path / "specification" / "req.md", "REQ-F-AUTH-001\n")
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        view = build_feature_view("REQ-F-AUTH-001", tmp_path)
        assert 0.0 <= view.coverage_pct <= 100.0

    def test_missing_stages_are_those_not_found(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        view = build_feature_view("REQ-F-AUTH-001", tmp_path, expected_stages=["code", "tests"])
        assert "code" not in view.missing_stages
        assert "tests" in view.missing_stages


# ── build_all_feature_views ───────────────────────────────────────────────────


class TestBuildAllFeatureViews:
    def test_returns_view_per_key(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        write(tmp_path / "src" / "api.py", "# Implements: REQ-F-API-001\n")
        views = build_all_feature_views(["REQ-F-AUTH-001", "REQ-F-API-001"], tmp_path)
        assert "REQ-F-AUTH-001" in views
        assert "REQ-F-API-001" in views

    def test_empty_keys_returns_empty(self, tmp_path: Path) -> None:
        assert build_all_feature_views([], tmp_path) == {}


# ── coverage_report ───────────────────────────────────────────────────────────


class TestCoverageReport:
    def test_sorted_by_coverage_ascending(self, tmp_path: Path) -> None:
        write(tmp_path / "src" / "auth.py", "# Implements: REQ-F-AUTH-001\n")
        # AUTH has some coverage, API has none
        views = build_all_feature_views(["REQ-F-AUTH-001", "REQ-F-API-001"], tmp_path)
        report = coverage_report(views)
        assert len(report) == 2
        # Least covered first
        assert report[0]["coverage_pct"] <= report[1]["coverage_pct"]

    def test_report_fields_present(self, tmp_path: Path) -> None:
        views = build_all_feature_views(["REQ-F-AUTH-001"], tmp_path)
        report = coverage_report(views)
        row = report[0]
        assert "req_key" in row
        assert "coverage" in row
        assert "total_stages" in row
        assert "coverage_pct" in row
        assert "stages_present" in row
        assert "missing_stages" in row
        assert "summary" in row
