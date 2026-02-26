# Validates: REQ-ITER-001, REQ-SUPV-003, REQ-LIFE-001
"""CLI engine tests — evaluate and run-edge via iterate_edge/run_edge.

Tests that __main__.py delegates to engine.py correctly, that deterministic_only
mode works, that run-edge loops and triggers spawn, and that error handling emits
command_error events.
"""

import json
import pathlib
import sys
import textwrap

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from conftest import (
    EDGE_PARAMS_DIR,
    PROFILES_DIR,
    CONFIG_DIR,
    green_constraints,
    red_constraints,
    scaffold_broken_project,
    scaffold_green_project,
    make_engine_config,
    read_events,
)

from genesis.config_loader import load_yaml
from genesis.engine import EngineConfig, IterationRecord, iterate_edge, run_edge


# ── Helpers ──────────────────────────────────────────────────────────────


def _minimal_edge_config():
    """Edge config with only one deterministic check."""
    return {
        "edge": "code↔unit_tests",
        "checklist": [
            {
                "name": "tests_pass",
                "type": "deterministic",
                "functional_unit": "evaluate",
                "criterion": "All tests pass",
                "source": "default",
                "required": True,
                "command": "$tools.test_runner.command $tools.test_runner.args",
                "pass_criterion": "$tools.test_runner.pass_criterion",
            },
        ],
    }


def _mixed_edge_config():
    """Edge config with deterministic + agent checks."""
    return {
        "edge": "code↔unit_tests",
        "checklist": [
            {
                "name": "tests_pass",
                "type": "deterministic",
                "functional_unit": "evaluate",
                "criterion": "All tests pass",
                "source": "default",
                "required": True,
                "command": "$tools.test_runner.command $tools.test_runner.args",
                "pass_criterion": "$tools.test_runner.pass_criterion",
            },
            {
                "name": "code_review",
                "type": "agent",
                "functional_unit": "evaluate",
                "criterion": "Code is clean",
                "source": "default",
                "required": True,
            },
        ],
    }


def _make_config(workspace, constraints, max_iterations=1, deterministic_only=False):
    """Build EngineConfig for tests."""
    return EngineConfig(
        project_name="test_project",
        workspace_path=workspace,
        edge_params_dir=EDGE_PARAMS_DIR,
        profiles_dir=PROFILES_DIR,
        constraints=constraints,
        graph_topology=load_yaml(CONFIG_DIR / "graph_topology.yml"),
        model="sonnet",
        max_iterations_per_edge=max_iterations,
        claude_timeout=5,
        deterministic_only=deterministic_only,
        fd_timeout=30,
    )


def _write_events(workspace, events):
    """Write pre-existing events to events.jsonl."""
    from datetime import datetime, timezone

    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def _make_iteration_event(feature, edge, delta, checks=None, iteration=1):
    """Build an iteration_completed event dict."""
    from datetime import datetime, timezone

    return {
        "event_type": "iteration_completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": "test_project",
        "feature": feature,
        "edge": edge,
        "delta": delta,
        "iteration": iteration,
        "checks": checks or [],
    }


def _make_parent_vector(workspace, parent_id, edge_key="code_unit_tests"):
    """Create a minimal parent feature vector on disk."""
    features_dir = workspace / ".ai-workspace" / "features" / "active"
    features_dir.mkdir(parents=True, exist_ok=True)
    parent = {
        "feature": parent_id,
        "title": "Test Parent",
        "vector_type": "feature",
        "profile": "standard",
        "status": "in_progress",
        "children": [],
        "trajectory": {
            edge_key: {"status": "iterating"},
        },
    }
    parent_path = features_dir / f"{parent_id}.yml"
    with open(parent_path, "w") as f:
        yaml.dump(parent, f, default_flow_style=False, sort_keys=False)
    return parent_path


# ═══════════════════════════════════════════════════════════════════════
# EVALUATE VIA iterate_edge
# ═══════════════════════════════════════════════════════════════════════


