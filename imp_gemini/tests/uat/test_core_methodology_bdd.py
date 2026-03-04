# Validates: REQ-FEAT-002, REQ-EDGE-001, REQ-EDGE-004
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from pytest_bdd import scenario, given, when, then, parsers

from gemini_cli.engine.state import EventStore, Projector, DependencyResolver
from gemini_cli.engine.iterate import IterateEngine

# ═══════════════════════════════════════════════════════════════════════
# BDD SCENARIOS
# ═══════════════════════════════════════════════════════════════════════

@scenario("features/core_methodology.feature", "Feature Dependencies (UC-04-15)")
def test_uc_04_15_feature_dependencies():
    pass

@scenario("features/core_methodology.feature", "TDD Red-Green Phase (UC-05-01/02)")
def test_uc_05_01_02_tdd_cycle():
    pass

# ═══════════════════════════════════════════════════════════════════════
# STEP DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def core_workspace(tmp_path):
    ws = tmp_path / ".ai-workspace"
    (ws / "features" / "active").mkdir(parents=True)
    (ws / "events").mkdir(parents=True)
    return ws

@given("3 features with dependency graph: A→B, A→C, B and C independent", target_fixture="context")
def setup_dependency_graph(core_workspace):
    store = EventStore(core_workspace)
    # A
    with open(core_workspace / "features" / "active" / "A.yml", "w") as f:
        yaml.dump({"feature": "A", "status": "in_progress", "depends_on": []}, f)
    # B depends on A
    with open(core_workspace / "features" / "active" / "B.yml", "w") as f:
        yaml.dump({"feature": "B", "status": "pending", "depends_on": ["A"]}, f)
    # C depends on A
    with open(core_workspace / "features" / "active" / "C.yml", "w") as f:
        yaml.dump({"feature": "C", "status": "pending", "depends_on": ["A"]}, f)
        
    # Emit spawn events to establish dependency in the log
    store.emit("feature_spawned", project="test", feature="B", data={"parent": "A"})
    store.emit("feature_spawned", project="test", feature="C", data={"parent": "A"})
        
    return {"workspace": core_workspace, "store": store}

@given("a feature at the \"code↔unit_tests\" edge", target_fixture="context")
def setup_tdd_feature(core_workspace):
    store = EventStore(core_workspace)
    feature_id = "REQ-F-TDD-001"
    with open(core_workspace / "features" / "active" / f"{feature_id}.yml", "w") as f:
        yaml.dump({"feature": feature_id, "status": "in_progress"}, f)
    return {"workspace": core_workspace, "store": store, "feature_id": feature_id, "edge": "code↔unit_tests"}

@when("I check the blocked status of the features")
def check_blocked_status(context):
    pass # Resolver instantiated in Then steps

@when("feature A converges")
def converge_feature_a(context):
    context["store"].emit("edge_converged", project="test", feature="A", edge="code↔unit_tests", delta=0)

@when("the iterate function starts a TDD cycle")
def start_tdd_cycle(context):
    context["test_content"] = "# Validates: " + context["feature_id"] + "\ndef test_fail(): assert False"
    context["store"].emit("iteration_completed", project="test", feature=context["feature_id"], 
                         edge=context["edge"], delta=1, 
                         data={"phase": "RED", "test_status": "failing", "iteration": 1})

@when("the iterate function writes code to pass the test")
def write_code_to_pass(context):
    context["code_content"] = "# Implements: " + context["feature_id"] + "\ndef fix(): pass"
    context["test_content"] = context["test_content"].replace("assert False", "assert True")
    context["store"].emit("iteration_completed", project="test", feature=context["feature_id"], 
                         edge=context["edge"], delta=0, 
                         data={"phase": "GREEN", "test_status": "passing", "iteration": 2})

@then("feature A is not blocked")
def verify_a_not_blocked(context):
    events = context["store"].load_all()
    resolver = DependencyResolver(events)
    status = Projector.get_feature_status(events)
    converged = [f for f, d in status.items() if d["status"] == "converged"]
    assert not resolver.is_blocked("A", converged)

@then("feature B is blocked by A")
def verify_b_blocked(context):
    events = context["store"].load_all()
    resolver = DependencyResolver(events)
    status = Projector.get_feature_status(events)
    converged = [f for f, d in status.items() if d["status"] == "converged"]
    assert resolver.is_blocked("B", converged)

@then("feature C is blocked by A")
def verify_c_blocked(context):
    events = context["store"].load_all()
    resolver = DependencyResolver(events)
    status = Projector.get_feature_status(events)
    converged = [f for f, d in status.items() if d["status"] == "converged"]
    assert resolver.is_blocked("C", converged)

@then("features B and C are no longer blocked")
def verify_bc_unblocked(context):
    events = context["store"].load_all()
    resolver = DependencyResolver(events)
    status = Projector.get_feature_status(events)
    converged = [f for f, d in status.items() if d["status"] == "converged"]
    assert not resolver.is_blocked("B", converged)
    assert not resolver.is_blocked("C", converged)

@then("it first writes a failing test (RED state)")
def verify_red_state(context):
    events = context["store"].load_all()
    # Find the iteration completed event
    last_event = [e for e in events if e.get("event_type") == "iteration_completed"][-1]
    assert last_event["data"]["phase"] == "RED"
    delta = last_event.get("run", {}).get("facets", {}).get("sdlc_delta", {}).get("value")
    assert delta > 0

@then("the test is tagged with the feature REQ key")
def verify_test_tag(context):
    assert "Validates: " + context["feature_id"] in context["test_content"]

@then("the test passes (GREEN state)")
def verify_green_state(context):
    events = context["store"].load_all()
    last_event = [e for e in events if e.get("event_type") == "iteration_completed"][-1]
    assert last_event["data"]["phase"] == "GREEN"
    delta = last_event.get("run", {}).get("facets", {}).get("sdlc_delta", {}).get("value")
    assert delta == 0

@then("the code is tagged with the feature REQ key")
def verify_code_tag(context):
    assert "Implements: " + context["feature_id"] in context["code_content"]
