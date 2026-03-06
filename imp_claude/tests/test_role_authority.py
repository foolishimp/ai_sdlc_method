# Validates: REQ-COORD-005 (Role-Based Evaluator Authority)
"""Tests for role_authority.py — REQ-COORD-005."""

import json
from pathlib import Path

import pytest

from genesis.role_authority import (
    check_convergence_gate,
    check_role_authority,
    convergence_action,
    emit_convergence_escalated,
    get_outside_authority_action,
    load_role_config,
    normalise_edge,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def minimal_roles_config() -> dict:
    return {
        "roles": {
            "architect": {
                "description": "designs architecture",
                "converge_edges": [
                    "intent_requirements",
                    "requirements_design",
                    "design_code",
                ],
            },
            "tdd_engineer": {
                "description": "TDD co-evolution",
                "converge_edges": ["code_unit_tests", "design_test_cases"],
            },
            "full_stack": {
                "description": "all edges",
                "converge_edges": ["all"],
            },
        },
        "authority": {
            "human_authority": "universal",
            "outside_authority_action": "escalate",
            "spec_mutation_requires_human": True,
        },
    }


@pytest.fixture
def warn_config(minimal_roles_config: dict) -> dict:
    cfg = dict(minimal_roles_config)
    cfg["authority"] = dict(minimal_roles_config["authority"])
    cfg["authority"]["outside_authority_action"] = "warn"
    return cfg


@pytest.fixture
def reject_config(minimal_roles_config: dict) -> dict:
    cfg = dict(minimal_roles_config)
    cfg["authority"] = dict(minimal_roles_config["authority"])
    cfg["authority"]["outside_authority_action"] = "reject"
    return cfg


# ── normalise_edge ─────────────────────────────────────────────────────────


class TestNormaliseEdge:
    def test_arrow_to_underscore(self) -> None:
        assert normalise_edge("design→code") == "design_code"

    def test_bidir_arrow_to_underscore(self) -> None:
        assert normalise_edge("code↔unit_tests") == "code_unit_tests"

    def test_intent_requirements(self) -> None:
        assert normalise_edge("intent→requirements") == "intent_requirements"

    def test_already_normalised(self) -> None:
        assert normalise_edge("code_unit_tests") == "code_unit_tests"

    def test_lowercased(self) -> None:
        assert normalise_edge("Design→Code") == "design_code"

    def test_telemetry_feedback(self) -> None:
        assert normalise_edge("telemetry→intent") == "telemetry_intent"


# ── check_role_authority ───────────────────────────────────────────────────


class TestCheckRoleAuthority:
    def test_architect_can_converge_intent_requirements(
        self, minimal_roles_config: dict
    ) -> None:
        assert check_role_authority("architect", "intent→requirements", minimal_roles_config)

    def test_architect_cannot_converge_code_unit_tests(
        self, minimal_roles_config: dict
    ) -> None:
        assert not check_role_authority(
            "architect", "code↔unit_tests", minimal_roles_config
        )

    def test_tdd_engineer_can_converge_tdd_edge(
        self, minimal_roles_config: dict
    ) -> None:
        assert check_role_authority(
            "tdd_engineer", "code↔unit_tests", minimal_roles_config
        )

    def test_tdd_engineer_cannot_converge_design_edge(
        self, minimal_roles_config: dict
    ) -> None:
        assert not check_role_authority(
            "tdd_engineer", "intent→requirements", minimal_roles_config
        )

    def test_full_stack_can_converge_any_edge(
        self, minimal_roles_config: dict
    ) -> None:
        assert check_role_authority(
            "full_stack", "code↔unit_tests", minimal_roles_config
        )
        assert check_role_authority(
            "full_stack", "intent→requirements", minimal_roles_config
        )
        assert check_role_authority(
            "full_stack", "running_system→telemetry", minimal_roles_config
        )

    def test_unknown_role_is_denied(self, minimal_roles_config: dict) -> None:
        assert not check_role_authority(
            "mystery_role", "code↔unit_tests", minimal_roles_config
        )

    def test_empty_config_fails_open(self) -> None:
        # No roles section → fail-open (allow)
        assert check_role_authority("any_role", "any_edge", {})

    def test_arrow_and_underscore_forms_equivalent(
        self, minimal_roles_config: dict
    ) -> None:
        # Arrow form "design→code" and snake form "design_code" are the same edge
        assert check_role_authority("architect", "design→code", minimal_roles_config)
        assert check_role_authority("architect", "design_code", minimal_roles_config)


# ── convergence_action ─────────────────────────────────────────────────────


class TestConvergenceAction:
    def test_default_escalate(self, minimal_roles_config: dict) -> None:
        assert convergence_action("tdd_engineer", "design_code", minimal_roles_config) == "escalate"

    def test_warn_configured(self, warn_config: dict) -> None:
        assert convergence_action("tdd_engineer", "design_code", warn_config) == "warn"

    def test_reject_configured(self, reject_config: dict) -> None:
        assert convergence_action("tdd_engineer", "design_code", reject_config) == "reject"

    def test_empty_config_defaults_escalate(self) -> None:
        assert convergence_action("any_role", "any_edge", {}) == "escalate"


# ── get_outside_authority_action ───────────────────────────────────────────


class TestGetOutsideAuthorityAction:
    def test_granted_when_authorised(self, minimal_roles_config: dict) -> None:
        assert (
            get_outside_authority_action("architect", "design→code", minimal_roles_config)
            == "granted"
        )

    def test_escalate_when_not_authorised(self, minimal_roles_config: dict) -> None:
        assert (
            get_outside_authority_action(
                "tdd_engineer", "design→code", minimal_roles_config
            )
            == "escalate"
        )

    def test_warn_action_when_not_authorised_warn_config(
        self, warn_config: dict
    ) -> None:
        assert (
            get_outside_authority_action("tdd_engineer", "design→code", warn_config)
            == "warn"
        )


# ── emit_convergence_escalated ─────────────────────────────────────────────


class TestEmitConvergenceEscalated:
    def test_emits_event_to_file(self, workspace: Path) -> None:
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        emit_convergence_escalated(
            events_path=events_path,
            project="test-proj",
            agent_id="agent-1",
            agent_role="tdd_engineer",
            feature="REQ-F-A",
            edge="design→code",
            reason="role not authorised",
            action="escalate",
        )
        assert events_path.exists()
        lines = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        ev = lines[0]
        assert ev["event_type"] == "convergence_escalated"
        assert ev["feature"] == "REQ-F-A"
        assert ev["edge"] == "design→code"
        assert ev["agent_id"] == "agent-1"
        assert ev["data"]["agent_role"] == "tdd_engineer"
        assert ev["data"]["action"] == "escalate"
        assert ev["data"]["norm_edge"] == "design_code"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        events_path = tmp_path / "deep" / "nested" / "events.jsonl"
        emit_convergence_escalated(
            events_path=events_path,
            project="test",
            agent_id="a",
            agent_role="tdd_engineer",
            feature="REQ-F-A",
            edge="design→code",
            reason="test",
        )
        assert events_path.exists()


# ── check_convergence_gate ─────────────────────────────────────────────────


class TestCheckConvergenceGate:
    def test_granted_for_authorised_role(
        self, workspace: Path, minimal_roles_config: dict
    ) -> None:
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="architect",
            feature="REQ-F-A",
            edge="design→code",
            roles_config=minimal_roles_config,
        )
        assert result["allowed"] is True
        assert result["action"] == "granted"
        # No event emitted for allowed convergences
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        assert not events_path.exists()

    def test_escalated_for_unauthorised_role(
        self, workspace: Path, minimal_roles_config: dict
    ) -> None:
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="tdd_engineer",
            feature="REQ-F-A",
            edge="intent→requirements",
            roles_config=minimal_roles_config,
        )
        assert result["allowed"] is False
        assert result["action"] == "escalate"

        # Event emitted
        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        assert len(events) == 1
        assert events[0]["event_type"] == "convergence_escalated"

    def test_warn_allows_convergence_and_emits_event(
        self, workspace: Path, warn_config: dict
    ) -> None:
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="tdd_engineer",
            feature="REQ-F-A",
            edge="intent→requirements",
            roles_config=warn_config,
        )
        assert result["allowed"] is True
        assert result["action"] == "warn"

        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        assert events[0]["event_type"] == "convergence_escalated"
        assert events[0]["data"]["action"] == "warn"

    def test_reject_blocks_convergence(
        self, workspace: Path, reject_config: dict
    ) -> None:
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="tdd_engineer",
            feature="REQ-F-A",
            edge="intent→requirements",
            roles_config=reject_config,
        )
        assert result["allowed"] is False
        assert result["action"] == "reject"

    def test_full_stack_always_granted(
        self, workspace: Path, minimal_roles_config: dict
    ) -> None:
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="full_stack",
            feature="REQ-F-A",
            edge="running_system→telemetry",
            roles_config=minimal_roles_config,
        )
        assert result["allowed"] is True
        assert result["action"] == "granted"

    def test_loads_default_config_when_none_provided(self, workspace: Path) -> None:
        """Should not raise — default config loads from bundled agent_roles.yml."""
        result = check_convergence_gate(
            workspace=workspace,
            project="test-proj",
            agent_id="agent-1",
            agent_role="full_stack",
            feature="REQ-F-A",
            edge="code↔unit_tests",
        )
        assert result["allowed"] is True
