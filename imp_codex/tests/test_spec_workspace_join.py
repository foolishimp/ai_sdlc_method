# Validates: REQ-EVOL-002
"""Codex JOIN tests derived from the Claude spec/workspace JOIN spec tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from imp_codex.runtime import RuntimePaths, bootstrap_workspace
from imp_codex.runtime.projections import compute_spec_workspace_join, extract_spec_feature_ids


def _write_feature(project_root: Path, fid: str, subdir: str = "active", status: str = "pending") -> Path:
    paths = RuntimePaths(project_root)
    feature_dir = paths.active_features_dir if subdir == "active" else paths.completed_features_dir
    feature_dir.mkdir(parents=True, exist_ok=True)
    path = feature_dir / f"{fid}.yml"
    path.write_text(yaml.safe_dump({"feature": fid, "status": status}, sort_keys=False))
    return path


def _write_spec(project_root: Path, content: str) -> Path:
    spec_dir = project_root / "specification" / "features"
    spec_dir.mkdir(parents=True, exist_ok=True)
    path = spec_dir / "FEATURE_VECTORS.md"
    path.write_text(content)
    return path


def test_extract_spec_feature_ids_returns_sorted_unique_req_f_ids(tmp_path):
    spec = tmp_path / "FEATURE_VECTORS.md"
    spec.write_text(
        "\n".join(
            [
                "REQ-F-ENGINE-001 mentioned twice",
                "REQ-F-ENGINE-001 mentioned twice",
                "REQ-GRAPH-001 should not match",
                "REQ-F-EVAL-001 should match",
            ]
        )
    )

    ids = extract_spec_feature_ids(spec)

    assert ids == ["REQ-F-ENGINE-001", "REQ-F-EVAL-001"]


def test_compute_spec_workspace_join_marks_matching_features_active(tmp_path):
    project_root = tmp_path / "demo"
    bootstrap_workspace(project_root, project_name="demo")
    _write_spec(project_root, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\n")
    _write_feature(project_root, "REQ-F-ENGINE-001", "active")
    _write_feature(project_root, "REQ-F-EVAL-001", "active")

    result = compute_spec_workspace_join(project_root)

    assert result["spec_readable"] is True
    assert result["spec_count"] == 2
    assert result["workspace_count"] == 2
    assert result["active"] == ["REQ-F-ENGINE-001", "REQ-F-EVAL-001"]
    assert result["completed"] == []
    assert result["pending"] == []
    assert result["orphan"] == []


def test_compute_spec_workspace_join_marks_missing_spec_features_pending(tmp_path):
    project_root = tmp_path / "demo"
    bootstrap_workspace(project_root, project_name="demo")
    _write_spec(project_root, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\nREQ-F-CTX-001\n")
    _write_feature(project_root, "REQ-F-ENGINE-001", "active")

    result = compute_spec_workspace_join(project_root)

    assert result["active"] == ["REQ-F-ENGINE-001"]
    assert result["pending"] == ["REQ-F-CTX-001", "REQ-F-EVAL-001"]
    assert result["orphan"] == []


def test_compute_spec_workspace_join_marks_workspace_only_features_orphan(tmp_path):
    project_root = tmp_path / "demo"
    bootstrap_workspace(project_root, project_name="demo")
    _write_spec(project_root, "REQ-F-ENGINE-001\n")
    _write_feature(project_root, "REQ-F-ENGINE-001", "active")
    _write_feature(project_root, "REQ-F-STALE-001", "active")

    result = compute_spec_workspace_join(project_root)

    assert result["active"] == ["REQ-F-ENGINE-001"]
    assert result["orphan"] == ["REQ-F-STALE-001"]
    assert result["pending"] == []


def test_compute_spec_workspace_join_reports_completed_directory_separately(tmp_path):
    project_root = tmp_path / "demo"
    bootstrap_workspace(project_root, project_name="demo")
    _write_spec(project_root, "REQ-F-ENGINE-001\nREQ-F-EVAL-001\n")
    _write_feature(project_root, "REQ-F-ENGINE-001", "active")
    _write_feature(project_root, "REQ-F-EVAL-001", "completed", status="converged")

    result = compute_spec_workspace_join(project_root)

    assert result["active"] == ["REQ-F-ENGINE-001"]
    assert result["completed"] == ["REQ-F-EVAL-001"]
    assert result["pending"] == []
    assert result["workspace_count"] == 2


def test_compute_spec_workspace_join_treats_missing_spec_as_unreadable(tmp_path):
    project_root = tmp_path / "demo"
    bootstrap_workspace(project_root, project_name="demo")
    _write_feature(project_root, "REQ-F-ENGINE-001", "active")

    result = compute_spec_workspace_join(project_root)

    assert result["spec_readable"] is False
    assert result["spec_count"] == 0
    assert result["orphan"] == ["REQ-F-ENGINE-001"]
