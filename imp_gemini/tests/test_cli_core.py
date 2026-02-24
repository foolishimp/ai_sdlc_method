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
            return {"delta": 0 if "pass" in candidate else 1}

    engine = IterateEngine(functors=[MockFunctor()])
    asset_path = workspace / "asset.txt"
    
    # Test Failure
    asset_path.write_text("fail")
    result = engine.run(asset_path, {})
    assert result["converged"] is False
    assert result["delta"] == 1
    
    # Test Success
    asset_path.write_text("pass")
    result = engine.run(asset_path, {})
    assert result["converged"] is True
    assert result["delta"] == 0

def test_recursive_spawn_detection():
    # REQ-CLI-006: Recursive Spawning
    functor = GeminiFunctor()
    
    # Simulate 'stuck' context
    context = {"iteration_count": 5}
    result = functor.evaluate("some candidate", context)
    
    assert "spawn" in result
    assert isinstance(result["spawn"], SpawnRequest)
    assert "Triggering recursion" in result["reasoning"]

def test_recursive_self_validation(workspace):
    # Dogfooding: Check if engine detects invariant violations
    engine = IterateEngine(functors=[])
    events = [
        {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "data": {"delta": 5}},
        {"event_type": "iteration_completed", "feature": "F1", "edge": "E1", "data": {"delta": 10}}, # VIOLATION: Delta increased
    ]
    
    violations = engine.validate_invariants(events)
    assert len(violations) == 1
    assert "Delta increased" in violations[0]
