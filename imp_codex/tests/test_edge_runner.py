# Validates: REQ-F-DISPATCH-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Codex-native EDGE_RUNNER tests derived from the Claude spec suite."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from imp_codex.runtime.edge_runner import (
    COST_PER_FP_ITERATION,
    DispatchTarget,
    EdgeRunResult,
    _check_fp_result,
    _write_fp_manifest,
    run_edge,
)
from imp_codex.runtime.events import load_events
from imp_codex.runtime.paths import RuntimePaths, bootstrap_workspace


def _make_target(
    *,
    intent_id: str = "INT-001",
    feature_id: str = "REQ-F-TEST-001",
    edge: str = "code↔unit_tests",
    feature_vector: dict | None = None,
) -> DispatchTarget:
    return DispatchTarget(
        intent_id=intent_id,
        feature_id=feature_id,
        edge=edge,
        intent_event={"intent_id": intent_id},
        feature_vector=feature_vector or {
            "feature": feature_id,
            "profile": "standard",
            "trajectory": {},
        },
    )


def _event_types(events_path: Path) -> list[str]:
    return [
        event.raw.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type")
        for event in load_events(events_path)
    ]


def _configure_noop_tools(paths: RuntimePaths) -> None:
    constraints = yaml.safe_load(paths.project_constraints_path.read_text())
    for tool_name in ("syntax_checker", "linter", "type_checker", "test_runner", "coverage", "formatter"):
        constraints["tools"][tool_name]["command"] = "python"
        constraints["tools"][tool_name]["args"] = "-c \"print('ok')\""
    paths.project_constraints_path.write_text(yaml.safe_dump(constraints, sort_keys=False))


def _configure_agent_invocation(paths: RuntimePaths) -> Path:
    constraints = yaml.safe_load(paths.project_constraints_path.read_text())
    constraints["agent_invocation"] = {
        "mode": "file",
        "fallback": "heuristic",
        "file": ".ai-workspace/codex/context/agent_evaluations.json",
    }
    paths.project_constraints_path.write_text(yaml.safe_dump(constraints, sort_keys=False))
    return paths.codex_context_dir / "agent_evaluations.json"


def _write_feature(paths: RuntimePaths, feature_id: str) -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = "standard"
    feature_doc["status"] = "in_progress"
    feature_doc["trajectory"] = {
        "requirements": {"status": "converged", "delta": 0},
        "design": {"status": "converged", "delta": 0},
        "code": {"status": "converged", "delta": 0},
    }
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def test_fd_converged_returns_converged_status(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (0, []))

    result = run_edge(target, tmp_path)

    assert result.status == "converged"
    assert result.delta == 0
    assert result.iterations == 1


def test_fd_converged_emits_edge_started_and_edge_converged(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (0, []))

    result = run_edge(target, tmp_path)

    assert "EdgeStarted" in result.events_emitted
    assert "IterationCompleted" in result.events_emitted
    assert "EdgeConverged" in result.events_emitted
    assert _event_types(tmp_path / ".ai-workspace" / "events" / "events.jsonl") == [
        "edge_started",
        "iteration_completed",
        "edge_converged",
    ]


def test_fd_delta_triggers_fp_dispatch_and_manifest_write(tmp_path, monkeypatch):
    target = _make_target(feature_id="REQ-F-DISP-001", edge="design→code")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (2, ["fd_check"]))

    result = run_edge(target, tmp_path)

    assert result.status == "fp_dispatched"
    assert result.delta == 2
    assert result.fp_manifest_path
    manifest = json.loads(Path(result.fp_manifest_path).read_text())
    assert manifest["edge"] == "design→code"
    assert manifest["feature"] == "REQ-F-DISP-001"
    assert manifest["intent_id"] == "INT-001"
    assert manifest["status"] == "pending"
    assert manifest["failures"] == ["fd_check"]


