# Validates: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003, REQ-F-GEMINI-CLI-001, REQ-F-UX-001, REQ-F-TOOL-001
"""
Dynamic E2E Test: Full CLI Workflow.
This test runs the 'gemini' CLI through a multi-edge journey.
"""

import pytest
import subprocess
import json
import yaml
from pathlib import Path

@pytest.fixture
def test_workspace(tmp_path):
    # Setup fresh workspace
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    (ws / "events").mkdir()
    (ws / "vectors").mkdir()
    (ws / "vectors" / "active").mkdir()
    
    # Mock constraints
    genesis = ws / "gemini_genesis"
    genesis.mkdir()
    (genesis / "project_constraints.yml").write_text("project:\n  name: e2e-test")
    
    # Mock Intent
    spec = tmp_path / "specification"
    spec.mkdir()
    (spec / "INTENT.md").write_text("# Project Intent\nTo build a test system.")
    
    return tmp_path

import sys

def run_gemini(workspace, cmd, *args):
    """Helper to run the CLI."""
    full_cmd = [sys.executable, "-m", "gemini_cli.cli", "--workspace", str(workspace / ".ai-workspace"), cmd] + list(args)
    env = {"PYTHONPATH": f"{Path.cwd()}:{Path.cwd().parent}"}
    result = subprocess.run(
        full_cmd, 
        capture_output=True, 
        text=True, 
        env=env
    )
    return result

def test_full_journey_convergence(test_workspace):
    # 1. Start Journey: intent→requirements
    # We simulate the file existing
    asset = test_workspace / "requirements.md"
    asset.write_text("Implements: REQ-F-1") # Valid according to GeminiFunctor mock logic
    
    res = run_gemini(test_workspace, "iterate", "--feature", "REQ-F-1", "--edge", "intent→requirements", "--asset", str(asset), "--mode", "headless")
    assert res.returncode == 0
    assert "converged" in res.stdout
    
    # 2. Check Status
    run_gemini(test_workspace, "status")
    status_md = test_workspace / ".ai-workspace" / "STATUS.md"
    assert status_md.exists()
    content = status_md.read_text()
    # If REQ-F-1 was processed, it should be in STATUS.md
    assert "REQ-F-1" in content
    
    # 3. Next Edge: requirements→design
    design_asset = test_workspace / "design.md"
    design_asset.write_text("Implements: REQ-F-1\nSome design content.")
    
    res = run_gemini(test_workspace, "iterate", "--feature", "REQ-F-1", "--edge", "requirements→design", "--asset", str(design_asset), "--mode", "headless")
    assert res.returncode == 0
    assert "converged" in res.stdout
    
    # 4. Final Status Validation
    res = run_gemini(test_workspace, "status")
    # All features converged, state might be ALL_CONVERGED or NO_FEATURES
    assert "REQ-F-1" in res.stdout
    # We don't assert specific edge arrows here as they might be hidden in some states
    
    # 5. Verify Event Log Integrity
    events_file = test_workspace / ".ai-workspace" / "events" / "events.jsonl"
    with open(events_file) as f:
        events = [json.loads(line) for line in f]
        
    # Check for the causal chain
    from gemini_cli.engine.ol_event import normalize_event
    normalized_events = [normalize_event(e) for e in events]
    event_types = [e.get("event_type") for e in normalized_events]
    assert "edge_started" in event_types
    assert "iteration_completed" in event_types
    assert "edge_converged" in event_types
    
    # Verify REQ keys are preserved in events
    assert all(e["feature"] == "REQ-F-1" for e in events if "feature" in e)

def test_recursive_spawn_workflow(test_workspace):
    # This test proves that the engine can handle a 'SpawnRequest' from GeminiFunctor
    # Asset doesn't matter, we just need to trigger the iterate command
    asset = test_workspace / "design.md"
    asset.write_text("Some content.")
    
    # We pass a feature ID that our mock GeminiFunctor won't 'validate' (no REQ tag)
    # Run 4 times to trigger the 'stuck' logic (count > 3)
    for _ in range(4):
        run_gemini(test_workspace, "iterate", "--feature", "REQ-STUCK-1", "--edge", "design→code", "--asset", str(asset), "--mode", "headless")
    
    # The 5th run should trigger recursion
    res = run_gemini(test_workspace, "iterate", "--feature", "REQ-STUCK-1", "--edge", "design→code", "--asset", str(asset), "--mode", "headless")
    
    # Check if recursion was triggered in output or event log
    # In some modes, stdout might not explicitly say RECURSION but the event is emitted
    
    # Verify the event log recorded the spawn event
    events_file = test_workspace / ".ai-workspace" / "events" / "events.jsonl"
    with open(events_file) as f:
        events = [json.loads(line) for line in f]
    
    # Normalize event types
    from gemini_cli.engine.ol_event import normalize_event
    normalized_events = [normalize_event(e) for e in events]
    event_types = [e.get("event_type") for e in normalized_events]
    
    assert "spawn_created" in event_types or "feature_spawned" in event_types
    
    # Verify recursion triggered a compensation event or blocked status
    compensation_events = [e for e in normalized_events if e.get("event_type") == "compensation_triggered"]
    assert len(compensation_events) > 0 or "blocked" in [e.get("status") for e in normalized_events]
