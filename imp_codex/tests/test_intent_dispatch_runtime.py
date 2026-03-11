# Validates: REQ-F-DISPATCH-001, REQ-F-INTENT-001, REQ-F-UX-001
"""Codex dispatch tests derived from the Claude intent_observer spec tests.

These tests keep the Claude behavioral contract but target the Codex-native
runtime surface: ``gen_dispatch_intents()`` and ``resolve_affected_features()``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from imp_codex.runtime import RuntimePaths, append_run_event, bootstrap_workspace, gen_dispatch_intents
from imp_codex.runtime.intents import resolve_affected_features


def _write_intent(project_root: Path) -> None:
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nDispatch spec fixture.\n")


def _write_feature(
    paths: RuntimePaths,
    feature_id: str,
    *,
    profile: str = "standard",
    trajectory: dict | None = None,
    requirements: list[str] | None = None,
) -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = profile
    feature_doc["status"] = "in_progress"
    feature_doc["trajectory"] = trajectory or {}
    if requirements is not None:
        feature_doc["requirements"] = requirements
    paths.active_features_dir.mkdir(parents=True, exist_ok=True)
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def _emit_intent(
    paths: RuntimePaths,
    *,
    intent_id: str,
    feature: str | None = None,
    affected_features: list[str] | None = None,
    affected_req_keys: list[str] | None = None,
) -> None:
    append_run_event(
        paths.events_file,
        project_name="demo",
        semantic_type="intent_raised",
        actor="pytest",
        feature=feature,
        edge="gap_analysis",
        payload={
            "intent_id": intent_id,
            "trigger": "dispatch test",
            "delta": "pending work",
            "signal_source": "gap",
            "vector_type": "feature",
            "severity": "high",
            "requires_spec_change": False,
            "affected_features": list(affected_features or []),
            "affected_req_keys": list(affected_req_keys or []),
        },
    )


def _emit_edge_started(
    paths: RuntimePaths,
    *,
    feature: str,
    edge: str,
    intent_id: str | None = None,
) -> None:
    payload = {
        "feature": feature,
        "edge": edge,
        "status": "iterating",
    }
    if intent_id:
        payload["intent_id"] = intent_id
    append_run_event(
        paths.events_file,
        project_name="demo",
        semantic_type="edge_started",
        actor="pytest",
        feature=feature,
        edge=edge,
        payload=payload,
    )


def test_dispatch_returns_empty_when_no_intents_exist(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    bootstrap_workspace(project_root, project_name="demo")

    result = gen_dispatch_intents(project_root)

    assert result["dispatched_count"] == 0
    assert result["dispatches"] == []


def test_handled_intent_is_not_dispatched_again(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-TEST-001", profile="minimal")
    _emit_intent(paths, intent_id="INT-001", affected_features=["REQ-F-TEST-001"])
    _emit_edge_started(
        paths,
        feature="REQ-F-TEST-001",
        edge="intent→requirements",
        intent_id="INT-001",
    )

    result = gen_dispatch_intents(project_root)

    assert result["dispatched_count"] == 0
    assert result["dispatches"] == []


def test_edge_started_without_intent_id_does_not_mark_intent_handled(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-TEST-001", profile="minimal")
    _emit_intent(paths, intent_id="INT-001", affected_features=["REQ-F-TEST-001"])
    _emit_edge_started(
        paths,
        feature="REQ-F-TEST-001",
        edge="intent→requirements",
    )

    result = gen_dispatch_intents(project_root, max_dispatch=1)

    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["intent_id"] == "INT-001"
    assert result["dispatches"][0]["feature"] == "REQ-F-TEST-001"
    assert result["dispatches"][0]["edge_started_run_id"] is not None
    assert result["dispatches"][0]["completed_run_id"] is not None


def test_dispatch_scope_all_targets_each_non_converged_feature(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-ALPHA-001", profile="minimal")
    _write_feature(paths, "REQ-F-BETA-001", profile="minimal")
    _write_feature(paths, "REQ-F-DONE-001", profile="minimal")

    done_path = paths.active_features_dir / "REQ-F-DONE-001.yml"
    done_doc = yaml.safe_load(done_path.read_text())
    done_doc["status"] = "converged"
    (paths.completed_features_dir / done_path.name).write_text(yaml.safe_dump(done_doc, sort_keys=False))
    done_path.unlink()

    _emit_intent(paths, intent_id="INT-ALL-001", affected_features=["all"])

    result = gen_dispatch_intents(project_root, max_dispatch=10)

    assert result["dispatched_count"] == 2
    dispatched = {(item["intent_id"], item["feature"], item["edge"]) for item in result["dispatches"]}
    assert dispatched == {
        ("INT-ALL-001", "REQ-F-ALPHA-001", "intent→requirements"),
        ("INT-ALL-001", "REQ-F-BETA-001", "intent→requirements"),
    }


def test_dispatch_selects_first_unconverged_edge_from_feature_trajectory(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(
        paths,
        "REQ-F-EDGE-001",
        profile="standard",
        trajectory={
            "requirements": {
                "status": "converged",
                "iteration": 1,
            }
        },
    )
    _emit_intent(paths, intent_id="INT-EDGE-001", affected_features=["REQ-F-EDGE-001"])

    result = gen_dispatch_intents(project_root, max_dispatch=1)

    assert result["dispatched_count"] == 1
    assert result["dispatches"][0]["edge"] == "requirements→design"


def test_resolve_affected_features_maps_req_keys_to_owning_feature(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(
        paths,
        "REQ-F-AUTH-001",
        requirements=["REQ-BR-AUTH-001", "REQ-NFR-PERF-001"],
    )

    resolved = resolve_affected_features(
        paths,
        feature=None,
        affected_req_keys=["REQ-BR-AUTH-001"],
    )

    assert resolved == ["REQ-F-AUTH-001"]
