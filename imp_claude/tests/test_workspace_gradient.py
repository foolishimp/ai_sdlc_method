# Validates: REQ-LIFE-009 (Spec Review as Gradient Check)
"""Tests for workspace_gradient.py — delta(workspace, spec) computation."""

from pathlib import Path

import pytest
import yaml

from genesis.workspace_gradient import (
    WorkspaceGradient,
    compute_workspace_gradient,
    extract_spec_req_keys,
    generate_intent_proposals,
    get_workspace_feature_ids,
    DELTA_ORPHAN,
    DELTA_PENDING,
    DELTA_STALE,
    SEVERITY_WARNING,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def write_spec(path: Path, feature_ids: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "# Feature Vectors\n"
    for fid in feature_ids:
        content += f"\n## {fid}\n**{fid}**: Some feature.\n"
    path.write_text(content)
    return path


def write_workspace_vector(workspace: Path, feature_id: str, status: str = "in_progress", status_dir: str = "active") -> Path:
    fdir = workspace / ".ai-workspace" / "features" / status_dir
    fdir.mkdir(parents=True, exist_ok=True)
    fpath = fdir / f"{feature_id}.yml"
    data = {"id": feature_id, "title": feature_id, "status": status, "vector_type": "feature"}
    fpath.write_text(yaml.dump(data))
    return fpath


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / ".ai-workspace" / "features" / "active").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "features" / "completed").mkdir(parents=True)
    return tmp_path


# ── extract_spec_req_keys ─────────────────────────────────────────────────────


