# Validates: REQ-TOOL-016, REQ-ITER-001, REQ-LIFE-003
"""Codex-native workspace analysis tests derived from the Claude spec suite."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from imp_codex.runtime.paths import CONFIG_ROOT
from imp_codex.runtime.workspace_analysis import (
    EVAL_LOG_COMPLETE,
    EVAL_NO_ORPHANS,
    EVAL_NO_STALE,
    EVAL_SPEC_ALIGNED,
    WorkspaceAnalysisResult,
    WorkspaceAsset,
    build_workspace_asset,
    run_workspace_analysis,
)


def make_workspace(tmp_path: Path) -> Path:
    (tmp_path / ".ai-workspace" / "features" / "active").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "features" / "completed").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
    return tmp_path


def write_spec(workspace: Path, feature_ids: list[str]) -> Path:
    spec_dir = workspace / "specification" / "features"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "FEATURE_VECTORS.md"
    content = "# Feature Vectors\n"
    for feature_id in feature_ids:
        content += f"\n## {feature_id}\n**{feature_id}**: Some feature.\n"
    spec_path.write_text(content)
    return spec_path


def write_vector(workspace: Path, feature_id: str, *, status: str = "in_progress", status_dir: str = "active") -> Path:
    feature_dir = workspace / ".ai-workspace" / "features" / status_dir
    feature_dir.mkdir(parents=True, exist_ok=True)
    path = feature_dir / f"{feature_id}.yml"
    data = {
        "feature": feature_id,
        "id": feature_id,
        "title": feature_id,
        "status": status,
        "vector_type": "feature",
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def write_events(workspace: Path, events: list[dict]) -> Path:
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    events_path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return events_path


def iteration_event(feature: str) -> dict:
    return {
        "event_type": "iteration_completed",
        "timestamp": "2026-03-11T00:00:00Z",
        "project": "test",
        "feature": feature,
        "edge": "code↔unit_tests",
        "iteration": 1,
        "status": "iterating",
        "delta": 0,
    }


def test_build_workspace_asset_derives_counts_and_gradient(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    spec = write_spec(workspace, ["REQ-F-A-001"])
    write_vector(workspace, "REQ-F-A-001")

    asset = build_workspace_asset(workspace, spec)

    assert isinstance(asset, WorkspaceAsset)
    assert asset.feature_count == 1
    assert asset.active_count == 1
    assert asset.converged_count == 0
    assert asset.gradient.pending == []
    assert asset.gradient.is_at_rest
    assert "features=1" in asset.summary()


def test_build_workspace_asset_marks_incomplete_active_features(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    write_vector(workspace, "REQ-F-A-001")

    asset = build_workspace_asset(workspace)

    assert asset.incomplete_features == ["REQ-F-A-001"]
    assert not asset.is_at_rest()


def test_build_workspace_asset_tolerates_corrupt_event_lines(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    write_vector(workspace, "REQ-F-A-001")
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    events_path.write_text(
        '{"event_type": "iteration_completed", "feature": "REQ-F-A-001"}\n'
        "NOT JSON\n"
    )

    asset = build_workspace_asset(workspace)

    assert asset.event_count == 1
    assert asset.incomplete_features == []


def test_workspace_analysis_converges_when_spec_matches_and_events_exist(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    spec = write_spec(workspace, ["REQ-F-A-001"])
    write_vector(workspace, "REQ-F-A-001")
    write_events(workspace, [iteration_event("REQ-F-A-001")])

    result = run_workspace_analysis(workspace, project="test", spec_features_path=spec)

    assert isinstance(result, WorkspaceAnalysisResult)
    assert result.is_converged
    assert result.total_delta == 0
    assert result.intent_proposals == []


def test_workspace_analysis_detects_pending_spec_features(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    spec = write_spec(workspace, ["REQ-F-A-001", "REQ-F-A-002"])
    write_vector(workspace, "REQ-F-A-001")

    result = run_workspace_analysis(workspace, project="gap_analysis", spec_features_path=spec)
    aligned = next(item for item in result.evaluator_results if item.name == EVAL_SPEC_ALIGNED)

    assert not result.is_converged
    assert aligned.passed is False
    assert aligned.delta_count == 1
    assert aligned.details == ["REQ-F-A-002"]
    assert any(proposal["event_type"] == "intent_raised" for proposal in result.intent_proposals)


def test_workspace_analysis_detects_incomplete_event_log_and_raises_log_intent(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    write_vector(workspace, "REQ-F-A-001")

    result = run_workspace_analysis(workspace, project="test")
    log_eval = next(item for item in result.evaluator_results if item.name == EVAL_LOG_COMPLETE)
    log_intents = [
        proposal for proposal in result.intent_proposals
        if "LOG_COMPLETE" in proposal["data"]["intent_id"]
    ]

    assert log_eval.passed is False
    assert log_eval.details == ["REQ-F-A-001"]
    assert len(log_intents) == 1


def test_workspace_analysis_ignores_completed_orphans_for_orphan_gate(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    spec = write_spec(workspace, ["REQ-F-A-001"])
    write_vector(workspace, "REQ-F-A-001")
    write_vector(workspace, "REQ-F-OLD-001", status="converged", status_dir="completed")

    result = run_workspace_analysis(workspace, project="test", spec_features_path=spec)
    orphan_eval = next(item for item in result.evaluator_results if item.name == EVAL_NO_ORPHANS)

    assert orphan_eval.passed
    assert orphan_eval.delta_count == 0


def test_workspace_analysis_reports_duplicate_feature_as_stale(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    write_vector(workspace, "REQ-F-A-001")
    write_vector(workspace, "REQ-F-A-001", status="converged", status_dir="completed")
    write_events(workspace, [iteration_event("REQ-F-A-001")])

    result = run_workspace_analysis(workspace, project="test")
    stale = next(item for item in result.evaluator_results if item.name == EVAL_NO_STALE)

    assert stale.passed is False
    assert stale.details == ["REQ-F-A-001"]


def test_workspace_analysis_uses_shared_source_of_truth_across_runs(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    spec = write_spec(workspace, ["REQ-F-A-001", "REQ-F-A-002"])
    write_vector(workspace, "REQ-F-A-001")
    write_events(workspace, [iteration_event("REQ-F-A-001")])

    result_a = run_workspace_analysis(workspace, project="gap_analysis", spec_features_path=spec)
    result_b = run_workspace_analysis(workspace, project="postmortem", spec_features_path=spec)

    assert result_a.total_delta == result_b.total_delta
    assert result_a.is_converged == result_b.is_converged


def test_workspace_analysis_without_spec_is_graceful(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)
    write_vector(workspace, "REQ-F-A-001")

    asset = build_workspace_asset(workspace)

    assert asset.gradient.spec_count == 0
    assert asset.gradient.workspace_count == 1


def test_workspace_analysis_summary_and_counts_are_populated(tmp_path: Path) -> None:
    workspace = make_workspace(tmp_path)

    result = run_workspace_analysis(workspace, project="test")

    assert "workspace_analysis" in result.summary()
    assert result.total_count == 4
    assert 0 <= result.passed_count <= result.total_count


def test_workspace_analysis_config_exists_and_declares_required_checks() -> None:
    config_path = CONFIG_ROOT / "edge_params" / "workspace_analysis.yml"
    config = yaml.safe_load(config_path.read_text())
    evaluator_names = [item["name"] for item in config.get("evaluators", [])]

    assert config_path.exists()
    assert EVAL_SPEC_ALIGNED in evaluator_names
    assert EVAL_NO_ORPHANS in evaluator_names
    assert EVAL_NO_STALE in evaluator_names
    assert EVAL_LOG_COMPLETE in evaluator_names
    assert EVAL_SPEC_ALIGNED in config["convergence"]["required_checks"]
    assert EVAL_LOG_COMPLETE in config["convergence"]["required_checks"]
