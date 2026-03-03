# Validates: REQ-EVENT-001, REQ-EVENT-003, REQ-EVENT-004
import pytest
from pathlib import Path
from typing import Dict, Any
from gemini_cli.engine.iterate import IterateEngine, Functor
from gemini_cli.engine.models import FunctorResult, Outcome, SpawnRequest

class MockSpawnFunctor:
    def evaluate(self, candidate: str, context: Dict) -> FunctorResult:
        return FunctorResult(
            name="mock_spawn",
            outcome=Outcome.FAIL,
            delta=1,
            reasoning="Need to spawn",
            spawn=SpawnRequest(question="Why?", vector_type="discovery")
        )

def test_iterate_engine_saga_invariant(tmp_path: Path):
    """Verifies IterationStarted and CompensationTriggered events are emitted."""
    # Setup
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()
    
    constraints = {"project": {"name": "test_project"}}
    engine = IterateEngine(
        functor_map={"mock": MockSpawnFunctor()}, 
        constraints=constraints, 
        project_root=tmp_path
    )
    
    asset_path = tmp_path / "dummy.txt"
    
    # Run
    records = engine.run_edge(
        edge="test→edge",
        feature_id="REQ-F-TEST-001",
        asset_path=asset_path,
        context={"edge": "test→edge"},
        checklist=[{"evaluator": "mock"}]
    )
    
    # Verify Events
    events = engine.store.load_all()
    
    event_types = []
    for ev in events:
        # Check standard format
        if "eventType" in ev:
            t = ev.get("run", {}).get("facets", {}).get("sdlc_event_type", {}).get("type")
            if t:
                event_types.append(t)
        # Check backward compatibility format
        elif "event_type" in ev:
            event_types.append(ev["event_type"])
            
    assert "iteration_started" in event_types
    assert "compensation_triggered" in event_types
    
    # Ensure it stopped after the spawn
    assert len(records) == 1
    assert records[0].report.spawn is not None
