# Validates: REQ-EVOL-002 (Feature Display Tools Must JOIN Spec and Workspace)
"""Tests for compute_spec_workspace_join() — spec+workspace JOIN categorisation."""

import textwrap
from pathlib import Path

import pytest
import yaml

from genesis.workspace_state import (
    compute_spec_workspace_join,
    extract_spec_feature_ids,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Minimal workspace with active + completed feature directories."""
    (tmp_path / ".ai-workspace" / "features" / "active").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "features" / "completed").mkdir(parents=True)
    return tmp_path


def _write_feature(workspace: Path, fid: str, subdir: str = "active") -> Path:
    """Write a minimal feature YAML and return its path."""
    path = (
        workspace / ".ai-workspace" / "features" / subdir / f"{fid}.yml"
    )
    path.write_text(yaml.dump({"feature": fid, "status": "pending"}))
    return path


def _write_spec(workspace: Path, content: str) -> Path:
    """Write a mock FEATURE_VECTORS.md to specification/features/."""
    spec_dir = workspace / "specification" / "features"
    spec_dir.mkdir(parents=True, exist_ok=True)
    path = spec_dir / "FEATURE_VECTORS.md"
    path.write_text(content)
    return path


# ── extract_spec_feature_ids ─────────────────────────────────────────────────


class TestExtractSpecFeatureIds:
    def test_extracts_req_f_ids(self, tmp_path: Path) -> None:
        spec = tmp_path / "FEATURE_VECTORS.md"
        spec.write_text(
            "### REQ-F-ENGINE-001: Asset Graph Engine\n"
            "### REQ-F-EVAL-001: Evaluator Framework\n"
            "### REQ-F-CTX-001: Context Management\n"
        )
        ids = extract_spec_feature_ids(spec)
        assert ids == ["REQ-F-CTX-001", "REQ-F-ENGINE-001", "REQ-F-EVAL-001"]

    def test_deduplicates(self, tmp_path: Path) -> None:
        spec = tmp_path / "FEATURE_VECTORS.md"
        spec.write_text(
            "REQ-F-ENGINE-001 mentioned here\n"
            "REQ-F-ENGINE-001 mentioned again\n"
            "REQ-F-EVAL-001 once\n"
        )
        ids = extract_spec_feature_ids(spec)
        assert ids.count("REQ-F-ENGINE-001") == 1

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        ids = extract_spec_feature_ids(tmp_path / "nonexistent.md")
        assert ids == []

    def test_does_not_extract_non_req_f_patterns(self, tmp_path: Path) -> None:
        spec = tmp_path / "FEATURE_VECTORS.md"
        spec.write_text(
            "REQ-GRAPH-001 should not match\n"
            "REQ-EVAL-001 should not match\n"
            "REQ-F-ENGINE-001 should match\n"
        )
        ids = extract_spec_feature_ids(spec)
        assert ids == ["REQ-F-ENGINE-001"]

    def test_sorted_output(self, tmp_path: Path) -> None:
        spec = tmp_path / "FEATURE_VECTORS.md"
        spec.write_text("REQ-F-ZZZ-001\nREQ-F-AAA-001\nREQ-F-MMM-001\n")
        ids = extract_spec_feature_ids(spec)
        assert ids == sorted(ids)


# ── compute_spec_workspace_join ───────────────────────────────────────────────


class TestComputeSpecWorkspaceJoin:
    def test_all_active_when_spec_and_workspace_match(self, workspace: Path) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\n")
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        _write_feature(workspace, "REQ-F-EVAL-001", "active")

        result = compute_spec_workspace_join(workspace)

        assert result["spec_readable"] is True
        assert result["spec_count"] == 2
        assert set(result["active"]) == {"REQ-F-ENGINE-001", "REQ-F-EVAL-001"}
        assert result["pending"] == []
        assert result["orphan"] == []
        assert result["completed"] == []

    def test_pending_when_spec_feature_absent_from_workspace(
        self, workspace: Path
    ) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\nREQ-F-CTX-001\n")
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        # REQ-F-EVAL-001 and REQ-F-CTX-001 not in workspace

        result = compute_spec_workspace_join(workspace)

        assert set(result["pending"]) == {"REQ-F-EVAL-001", "REQ-F-CTX-001"}
        assert result["active"] == ["REQ-F-ENGINE-001"]
        assert result["orphan"] == []

    def test_orphan_when_workspace_feature_absent_from_spec(
        self, workspace: Path
    ) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\n")
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        _write_feature(workspace, "REQ-F-STALE-001", "active")  # not in spec

        result = compute_spec_workspace_join(workspace)

        assert result["orphan"] == ["REQ-F-STALE-001"]
        assert result["active"] == ["REQ-F-ENGINE-001"]
        assert result["pending"] == []

    def test_completed_from_completed_directory(self, workspace: Path) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\n")
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        _write_feature(workspace, "REQ-F-EVAL-001", "completed")

        result = compute_spec_workspace_join(workspace)

        assert result["active"] == ["REQ-F-ENGINE-001"]
        assert result["completed"] == ["REQ-F-EVAL-001"]
        assert result["pending"] == []

    def test_spec_unreadable_returns_empty_spec(self, workspace: Path) -> None:
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        # no spec file written

        result = compute_spec_workspace_join(workspace)

        assert result["spec_readable"] is False
        assert result["spec_count"] == 0
        assert result["orphan"] == ["REQ-F-ENGINE-001"]

    def test_explicit_spec_path_override(self, workspace: Path, tmp_path: Path) -> None:
        custom_spec = tmp_path / "custom_features.md"
        custom_spec.write_text("REQ-F-CUSTOM-001\n")
        _write_feature(workspace, "REQ-F-CUSTOM-001", "active")

        result = compute_spec_workspace_join(workspace, spec_features_path=custom_spec)

        assert result["active"] == ["REQ-F-CUSTOM-001"]
        assert result["pending"] == []
        assert result["orphan"] == []

    def test_workspace_count_reflects_total(self, workspace: Path) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\n")
        _write_feature(workspace, "REQ-F-ENGINE-001", "active")
        _write_feature(workspace, "REQ-F-EVAL-001", "completed")

        result = compute_spec_workspace_join(workspace)

        assert result["workspace_count"] == 2

    def test_empty_workspace_all_pending(self, workspace: Path) -> None:
        _write_spec(workspace, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\nREQ-F-CTX-001\n")
        # no workspace features

        result = compute_spec_workspace_join(workspace)

        assert len(result["pending"]) == 3
        assert result["active"] == []
        assert result["orphan"] == []

    def test_counts_correct_on_real_spec(self, workspace: Path) -> None:
        """Smoke test: run against real specification if available."""
        real_spec = Path(__file__).parent.parent.parent / "specification" / "features" / "FEATURE_VECTORS.md"
        if not real_spec.exists():
            pytest.skip("Real spec not available")

        result = compute_spec_workspace_join(workspace, spec_features_path=real_spec)

        # The real spec has many features; verify the join runs without error
        assert result["spec_readable"] is True
        assert result["spec_count"] > 0
        # All categories are disjoint
        all_ids = set(result["active"]) | set(result["completed"]) | set(result["pending"]) | set(result["orphan"])
        # No ID appears in multiple categories (spec-side intersection check)
        spec_workspace_overlap = set(result["active"]) | set(result["completed"])
        assert not (set(result["pending"]) & spec_workspace_overlap)
