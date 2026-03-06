# Validates: REQ-EVAL-003 (Human Accountability)
"""Tests for human_audit.py — human gate events and accountability audit trail."""

import json
from pathlib import Path

import pytest

from genesis.human_audit import (
    DECISION_APPROVE,
    DECISION_DEFER,
    DECISION_OVERRIDE_APPROVE,
    DECISION_REJECT,
    audit_summary,
    emit_human_decision,
    emit_human_gate_entered,
    get_human_decisions,
    get_human_gates,
    get_override_decisions,
    get_pending_gates,
    get_human_evaluators,
    load_events,
    requires_human_review,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _events_path(tmp_path: Path) -> Path:
    return tmp_path / "events" / "events.jsonl"


def _read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ── requires_human_review ─────────────────────────────────────────────────────


class TestRequiresHumanReview:
    def test_true_when_human_evaluator_present(self):
        config = {"checklist": [
            {"name": "agent_check", "type": "agent"},
            {"name": "human_approval", "type": "human"},
        ]}
        assert requires_human_review(config) is True

    def test_false_when_no_human_evaluator(self):
        config = {"checklist": [
            {"name": "tests_pass", "type": "deterministic"},
            {"name": "agent_check", "type": "agent"},
        ]}
        assert requires_human_review(config) is False

    def test_false_on_empty_checklist(self):
        assert requires_human_review({"checklist": []}) is False

    def test_false_on_missing_checklist(self):
        assert requires_human_review({}) is False

    def test_case_insensitive_type(self):
        config = {"checklist": [{"name": "human_check", "type": "Human"}]}
        assert requires_human_review(config) is True

    def test_get_human_evaluators_returns_correct_entries(self):
        config = {"checklist": [
            {"name": "det", "type": "deterministic"},
            {"name": "human1", "type": "human", "criterion": "approve?"},
            {"name": "agent1", "type": "agent"},
            {"name": "human2", "type": "human", "criterion": "sign off?"},
        ]}
        human_evals = get_human_evaluators(config)
        assert len(human_evals) == 2
        assert all(e["type"] == "human" for e in human_evals)


# ── emit_human_gate_entered ───────────────────────────────────────────────────


class TestEmitHumanGateEntered:
    def test_emits_event_to_jsonl(self, tmp_path):
        path = _events_path(tmp_path)
        gate_id = emit_human_gate_entered(
            path, feature="REQ-F-AUTH-001", edge="design→code",
            project="test-proj", actor="jim",
        )
        events = _read_events(path)
        assert len(events) == 1
        ev = events[0]
        assert ev["event_type"] == "human_gate_entered"
        assert ev["feature"] == "REQ-F-AUTH-001"
        assert ev["edge"] == "design→code"
        assert ev["actor"] == "jim"
        assert ev["event_id"] == gate_id

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "events.jsonl"
        emit_human_gate_entered(
            path, feature="REQ-F-X-001", edge="code↔unit_tests",
            project="p", actor="reviewer",
        )
        assert path.exists()

    def test_trigger_field(self, tmp_path):
        path = _events_path(tmp_path)
        emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="a",
            trigger="escalated",
        )
        ev = _read_events(path)[0]
        assert ev["trigger"] == "escalated"

    def test_suggestions_recorded(self, tmp_path):
        path = _events_path(tmp_path)
        suggestions = [{"source": "agent", "verdict": "looks good"}]
        emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="a",
            suggestions=suggestions,
        )
        ev = _read_events(path)[0]
        assert ev["suggestions"] == suggestions

    def test_returns_unique_ids(self, tmp_path):
        path = _events_path(tmp_path)
        ids = {
            emit_human_gate_entered(path, feature="F", edge="E", project="p", actor="a")
            for _ in range(5)
        }
        assert len(ids) == 5


# ── emit_human_decision ───────────────────────────────────────────────────────


