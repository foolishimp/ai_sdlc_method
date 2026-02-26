"""Tests for genesis_engine.engine — core iterate/evaluate with pluggable F_P."""

import json
from pathlib import Path

import yaml

from genesis_engine.engine import EngineConfig, iterate_edge, run_edge
from genesis_engine.models import CheckOutcome, CheckResult, ResolvedCheck
from genesis_engine.providers.base import FPProvider


class AlwaysPassProvider(FPProvider):
    """Test provider that always passes agent checks."""

    @property
    def name(self):
        return "always_pass"

    def run_check(self, check, asset_content, context="", timeout=120):
        return CheckResult(
            name=check.name, outcome=CheckOutcome.PASS,
            required=check.required, check_type=check.check_type,
            functional_unit=check.functional_unit, message="auto pass",
        )


class AlwaysFailProvider(FPProvider):
    """Test provider that always fails agent checks."""

    @property
    def name(self):
        return "always_fail"

    def run_check(self, check, asset_content, context="", timeout=120):
        return CheckResult(
            name=check.name, outcome=CheckOutcome.FAIL,
            required=check.required, check_type=check.check_type,
            functional_unit=check.functional_unit, message="auto fail",
        )


def _make_edge_config(checks):
    """Build an edge config dict with a checklist."""
    return {"checklist": checks}


def _make_config(tmp_workspace, constraints, provider=None, det_only=False):
    """Build an EngineConfig for testing."""
    edge_params = tmp_workspace / ".ai-workspace" / "graph" / "edges"
    edge_params.mkdir(parents=True, exist_ok=True)
    profiles = tmp_workspace / ".ai-workspace" / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)

    return EngineConfig(
        project_name="test-project",
        workspace_path=tmp_workspace,
        edge_params_dir=edge_params,
        profiles_dir=profiles,
        constraints=constraints,
        graph_topology={},
        provider=provider,
        deterministic_only=det_only,
    )


