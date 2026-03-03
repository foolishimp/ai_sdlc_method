# Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-005
import pytest
import time
import yaml
import os
from pathlib import Path
from gemini_cli.engine.sensory import SensoryService
from gemini_cli.engine.state import EventStore

def test_sensory_artifact_write(tmp_path: Path):
    """Verifies that writing an artifact is detected by the sensory service."""
    # Setup
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()
    
    # Create required folders
    (tmp_path / "code").mkdir()
    
    service = SensoryService(workspace_root)
    store = EventStore(workspace_root)
    
    # Run once to establish baseline
    service.run_all_monitors()
    
    # Act: Create a new artifact
    new_file = tmp_path / "code" / "new_module.py"
    new_file.write_text("# Implements: REQ-F-TEST-001")
    
    # Run again
    service.run_all_monitors()
    
    # Verify: Check event log for artifact_write signal
    events = store.load_all()
    signal_events = [e for e in events if e.get("event_type") == "exteroceptive_signal" and e.get("name") == "artifact_write"]
    
    assert len(signal_events) > 0
    assert signal_events[0]["file"] == "code/new_module.py"
    assert signal_events[0]["status"] == "new"

def test_sensory_feature_vector_stall(tmp_path: Path):
    """Verifies that stalled feature vectors are detected."""
    # Setup
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()
    features_dir = workspace_root / "features" / "active"
    features_dir.mkdir(parents=True)
    
    # Create a feature vector
    fv_path = features_dir / "REQ-F-STALE-001.yml"
    fv_data = {
        "feature": "REQ-F-STALE-001",
        "status": "in_progress",
        "trajectory": {}
    }
    with open(fv_path, "w") as f:
        yaml.dump(fv_data, f)
    
    # Force mtime to be in the past (e.g., 20 days ago)
    past_time = time.time() - (20 * 24 * 3600)
    os.utime(fv_path, (past_time, past_time))
    
    service = SensoryService(workspace_root)
    store = EventStore(workspace_root)
    
    # Act
    service.run_all_monitors()
    
    # Verify
    events = store.load_all()
    stall_signals = [e for e in events if e.get("event_type") == "interoceptive_signal" and e.get("name") == "feature_vector_stall"]
    
    assert len(stall_signals) > 0
    assert any(f["feature"] == "REQ-F-STALE-001" for f in stall_signals[0]["stalled_features"])
