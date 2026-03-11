# Validates: REQ-TOOL-016 (Workspace Analysis Edge)
# Validates: REQ-ITER-001 (Universal Iteration Function — workspace_state instance)
# Validates: REQ-LIFE-003 (Feedback Loop Closure — delta → intent_raised)
"""Tests for workspace_analysis.py — iterate(Asset<workspace_state>, Context[], Evaluators[]).

Verifies all 5 acceptance criteria from REQ-TOOL-016:
- AC-1: Asset is fully derivable from existing artifacts
- AC-2: Gap analysis and postmortem share same source of truth
- AC-3: delta > 0 → intent_raised for every failing check
- AC-4: Incomplete event log is a delta item, not a footnote
- AC-5: Evaluators defined in config, not hardcoded
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from genesis.workspace_analysis import (
    WorkspaceAsset,
    WorkspaceAnalysisResult,
    build_workspace_asset,
    run_workspace_analysis,
    EVAL_SPEC_ALIGNED,
    EVAL_NO_ORPHANS,
    EVAL_NO_STALE,
    EVAL_LOG_COMPLETE,
)


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════


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
    for fid in feature_ids:
        content += f"\n## {fid}\n**{fid}**: Some feature.\n"
    spec_path.write_text(content)
    return spec_path


def write_vector(workspace: Path, feature_id: str, status: str = "in_progress", status_dir: str = "active") -> Path:
    fdir = workspace / ".ai-workspace" / "features" / status_dir
    fdir.mkdir(parents=True, exist_ok=True)
    fpath = fdir / f"{feature_id}.yml"
    data = {
        "feature": feature_id,
        "id": feature_id,
        "title": feature_id,
        "status": status,
        "vector_type": "feature",
    }
    fpath.write_text(yaml.dump(data))
    return fpath


def write_events(workspace: Path, events: list[dict]) -> Path:
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    lines = "\n".join(json.dumps(ev) for ev in events)
    events_path.write_text(lines + "\n")
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


# ═══════════════════════════════════════════════════════════════════════
# WorkspaceAsset: build_workspace_asset (AC-1)
# ═══════════════════════════════════════════════════════════════════════


class TestBuildWorkspaceAsset:
    """AC-1: Asset is fully derivable from existing artifacts."""

    def test_empty_workspace_produces_valid_asset(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        asset = build_workspace_asset(ws)
        assert isinstance(asset, WorkspaceAsset)
        assert asset.feature_count == 0
        assert asset.event_count == 0
        assert asset.incomplete_features == []

    def test_counts_active_vectors(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        write_vector(ws, "REQ-F-A-002")
        asset = build_workspace_asset(ws)
        assert asset.feature_count == 2
        assert asset.active_count == 2

    def test_counts_completed_vectors(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001", status="converged", status_dir="completed")
        asset = build_workspace_asset(ws)
        assert asset.converged_count == 1

    def test_counts_events(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_events(ws, [iteration_event("REQ-F-A-001"), iteration_event("REQ-F-A-002")])
        asset = build_workspace_asset(ws)
        assert asset.event_count == 2

    def test_snapshot_at_is_iso8601(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        asset = build_workspace_asset(ws)
        assert "T" in asset.snapshot_at
        assert asset.snapshot_at.endswith("+00:00") or "Z" in asset.snapshot_at or "+" in asset.snapshot_at

    def test_gradient_is_at_rest_for_aligned_workspace(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        asset = build_workspace_asset(ws, spec)
        assert asset.gradient.pending == []
        assert asset.gradient.is_at_rest  # no delta in gradient

    def test_is_at_rest_requires_no_incomplete_features(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        # No events written → incomplete
        asset = build_workspace_asset(ws, spec)
        assert not asset.is_at_rest()

    def test_is_at_rest_when_events_and_gradient_clear(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])
        asset = build_workspace_asset(ws, spec)
        assert asset.gradient.is_at_rest
        assert asset.incomplete_features == []
        assert asset.is_at_rest()

    def test_summary_includes_key_counts(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        asset = build_workspace_asset(ws)
        s = asset.summary()
        assert "features=1" in s
        assert "events=0" in s


# ═══════════════════════════════════════════════════════════════════════
# Incomplete feature detection (AC-4)
# ═══════════════════════════════════════════════════════════════════════


class TestIncompleteFeatureDetection:
    """AC-4: Incomplete event log is a delta item, not a footnote."""

    def test_active_feature_with_no_events_is_incomplete(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        # No events
        asset = build_workspace_asset(ws)
        assert "REQ-F-A-001" in asset.incomplete_features

    def test_active_feature_with_iteration_event_is_complete(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])
        asset = build_workspace_asset(ws)
        assert "REQ-F-A-001" not in asset.incomplete_features

    def test_completed_feature_not_counted_as_incomplete(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001", status="converged", status_dir="completed")
        # No events — completed vectors don't need events
        asset = build_workspace_asset(ws)
        assert "REQ-F-A-001" not in asset.incomplete_features

    def test_multiple_incomplete_features_all_reported(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        write_vector(ws, "REQ-F-A-002")
        write_vector(ws, "REQ-F-A-003")
        write_events(ws, [iteration_event("REQ-F-A-002")])
        asset = build_workspace_asset(ws)
        assert "REQ-F-A-001" in asset.incomplete_features
        assert "REQ-F-A-002" not in asset.incomplete_features
        assert "REQ-F-A-003" in asset.incomplete_features

    def test_tolerates_corrupted_event_lines(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        events_path = ws / ".ai-workspace" / "events" / "events.jsonl"
        events_path.write_text(
            '{"event_type": "iteration_completed", "feature": "REQ-F-A-001"}\n'
            "THIS IS CORRUPT JSON\n"
        )
        # Should not raise
        asset = build_workspace_asset(ws)
        assert "REQ-F-A-001" not in asset.incomplete_features

    def test_empty_events_file_does_not_raise(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        (ws / ".ai-workspace" / "events" / "events.jsonl").write_text("")
        asset = build_workspace_asset(ws)
        assert asset.event_count == 0


# ═══════════════════════════════════════════════════════════════════════
# Evaluator checks
# ═══════════════════════════════════════════════════════════════════════


class TestEvaluatorSpecAligned:
    def test_passes_when_spec_and_workspace_match(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001", "REQ-F-A-002"])
        write_vector(ws, "REQ-F-A-001")
        write_vector(ws, "REQ-F-A-002")
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        aligned = next(r for r in result.evaluator_results if r.name == EVAL_SPEC_ALIGNED)
        assert aligned.passed

    def test_fails_when_spec_feature_missing_from_workspace(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001", "REQ-F-A-002"])
        write_vector(ws, "REQ-F-A-001")
        # REQ-F-A-002 is in spec but not in workspace
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        aligned = next(r for r in result.evaluator_results if r.name == EVAL_SPEC_ALIGNED)
        assert not aligned.passed
        assert "REQ-F-A-002" in aligned.details

    def test_delta_count_equals_pending_count(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001", "REQ-F-A-002", "REQ-F-A-003"])
        write_vector(ws, "REQ-F-A-001")
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        aligned = next(r for r in result.evaluator_results if r.name == EVAL_SPEC_ALIGNED)
        assert aligned.delta_count == 2  # A-002, A-003 missing


class TestEvaluatorNoOrphans:
    def test_passes_when_no_active_orphans(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        orphan = next(r for r in result.evaluator_results if r.name == EVAL_NO_ORPHANS)
        assert orphan.passed

    def test_fails_when_active_vector_not_in_spec(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        write_vector(ws, "REQ-F-UNLISTED-001")  # not in spec
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        orphan = next(r for r in result.evaluator_results if r.name == EVAL_NO_ORPHANS)
        assert not orphan.passed

    def test_completed_orphan_does_not_fail_evaluator(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        # Completed vector not in spec — info severity, should not block
        write_vector(ws, "REQ-F-OLD-001", status="converged", status_dir="completed")
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        orphan = next(r for r in result.evaluator_results if r.name == EVAL_NO_ORPHANS)
        assert orphan.passed


class TestEvaluatorEventLogComplete:
    def test_passes_when_all_active_features_have_events(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])
        result = run_workspace_analysis(ws, project="test")
        log_eval = next(r for r in result.evaluator_results if r.name == EVAL_LOG_COMPLETE)
        assert log_eval.passed

    def test_fails_when_active_feature_has_no_events(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        # No events
        result = run_workspace_analysis(ws, project="test")
        log_eval = next(r for r in result.evaluator_results if r.name == EVAL_LOG_COMPLETE)
        assert not log_eval.passed
        assert "REQ-F-A-001" in log_eval.details

    def test_is_required_evaluator(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        result = run_workspace_analysis(ws, project="test")
        log_eval = next(r for r in result.evaluator_results if r.name == EVAL_LOG_COMPLETE)
        assert log_eval.required is True


# ═══════════════════════════════════════════════════════════════════════
# run_workspace_analysis (AC-3: delta → intent_raised)
# ═══════════════════════════════════════════════════════════════════════


class TestRunWorkspaceAnalysis:
    def test_returns_workspace_analysis_result(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        result = run_workspace_analysis(ws, project="test")
        assert isinstance(result, WorkspaceAnalysisResult)

    def test_converged_when_aligned_and_events_present(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        assert result.is_converged
        assert result.total_delta == 0

    def test_not_converged_when_spec_pending(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        # No workspace vector
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        assert not result.is_converged
        assert result.total_delta > 0

    def test_not_converged_when_event_log_incomplete(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        # No events
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        assert not result.is_converged

    def test_generates_intents_for_pending_features(self, tmp_path: Path) -> None:
        """AC-3: delta > 0 → intent_raised events generated."""
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        # No workspace vector → PENDING gap
        result = run_workspace_analysis(ws, project="myproject", spec_features_path=spec)
        assert len(result.intent_proposals) > 0
        intent_types = {p.get("event_type") for p in result.intent_proposals}
        assert "intent_raised" in intent_types

    def test_generates_intent_for_incomplete_event_log(self, tmp_path: Path) -> None:
        """AC-4: Incomplete event log treated as delta, emits intent_raised."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        # No events
        result = run_workspace_analysis(ws, project="test")
        log_intents = [
            p for p in result.intent_proposals
            if "LOG_INCOMPLETE" in str(p.get("data", {}).get("intent_id", ""))
        ]
        assert len(log_intents) > 0

    def test_no_intents_when_workspace_at_rest(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001"])
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])
        result = run_workspace_analysis(ws, project="test", spec_features_path=spec)
        assert result.is_converged
        assert result.total_delta == 0
        # No delta → no intents needed
        assert len(result.intent_proposals) == 0

    def test_summary_includes_status(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        result = run_workspace_analysis(ws, project="test")
        s = result.summary()
        assert "workspace_analysis" in s

    def test_passed_count_and_total_count(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        result = run_workspace_analysis(ws, project="test")
        assert result.total_count == 4  # 4 evaluators defined
        assert 0 <= result.passed_count <= result.total_count


# ═══════════════════════════════════════════════════════════════════════
# AC-2: Gap analysis and postmortem share same source of truth
# ═══════════════════════════════════════════════════════════════════════


class TestSharedSourceOfTruth:
    """AC-2: Two runs on the same snapshot produce identical coverage numbers."""

    def test_two_runs_on_same_workspace_produce_same_delta(self, tmp_path: Path) -> None:
        ws = make_workspace(tmp_path)
        spec = write_spec(ws, ["REQ-F-A-001", "REQ-F-A-002"])
        write_vector(ws, "REQ-F-A-001")
        write_events(ws, [iteration_event("REQ-F-A-001")])

        result_a = run_workspace_analysis(ws, project="gap_analysis", spec_features_path=spec)
        result_b = run_workspace_analysis(ws, project="postmortem", spec_features_path=spec)

        # Both reads of the same asset must agree on coverage numbers
        assert result_a.total_delta == result_b.total_delta
        assert result_a.is_converged == result_b.is_converged

    def test_asset_is_derivable_without_spec_file(self, tmp_path: Path) -> None:
        """AC-1: No additional data collection — missing spec is handled gracefully."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001")
        # spec_features_path is None and default path doesn't exist
        asset = build_workspace_asset(ws)
        assert asset.gradient.spec_count == 0  # spec has no keys → no PENDING
        assert asset.gradient.workspace_count == 1


# ═══════════════════════════════════════════════════════════════════════
# AC-5: Evaluator config file
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeParamsConfig:
    """AC-5: Evaluators defined in edge_params/workspace_analysis.yml, not hardcoded."""

    def test_workspace_analysis_yml_exists(self, tmp_path: Path) -> None:
        """The edge_params config file must exist in the plugin."""
        # Find the config relative to this test's source location
        test_dir = Path(__file__).parent
        # Walk up to find the plugin root
        plugin_root = test_dir.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
        config_path = plugin_root / "config" / "edge_params" / "workspace_analysis.yml"
        assert config_path.exists(), (
            f"workspace_analysis.yml not found at {config_path}. "
            "AC-5 requires evaluators defined in config, not hardcoded."
        )

    def test_workspace_analysis_yml_has_required_evaluators(self, tmp_path: Path) -> None:
        import yaml as _yaml

        test_dir = Path(__file__).parent
        plugin_root = test_dir.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
        config_path = plugin_root / "config" / "edge_params" / "workspace_analysis.yml"

        if not config_path.exists():
            pytest.skip("workspace_analysis.yml not found")

        config = _yaml.safe_load(config_path.read_text())
        evaluator_names = [e["name"] for e in config.get("evaluators", [])]

        assert EVAL_SPEC_ALIGNED in evaluator_names
        assert EVAL_NO_ORPHANS in evaluator_names
        assert EVAL_NO_STALE in evaluator_names
        assert EVAL_LOG_COMPLETE in evaluator_names

    def test_workspace_analysis_yml_has_convergence_section(self, tmp_path: Path) -> None:
        import yaml as _yaml

        test_dir = Path(__file__).parent
        plugin_root = test_dir.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
        config_path = plugin_root / "config" / "edge_params" / "workspace_analysis.yml"

        if not config_path.exists():
            pytest.skip("workspace_analysis.yml not found")

        config = _yaml.safe_load(config_path.read_text())
        convergence = config.get("convergence", {})
        assert "required_checks" in convergence
        assert EVAL_SPEC_ALIGNED in convergence["required_checks"]
        assert EVAL_LOG_COMPLETE in convergence["required_checks"]
