# Validates: ADR-S-025, REQ-F-EVAL-001
import pathlib
import pytest
import yaml
from tests.e2e.conftest import (
    CONFIG_DIR, EDGE_PARAMS_DIR, PROFILES_DIR, IMP_GEMINI, 
    PROJECT_CONSTRAINTS_YML, MockGeminiRunner, skip_no_gemini, _persist_run
)
from tests.e2e.validators import load_events
from datetime import datetime, timezone
import shutil

@pytest.fixture(scope="module")
def consensus_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-consensus")
    ws = project_dir / ".ai-workspace"
    timestamp = datetime.now(timezone.utc).isoformat()
    for d in ["graph/edges", "profiles", "vectors/active", "events", "gemini_genesis"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"): shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"): shutil.copy2(yml, ws / "profiles" / yml.name)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)
    
    iv_data = {
        "id": "INTENT-ADR-099",
        "trajectory": {"intent": {"status": "converged"}}
    }
    with open(ws / "vectors" / "active" / "INTENT-ADR-099.yml", "w") as f:
        yaml.dump(iv_data, f)
    return project_dir

@pytest.fixture(scope="module")
def consensus_result(consensus_project_dir: pathlib.Path) -> pathlib.Path:
    runner = MockGeminiRunner(consensus_project_dir)
    runner.run_consensus("INTENT-ADR-099")
    _persist_run(consensus_project_dir, failed=False)
    return consensus_project_dir

@pytest.mark.e2e
class TestE2EConsensus:
    def test_proposal_published(self, consensus_result: pathlib.Path):
        events = load_events(consensus_result)
        assert any(e.get("event_type") == "proposal_published" for e in events)
    def test_votes_recorded(self, consensus_result: pathlib.Path):
        events = load_events(consensus_result)
        assert len([e for e in events if e.get("event_type") == "vote_cast"]) >= 2
    def test_consensus_reached(self, consensus_result: pathlib.Path):
        events = load_events(consensus_result)
        assert any(e.get("event_type") == "consensus_reached" for e in events)
