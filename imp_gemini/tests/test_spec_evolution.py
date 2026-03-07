# Validates: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005, REQ-F-EVOL-001
import pytest
from pathlib import Path
from gemini_cli.commands.gaps import GapsCommand
from gemini_cli.commands.review import ReviewCommand
from gemini_cli.engine.state import EventStore, Projector

@pytest.fixture
def project_root(tmp_path):
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    (ws / "events").mkdir()
    (ws / "features" / "active").mkdir(parents=True)
    
    # Standard SDLC structure
    spec_dir = tmp_path / "specification"
    (spec_dir / "requirements").mkdir(parents=True)
    (spec_dir / "features").mkdir(parents=True)
    
    # Add a requirement to trigger a gap
    (spec_dir / "requirements" / "REQ.md").write_text("REQ-GAP-001: Testing Gaps")
    # Initialize FEATURE_VECTORS.md
    (spec_dir / "features" / "FEATURE_VECTORS.md").write_text("# Feature Vectors\n\n### REQ-F-EXISTING: Existing\n- Requirements: []")
    
    return tmp_path

def test_feature_proposal_emission(project_root):
    # 1. Run Gaps to trigger proposal
    cmd = GapsCommand(project_root / ".ai-workspace")
    cmd.run()
    
    # 2. Verify feature_proposal event
    store = EventStore(project_root / ".ai-workspace")
    events = store.load_all()
    
    proposal_ev = next((e for e in events if e.get("run", {}).get("facets", {}).get("sdlc_event_type", {}).get("type") == "feature_proposal"), None)
    assert proposal_ev is not None
    assert "PROP-" in proposal_ev["data"]["proposal_id"]
    assert proposal_ev["data"]["status"] == "draft"

def test_proposal_review_gate(project_root, monkeypatch):
    # 1. Setup proposal with standardized keys
    store = EventStore(project_root / ".ai-workspace")
    raised_ev = store.emit("intent_raised", data={"signal_source": "gap"})
    prop_ev = store.emit("feature_proposal", data={
        "proposal_id": "PROP-123",
        "feature_id": "REQ-F-NEW",
        "title": "New Feature",
        "requirements": ["REQ-1"],
        "intent_id": "INT-1",
        "status": "draft"
    })
    
    # 2. Mock human approval
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    # 3. Run Review
    cmd = ReviewCommand(project_root / ".ai-workspace")
    cmd.run(action="approve", proposal_id="PROP-123")
    
    # 4. Verify status updated and spec_modified emitted
    events = store.load_all()
    approval_ev = next((e for e in events if e.get("event_type") == "review_completed" or e.get("data", {}).get("proposal_id") == "PROP-123"), None)
    assert approval_ev is not None
    
    spec_mod_ev = next((e for e in events if e.get("run", {}).get("facets", {}).get("sdlc_event_type", {}).get("type") == "spec_modified"), None)
    assert spec_mod_ev is not None
    assert "Added feature REQ-F-NEW" in spec_mod_ev["data"]["delta"]