class TestExtractSpecReqKeys:
    def test_extracts_req_f_keys(self, tmp_path: Path) -> None:
        spec = write_spec(tmp_path / "spec.md", ["REQ-F-AUTH-001", "REQ-F-API-001"])
        keys = extract_spec_req_keys(spec)
        assert "REQ-F-AUTH-001" in keys
        assert "REQ-F-API-001" in keys

    def test_deduplicates(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.md"
        spec.write_text("REQ-F-AUTH-001\nREQ-F-AUTH-001\n")
        keys = extract_spec_req_keys(spec)
        assert keys.count("REQ-F-AUTH-001") == 1

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert extract_spec_req_keys(tmp_path / "no_spec.md") == []

    def test_sorted_output(self, tmp_path: Path) -> None:
        spec = write_spec(tmp_path / "spec.md", ["REQ-F-B-001", "REQ-F-A-001"])
        keys = extract_spec_req_keys(spec)
        assert keys == sorted(keys)

    def test_excludes_non_req_f_keys(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.md"
        spec.write_text("REQ-NFR-PERF-001 and REQ-F-AUTH-001 and REQ-TOOL-001\n")
        keys = extract_spec_req_keys(spec)
        # Only REQ-F-* keys
        assert all(k.startswith("REQ-F-") for k in keys)


# ── get_workspace_feature_ids ─────────────────────────────────────────────────


class TestGetWorkspaceFeatureIds:
    def test_returns_active_vectors(self, workspace: Path) -> None:
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        vectors = get_workspace_feature_ids(workspace)
        assert "REQ-F-AUTH-001" in vectors

    def test_returns_completed_vectors(self, workspace: Path) -> None:
        write_workspace_vector(workspace, "REQ-F-AUTH-001", status="converged", status_dir="completed")
        vectors = get_workspace_feature_ids(workspace)
        assert "REQ-F-AUTH-001" in vectors

    def test_empty_workspace_returns_empty(self, workspace: Path) -> None:
        assert get_workspace_feature_ids(workspace) == {}

    def test_includes_status_dir_in_vector(self, workspace: Path) -> None:
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        vectors = get_workspace_feature_ids(workspace)
        assert vectors["REQ-F-AUTH-001"]["_status_dir"] == "active"


# ── compute_workspace_gradient ────────────────────────────────────────────────


class TestComputeWorkspaceGradient:
    def test_at_rest_when_spec_and_workspace_match(self, workspace: Path) -> None:
        spec = write_spec(
            workspace / "specification" / "features" / "FEATURE_VECTORS.md",
            ["REQ-F-AUTH-001"]
        )
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.is_at_rest
        assert gradient.total_delta == 0

    def test_pending_when_spec_has_no_workspace(self, workspace: Path) -> None:
        spec = write_spec(
            workspace / "spec.md",
            ["REQ-F-AUTH-001", "REQ-F-API-001"]
        )
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        gradient = compute_workspace_gradient(workspace, spec)
        assert len(gradient.pending) == 1
        assert gradient.pending[0].feature_id == "REQ-F-API-001"
        assert gradient.pending[0].delta_type == DELTA_PENDING

    def test_orphan_when_workspace_not_in_spec(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        write_workspace_vector(workspace, "REQ-F-EXTRA-001")  # not in spec
        gradient = compute_workspace_gradient(workspace, spec)
        assert len(gradient.orphans) == 1
        assert gradient.orphans[0].feature_id == "REQ-F-EXTRA-001"
        assert gradient.orphans[0].delta_type == DELTA_ORPHAN

    def test_total_delta_sums_all_categories(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001", "REQ-F-API-001"])
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        write_workspace_vector(workspace, "REQ-F-EXTRA-001")  # orphan
        # REQ-F-API-001 is pending (no workspace vector)
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.total_delta == 2  # 1 pending + 1 orphan
        assert not gradient.is_at_rest

    def test_empty_spec_and_workspace_at_rest(self, workspace: Path) -> None:
        spec = workspace / "spec.md"
        spec.write_text("# Empty spec\n")
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.is_at_rest
        assert gradient.spec_count == 0
        assert gradient.workspace_count == 0

    def test_spec_count_and_workspace_count(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001", "REQ-F-API-001"])
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.spec_count == 2
        assert gradient.workspace_count == 1

    def test_summary_contains_key_info(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        gradient = compute_workspace_gradient(workspace, spec)
        summary = gradient.summary()
        assert "PENDING" in summary

    def test_idempotent_same_result_twice(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        write_workspace_vector(workspace, "REQ-F-EXTRA-001")
        g1 = compute_workspace_gradient(workspace, spec)
        g2 = compute_workspace_gradient(workspace, spec)
        assert g1.total_delta == g2.total_delta
        assert g1.pending[0].feature_id == g2.pending[0].feature_id
        assert g1.orphans[0].feature_id == g2.orphans[0].feature_id

    def test_completed_orphan_is_info_not_warning(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", [])
        write_workspace_vector(workspace, "REQ-F-DONE-001", status="converged", status_dir="completed")
        gradient = compute_workspace_gradient(workspace, spec)
        assert len(gradient.orphans) == 1
        # Completed orphans are lower severity
        assert gradient.orphans[0].severity == "info"

    def test_pending_items_have_signal_source_gap(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.pending[0].signal_source == "gap"

    def test_orphan_items_have_signal_source_process_gap(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", [])
        write_workspace_vector(workspace, "REQ-F-EXTRA-001")
        gradient = compute_workspace_gradient(workspace, spec)
        assert gradient.orphans[0].signal_source == "process_gap"


# ── generate_intent_proposals ─────────────────────────────────────────────────


class TestGenerateIntentProposals:
    def test_generates_one_proposal_per_delta_item(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001", "REQ-F-API-001"])
        gradient = compute_workspace_gradient(workspace, spec)
        proposals = generate_intent_proposals(gradient, project="test-proj")
        assert len(proposals) == 2  # 2 pending items

    def test_proposal_schema_correct(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        gradient = compute_workspace_gradient(workspace, spec)
        proposals = generate_intent_proposals(gradient, project="test-proj")
        p = proposals[0]
        assert p["event_type"] == "intent_raised"
        assert p["project"] == "test-proj"
        assert "intent_id" in p["data"]
        assert "signal_source" in p["data"]
        assert "severity" in p["data"]
        assert p["data"]["draft"] is True

    def test_no_proposals_when_at_rest(self, workspace: Path) -> None:
        spec = write_spec(workspace / "spec.md", ["REQ-F-AUTH-001"])
        write_workspace_vector(workspace, "REQ-F-AUTH-001")
        gradient = compute_workspace_gradient(workspace, spec)
        proposals = generate_intent_proposals(gradient, project="test-proj")
        assert proposals == []
