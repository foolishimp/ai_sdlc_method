# Validates: REQ-CLI-002, REQ-CLI-003, REQ-CLI-005, REQ-CLI-006
"""
E2E Unit Tests for the Gemini CLI Core.
Validates Event Sourcing, Universal Iteration, and Recursive Spawning.
"""

import pytest
import json
from pathlib import Path
from gemini_cli.engine.state import EventStore, Projector
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.functors.f_probabilistic import GeminiFunctor, SpawnRequest
from gemini_cli.engine.models import Outcome, FunctorResult

@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    return ws

def test_event_store_integrity(workspace):
    # REQ-CLI-002: Event Sourcing
    store = EventStore(workspace)
    store.emit("test_event", "test_proj", feature="REQ-1", data={"val": 1})
    
    events = store.load_all()
    assert len(events) == 1
    assert events[0]["event_type"] == "test_event"
    assert events[0]["data"]["val"] == 1

def test_iterate_engine_convergence(workspace):
    # REQ-CLI-003: Universal iterate() engine
    class MockFunctor:
        def evaluate(self, candidate, context):
            passed = "pass" in candidate
            return FunctorResult(
                name="mock", 
                outcome=Outcome.PASS if passed else Outcome.FAIL,
                delta=0 if passed else 1,
                reasoning="test"
            )

    engine = IterateEngine(functors=[MockFunctor()])
    asset_path = workspace / "asset.txt"
    
    # Test Failure
    asset_path.write_text("fail")
    report = engine.run(asset_path, {})
    assert report.converged is False
    assert report.delta == 1
    
    # Test Success
    asset_path.write_text("pass")
    report = engine.run(asset_path, {})
    assert report.converged is True
    assert report.delta == 0

def test_recursive_spawn_detection():
    # REQ-CLI-006: Recursive Spawning
    functor = GeminiFunctor()
    
    # Simulate 'stuck' context
    context = {"iteration_count": 5}
    result = functor.evaluate("some candidate", context)
    
    assert result.spawn is not None
    assert isinstance(result.spawn, SpawnRequest)
    assert "Triggering recursion" in result.reasoning

def test_recursive_self_validation(workspace):
    # Dogfooding: Check if engine detects invariant violations
    engine = IterateEngine(functors=[])
    events = [
        {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "delta": 5},
        {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "delta": 10}, # VIOLATION: Delta increased
    ]
    
    violations = engine.validate_invariants(events)
    assert len(violations) == 1
    assert "Delta increased" in violations[0]