def test_iterate_edge_deterministic_pass(tmp_workspace, constraints):
    """A passing deterministic check should converge."""
    edge_config = _make_edge_config([
        {
            "name": "echo_test",
            "type": "deterministic",
            "criterion": "echo succeeds",
            "command": "echo hello",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, det_only=True)

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.converged is True
    assert record.evaluation.delta == 0
    assert record.evaluation.checks[0].outcome == CheckOutcome.PASS

    # Check event was emitted
    events_path = tmp_workspace / ".ai-workspace" / "events" / "events.jsonl"
    assert events_path.exists()
    lines = events_path.read_text().strip().split("\n")
    assert len(lines) >= 1
    event = json.loads(lines[0])
    assert event["event_type"] == "iteration_completed"


def test_iterate_edge_deterministic_fail(tmp_workspace, constraints):
    """A failing required check should produce delta > 0."""
    edge_config = _make_edge_config([
        {
            "name": "bad_check",
            "type": "deterministic",
            "criterion": "must fail",
            "command": "false",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, det_only=True)

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.converged is False
    assert record.evaluation.delta == 1


def test_iterate_edge_with_provider_pass(tmp_workspace, constraints):
    """Agent checks should use the pluggable provider."""
    edge_config = _make_edge_config([
        {
            "name": "agent_check",
            "type": "agent",
            "criterion": "is code good?",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, provider=AlwaysPassProvider())

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.converged is True
    assert record.evaluation.checks[0].outcome == CheckOutcome.PASS


def test_iterate_edge_with_provider_fail(tmp_workspace, constraints):
    """Failing agent provider should produce delta."""
    edge_config = _make_edge_config([
        {
            "name": "agent_check",
            "type": "agent",
            "criterion": "is code good?",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, provider=AlwaysFailProvider())

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.converged is False
    assert record.evaluation.delta == 1
    assert record.evaluation.checks[0].outcome == CheckOutcome.FAIL


def test_iterate_edge_no_provider_skips_agent(tmp_workspace, constraints):
    """Without a provider, agent checks should be skipped."""
    edge_config = _make_edge_config([
        {
            "name": "agent_check",
            "type": "agent",
            "criterion": "test",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, provider=None)

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.checks[0].outcome == CheckOutcome.SKIP
    assert "no F_P provider" in record.evaluation.checks[0].message


def test_iterate_edge_human_skipped(tmp_workspace, constraints):
    """Human checks should always be skipped."""
    edge_config = _make_edge_config([
        {
            "name": "human_review",
            "type": "human",
            "criterion": "human approval",
            "required": False,
        }
    ])
    config = _make_config(tmp_workspace, constraints)

    record = iterate_edge(
        edge="intent→requirements", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.checks[0].outcome == CheckOutcome.SKIP


def test_iterate_edge_mixed_checks(tmp_workspace, constraints):
    """Mixed deterministic + agent checks with provider."""
    edge_config = _make_edge_config([
        {
            "name": "det_pass",
            "type": "deterministic",
            "criterion": "echo ok",
            "command": "echo ok",
            "required": True,
        },
        {
            "name": "agent_pass",
            "type": "agent",
            "criterion": "looks good?",
            "required": True,
        },
    ])
    config = _make_config(tmp_workspace, constraints, provider=AlwaysPassProvider())

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert record.evaluation.converged is True
    assert record.evaluation.delta == 0
    assert len(record.evaluation.checks) == 2


def test_iterate_edge_emits_convergence_event(tmp_workspace, constraints):
    """Converged iteration should emit both iteration_completed and edge_converged."""
    edge_config = _make_edge_config([
        {
            "name": "pass_check",
            "type": "deterministic",
            "criterion": "pass",
            "command": "true",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, det_only=True)

    iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    events_path = tmp_workspace / ".ai-workspace" / "events" / "events.jsonl"
    lines = events_path.read_text().strip().split("\n")
    event_types = [json.loads(line)["event_type"] for line in lines]
    assert "iteration_completed" in event_types
    assert "edge_converged" in event_types


def test_iterate_edge_records_provider_in_event(tmp_workspace, constraints):
    """Events should record which provider was used."""
    edge_config = _make_edge_config([
        {
            "name": "agent_check",
            "type": "agent",
            "criterion": "test",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, provider=AlwaysPassProvider())

    iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    events_path = tmp_workspace / ".ai-workspace" / "events" / "events.jsonl"
    event = json.loads(events_path.read_text().strip().split("\n")[0])
    assert event["provider"] == "always_pass"


def test_run_edge_converges(tmp_workspace, constraints):
    """run_edge should stop on convergence."""
    edge_params = tmp_workspace / ".ai-workspace" / "graph" / "edges"
    edge_params.mkdir(parents=True, exist_ok=True)

    edge_config = {
        "checklist": [
            {
                "name": "pass_check",
                "type": "deterministic",
                "criterion": "always pass",
                "command": "true",
                "required": True,
            }
        ]
    }
    with open(edge_params / "tdd.yml", "w") as f:
        yaml.dump(edge_config, f)

    config = _make_config(tmp_workspace, constraints, det_only=True)

    records = run_edge(
        edge="code↔unit_tests", config=config,
        feature_id="REQ-F-TEST-001", profile={},
        asset_content="test",
    )

    assert len(records) == 1
    assert records[0].evaluation.converged is True


def test_escalation_detection(tmp_workspace, constraints):
    """Failing required checks should generate escalation entries."""
    edge_config = _make_edge_config([
        {
            "name": "failing_det",
            "type": "deterministic",
            "criterion": "must fail",
            "command": "false",
            "required": True,
        }
    ])
    config = _make_config(tmp_workspace, constraints, det_only=True)

    record = iterate_edge(
        edge="code↔unit_tests", edge_config=edge_config,
        config=config, feature_id="REQ-F-TEST-001", asset_content="test",
    )

    assert len(record.evaluation.escalations) == 1
    assert "η_D→P" in record.evaluation.escalations[0]
