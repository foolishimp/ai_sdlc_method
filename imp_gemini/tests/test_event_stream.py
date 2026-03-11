# Validates: REQ-EVENT-001, REQ-EVENT-003, REQ-EVENT-004, REQ-F-EVENT-001
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.engine.models import IterationRecord, IterationReport, FunctorResult, Outcome, SpawnRequest

def test_iterate_engine_saga_invariant(tmp_path: Path):
    """Verifies IterationStarted and CompensationTriggered events are emitted."""
    # Setup
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()

    constraints = {"project": {"name": "test_project"}}
    engine = IterateEngine(
        functor_map={}, 
        constraints=constraints, 
        project_root=tmp_path
    )

    asset_path = tmp_path / "dummy.txt"
    asset_path.write_text("content")
    
    # We mock run_iteration to return a spawn request immediately
    from gemini_cli.engine.models import IterationReport
    mock_report = IterationReport(
        asset_path=str(asset_path),
        delta=1,
        converged=False,
        functor_results=[
            FunctorResult(
                name="mock_spawn",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="Need to spawn",
                spawn=SpawnRequest(
                    question="Why?", 
                    vector_type="discovery",
                    parent_feature="REQ-F-TEST-001",
                    triggered_at_edge="test\u2192edge"
                )
            )
        ],
        guardrail_results=[],
        spawn=SpawnRequest(
            question="Why?", 
            vector_type="discovery",
            parent_feature="REQ-F-TEST-001",
            triggered_at_edge="test\u2192edge"
        )
    )

    emitted_events = []
    def mock_emit_side_effect(path, event):
        emitted_events.append(event)
        return "mock-run-id"

    with patch("gemini_cli.engine.stateless.run_iteration", return_value=mock_report):
        with patch("gemini_cli.engine.ol_event.emit_ol_event", side_effect=mock_emit_side_effect):
            with patch("gemini_cli.engine.fd_spawn.detect_spawn_condition", return_value=mock_report.spawn):
                records = engine.run_edge(
                    edge="test\u2192edge",
                    feature_id="REQ-F-TEST-001",
                    asset_path=asset_path,
                    context={"edge": "test\u2192edge", "feature_id": "REQ-F-TEST-001"}
                )
            
            # Verify CompensationTriggered was emitted
            found = False
            for ev in emitted_events:
                facets = ev.get("run", {}).get("facets", {})
                t = facets.get("sdlc:event_type", {}).get("type") or facets.get("sdlc_event_type", {}).get("type")
                if t == "CompensationTriggered":
                    found = True
                    break
            
            assert found, f"CompensationTriggered not found. Events: {[e.get('run', {}).get('facets', {}).get('sdlc:event_type', {}).get('type') or e.get('run', {}).get('facets', {}).get('sdlc_event_type', {}).get('type') for e in emitted_events]}"
            
            # Ensure it stopped after the spawn (1 iteration)
            assert len(records) == 1
