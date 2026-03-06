# Validates: REQ-EVENT-003 (Required Event Taxonomy), REQ-EVENT-004 (Saga Invariant)
"""
Tests for the full OL event taxonomy (REQ-EVENT-003, REQ-EVENT-004).

Covers:
  - All required event types present in _OL_EVENT_TYPE with correct OL mapping
  - Convergence events: EvaluatorVoted, ConsensusReached, ConvergenceAchieved
  - Context events: ContextArrived
  - Transition gate events: TransitionAuthorized, TransitionDenied
  - Saga compensation: CompensationTriggered, CompensationCompleted
  - IterationStarted emission in engine.iterate_edge()
"""

import json
import pytest


# ── Event type registry completeness ─────────────────────────────────


class TestEventTaxonomyRegistry:
    """REQ-EVENT-003: all required event types must be registered."""

    def test_core_lifecycle_events_present(self):
        """Core lifecycle events map to correct OL event types."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["IterationStarted"] == "START"
        assert _OL_EVENT_TYPE["IterationCompleted"] == "COMPLETE"
        assert _OL_EVENT_TYPE["IterationFailed"] == "FAIL"
        assert _OL_EVENT_TYPE["IterationAbandoned"] == "ABORT"

    def test_convergence_events_present(self):
        """Convergence events map to correct OL event types."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["EvaluatorVoted"] == "OTHER"
        assert _OL_EVENT_TYPE["ConsensusReached"] == "COMPLETE"
        assert _OL_EVENT_TYPE["ConvergenceAchieved"] == "COMPLETE"

    def test_context_event_present(self):
        """ContextArrived maps to OTHER — not a terminal event."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["ContextArrived"] == "OTHER"

    def test_transition_gate_events_present(self):
        """Transition gate events map to COMPLETE/FAIL."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["TransitionAuthorized"] == "COMPLETE"
        assert _OL_EVENT_TYPE["TransitionDenied"] == "FAIL"

    def test_saga_compensation_events_present(self):
        """Saga compensation events map to OTHER/COMPLETE (REQ-EVENT-004)."""
        from genesis.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["CompensationTriggered"] == "OTHER"
        assert _OL_EVENT_TYPE["CompensationCompleted"] == "COMPLETE"


# ── ConsensusReached constructor ──────────────────────────────────────


class TestConsensusReachedConstructor:
    """Validates: ConsensusReached event (all evaluators passed)."""

    def test_consensus_reached_returns_complete_event(self):
        """consensus_reached() produces a COMPLETE OL event."""
        from genesis.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="code↔unit_tests",
            evaluator_count=3,
        )
        assert ev["eventType"] == "COMPLETE"

    def test_consensus_reached_job_name_is_edge(self):
        """Job name is the edge name for tracing convergence."""
        from genesis.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="design→code",
            evaluator_count=5,
        )
        assert ev["job"]["name"] == "design→code"

    def test_consensus_reached_payload_contains_edge_and_count(self):
        """Payload carries edge and evaluator_count."""
        from genesis.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="code↔unit_tests",
            evaluator_count=4,
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["edge"] == "code↔unit_tests"
        assert payload["evaluator_count"] == 4

    def test_consensus_reached_event_type_facet(self):
        """sdlc:event_type facet is ConsensusReached."""
        from genesis.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="design→code",
            evaluator_count=2,
        )
        assert ev["run"]["facets"]["sdlc:event_type"]["type"] == "ConsensusReached"


# ── EvaluatorVoted constructor ────────────────────────────────────────