class TestEmitHumanDecision:
    def test_emits_approve_decision(self, tmp_path):
        path = _events_path(tmp_path)
        gate_id = emit_human_gate_entered(
            path, feature="REQ-F-AUTH-001", edge="design→code",
            project="p", actor="jim",
        )
        dec_id = emit_human_decision(
            path, feature="REQ-F-AUTH-001", edge="design→code", project="p",
            actor="jim", decision=DECISION_APPROVE, reason="LGTM",
            gate_event_id=gate_id,
        )
        events = _read_events(path)
        dec = next(e for e in events if e["event_type"] == "human_decision")
        assert dec["decision"] == "approve"
        assert dec["actor"] == "jim"
        assert dec["reason"] == "LGTM"
        assert dec["gate_event_id"] == gate_id
        assert dec["event_id"] == dec_id

    def test_overrides_ai_flag(self, tmp_path):
        path = _events_path(tmp_path)
        gate_id = emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="reviewer",
        )
        emit_human_decision(
            path, feature="F", edge="E", project="p",
            actor="reviewer", decision=DECISION_OVERRIDE_APPROVE,
            reason="I disagree with agent", gate_event_id=gate_id,
            overrides_ai=True,
        )
        ev = next(e for e in _read_events(path) if e["event_type"] == "human_decision")
        assert ev["overrides_ai"] is True

    def test_invalid_decision_raises(self, tmp_path):
        path = _events_path(tmp_path)
        with pytest.raises(ValueError, match="Invalid decision"):
            emit_human_decision(
                path, feature="F", edge="E", project="p",
                actor="jim", decision="maybe", reason="unsure",
                gate_event_id="fake-id",
            )

    def test_ai_actor_rejected(self, tmp_path):
        path = _events_path(tmp_path)
        with pytest.raises(ValueError, match="AI identity"):
            emit_human_decision(
                path, feature="F", edge="E", project="p",
                actor="claude-agent", decision=DECISION_APPROVE,
                reason="auto-approved", gate_event_id="gid",
            )

    def test_various_ai_actor_names_rejected(self, tmp_path):
        path = _events_path(tmp_path)
        ai_names = ["gpt-4", "anthropic-worker", "llm-evaluator", "gemini-agent", "codex-bot"]
        for name in ai_names:
            with pytest.raises(ValueError, match="AI identity"):
                emit_human_decision(
                    path, feature="F", edge="E", project="p",
                    actor=name, decision=DECISION_APPROVE,
                    reason="auto", gate_event_id="gid",
                )

    def test_human_username_accepted(self, tmp_path):
        path = _events_path(tmp_path)
        gate_id = emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="alice",
        )
        # Should not raise
        emit_human_decision(
            path, feature="F", edge="E", project="p",
            actor="alice", decision=DECISION_REJECT,
            reason="not ready", gate_event_id=gate_id,
        )

    def test_defer_decision(self, tmp_path):
        path = _events_path(tmp_path)
        gate_id = emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="bob",
        )
        emit_human_decision(
            path, feature="F", edge="E", project="p",
            actor="bob", decision=DECISION_DEFER,
            reason="need more context", gate_event_id=gate_id,
        )
        ev = next(e for e in _read_events(path) if e["event_type"] == "human_decision")
        assert ev["decision"] == "defer"


# ── query functions ───────────────────────────────────────────────────────────


class TestQueryFunctions:
    @pytest.fixture
    def populated_events(self, tmp_path) -> list[dict]:
        path = _events_path(tmp_path)
        gid1 = emit_human_gate_entered(
            path, feature="REQ-F-AUTH-001", edge="design→code", project="p", actor="jim",
        )
        emit_human_decision(
            path, feature="REQ-F-AUTH-001", edge="design→code", project="p",
            actor="jim", decision=DECISION_APPROVE, reason="ok", gate_event_id=gid1,
        )
        gid2 = emit_human_gate_entered(
            path, feature="REQ-F-API-001", edge="code↔unit_tests", project="p", actor="alice",
        )
        emit_human_decision(
            path, feature="REQ-F-API-001", edge="code↔unit_tests", project="p",
            actor="alice", decision=DECISION_OVERRIDE_APPROVE,
            reason="trust me", gate_event_id=gid2, overrides_ai=True,
        )
        # Pending gate (no decision)
        emit_human_gate_entered(
            path, feature="REQ-F-DB-001", edge="design→code", project="p", actor="bob",
        )
        return load_events(path)

    def test_get_human_gates_all(self, populated_events):
        gates = get_human_gates(populated_events)
        assert len(gates) == 3

    def test_get_human_gates_filtered_by_feature(self, populated_events):
        gates = get_human_gates(populated_events, feature="REQ-F-AUTH-001")
        assert len(gates) == 1
        assert gates[0]["feature"] == "REQ-F-AUTH-001"

    def test_get_human_gates_filtered_by_edge(self, populated_events):
        gates = get_human_gates(populated_events, edge="design→code")
        assert len(gates) == 2

    def test_get_human_decisions_all(self, populated_events):
        decisions = get_human_decisions(populated_events)
        assert len(decisions) == 2

    def test_get_human_decisions_filtered_by_actor(self, populated_events):
        decisions = get_human_decisions(populated_events, actor="alice")
        assert len(decisions) == 1
        assert decisions[0]["actor"] == "alice"

    def test_get_pending_gates(self, populated_events):
        pending = get_pending_gates(populated_events)
        assert len(pending) == 1
        assert pending[0]["feature"] == "REQ-F-DB-001"

    def test_get_override_decisions(self, populated_events):
        overrides = get_override_decisions(populated_events)
        assert len(overrides) == 1
        assert overrides[0]["decision"] == DECISION_OVERRIDE_APPROVE

    def test_no_pending_when_all_decided(self, tmp_path):
        path = _events_path(tmp_path)
        gid = emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="jim",
        )
        emit_human_decision(
            path, feature="F", edge="E", project="p",
            actor="jim", decision=DECISION_APPROVE,
            reason="ok", gate_event_id=gid,
        )
        events = load_events(path)
        assert get_pending_gates(events) == []