def test_fp_result_re_evaluates_until_converged(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    calls = {"count": 0}

    def _fd(*_args, **_kwargs):
        calls["count"] += 1
        return (1, ["check_a"]) if calls["count"] == 1 else (0, [])

    monkeypatch.setattr(er, "_run_fd_evaluation", _fd)
    monkeypatch.setattr(
        er,
        "_check_fp_result",
        lambda *_args, **_kwargs: {
            "converged": True,
            "delta": 0,
            "cost_usd": 0.10,
            "artifacts": [],
            "spawns": [],
        },
    )

    result = run_edge(target, tmp_path)

    assert result.status == "converged"
    assert result.iterations == 2
    assert result.cost_usd == 0.1


def test_max_fp_iterations_escalates_to_fh_required(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (1, ["check_a"]))
    monkeypatch.setattr(
        er,
        "_check_fp_result",
        lambda *_args, **_kwargs: {
            "converged": False,
            "delta": 1,
            "cost_usd": 0.05,
            "artifacts": [],
            "spawns": [],
        },
    )

    result = run_edge(target, tmp_path, max_fp_iterations=2)

    assert result.status == "fh_required"
    events = load_events(tmp_path / ".ai-workspace" / "events" / "events.jsonl")
    intent_events = [
        event for event in events
        if event.raw.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "intent_raised"
    ]
    assert len(intent_events) == 1
    assert intent_events[0].raw["run"]["facets"]["sdlc:payload"]["signal_source"] == "human_gate_required"


def test_pending_review_with_consensus_policy_opens_review_cycle(tmp_path, monkeypatch):
    target = _make_target(
        feature_id="REQ-F-CONS-001",
        edge="intent→requirements",
        feature_vector={
            "feature": "REQ-F-CONS-001",
            "profile": "standard",
            "trajectory": {},
        },
    )

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(
        er,
        "_review_policy",
        lambda *_args, **_kwargs: {
            "mode": "consensus",
            "roster": ["human:alice", "human:bob"],
            "quorum": "majority",
            "asset_version": "v1",
            "min_duration_seconds": 0,
            "review_closes_in": 86400,
        },
    )

    result = run_edge(target, tmp_path)

    assert result.status == "consensus_requested"
    assert result.fh_mode == "consensus"
    assert result.review_id is not None
    assert result.cycle_id == "CYCLE-001"
    assert result.consensus_requested_run_id is not None
    assert "ConsensusRequested" in result.events_emitted
    assert "consensus_requested" in _event_types(tmp_path / ".ai-workspace" / "events" / "events.jsonl")


def test_budget_exhaustion_with_consensus_policy_opens_review_cycle(tmp_path, monkeypatch):
    target = _make_target(feature_id="REQ-F-CONS-002", edge="design→code")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (1, ["check_a"]))
    monkeypatch.setattr(
        er,
        "_review_policy",
        lambda *_args, **_kwargs: {
            "mode": "consensus",
            "roster": ["human:alice", "human:bob"],
            "quorum": "majority",
            "asset_version": "v2",
            "min_duration_seconds": 0,
            "review_closes_in": 86400,
        },
    )

    result = run_edge(target, tmp_path, budget_usd=0.0)

    assert result.status == "consensus_requested"
    assert result.fh_mode == "consensus"
    assert result.review_id is not None
    semantic_types = _event_types(tmp_path / ".ai-workspace" / "events" / "events.jsonl")
    assert "consensus_requested" in semantic_types
    assert "intent_raised" not in semantic_types


def test_budget_exhaustion_escalates_before_fp_dispatch(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (1, ["check_a"]))
    monkeypatch.setattr(
        er,
        "_check_fp_result",
        lambda *_args, **_kwargs: {
            "converged": True,
            "delta": 0,
            "cost_usd": 1.0,
            "artifacts": [],
            "spawns": [],
        },
    )

    result = run_edge(target, tmp_path, budget_usd=COST_PER_FP_ITERATION / 3)

    assert result.status == "fh_required"


def test_fp_failure_result_emits_iteration_failed_and_schedules_retry(tmp_path, monkeypatch):
    target = _make_target(feature_id="REQ-F-RETRY-001", edge="design→code")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (1, ["check_a"]))
    monkeypatch.setattr(er, "_check_fp_result", lambda *_args, **_kwargs: {"status": "timeout", "cost_usd": 0.0})

    result = run_edge(target, tmp_path, max_fp_iterations=3)

    assert result.status == "fp_dispatched"
    assert result.fp_manifest_path
    assert Path(result.fp_manifest_path).exists()
    semantic_types = _event_types(tmp_path / ".ai-workspace" / "events" / "events.jsonl")
    assert semantic_types.count("edge_started") == 2
    assert "IterationFailed" in semantic_types


def test_terminal_fp_failure_routes_to_human_gate(tmp_path, monkeypatch):
    target = _make_target(feature_id="REQ-F-FP-FAIL-001", edge="design→code")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (1, ["check_a"]))
    monkeypatch.setattr(er, "_check_fp_result", lambda *_args, **_kwargs: {"status": "timeout", "cost_usd": 0.0})

    result = run_edge(target, tmp_path, max_fp_iterations=1)

    assert result.status == "fh_required"
    assert result.intent_run_id is not None
    semantic_types = _event_types(tmp_path / ".ai-workspace" / "events" / "events.jsonl")
    assert "IterationAbandoned" in semantic_types
    assert "intent_raised" in semantic_types


def test_run_id_is_unique_per_invocation(tmp_path, monkeypatch):
    target = _make_target()

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (0, []))

    result1 = run_edge(target, tmp_path)
    result2 = run_edge(target, tmp_path)

    assert result1.run_id != result2.run_id


def test_edge_started_payload_carries_intent_id(tmp_path, monkeypatch):
    target = _make_target(intent_id="INT-TRACK-001")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (0, []))

    run_edge(target, tmp_path)
    events = load_events(tmp_path / ".ai-workspace" / "events" / "events.jsonl")
    started = events[0]
    assert started.raw["run"]["facets"]["sdlc:payload"]["intent_id"] == "INT-TRACK-001"


