# Validates: REQ-F-BOOT-001
import pytest
import json
from pathlib import Path
from gemini_cli.internal.state_machine import StateManager, ProjectState

def test_detect_uninitialised(tmp_path):
    # Arrange: Create a directory with no .ai-workspace
    workspace = tmp_path / "non_existent"
    state_mgr = StateManager(workspace_root=str(workspace))
    
    # Act
    state = state_mgr.get_current_state()
    
    # Assert
    assert state == ProjectState.UNINITIALISED

def test_detect_needs_intent(tmp_path):
    # Arrange: Create .ai-workspace but no INTENT.md
    workspace = tmp_path / ".ai-workspace"
    workspace.mkdir()
    (workspace / "gemini_genesis").mkdir()
    (workspace / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test")
    (workspace / "spec").mkdir()
    state_mgr = StateManager(workspace_root=str(workspace))
    
    # Act
    state = state_mgr.get_current_state()
    
    # Assert
    assert state == ProjectState.NEEDS_INTENT

def test_detect_stuck(tmp_path):
    # Arrange: Create .ai-workspace, INTENT.md, features, and STUCK events
    workspace = tmp_path / ".ai-workspace"
    workspace.mkdir()
    (workspace / "gemini_genesis").mkdir()
    (workspace / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test")
    (workspace / "spec").mkdir()
    (workspace / "spec" / "INTENT.md").write_text("Intent content")
    (workspace / "features").mkdir()
    (workspace / "features" / "active").mkdir()
    (workspace / "features" / "active" / "REQ-F-TEST-001.yml").write_text("feature: REQ-F-TEST-001")
    (workspace / "events").mkdir()
    events_file = workspace / "events" / "events.jsonl"
    
    # 3 iterations with same delta=5
    stuck_events = [
        {"event_type": "iteration_completed", "feature": "REQ-F-TEST-001", "edge": "intent→requirements", "delta": 5},
        {"event_type": "iteration_completed", "feature": "REQ-F-TEST-001", "edge": "intent→requirements", "delta": 5},
        {"event_type": "iteration_completed", "feature": "REQ-F-TEST-001", "edge": "intent→requirements", "delta": 5}
    ]
    with open(events_file, "w") as f:
        for e in stuck_events:
            f.write(json.dumps(e) + "\n")
            
    state_mgr = StateManager(workspace_root=str(workspace))
    
    # Act
    state = state_mgr.get_current_state()
    
    # Assert
    assert state == ProjectState.STUCK

def test_detect_all_converged(tmp_path):
    # Arrange: Create .ai-workspace, INTENT.md, and CONVERGED features
    workspace = tmp_path / ".ai-workspace"
    workspace.mkdir()
    (workspace / "gemini_genesis").mkdir()
    (workspace / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test")
    (workspace / "spec").mkdir()
    (workspace / "spec" / "INTENT.md").write_text("Intent content")
    (workspace / "features").mkdir()
    (workspace / "features" / "active").mkdir()
    (workspace / "features" / "active" / "REQ-F-TEST-001.yml").write_text("status: converged\nfeature: REQ-F-TEST-001")
    (workspace / "features" / "active" / "REQ-F-TEST-002.yml").write_text("status: converged\nfeature: REQ-F-TEST-002")
    
    state_mgr = StateManager(workspace_root=str(workspace))
    
    # Act
    state = state_mgr.get_current_state()
    
    # Assert
    assert state == ProjectState.ALL_CONVERGED
