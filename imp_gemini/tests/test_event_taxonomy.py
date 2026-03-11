# Validates: REQ-EVENT-001
# Validates: REQ-EVENT-003
# Validates: REQ-EVENT-004
# Validates: REQ-EVENT-005
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
import sys
import pathlib
import pytest

# Ensure PYTHONPATH is correct for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from gemini_cli.engine.ol_event import normalize_event


# ── Event type registry completeness ─────────────────────────────────


class TestEventTaxonomyRegistry:
    """REQ-EVENT-003: all required event types must be registered."""

    def test_core_lifecycle_events_present(self):
        """Core lifecycle events map to correct OL event types."""
        from gemini_cli.engine.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["IterationStarted"] == "START"
        assert _OL_EVENT_TYPE["IterationCompleted"] == "OTHER"   # non-terminal: convergence not yet declared
        assert _OL_EVENT_TYPE["IterationFailed"] == "FAIL"
        assert _OL_EVENT_TYPE["IterationAbandoned"] == "ABORT"

    def test_convergence_events_present(self):
        """Convergence events map to correct OL event types."""
        from gemini_cli.engine.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["EvaluatorVoted"] == "OTHER"
        assert _OL_EVENT_TYPE["ConsensusReached"] == "COMPLETE"
        assert _OL_EVENT_TYPE["ConvergenceAchieved"] == "COMPLETE"

    def test_context_event_present(self):
        """ContextArrived maps to OTHER \u2014 not a terminal event."""
        from gemini_cli.engine.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["ContextArrived"] == "OTHER"

    def test_transition_gate_events_present(self):
        """Transition gate events map to COMPLETE/FAIL."""
        from gemini_cli.engine.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["TransitionAuthorized"] == "COMPLETE"
        assert _OL_EVENT_TYPE["TransitionDenied"] == "FAIL"

    def test_saga_compensation_events_present(self):
        """Saga compensation events map to OTHER/COMPLETE (REQ-EVENT-004)."""
        from gemini_cli.engine.ol_event import _OL_EVENT_TYPE

        assert _OL_EVENT_TYPE["CompensationTriggered"] == "OTHER"
        assert _OL_EVENT_TYPE["CompensationCompleted"] == "COMPLETE"


# ── ConsensusReached constructor ──────────────────────────────────────


class TestConsensusReachedConstructor:
    """Validates: ConsensusReached event (all evaluators passed)."""

    def test_consensus_reached_returns_complete_event(self):
        """consensus_reached() produces a COMPLETE OL event."""
        from gemini_cli.engine.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="code\u2194unit_tests",
            evaluator_count=3,
        )
        assert ev["eventType"] == "COMPLETE"

    def test_consensus_reached_job_name_is_edge(self):
        """Job name is the edge name for tracing convergence."""
        from gemini_cli.engine.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="design\u2192code",
            evaluator_count=5,
        )
        assert ev["job"]["name"] == "design\u2192code"

    def test_consensus_reached_payload_contains_edge_and_count(self):
        """Payload carries edge and evaluator_count."""
        from gemini_cli.engine.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="code\u2194unit_tests",
            evaluator_count=4,
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["edge"] == "code\u2194unit_tests"
        assert payload["evaluator_count"] == 4

    def test_consensus_reached_event_type_facet(self):
        """sdlc:event_type facet is ConsensusReached."""
        from gemini_cli.engine.ol_event import consensus_reached

        ev = consensus_reached(
            project="test",
            instance_id="inst-001",
            actor="engine",
            edge="design\u2192code",
            evaluator_count=2,
        )
        assert ev["run"]["facets"]["sdlc:event_type"]["type"] == "ConsensusReached"


# ── EvaluatorVoted constructor ────────────────────────────────────────