class TestEvaluatorVotedConstructor:
    """Validates: EvaluatorVoted intermediate event."""

    def test_evaluator_voted_returns_other_event(self):
        """evaluator_voted() produces an OTHER OL event (intermediate)."""
        from genesis.ol_event import evaluator_voted

        ev = evaluator_voted(
            project="test",
            instance_id="inst-001",
            actor="engine",
            evaluator_type="deterministic",
            result="pass",
            evidence="all 12 checks pass",
        )
        assert ev["eventType"] == "OTHER"

    def test_evaluator_voted_payload_fields(self):
        """Payload carries evaluator_type, result, and evidence."""
        from genesis.ol_event import evaluator_voted

        ev = evaluator_voted(
            project="test",
            instance_id="inst-001",
            actor="engine",
            evaluator_type="agent",
            result="fail",
            evidence="missing error handling in auth module",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["evaluator_type"] == "agent"
        assert payload["result"] == "fail"
        assert payload["evidence"] == "missing error handling in auth module"


# ── ContextArrived constructor ────────────────────────────────────────


class TestContextArrivedConstructor:
    """Validates: ContextArrived event (push context into iteration)."""

    def test_context_arrived_returns_other_event(self):
        """context_arrived() produces an OTHER OL event."""
        from genesis.ol_event import context_arrived

        ev = context_arrived(
            project="test",
            instance_id="inst-001",
            actor="human",
            source_type="spec_document",
            payload_ref="specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md",
        )
        assert ev["eventType"] == "OTHER"

    def test_context_arrived_payload_fields(self):
        """Payload carries source_type and payload_ref."""
        from genesis.ol_event import context_arrived

        ev = context_arrived(
            project="test",
            instance_id="inst-001",
            actor="human",
            source_type="design_adr",
            payload_ref="imp_claude/design/adrs/ADR-024.md",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["source_type"] == "design_adr"
        assert payload["payload_ref"] == "imp_claude/design/adrs/ADR-024.md"


# ── Saga compensation constructors ───────────────────────────────────


class TestSagaCompensationConstructors:
    """Validates: CompensationTriggered / CompensationCompleted (REQ-EVENT-004)."""

    def test_compensation_triggered_returns_other_event(self):
        """compensation_triggered() produces OTHER event — not terminal."""
        from genesis.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="design→code",
            target_edge="intent→requirements",
        )
        assert ev["eventType"] == "OTHER"

    def test_compensation_triggered_job_name_is_compensate_prefixed(self):
        """Job name is COMPENSATE:{target_edge} for routing."""
        from genesis.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code↔unit_tests",
            target_edge="design→code",
        )
        assert ev["job"]["name"] == "COMPENSATE:design→code"

    def test_compensation_triggered_payload_carries_edge_pair(self):
        """Payload identifies both the failed edge and compensation target."""
        from genesis.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code↔unit_tests",
            target_edge="design→code",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["failed_edge"] == "code↔unit_tests"
        assert payload["target_edge"] == "design→code"

    def test_compensation_completed_returns_complete_event(self):
        """compensation_completed() produces COMPLETE event — chain restored."""
        from genesis.ol_event import compensation_completed

        ev = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design→code",
            restored_projection_hash="sha256:abc123",
        )
        assert ev["eventType"] == "COMPLETE"

    def test_compensation_completed_payload_has_hash(self):
        """Payload carries restored_projection_hash for verifiability."""
        from genesis.ol_event import compensation_completed

        ev = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design→code",
            restored_projection_hash="sha256:deadbeef",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["restored_projection_hash"] == "sha256:deadbeef"
        assert payload["target_edge"] == "design→code"

    def test_saga_sequence_compensation_follows_failure(self, tmp_path):
        """Failure → compensation_triggered → compensation_completed sequence."""
        from genesis.ol_event import (
            iteration_failed,
            compensation_triggered,
            compensation_completed,
            emit_ol_event,
        )

        events_path = tmp_path / "events.jsonl"
        correlation_id = None

        ev_failed = iteration_failed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="code↔unit_tests",
            reason="3 tests failed after 10 iterations",
        )
        correlation_id = ev_failed["run"]["runId"]
        emit_ol_event(events_path, ev_failed)

        ev_triggered = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code↔unit_tests",
            target_edge="design→code",
            causation_id=correlation_id,
            correlation_id=correlation_id,
        )
        emit_ol_event(events_path, ev_triggered)

        ev_completed = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design→code",
            restored_projection_hash="sha256:abc",
            causation_id=ev_triggered["run"]["runId"],
            correlation_id=correlation_id,
        )
        emit_ol_event(events_path, ev_completed)

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 3
        failed, triggered, completed = [json.loads(l) for l in lines]

        assert failed["eventType"] == "FAIL"
        assert triggered["eventType"] == "OTHER"
        assert completed["eventType"] == "COMPLETE"

        # Causal chain preserved
        assert triggered["run"]["facets"]["sdlc:universal"]["correlation_id"] == correlation_id
        assert completed["run"]["facets"]["sdlc:universal"]["correlation_id"] == correlation_id


# ── IterationStarted emission in engine ──────────────────────────────


class TestIterationStartedEmission:
    """Validates: iterate_edge() emits iteration_started event (REQ-EVENT-003)."""

    def _make_minimal_edge_config(self) -> dict:
        return {
            "edge": "design→code",
            "evaluators": [],
            "checklist": [],
        }

    def _make_engine_config(self, tmp_path):
        from genesis.engine import EngineConfig
        from pathlib import Path

        return EngineConfig(
            project_name="test",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            fd_timeout=5,
        )

    def test_iterate_edge_emits_iteration_started(self, tmp_path):
        """iterate_edge() emits an iteration_started event before evaluation."""
        from genesis.engine import iterate_edge, EngineConfig

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        config = EngineConfig(
            project_name="test",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            fd_timeout=5,
        )

        edge_config = {"edge": "design→code", "checklist": []}

        iterate_edge(
            edge="design→code",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="test content",
            iteration=1,
        )

        events = events_path.read_text().strip().splitlines()
        started_events = [
            json.loads(e) for e in events
            if json.loads(e).get("event_type") == "iteration_started"
        ]
        assert len(started_events) == 1
        ev = started_events[0]
        assert ev["feature"] == "REQ-F-TEST-001"
        assert ev["edge"] == "design→code"
        assert ev["iteration"] == 1

    def test_iterate_edge_started_before_completed(self, tmp_path):
        """iteration_started event is emitted before iteration_completed."""
        from genesis.engine import iterate_edge, EngineConfig

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        config = EngineConfig(
            project_name="test",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            fd_timeout=5,
        )

        iterate_edge(
            edge="design→code",
            edge_config={"edge": "design→code", "checklist": []},
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="content",
            iteration=2,
        )

        events = [json.loads(l) for l in events_path.read_text().strip().splitlines()]
        event_types = [e["event_type"] for e in events]

        # iteration_started must precede iteration_completed
        started_idx = event_types.index("iteration_started")
        completed_idx = next(
            (i for i, t in enumerate(event_types) if t == "iteration_completed"),
            None,
        )
        if completed_idx is not None:
            assert started_idx < completed_idx

    def test_iterate_edge_started_carries_iteration_number(self, tmp_path):
        """iteration_started event records the iteration number."""
        from genesis.engine import iterate_edge, EngineConfig

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        config = EngineConfig(
            project_name="test",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            fd_timeout=5,
        )

        for i in range(1, 4):
            iterate_edge(
                edge="code↔unit_tests",
                edge_config={"edge": "code↔unit_tests", "checklist": []},
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="content",
                iteration=i,
            )

        events = [json.loads(l) for l in events_path.read_text().strip().splitlines()]
        started = [e for e in events if e["event_type"] == "iteration_started"]
        assert len(started) == 3
        assert [e["iteration"] for e in started] == [1, 2, 3]
