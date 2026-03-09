# Validates: REQ-F-CDX-008
"""Runtime behavior contract tests for the Codex tenant."""

from __future__ import annotations

from pathlib import Path

from imp_codex.runtime import gen_iterate, gen_review
from imp_codex.runtime.behaviors import (
    apply_review_behavior,
    get_behavior_registry,
    resolve_candidate_artifact_behavior,
)


def _write_intent(project_root: Path) -> None:
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nBuild a runtime stub.\n")


def test_behavior_registry_lists_named_contracts():
    assert get_behavior_registry() == {
        "construct": "candidate_artifact_refs_v1",
        "evaluate": "edge_evaluator_mix_v1",
        "review": "human_gate_closeout_v1",
    }


def test_resolve_candidate_artifact_behavior_hashes_relative_paths(tmp_path):
    project_root = tmp_path / "demo"
    candidate = project_root / "src" / "feature.py"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("print('ok')\n")

    behavior = resolve_candidate_artifact_behavior(project_root, ["src/feature.py"])

    assert behavior["behavior"] == "candidate_artifact_refs_v1"
    assert behavior["artifact_count"] == 1
    assert behavior["artifact_refs"][0]["path"] == "src/feature.py"
    assert behavior["artifact_refs"][0]["sha256"].startswith("sha256:")


def test_apply_review_behavior_updates_human_gate_state():
    feature_doc = {
        "trajectory": {
            "requirements": {
                "status": "pending_review",
                "iteration": 1,
            }
        }
    }

    review = apply_review_behavior(
        feature_doc,
        review_edge="intent→requirements",
        decision="approved",
        feedback="Looks correct",
        iteration=1,
        latest_delta=0,
        timestamp="2026-03-09T00:00:00Z",
    )

    assert review["behavior"] == "human_gate_closeout_v1"
    assert review["all_evaluators_pass"] is True
    assert review["feature_doc"]["trajectory"]["requirements"]["status"] == "converged"
    assert review["feature_doc"]["trajectory"]["requirements"]["human_review"]["feedback"] == "Looks correct"


def test_commands_report_behavior_contracts(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)

    iterate = gen_iterate(
        project_root,
        feature="REQ-F-REVIEW-001",
        edge="intent→requirements",
        profile="standard",
        delta=0,
        converged=True,
    )
    review = gen_review(
        project_root,
        feature="REQ-F-REVIEW-001",
        edge="intent→requirements",
        decision="approved",
        feedback="Looks correct",
    )

    assert iterate["behaviors"]["construct"]["behavior"] == "candidate_artifact_refs_v1"
    assert iterate["behaviors"]["evaluate"]["behavior"] == "edge_evaluator_mix_v1"
    assert review["behaviors"]["review"]["behavior"] == "human_gate_closeout_v1"