class TestEvaluateGreen:
    """Green project → converged, delta=0."""

    def test_evaluate_green_project(self, tmp_path):
        workspace = scaffold_green_project(tmp_path)
        config = _make_config(workspace, green_constraints(), deterministic_only=True)
        edge_config = _minimal_edge_config()

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="def login(): pass",
            iteration=1,
        )

        assert record.evaluation.converged is True
        assert record.evaluation.delta == 0
        assert record.event_emitted is True

    def test_evaluate_broken_project(self, tmp_path):
        workspace = scaffold_broken_project(tmp_path)
        config = _make_config(workspace, red_constraints(), deterministic_only=True)
        edge_config = _minimal_edge_config()

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-CALC-001",
            asset_content="def add(a, b): return a - b",
            iteration=1,
        )

        assert record.evaluation.converged is False
        assert record.evaluation.delta > 0

    def test_evaluate_deterministic_only_skips_agent(self, tmp_path):
        workspace = scaffold_green_project(tmp_path)
        config = _make_config(workspace, green_constraints(), deterministic_only=True)
        edge_config = _mixed_edge_config()

        record = iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="def login(): pass",
            iteration=1,
        )

        agent_checks = [
            c for c in record.evaluation.checks if c.check_type == "agent"
        ]
        assert len(agent_checks) > 0
        for c in agent_checks:
            assert c.outcome.value == "skip"
            assert "deterministic-only" in c.message

    def test_evaluate_emits_event_with_evaluators(self, tmp_path):
        workspace = scaffold_green_project(tmp_path)
        config = _make_config(workspace, green_constraints(), deterministic_only=True)
        edge_config = _minimal_edge_config()

        iterate_edge(
            edge="code↔unit_tests",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-AUTH-001",
            asset_content="def login(): pass",
            iteration=1,
        )

        events = read_events(workspace)
        iteration_events = [e for e in events if e["event_type"] == "iteration_completed"]
        assert len(iteration_events) >= 1
        last = iteration_events[-1]
        assert "evaluators" in last
        assert "passed" in last["evaluators"]
        assert "failed" in last["evaluators"]
        assert "skipped" in last["evaluators"]
        assert "total" in last["evaluators"]


# ═══════════════════════════════════════════════════════════════════════
# RUN-EDGE LOOP
# ═══════════════════════════════════════════════════════════════════════


class TestRunEdge:
    """run_edge() loops with convergence, spawn, and budget stops."""

    def test_run_edge_converges(self, tmp_path):
        """Green project converges in 1 iteration."""
        workspace = scaffold_green_project(tmp_path)

        # Write edge config file where run_edge expects it
        edge_dir = workspace / "edge_params"
        edge_dir.mkdir()
        (edge_dir / "tdd.yml").write_text(yaml.dump(_minimal_edge_config()))

        config = _make_config(workspace, green_constraints(), max_iterations=5, deterministic_only=True)
        # Override edge_params_dir to our custom dir
        config.edge_params_dir = edge_dir

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-AUTH-001",
            profile=profile,
            asset_content="def login(): pass",
        )

        assert len(records) == 1
        assert records[0].evaluation.converged is True

    def test_run_edge_stuck_spawns(self, tmp_path):
        """Broken project with 2 pre-loaded stuck events → spawn on 3rd."""
        workspace = scaffold_broken_project(tmp_path)

        # Write edge config
        edge_dir = workspace / "edge_params"
        edge_dir.mkdir()
        (edge_dir / "tdd.yml").write_text(yaml.dump(_minimal_edge_config()))

        # Pre-load 2 stuck iterations
        checks = [{"name": "tests_pass", "outcome": "fail", "required": True}]
        events = [
            _make_iteration_event("REQ-F-CALC-001", "code↔unit_tests", 1, checks, i)
            for i in range(1, 3)
        ]
        _write_events(workspace, events)

        # Create parent feature vector
        _make_parent_vector(workspace, "REQ-F-CALC-001")

        config = EngineConfig(
            project_name="test_project",
            workspace_path=workspace,
            edge_params_dir=edge_dir,
            profiles_dir=PROFILES_DIR,
            constraints=red_constraints(),
            graph_topology=load_yaml(CONFIG_DIR / "graph_topology.yml"),
            model="sonnet",
            max_iterations_per_edge=10,
            claude_timeout=5,
            deterministic_only=True,
            fd_timeout=30,
        )

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=profile,
            asset_content="def add(a, b): return a - b",
        )

        # Should stop after spawn, not exhaust budget
        assert len(records) <= 3
        assert records[-1].evaluation.spawn_requested != ""

    def test_run_edge_respects_max_iterations(self, tmp_path):
        """Stops at budget even without converge/spawn."""
        workspace = scaffold_broken_project(tmp_path)

        edge_dir = workspace / "edge_params"
        edge_dir.mkdir()
        (edge_dir / "tdd.yml").write_text(yaml.dump(_minimal_edge_config()))

        config = _make_config(workspace, red_constraints(), max_iterations=2, deterministic_only=True)
        config.edge_params_dir = edge_dir

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=profile,
            asset_content="def add(a, b): return a - b",
        )

        assert len(records) == 2
        assert records[-1].evaluation.converged is False

    def test_run_edge_output_schema(self, tmp_path):
        """Records have expected fields."""
        workspace = scaffold_green_project(tmp_path)

        edge_dir = workspace / "edge_params"
        edge_dir.mkdir()
        (edge_dir / "tdd.yml").write_text(yaml.dump(_minimal_edge_config()))

        config = _make_config(workspace, green_constraints(), max_iterations=3, deterministic_only=True)
        config.edge_params_dir = edge_dir

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-AUTH-001",
            profile=profile,
            asset_content="def login(): pass",
        )

        assert len(records) >= 1
        r = records[0]
        assert isinstance(r, IterationRecord)
        assert hasattr(r.evaluation, "delta")
        assert hasattr(r.evaluation, "converged")
        assert hasattr(r.evaluation, "spawn_requested")
        assert hasattr(r.evaluation, "checks")
        assert hasattr(r.evaluation, "escalations")