def test_write_fp_manifest_writes_expected_shape(tmp_path):
    target = _make_target(feature_id="REQ-F-X-001", edge="design→code")

    path = _write_fp_manifest(target, tmp_path, "run-456", 2, 0.5, ["f1", "f2"])

    assert path.name == "fp_intent_run-456.json"
    data = json.loads(path.read_text())
    assert data["run_id"] == "run-456"
    assert data["edge"] == "design→code"
    assert data["feature"] == "REQ-F-X-001"
    assert data["iteration"] == 2
    assert data["failures"] == ["f1", "f2"]
    assert data["budget_remaining_usd"] == 0.5
    assert "result_path" in data


def test_check_fp_result_returns_none_without_result_file(tmp_path):
    assert _check_fp_result(tmp_path, "missing-run") is None


def test_edge_run_result_shape_is_populated(tmp_path, monkeypatch):
    target = _make_target(feature_id="REQ-F-DISP-001", edge="design→code")

    import imp_codex.runtime.edge_runner as er

    monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: (0, []))

    result = run_edge(target, tmp_path)

    assert isinstance(result, EdgeRunResult)
    assert result.run_id
    assert result.edge_started_run_id == result.run_id
    assert result.feature_id == "REQ-F-DISP-001"
    assert result.edge == "design→code"
    assert result.status == "converged"
    assert result.iterations >= 1
    assert result.cost_usd >= 0.0
    assert isinstance(result.events_emitted, list)


def test_default_run_edge_populates_iteration_run_ids(tmp_path):
    target = _make_target(
        feature_id="REQ-F-INTEGRATED-001",
        edge="intent→requirements",
        feature_vector={
            "feature": "REQ-F-INTEGRATED-001",
            "profile": "minimal",
            "trajectory": {},
        },
    )

    result = run_edge(target, tmp_path)

    assert result.edge_started_run_id == result.run_id
    assert result.iteration_start_run_id is not None
    assert result.completed_run_id is not None
    assert result.status in {"converged", "fp_dispatched", "pending_review", "fh_required"}

    semantic_types = [event.semantic_type for event in load_events(tmp_path / ".ai-workspace" / "events" / "events.jsonl")]
    assert "IterationStarted" in semantic_types
    assert "IterationCompleted" in semantic_types


def test_run_edge_run_agent_executes_fp_work_and_converges_with_file_contract(tmp_path):
    project_root = tmp_path / "demo"
    paths = bootstrap_workspace(project_root, project_name="demo")
    _configure_noop_tools(paths)
    invocation_file = _configure_agent_invocation(paths)

    specification = project_root / "specification"
    specification.mkdir(parents=True, exist_ok=True)
    (specification / "INTENT.md").write_text("# Intent\n\nBuild auth.\n")
    (specification / "requirements.md").write_text("# Requirements\n\n- REQ-F-AUTH-001\n")

    _write_feature(paths, "REQ-F-AUTH-001")

    invocation_file.write_text(
        json.dumps(
            {
                "fp_results": [
                    {
                        "feature": "REQ-F-AUTH-001",
                        "edge": "code↔unit_tests",
                        "status": "completed",
                        "message": "Generated code and tests",
                        "converged": False,
                        "delta": 1,
                        "cost_usd": 0.15,
                        "artifacts": [
                            {
                                "path": "src/auth.py",
                                "content": "\n".join(
                                    [
                                        "# Implements: REQ-F-AUTH-001",
                                        "",
                                        "def login() -> bool:",
                                        "    return True",
                                    ]
                                )
                                + "\n",
                            },
                            {
                                "path": "tests/test_auth.py",
                                "content": "\n".join(
                                    [
                                        "# Validates: REQ-F-AUTH-001",
                                        "",
                                        "def test_login() -> None:",
                                        "    assert True",
                                    ]
                                )
                                + "\n",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
    )

    target = _make_target(
        feature_id="REQ-F-AUTH-001",
        edge="code↔unit_tests",
        feature_vector={
            "feature": "REQ-F-AUTH-001",
            "profile": "standard",
            "status": "in_progress",
            "trajectory": {
                "requirements": {"status": "converged", "delta": 0},
                "design": {"status": "converged", "delta": 0},
                "code": {"status": "converged", "delta": 0},
            },
        },
    )

    result = run_edge(target, project_root, run_agent=True)

    assert result.status == "converged"
    assert result.iterations == 2
    assert result.fp_manifest_path
    assert (project_root / "src" / "auth.py").exists()
    assert (project_root / "tests" / "test_auth.py").exists()
    manifest = json.loads(Path(result.fp_manifest_path).read_text())
    assert manifest["status"] == "completed"
    fp_result = _check_fp_result(project_root, result.run_id)
    assert fp_result is not None
    assert fp_result["provider"] == "file"
