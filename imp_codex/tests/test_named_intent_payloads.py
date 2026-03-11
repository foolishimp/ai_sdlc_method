# Validates: REQ-F-NAMEDCOMP-001, REQ-INTENT-002
"""Typed intent payload tests for the Codex named composition registry.

These tests exercise the Codex-native registry and payload resolution helpers,
using Claude's named-composition tests as behavioral guidance rather than as a
schema copy.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from imp_codex.runtime import RuntimePaths, bootstrap_workspace
from imp_codex.runtime.intents import load_named_compositions, resolve_named_intent_payload


def _write_intent(project_root: Path) -> None:
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nNamed composition fixture.\n")


def _write_feature(
    paths: RuntimePaths,
    feature_id: str,
    *,
    requirements: list[str] | None = None,
) -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = "standard"
    feature_doc["status"] = "in_progress"
    if requirements is not None:
        feature_doc["requirements"] = requirements
    paths.active_features_dir.mkdir(parents=True, exist_ok=True)
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def test_load_named_compositions_reads_workspace_registry(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")

    registry = load_named_compositions(paths)

    assert set(registry) == {"STUCK_REWORK", "TRACE_GAP_CLOSURE", "PROCESS_REPAIR"}


def test_resolve_named_intent_payload_selects_matching_gap_rule(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")

    payload = resolve_named_intent_payload(
        paths,
        signal_source="gap",
        feature="REQ-F-AUTH-001",
        edge="gap_analysis",
        affected_req_keys=["REQ-F-AUTH-001", "REQ-F-AUTH-002"],
    )

    assert payload["composition_name"] == "TRACE_GAP_CLOSURE"
    assert payload["composition"]["macro"] == "TRACE_GAP_CLOSURE"
    assert payload["composition"]["version"] == "v1"
    assert payload["composition_expression"] == "TRACE_GAP(2) -> PLAN(traceability_closure)"
    assert payload["affected_features"] == ["REQ-F-AUTH-001", "REQ-F-AUTH-002"]
    assert payload["intent_vector"]["resolution_level"] == "feature_set"
    assert payload["intent_vector"]["profile"] == "minimal"


def test_resolve_named_intent_payload_falls_back_to_plan_when_no_rule_matches(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")

    payload = resolve_named_intent_payload(
        paths,
        signal_source="unknown_source",
        feature="REQ-F-ALPHA-001",
        edge="design→code",
        affected_req_keys=["REQ-F-ALPHA-001"],
    )

    assert payload["composition_name"] is None
    assert payload["composition"]["macro"] == "PLAN"
    assert payload["composition"]["version"] == "v1"
    assert payload["composition_expression"] == "PLAN(unknown_source)"
    assert payload["intent_vector"]["resolution_level"] == "feature"
    assert payload["intent_vector"]["profile"] == "standard"


def test_resolve_named_intent_payload_maps_non_feature_req_keys_to_owner(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(
        paths,
        "REQ-F-AUTH-001",
        requirements=["REQ-BR-AUTH-001", "REQ-NFR-PERF-001"],
    )

    payload = resolve_named_intent_payload(
        paths,
        signal_source="process_gap",
        feature=None,
        edge="design→code",
        affected_req_keys=["REQ-BR-AUTH-001"],
    )

    assert payload["composition_name"] == "PROCESS_REPAIR"
    assert payload["affected_features"] == ["REQ-F-AUTH-001"]
    assert payload["affected_req_keys"] == ["REQ-BR-AUTH-001"]