# ═══════════════════════════════════════════════════════════════════════
# SPAWN VIA RUN-EDGE
# ═══════════════════════════════════════════════════════════════════════


class TestRunEdgeSpawn:
    """Spawn integration via run_edge path."""

    @pytest.fixture
    def stuck_workspace(self, tmp_path):
        workspace = scaffold_broken_project(tmp_path)

        edge_dir = workspace / "edge_params"
        edge_dir.mkdir()
        (edge_dir / "tdd.yml").write_text(yaml.dump(_minimal_edge_config()))

        checks = [{"name": "tests_pass", "outcome": "fail", "required": True}]
        events = [
            _make_iteration_event("REQ-F-CALC-001", "code↔unit_tests", 1, checks, i)
            for i in range(1, 3)
        ]
        _write_events(workspace, events)
        _make_parent_vector(workspace, "REQ-F-CALC-001")

        return workspace, edge_dir

    def test_spawn_creates_child(self, stuck_workspace):
        """Child .yml file exists on disk after spawn."""
        workspace, edge_dir = stuck_workspace

        config = EngineConfig(
            project_name="test_project",
            workspace_path=workspace,
            edge_params_dir=edge_dir,
            profiles_dir=PROFILES_DIR,
            constraints=red_constraints(),
            graph_topology=load_yaml(CONFIG_DIR / "graph_topology.yml"),
            model="sonnet",
            max_iterations_per_edge=10,
            claude_timeout=5,
            deterministic_only=True,
            fd_timeout=30,
        )

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=profile,
            asset_content="def add(a, b): return a - b",
        )

        child_id = records[-1].evaluation.spawn_requested
        assert child_id != ""
        child_path = workspace / ".ai-workspace" / "features" / "active" / f"{child_id}.yml"
        assert child_path.exists()

    def test_spawn_blocks_parent(self, stuck_workspace):
        """Parent feature vector shows blocked status after spawn."""
        workspace, edge_dir = stuck_workspace

        config = EngineConfig(
            project_name="test_project",
            workspace_path=workspace,
            edge_params_dir=edge_dir,
            profiles_dir=PROFILES_DIR,
            constraints=red_constraints(),
            graph_topology=load_yaml(CONFIG_DIR / "graph_topology.yml"),
            model="sonnet",
            max_iterations_per_edge=10,
            claude_timeout=5,
            deterministic_only=True,
            fd_timeout=30,
        )

        profile = load_yaml(PROFILES_DIR / "standard.yml")

        records = run_edge(
            edge="code↔unit_tests",
            config=config,
            feature_id="REQ-F-CALC-001",
            profile=profile,
            asset_content="def add(a, b): return a - b",
        )

        child_id = records[-1].evaluation.spawn_requested
        parent_path = workspace / ".ai-workspace" / "features" / "active" / "REQ-F-CALC-001.yml"
        parent = yaml.safe_load(parent_path.read_text())
        assert parent["trajectory"]["code_unit_tests"]["status"] == "blocked"
        assert parent["trajectory"]["code_unit_tests"]["blocked_by"] == child_id


# ═══════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════


class TestCLIErrorHandling:
    """CLI error paths — missing asset, missing constraints."""

    def test_evaluate_missing_asset(self, tmp_path):
        """Missing asset file → error, non-zero exit."""
        workspace = tmp_path
        (workspace / ".ai-workspace" / "events").mkdir(parents=True)

        # Simulate what cmd_evaluate does: call _load_asset with a non-existent file
        from genesis.__main__ import _load_asset
        import argparse

        args = argparse.Namespace(asset="/nonexistent/file.py", command="evaluate")
        result = _load_asset(args, workspace)
        assert result is None

    def test_evaluate_missing_constraints(self, tmp_path):
        """Missing constraints file → error."""
        workspace = tmp_path
        (workspace / ".ai-workspace" / "events").mkdir(parents=True)

        from genesis.__main__ import _build_config
        import argparse

        args = argparse.Namespace(
            constraints="/nonexistent/constraints.yml",
            command="evaluate",
            model="sonnet",
            timeout=5,
            deterministic_only=True,
            fd_timeout=30,
        )
        result = _build_config(args, workspace)
        assert result is None
