# Validates: ADR-S-026, REQ-F-ITER-001
import pathlib
import pytest
import yaml
from tests.e2e.conftest import (
    CONFIG_DIR, EDGE_PARAMS_DIR, PROFILES_DIR, IMP_GEMINI, 
    PROJECT_CONSTRAINTS_YML, MockGeminiRunner, skip_no_gemini, _persist_run,
    INTENT_MD
)
from tests.e2e.validators import load_events
from datetime import datetime, timezone
import shutil

PLAN_INTENT_VECTOR_YML = """
id: "INTENT-AUTH-001"
source: "abiogenesis"
resolution_level: "intent"
composition_expression:
  macro: "PLAN"
  bindings:
    unit_category: "feature"
status: "iterating"
created_at: "{timestamp}"
trajectory:
  intent:
    status: converged
"""

@pytest.fixture(scope="module")
def plan_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-plan")
    ws = project_dir / ".ai-workspace"
    timestamp = datetime.now(timezone.utc).isoformat()
    for d in ["graph/edges", "profiles", "vectors/active", "events", "gemini_genesis", "specification"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
        (project_dir / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"): shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"): shutil.copy2(yml, ws / "profiles" / yml.name)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)
    with open(ws / "vectors" / "active" / "INTENT-AUTH-001.yml", "w") as f:
        f.write(PLAN_INTENT_VECTOR_YML.replace("{timestamp}", timestamp))
    return project_dir

@pytest.fixture(scope="module")
def plan_result(plan_project_dir: pathlib.Path) -> pathlib.Path:
    runner = MockGeminiRunner(plan_project_dir)
    runner.run_plan("INTENT-AUTH-001")
    _persist_run(plan_project_dir, failed=False)
    return plan_project_dir

@pytest.mark.e2e
class TestE2EPlan:
    def test_plan_published(self, plan_result: pathlib.Path):
        events = load_events(plan_result)
        assert any(e.get("event_type") == "plan_published" for e in events)
    def test_work_order_ratified(self, plan_result: pathlib.Path):
        events = load_events(plan_result)
        assert any(e.get("event_type") == "work_order_ratified" for e in events)
    def test_vector_trajectory_updated(self, plan_result: pathlib.Path):
        iv_path = plan_result / ".ai-workspace" / "vectors" / "active" / "INTENT-AUTH-001.yml"
        with open(iv_path, "r") as f:
            data = yaml.safe_load(f)
        assert "work_order" in data["trajectory"]["requirements"]
