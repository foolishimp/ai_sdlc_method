# Validates: REQ-EVENT-001, REQ-EVENT-004, REQ-ROBUST-002, REQ-ROBUST-008, ADR-S-015
import pytest
import json
from pathlib import Path
from gemini_cli.engine.state import EventStore
from gemini_cli.engine.stateless import run_iteration
from gemini_cli.engine.models import FunctorResult, Outcome

class MockFunctor:
    def evaluate(self, candidate, context):
        return FunctorResult(name="mock", outcome=Outcome.PASS, delta=0, reasoning="test")

@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    (ws / "events").mkdir()
    return ws

def test_iteration_emits_manifest(workspace, tmp_path):
    store = EventStore(workspace)
    asset_path = tmp_path / "asset.txt"
    asset_path.write_text("initial content")
    
    functors = {"agent": MockFunctor()}
    constraints = {}
    
    run_iteration(
        feature_id="REQ-F-TEST",
        edge="design\u2192code",
        asset_path=asset_path,
        context={},
        functors=functors,
        store=store,
        constraints=constraints
    )
    
    events = store.load_all()
    start_ev = next(e for e in events if e["eventType"] == "START")
    complete_ev = next(e for e in events if e["eventType"] == "COMPLETE")
    
    # Verify START manifest
    start_manifest = start_ev["run"]["facets"]["sdlc_manifest"]
    assert len(start_manifest["inputs"]) == 1
    assert start_manifest["inputs"][0]["path"] == "asset.txt"
    assert start_manifest["inputs"][0]["hash"] is not None
    
    # Verify COMPLETE manifest
    complete_manifest = complete_ev["run"]["facets"]["sdlc_manifest"]
    assert len(complete_manifest["outputs"]) == 1
    assert complete_manifest["outputs"][0]["path"] == "asset.txt"
