# Validates: REQ-CLI-001, REQ-CLI-002, REQ-CLI-003
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
    (ws / "features").mkdir()
    (ws / "features" / "active").mkdir()
    
    # Mock constraints
    genesis = ws / "gemini_genesis"
    genesis.mkdir()
    (genesis / "project_constraints.yml").write_text("project:\n  name: e2e-test")
    
    return tmp_path

def run_gemini(workspace, cmd, *args):
    """Helper to run the CLI."""
    full_cmd = ["python3", "-m", "gemini_cli.cli", "--workspace", str(workspace / ".ai-workspace"), cmd] + list(args)
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
    res = run_gemini(test_workspace, "status")
    assert "REQ-F-1" in res.stdout
    assert "✓ intent→requirements" in res.stdout
    
    # 3. Next Edge: requirements→design
    design_asset = test_workspace / "design.md"
    design_asset.write_text("Implements: REQ-F-1\nSome design content.")
    
    res = run_gemini(test_workspace, "iterate", "--feature", "REQ-F-1", "--edge", "requirements→design", "--asset", str(design_asset), "--mode", "headless")
    assert res.returncode == 0
    assert "converged" in res.stdout
    
    # 4. Final Status Validation
    res = run_gemini(test_workspace, "status")
    assert "intent→requirements" in res.stdout
    assert "requirements→design" in res.stdout
    assert "converged" in res.stdout
    
    # 5. Verify Event Log Integrity
    events_file = test_workspace / ".ai-workspace" / "events" / "events.jsonl"
    with open(events_file) as f:
        events = [json.loads(line) for line in f]
        
    # Check for the causal chain
    event_types = [e["event_type"] for e in events]
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
    
    # Check if recursion was triggered in output
    assert "RECURSION" in res.stdout
    assert "Spawned" in res.stdout and "vector" in res.stdout
    
    # Verify the event log recorded the feature_spawned event
    events_file = test_workspace / ".ai-workspace" / "events" / "events.jsonl"
    with open(events_file) as f:
        events = [json.loads(line) for line in f]
    
    event_types = [e["event_type"] for e in events]
    assert "feature_spawned" in event_types
    
    # Verify parent is 'blocked'
    last_iter = [e for e in events if e["event_type"] == "iteration_completed"][-1]
    assert last_iter["data"]["status"] == "blocked"
