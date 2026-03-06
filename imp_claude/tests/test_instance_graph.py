# Validates: REQ-UX-003, REQ-ROBUST-008
import pytest
from datetime import datetime
from genesis.workspace_state import project_instance_graph, InstanceNode

def test_project_instance_graph_empty():
    graph = project_instance_graph([], topology_version="2.9.0")
    assert len(graph.nodes) == 0
    assert graph.topology_version == "2.9.0"

def test_project_instance_graph_feature_spawned():
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"}
    ]
    graph = project_instance_graph(events)
    assert len(graph.nodes) == 1
    node = graph.nodes[0]
    assert node.feature_id == "REQ-F-1"
    assert node.status == "pending"

def test_project_instance_graph_edge_started_and_converged():
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"},
        {"event_type": "edge_started", "feature": "REQ-F-1", "edge": "design→code", "timestamp": "2026-03-01T12:01:00Z"},
        {"event_type": "iteration_completed", "feature": "REQ-F-1", "edge": "design→code", "delta": 2, "timestamp": "2026-03-01T12:02:00Z"},
        {"event_type": "edge_converged", "feature": "REQ-F-1", "edge": "design→code", "timestamp": "2026-03-01T12:05:00Z"},
    ]
    graph = project_instance_graph(events)
    node = graph.nodes[0]
    assert node.current_edge == "design→code"
    assert node.delta == 2
    assert "design→code" in node.converged_edges

def test_project_instance_graph_feature_converged():
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"},
        {"event_type": "feature_converged", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:06:00Z"},
    ]
    graph = project_instance_graph(events)
    node = graph.nodes[0]
    assert node.status == "archived"

def test_project_instance_graph_openlineage_event():
    events = [
        {
            "run": {
                "facets": {
                    "sdlc:event_type": {"type": "edge_started"}
                }
            },
            "feature": "REQ-F-2",
            "edge": "code↔unit_tests",
            "timestamp": "2026-03-01T13:00:00Z"
        }
    ]
    graph = project_instance_graph(events)
    assert len(graph.nodes) == 1
    node = graph.nodes[0]
    assert node.feature_id == "REQ-F-2"
    assert node.current_edge == "code↔unit_tests"
    assert node.status == "in_progress"