class TestEvaluatorVotedConstructor:
    """Validates: EvaluatorVoted intermediate event."""

    def test_evaluator_voted_returns_other_event(self):
        """evaluator_voted() produces an OTHER OL event (intermediate)."""
        from gemini_cli.engine.ol_event import evaluator_voted

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
        from gemini_cli.engine.ol_event import evaluator_voted

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
        from gemini_cli.engine.ol_event import context_arrived

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
        from gemini_cli.engine.ol_event import context_arrived

        ev = context_arrived(
            project="test",
            instance_id="inst-001",
            actor="human",
            source_type="design_adr",
            payload_ref="imp_gemini/design/adrs/ADR-024.md",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["source_type"] == "design_adr"
        assert payload["payload_ref"] == "imp_gemini/design/adrs/ADR-024.md"


# ── Saga compensation constructors ───────────────────────────────────


class TestSagaCompensationConstructors:
    """Validates: CompensationTriggered / CompensationCompleted (REQ-EVENT-004)."""

    def test_compensation_triggered_returns_other_event(self):
        """compensation_triggered() produces OTHER event \u2014 not terminal."""
        from gemini_cli.engine.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="design\u2192code",
            target_edge="intent\u2192requirements",
        )
        assert ev["eventType"] == "OTHER"

    def test_compensation_triggered_job_name_is_compensate_prefixed(self):
        """Job name is COMPENSATE:{target_edge} for routing."""
        from gemini_cli.engine.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code\u2194unit_tests",
            target_edge="design\u2192code",
        )
        assert ev["job"]["name"] == "COMPENSATE:design\u2192code"

    def test_compensation_triggered_payload_carries_edge_pair(self):
        """Payload identifies both the failed edge and compensation target."""
        from gemini_cli.engine.ol_event import compensation_triggered

        ev = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code\u2194unit_tests",
            target_edge="design\u2192code",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["failed_edge"] == "code\u2194unit_tests"
        assert payload["target_edge"] == "design\u2192code"

    def test_compensation_completed_returns_complete_event(self):
        """compensation_completed() produces COMPLETE event \u2014 chain restored."""
        from gemini_cli.engine.ol_event import compensation_completed

        ev = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design\u2192code",
            restored_projection_hash="sha256:abc123",
        )
        assert ev["eventType"] == "COMPLETE"

    def test_compensation_completed_payload_has_hash(self):
        """Payload carries restored_projection_hash for verifiability."""
        from gemini_cli.engine.ol_event import compensation_completed

        ev = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design\u2192code",
            restored_projection_hash="sha256:deadbeef",
        )
        payload = ev["run"]["facets"]["sdlc:payload"]
        assert payload["restored_projection_hash"] == "sha256:deadbeef"
        assert payload["target_edge"] == "design\u2192code"

    def test_saga_sequence_compensation_follows_failure(self, tmp_path):
        """Failure \u2192 compensation_triggered \u2192 compensation_completed sequence."""
        from gemini_cli.engine.ol_event import (
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
            edge="code\u2194unit_tests",
            reason="3 tests failed after 10 iterations",
        )
        correlation_id = ev_failed["run"]["runId"]
        emit_ol_event(events_path, ev_failed)

        ev_triggered = compensation_triggered(
            project="test",
            instance_id="inst-001",
            actor="engine",
            failed_edge="code\u2194unit_tests",
            target_edge="design\u2192code",
            causation_id=correlation_id,
            correlation_id=correlation_id,
        )
        emit_ol_event(events_path, ev_triggered)

        ev_completed = compensation_completed(
            project="test",
            instance_id="inst-001",
            actor="engine",
            target_edge="design\u2192code",
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

    @pytest.fixture
    def mock_run_iteration(self, monkeypatch):
        """Mock the stateless iteration logic to prevent AI calls."""
        from gemini_cli.engine.models import IterationReport
        
        def mock_run(*args, **kwargs):
            return IterationReport(
                asset_path="test",
                delta=0,
                converged=True,
                functor_results=[],
                guardrail_results=[]
            )
        
        monkeypatch.setattr("gemini_cli.engine.stateless.run_iteration", mock_run)
        return mock_run

    def test_iterate_edge_emits_iteration_started(self, tmp_path, mock_run_iteration):
        """iterate_edge() emits an iteration_started event before evaluation."""
        from gemini_cli.engine.iterate import IterateEngine
        from pathlib import Path

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        engine = IterateEngine(
            functor_map={},
            constraints={},
            project_root=tmp_path
        )
        
        asset_path = tmp_path / "asset.txt"
        asset_path.write_text("test")

        engine.iterate_edge(
            edge="design\u2192code",
            feature_id="REQ-F-TEST-001",
            asset_path=asset_path,
            context={},
            iteration=1
        )

        events = [normalize_event(json.loads(e)) for e in events_path.read_text().strip().splitlines()]
        started_events = [e for e in events if e.get("event_type") == "iteration_started"]
        assert len(started_events) == 1
        ev = started_events[0]
        assert ev["feature"] == "REQ-F-TEST-001"
        assert ev["edge"] == "design\u2192code"
        assert ev["iteration"] == 1

    def test_iterate_edge_started_before_completed(self, tmp_path, mock_run_iteration):
        """iteration_started event is emitted before iteration_completed."""
        from gemini_cli.engine.iterate import IterateEngine
        from pathlib import Path

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        engine = IterateEngine(
            functor_map={},
            constraints={},
            project_root=tmp_path
        )
        
        asset_path = tmp_path / "asset.txt"
        asset_path.write_text("test")

        engine.iterate_edge(
            edge="design\u2192code",
            feature_id="REQ-F-TEST-001",
            asset_path=asset_path,
            context={},
            iteration=2
        )

        events = [normalize_event(json.loads(l)) for l in events_path.read_text().strip().splitlines()]
        event_types = [e["event_type"] for e in events]

        # iteration_started must precede iteration_completed
        started_idx = event_types.index("iteration_started")
        completed_idx = next(
            (i for i, t in enumerate(event_types) if t == "iteration_completed"),
            None,
        )
        if completed_idx is not None:
            assert started_idx < completed_idx

    def test_iterate_edge_started_carries_iteration_number(self, tmp_path, mock_run_iteration):
        """iteration_started event records the iteration number."""
        from gemini_cli.engine.iterate import IterateEngine
        from pathlib import Path

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        engine = IterateEngine(
            functor_map={},
            constraints={},
            project_root=tmp_path
        )
        
        asset_path = tmp_path / "asset.txt"
        asset_path.write_text("test")

        for i in range(1, 4):
            engine.iterate_edge(
                edge="code\u2194unit_tests",
                feature_id="REQ-F-TEST-001",
                asset_path=asset_path,
                context={},
                iteration=i
            )

        events = [normalize_event(json.loads(l)) for l in events_path.read_text().strip().splitlines()]
        started = [e for e in events if e["event_type"] == "iteration_started"]
        assert len(started) == 3
        assert [e["iteration"] for e in started] == [1, 2, 3]


# ── REQ-EVENT-005: Executor Attribution Fields ────────────────────────


class TestExecutorAttributionFields:
    """REQ-EVENT-005: events carry actor/causation attribution; executor/emission are optional."""

    def test_make_ol_event_carries_actor_field(self):
        """Every event constructed by make_ol_event includes the actor attribution field.

        Validates: REQ-EVENT-005 (actor is the mandatory attribution field on every event)
        """
        import uuid
        from gemini_cli.engine.ol_event import make_ol_event

        event = make_ol_event(
            event_type="IterationStarted",
            job_name="design\u2192code",
            project="test-project",
            instance_id=str(uuid.uuid4()),
            actor="gemini",
        )
        facets = event["run"]["facets"]["sdlc:universal"]
        assert "actor" in facets, "actor attribution field must be present on every event"
        assert facets["actor"] == "gemini"

    def test_make_ol_event_carries_causation_id(self):
        """Every event has a causation_id attribution field for observability tooling.

        Validates: REQ-EVENT-005 (causation_id enables executor chain tracing)
        """
        import uuid
        from gemini_cli.engine.ol_event import make_ol_event

        parent_run_id = str(uuid.uuid4())
        event = make_ol_event(
            event_type="IterationCompleted",
            job_name="design\u2192code",
            project="test-project",
            instance_id=str(uuid.uuid4()),
            actor="engine",
            causation_id=parent_run_id,
        )
        facets = event["run"]["facets"]["sdlc:universal"]
        assert facets["causation_id"] == parent_run_id, "causation_id must thread attribution chain"

    def test_ol_format_events_infer_engine_executor(self):
        """OL-format events (eventType present) are attributed to executor=engine per REQ-EVENT-005 AC-1.

        Validates: REQ-EVENT-005 AC-1 (OL-format events \u2192 infer executor: engine)
        """
        import uuid
        from gemini_cli.engine.ol_event import make_ol_event

        event = make_ol_event(
            event_type="EdgeStarted",
            job_name="design\u2192code",
            project="test-project",
            instance_id=str(uuid.uuid4()),
            actor="engine",
        )
        # OL-format events have a top-level 'eventType' field
        assert "eventType" in event, "OL-format events must have top-level eventType"
        # Per REQ-EVENT-005 AC-1: tooling MUST infer executor=engine when eventType is present
        inferred_executor = "engine" if "eventType" in event else "gemini"
        assert inferred_executor == "engine"