# ── audit_summary ─────────────────────────────────────────────────────────────


class TestAuditSummary:
    def test_empty_event_log(self):
        summary = audit_summary([])
        assert summary["gates_entered"] == 0
        assert summary["decisions_made"] == 0
        assert summary["pending_gates"] == 0
        assert summary["override_count"] == 0
        assert summary["actors"] == []

    def test_summary_counts(self, tmp_path):
        path = _events_path(tmp_path)
        for i in range(3):
            gid = emit_human_gate_entered(
                path, feature=f"REQ-F-{i:03d}", edge="E", project="p", actor="jim",
            )
            if i < 2:  # 2 decided, 1 pending
                emit_human_decision(
                    path, feature=f"REQ-F-{i:03d}", edge="E", project="p",
                    actor="jim", decision=DECISION_APPROVE,
                    reason="ok", gate_event_id=gid,
                )
        events = load_events(path)
        summary = audit_summary(events)
        assert summary["gates_entered"] == 3
        assert summary["decisions_made"] == 2
        assert summary["pending_gates"] == 1

    def test_multiple_actors_tracked(self, tmp_path):
        path = _events_path(tmp_path)
        for actor in ("alice", "bob", "carol"):
            gid = emit_human_gate_entered(
                path, feature="F", edge="E", project="p", actor=actor,
            )
            emit_human_decision(
                path, feature="F", edge="E", project="p",
                actor=actor, decision=DECISION_APPROVE,
                reason="ok", gate_event_id=gid,
            )
        events = load_events(path)
        summary = audit_summary(events)
        assert set(summary["actors"]) == {"alice", "bob", "carol"}

    def test_by_decision_breakdown(self, tmp_path):
        path = _events_path(tmp_path)
        decisions_to_emit = [DECISION_APPROVE, DECISION_APPROVE, DECISION_REJECT, DECISION_DEFER]
        for i, dec in enumerate(decisions_to_emit):
            gid = emit_human_gate_entered(
                path, feature=f"REQ-F-{i}", edge="E", project="p", actor="jim",
            )
            emit_human_decision(
                path, feature=f"REQ-F-{i}", edge="E", project="p",
                actor="jim", decision=dec, reason="ok", gate_event_id=gid,
            )
        events = load_events(path)
        summary = audit_summary(events)
        assert summary["by_decision"][DECISION_APPROVE] == 2
        assert summary["by_decision"][DECISION_REJECT] == 1
        assert summary["by_decision"][DECISION_DEFER] == 1


# ── load_events ───────────────────────────────────────────────────────────────


class TestLoadEvents:
    def test_missing_file_returns_empty(self, tmp_path):
        assert load_events(tmp_path / "no_file.jsonl") == []

    def test_loads_all_events(self, tmp_path):
        path = _events_path(tmp_path)
        gid = emit_human_gate_entered(
            path, feature="F", edge="E", project="p", actor="jim",
        )
        emit_human_decision(
            path, feature="F", edge="E", project="p",
            actor="jim", decision=DECISION_APPROVE, reason="ok", gate_event_id=gid,
        )
        events = load_events(path)
        assert len(events) == 2

    def test_skips_malformed_lines(self, tmp_path):
        path = _events_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"event_type": "human_gate_entered"}\nnot-json\n{"event_type": "human_decision"}\n')
        events = load_events(path)
        assert len(events) == 2  # malformed line skipped
