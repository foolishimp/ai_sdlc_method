# Validates: REQ-ITER-001, REQ-ITER-002
import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta
from gemini_cli.engine.iterate import IterateEngine

@pytest.fixture
def engine(tmp_path):
    # Setup a mock workspace
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    (ws / "events").mkdir()
    (ws / "features").mkdir()
    (ws / "features" / "active").mkdir()
    (ws / "gemini_genesis").mkdir()
    (ws / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test-project")
    return IterateEngine(project_root=tmp_path)

def test_emit_event(engine):
    # Act
    engine.emit_event(
        event_type="test_event",
        feature="REQ-F-TEST-001",
        edge="design→code",
        data={"delta": 3}
    )
    
    # Assert
    events_file = engine.project_root / ".ai-workspace" / "events" / "events.jsonl"
    assert events_file.exists()
    
    with open(events_file) as f:
        lines = f.readlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "test_event"
        assert event["project"] == "test-project"
        assert event["feature"] == "REQ-F-TEST-001"
        assert event["delta"] == 3

def test_update_feature_vector(engine):
    # Act
    engine.update_feature_vector(
        feature_id="REQ-F-TEST-001",
        edge="design→code",
        iteration=1,
        status="iterating",
        delta=5,
        asset_path="code/test.py"
    )
    
    # Assert
    fv_path = engine.project_root / ".ai-workspace" / "features" / "active" / "REQ-F-TEST-001.yml"
    assert fv_path.exists()
    
    with open(fv_path) as f:
        data = yaml.safe_load(f)
        assert data["feature"] == "REQ-F-TEST-001"
        assert data["trajectory"]["code"]["status"] == "iterating"
        assert data["trajectory"]["code"]["delta"] == 5
        assert data["trajectory"]["code"]["asset"] == "code/test.py"

def test_verify_protocol_success(engine):
    # Arrange
    start_time = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    # Act
    engine.emit_event("iteration_completed", "REQ-F-TEST-001", "design→code", {"delta": 0})
    engine.update_feature_vector("REQ-F-TEST-001", "design→code", 1, "converged", 0)
    
    gaps = engine.verify_protocol(start_time)
    
    # Assert
    assert len(gaps) == 0

def test_verify_protocol_failure(engine):
    # Arrange
    start_time = datetime.now(timezone.utc)
    
    # Act: No side effects performed
    gaps = engine.verify_protocol(start_time)
    
    # Assert
    assert len(gaps) > 0
    assert any("No event emitted" in g for g in gaps)
    assert any("state not updated" in g for g in gaps)
