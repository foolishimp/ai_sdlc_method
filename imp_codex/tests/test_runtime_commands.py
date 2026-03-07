# Validates: REQ-F-ENGINE-001, REQ-F-LIFE-001, REQ-F-EVENT-001, REQ-F-UX-001
"""Executable runtime smoke tests for the Codex tenant."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from imp_codex.runtime import (
    RuntimePaths,
    append_run_event,
    bootstrap_workspace,
    gen_checkpoint,
    gen_fold_back,
    gen_gaps,
    gen_init,
    gen_iterate,
    gen_release,
    gen_review,
    gen_spawn,
    gen_start,
    gen_status,
    gen_trace,
)
from imp_codex.runtime.events import load_events


def _write_intent(project_root: Path) -> None:
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nBuild a runtime stub.\n")


def _write_simple_constraints(paths: RuntimePaths) -> None:
    constraints = yaml.safe_load(paths.project_constraints_path.read_text())
    for tool_name in ("syntax_checker", "linter", "type_checker", "test_runner", "coverage", "formatter"):
        constraints["tools"][tool_name]["command"] = "python"
        constraints["tools"][tool_name]["args"] = "-c \"print('ok')\""
    paths.project_constraints_path.write_text(yaml.safe_dump(constraints, sort_keys=False))


def _write_feature(paths: RuntimePaths, feature_id: str, *, dependencies=None, profile="minimal") -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = profile
    feature_doc["status"] = "in_progress"
    feature_doc["dependencies"] = dependencies or []
    paths.active_features_dir.mkdir(parents=True, exist_ok=True)
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def _write_traceability_assets(project_root: Path) -> None:
    specification = project_root / "specification"
    specification.mkdir(parents=True, exist_ok=True)
    (specification / "requirements.md").write_text(
        "\n".join(
            [
                "# Requirements",
                "",
                "- REQ-F-AUTH-001",
                "- REQ-F-AUTH-002",
                "- REQ-NFR-PERF-001",
            ]
        )
        + "\n"
    )

    src_dir = project_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "auth.py").write_text(
        "\n".join(
            [
                "# Implements: REQ-F-AUTH-001",
                '# telemetry req="REQ-F-AUTH-001"',
                "# Implements: REQ-F-AUTH-002",
                "def login():",
                "    return True",
            ]
        )
        + "\n"
    )

    tests_dir = project_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_auth.py").write_text(
        "\n".join(
            [
                "# Validates: REQ-F-AUTH-001",
                "def test_login():",
                "    assert True",
            ]
        )
        + "\n"
    )

    design_dir = project_root / "imp_codex" / "design"
    design_dir.mkdir(parents=True, exist_ok=True)
    (design_dir / "auth_design.md").write_text(
        "\n".join(
            [
                "# Auth Design",
                "",
                "Implements: REQ-F-AUTH-001",
                "Implements: REQ-F-AUTH-002",
            ]
        )
        + "\n"
    )


def test_append_run_event_uses_openlineage_shape(tmp_path):
    project_root = tmp_path / "demo"
    paths = bootstrap_workspace(project_root, project_name="demo")

    append_run_event(
        paths.events_file,
        project_name="demo",
        semantic_type="IterationStarted",
        actor="pytest",
        feature="REQ-F-DEMO-001",
        edge="intent→requirements",
        payload={"feature": "REQ-F-DEMO-001", "edge": "intent→requirements", "iteration": 1},
    )

    event = json.loads(paths.events_file.read_text().strip())
    assert event["eventType"] == "START"
    assert event["job"]["namespace"] == "aisdlc://demo"
    assert event["run"]["facets"]["sdlc:event_type"]["type"] == "IterationStarted"
    assert event["run"]["facets"]["sdlc:payload"]["feature"] == "REQ-F-DEMO-001"


def test_gen_init_scaffolds_workspace_and_emits_project_initialized(tmp_path):
    project_root = tmp_path / "demo"

    result = gen_init(project_root, project_name="demo")
    paths = RuntimePaths(project_root)

    assert Path(result["workspace_root"]).exists()
    assert paths.evaluator_defaults_path.exists()
    assert paths.context_manifest_path.exists()
    assert paths.intents_dir.exists()
    assert paths.snapshots_dir.exists()
    assert Path(result["intent_path"]).exists()
    assert Path(result["adr_template"]).exists()
    assert Path(result["status_file"]).exists()

    semantic_types = [event.semantic_type for event in load_events(paths.events_file)]
    assert semantic_types.count("ProjectInitialized") == 1

    result_again = gen_init(project_root, project_name="demo")
    semantic_types_again = [event.semantic_type for event in load_events(paths.events_file)]
    assert semantic_types_again.count("ProjectInitialized") == 1
    assert result_again["init_run_id"] == result["init_run_id"]


def test_gen_iterate_creates_feature_projection_and_status(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    result = gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="intent→requirements",
        profile="minimal",
        delta=2,
        evaluators=[
            {"name": "requirements_present", "type": "agent", "result": "fail", "required": True},
        ],
    )

    feature_path = Path(result["feature_path"])
    feature_doc = yaml.safe_load(feature_path.read_text())
    assert feature_doc["trajectory"]["requirements"]["status"] == "iterating"
    assert feature_doc["trajectory"]["requirements"]["iteration"] == 1
    assert Path(result["status_file"]).exists()
    assert Path(result["feature_index_file"]).exists()
    assert Path(result["active_tasks_file"]).exists()
    status_text = Path(result["status_file"]).read_text()
    assert "REQ-F-AUTH-001" in status_text
    assert "IN_PROGRESS" in status_text
    assert "Process Telemetry" in status_text

    events = load_events(Path(result["events_file"]))
    assert [event.semantic_type for event in events] == ["IterationStarted", "IterationCompleted"]


def test_gen_start_routes_next_edge_from_profile(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="intent→requirements",
        profile="minimal",
        delta=0,
        converged=True,
    )

    start = gen_start(project_root)
    assert start["state"] == "IN_PROGRESS"
    assert start["action"] == "iterate"
    assert start["feature"] == "REQ-F-AUTH-001"
    assert start["edge"] == "design→code"


def test_gen_iterate_moves_feature_to_completed_when_profile_is_done(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="intent→requirements",
        profile="minimal",
        delta=0,
        converged=True,
    )
    result = gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="design→code",
        profile="minimal",
        delta=0,
        converged=True,
    )

    paths = RuntimePaths(project_root)
    completed_path = paths.completed_features_dir / "REQ-F-AUTH-001.yml"
    assert completed_path.exists()
    assert not (paths.active_features_dir / "REQ-F-AUTH-001.yml").exists()

    status = gen_status(project_root)
    assert status["state"] == "ALL_CONVERGED"
    events = load_events(paths.events_file)
    assert events[-1].semantic_type == "ConvergenceAchieved"
    assert "ALL_CONVERGED" in Path(result["status_file"]).read_text()


def test_gen_status_health_and_task_projections_exist(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    result = gen_iterate(
        project_root,
        feature="REQ-F-HEALTH-001",
        edge="intent→requirements",
        profile="minimal",
        delta=1,
    )

    status = gen_status(project_root, health=True)
    assert status["health"]["corrupted_events"] == []
    assert status["health"]["missing_feature_vectors"] == []
    assert Path(status["active_tasks_file"]).exists()
    assert Path(status["feature_index_file"]).exists()
    assert "Next Action" in Path(status["active_tasks_file"]).read_text()
    feature_index = yaml.safe_load(Path(result["feature_index_file"]).read_text())
    assert feature_index["features"][0]["feature"] == "REQ-F-HEALTH-001"


def test_gen_iterate_emits_intent_when_delta_is_stuck(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    for _ in range(3):
        gen_iterate(
            project_root,
            feature="REQ-F-STUCK-001",
            edge="intent→requirements",
            profile="minimal",
            delta=2,
        )

    events = load_events(RuntimePaths(project_root).events_file)
    semantic_types = [event.semantic_type for event in events]
    assert semantic_types.count("IntentRaised") == 1

    start = gen_start(project_root)
    assert start["state"] == "STUCK"
    assert start["health"]["stuck_features"] == [{"feature": "REQ-F-STUCK-001", "edge": "intent→requirements"}]


def test_gen_iterate_can_run_deterministic_checks(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_simple_constraints(paths)

    result = gen_iterate(
        project_root,
        feature="REQ-F-CODE-001",
        edge="design→code",
        profile="minimal",
        run_deterministic=True,
    )

    assert result["evaluator_summary"]["passed"] >= 3
    assert result["converged"] is True


def test_gen_start_reports_all_blocked_when_dependencies_unresolved(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(
        paths,
        "REQ-F-BLOCKED-001",
        dependencies=[{"feature": "REQ-F-MISSING-001"}],
    )

    start = gen_start(project_root)
    assert start["state"] == "ALL_BLOCKED"
    assert start["action"] == "recover_blocked"
    assert start["blocked_features"] == [
        {
            "feature": "REQ-F-BLOCKED-001",
            "reasons": ["dependency REQ-F-MISSING-001 unresolved"],
        }
    ]


def test_gen_review_records_human_decision_and_persists_feature(tmp_path):
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
    assert iterate["status"] == "pending_review"

    result = gen_review(
        project_root,
        feature="REQ-F-REVIEW-001",
        edge="intent→requirements",
        decision="approved",
        feedback="Looks correct",
    )

    feature_doc = yaml.safe_load(Path(result["feature_path"]).read_text())
    review = feature_doc["trajectory"]["requirements"]["human_review"]
    assert review["decision"] == "approved"
    assert review["feedback"] == "Looks correct"
    assert feature_doc["status"] == "in_progress"

    semantic_types = [event.semantic_type for event in load_events(RuntimePaths(project_root).events_file)]
    assert "ReviewCompleted" in semantic_types


def test_gen_iterate_pauses_for_human_review_when_profile_requires_it(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)

    result = gen_iterate(
        project_root,
        feature="REQ-F-HUMAN-001",
        edge="intent→requirements",
        profile="standard",
        delta=0,
        converged=True,
    )

    feature_doc = yaml.safe_load(Path(result["feature_path"]).read_text())
    assert result["converged"] is False
    assert result["status"] == "pending_review"
    assert feature_doc["trajectory"]["requirements"]["status"] == "pending_review"
    assert result["evaluator_summary"]["pending"] == 1

    start = gen_start(project_root)
    assert start["state"] == "PENDING_HUMAN_REVIEW"
    assert start["action"] == "review"
    assert start["feature"] == "REQ-F-HUMAN-001"
    assert start["edge"] == "intent→requirements"


def test_gen_spawn_creates_child_and_blocks_parent(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-PARENT-001", profile="standard")

    result = gen_spawn(
        project_root,
        vector_type="spike",
        parent="REQ-F-PARENT-001",
        reason="Assess websocket viability",
        parent_edge="requirements→design",
    )

    child_doc = yaml.safe_load(Path(result["child_path"]).read_text())
    parent_doc = yaml.safe_load((paths.active_features_dir / "REQ-F-PARENT-001.yml").read_text())

    assert child_doc["vector_type"] == "spike"
    assert child_doc["parent"]["feature"] == "REQ-F-PARENT-001"
    assert child_doc["time_box"]["duration"] == "1 week"
    assert parent_doc["status"] == "blocked"
    assert parent_doc["trajectory"]["design"]["blocked_by"] == child_doc["feature"]

    semantic_types = [event.semantic_type for event in load_events(paths.events_file)]
    assert "SpawnCreated" in semantic_types


def test_gen_fold_back_updates_parent_and_completes_child(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-PARENT-002", profile="standard")
    spawn = gen_spawn(
        project_root,
        vector_type="spike",
        parent="REQ-F-PARENT-002",
        reason="Assess caching approach",
        parent_edge="requirements→design",
    )

    result = gen_fold_back(
        project_root,
        child=Path(spawn["child_path"]).stem,
        summary="Recommendation: proceed with Redis-backed cache.",
    )

    parent_doc = yaml.safe_load((paths.active_features_dir / "REQ-F-PARENT-002.yml").read_text())
    child_id = Path(spawn["child_path"]).stem
    completed_child = paths.completed_features_dir / f"{child_id}.yml"
    assert completed_child.exists()
    assert parent_doc["status"] == "in_progress"
    assert parent_doc["context"]["fold_backs"][0]["feature"] == child_id
    assert parent_doc["children"][0]["fold_back_status"] == "folded_back"
    assert Path(result["payload_path"]).exists()

    semantic_types = [event.semantic_type for event in load_events(paths.events_file)]
    assert "SpawnFoldedBack" in semantic_types


def test_gen_gaps_reports_clusters_and_emits_intents(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    _write_traceability_assets(project_root)

    result = gen_gaps(project_root)
    report = result["report"]

    assert report["total_req_keys"] == 3
    assert "REQ-F-AUTH-001" in report["full_coverage"]
    assert "REQ-F-AUTH-002" in report["partial_coverage"]
    assert "REQ-NFR-PERF-001" in report["no_coverage"]
    assert result["intent_run_ids"]

    semantic_types = [event.semantic_type for event in load_events(RuntimePaths(project_root).events_file)]
    assert "GapsValidated" in semantic_types
    assert semantic_types.count("IntentRaised") >= 2


def test_gen_release_writes_manifest_and_emits_release_event(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    _write_traceability_assets(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-REL-001", profile="minimal")
    feature_doc = yaml.safe_load((paths.active_features_dir / "REQ-F-REL-001.yml").read_text())
    feature_doc["status"] = "converged"
    (paths.completed_features_dir / "REQ-F-REL-001.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))
    (paths.active_features_dir / "REQ-F-REL-001.yml").unlink()

    result = gen_release(project_root, version="0.2.0")
    manifest = yaml.safe_load(Path(result["manifest_path"]).read_text())

    assert manifest["version"] == "0.2.0"
    assert manifest["date"].endswith("Z")
    assert manifest["features_included"] == {"REQ-F-REL-001": "converged"}
    assert result["release_run_id"] is not None

    semantic_types = [event.semantic_type for event in load_events(paths.events_file)]
    assert "ReleaseCreated" in semantic_types


def test_gen_trace_reconstructs_cross_artifact_paths(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    _write_traceability_assets(project_root)
    gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="intent→requirements",
        profile="minimal",
        delta=0,
        converged=True,
    )

    result = gen_trace(project_root, req_key="REQ-F-AUTH-001")

    assert result["req_key"] == "REQ-F-AUTH-001"
    assert result["forward"]["intent"] == "specification/INTENT.md"
    assert result["forward"]["features"][0]["feature"] == "REQ-F-AUTH-001"
    assert "src/auth.py" in result["forward"]["code"]
    assert "tests/test_auth.py" in result["forward"]["tests"]
    assert "imp_codex/design/auth_design.md" in result["forward"]["design"]
    assert "src/auth.py" in result["forward"]["telemetry"]
    assert result["gaps"] == []


def test_gen_checkpoint_writes_manifest_snapshot_and_event(tmp_path):
    project_root = tmp_path / "demo"
    gen_init(project_root, project_name="demo")
    paths = RuntimePaths(project_root)
    context_file = paths.codex_context_dir / "templates" / "coding.md"
    context_file.write_text("# Coding Standard\n")
    _write_feature(paths, "REQ-F-CP-001", profile="minimal")

    result = gen_checkpoint(project_root, message="pre-release")

    manifest = yaml.safe_load(Path(result["context_manifest_path"]).read_text())
    snapshot = yaml.safe_load(Path(result["snapshot_path"]).read_text())
    assert manifest["aggregate_hash"].startswith("sha256:")
    assert "templates/coding.md" in {entry["path"] for entry in manifest["entries"]}
    assert snapshot["message"] == "pre-release"
    assert snapshot["context_hash"] == manifest["aggregate_hash"]
    assert snapshot["feature_states"][0]["feature"] == "REQ-F-CP-001"

    semantic_types = [event.semantic_type for event in load_events(paths.events_file)]
    assert "CheckpointCreated" in semantic_types


def test_gen_iterate_can_run_agent_checks_from_edge_config(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    _write_traceability_assets(project_root)

    result = gen_iterate(
        project_root,
        feature="REQ-F-AUTH-001",
        edge="design→code",
        profile="minimal",
    )

    assert result["status"] == "converged"
    assert result["evaluator_summary"]["failed"] == 0
    assert result["evaluator_summary"]["passed"] >= 3
    assert all(item["name"] != "stub_execution" for item in result["evaluator_summary"]["details"])
