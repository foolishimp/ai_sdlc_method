# Validates: REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-002
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from pytest_bdd import scenario, given, when, then, parsers

from gemini_cli.engine.iterate import IterateEngine
from gemini_cli.commands.iterate import IterateCommand
from gemini_cli.engine.topology import GraphTopology
from gemini_cli.engine.state import EventStore, Projector

# ═══════════════════════════════════════════════════════════════════════
# BDD SCENARIOS
# ═══════════════════════════════════════════════════════════════════════

@scenario("features/graph_engine.feature", "Reject inadmissible transitions (UC-01-04)")
def test_uc_01_04_inadmissible_transition():
    pass

@scenario("features/graph_engine.feature", "Markov Stability on Convergence (UC-01-07/08)")
def test_uc_01_07_08_markov_stability():
    pass

# ═══════════════════════════════════════════════════════════════════════
# STEP DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def graph_workspace(tmp_path):
    ws = tmp_path / ".ai-workspace"
    (ws / "graph" / "edges").mkdir(parents=True)
    (ws / "features" / "active").mkdir(parents=True)
    (ws / "events").mkdir(parents=True)
    
    # Minimal topology
    topology = {
        "transitions": [
            {"source": "intent", "target": "requirements", "name": "intent→requirements"},
            {"source": "requirements", "target": "design", "name": "requirements→design"},
            {"source": "design", "target": "code", "name": "design→code"},
            {"source": "code", "target": "unit_tests", "name": "code↔unit_tests"}
        ]
    }
    with open(ws / "graph" / "graph_topology.yml", "w") as f:
        yaml.dump(topology, f)
        
    return ws

@given("an initialized workspace", target_fixture="context")
def setup_init_workspace(graph_workspace):
    return {"workspace": graph_workspace}

@given(parsers.parse("a feature at the \"{stage}\" stage"))
def setup_feature_stage(context, stage):
    feature_id = "REQ-F-TEST-001"
    fv_data = {
        "feature": feature_id,
        "status": "in_progress",
        "trajectory": {stage: {"status": "converged"}}
    }
    with open(context["workspace"] / "features" / "active" / f"{feature_id}.yml", "w") as f:
        yaml.dump(fv_data, f)
    context["feature_id"] = feature_id

@given(parsers.parse("a feature iterating on \"{edge}\""), target_fixture="context")
def setup_iterating_feature(graph_workspace, edge):
    feature_id = "REQ-F-TEST-002"
    return {"workspace": graph_workspace, "feature_id": feature_id, "edge": edge}

@when(parsers.parse("I attempt to iterate on the \"{edge}\" edge"))
def attempt_inadmissible_iteration(context, edge):
    cmd = IterateCommand(context["workspace"])
    # We expect this to fail or return False based on topology
    context["result"] = cmd.run(context["feature_id"], edge, "/tmp/dummy.md", mode="headless")

@when(parsers.parse("an iteration results in delta={delta:d}"))
def run_iteration_with_delta(context, delta):
    # Mocking the engine to produce a specific delta
    with patch("gemini_cli.engine.iterate.IterateEngine.iterate_edge") as mock_iterate:
        from gemini_cli.engine.models import IterationRecord, IterationReport
        
        report = IterationReport(
            asset_path="/tmp/dummy.md",
            delta=delta,
            converged=(delta == 0),
            functor_results=[],
            guardrail_results=[]
        )
        mock_iterate.return_value = IterationRecord(edge=context["edge"], iteration=1, report=report)
        
        cmd = IterateCommand(context["workspace"])
        context["result"] = cmd.run(context["feature_id"], context["edge"], "/tmp/dummy.md", mode="headless")
        context["last_delta"] = delta

@then("the system rejects the traversal")
def verify_rejection(context):
    assert context["result"] is False

@then("reports that the transition is inadmissible")
def verify_rejection_report(context):
    store = EventStore(context["workspace"])
    events = store.load_all()
    started_events = [e for e in events if e.get("event_type") == "edge_started"]
    assert not any(e.get("edge") == "requirements→unit_tests" for e in started_events)

@then("the asset achieves Markov object status")
def verify_markov_status(context):
    fv_path = context["workspace"] / "features" / "active" / f"{context['feature_id']}.yml"
    with open(fv_path, "r") as f:
        data = yaml.safe_load(f)
    
    traj_key = context["edge"].split("→")[-1].split("↔")[-1]
    assert data["trajectory"][traj_key]["status"] == "converged"

@then("the asset remains a \"candidate\"")
def verify_candidate_status(context):
    fv_path = context["workspace"] / "features" / "active" / f"{context['feature_id']}.yml"
    with open(fv_path, "r") as f:
        data = yaml.safe_load(f)
    
    traj_key = context["edge"].split("→")[-1].split("↔")[-1]
    assert data["trajectory"][traj_key]["status"] == "iterating"

@then(parsers.parse("the feature status is updated to \"{status}\" for that edge"))
def verify_edge_status(context, status):
    fv_path = context["workspace"] / "features" / "active" / f"{context['feature_id']}.yml"
    with open(fv_path, "r") as f:
        data = yaml.safe_load(f)
    traj_key = context["edge"].split("→")[-1].split("↔")[-1]
    assert data["trajectory"][traj_key]["status"] == status

@then(parsers.parse("the edge status is \"{status}\""))
def verify_edge_status_alt(context, status):
    verify_edge_status(context, status)
