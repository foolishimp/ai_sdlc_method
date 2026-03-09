# Validates: REQ-UX-003
# Validates: REQ-ROBUST-008
# Validates: REQ-EVENT-002
# Validates: REQ-LIFE-001
# Validates: REQ-SUPV-001
import pytest
from datetime import datetime
from genesis.workspace_state import (
    project_instance_graph, InstanceNode, summarise_instance_graph,
    compute_hamiltonian,
)

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

def test_project_instance_graph_feature_converged_legacy():
    """feature_converged without profile → archived (backward compat for old event streams)."""
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"},
        {"event_type": "feature_converged", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:06:00Z"},
    ]
    graph = project_instance_graph(events)
    node = graph.nodes[0]
    assert node.status == "archived"


def test_profile_coverage_derivation():
    """T-COMPLY-003: status derived from converged_edges ⊇ active_profile_edges."""
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"},
        {"event_type": "edge_converged", "feature": "REQ-F-1", "edge": "design→code", "timestamp": "2026-03-01T12:05:00Z"},
        {"event_type": "edge_converged", "feature": "REQ-F-1", "edge": "code↔unit_tests", "timestamp": "2026-03-01T12:06:00Z"},
    ]
    profile_edges = ["design→code", "code↔unit_tests"]
    graph = project_instance_graph(events, active_profile_edges=profile_edges)
    node = graph.nodes[0]
    assert node.status == "converged"
    assert "design→code" in node.converged_edges
    assert "code↔unit_tests" in node.converged_edges


def test_partial_coverage_not_converged():
    """T-COMPLY-003: coverage check requires ALL profile edges — partial is still in_progress."""
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-1", "timestamp": "2026-03-01T12:00:00Z"},
        {"event_type": "edge_converged", "feature": "REQ-F-1", "edge": "design→code", "timestamp": "2026-03-01T12:05:00Z"},
    ]
    profile_edges = ["design→code", "code↔unit_tests"]
    graph = project_instance_graph(events, active_profile_edges=profile_edges)
    node = graph.nodes[0]
    assert node.status == "in_progress"


def test_spawn_created_immediately_adds_child():
    """T-COMPLY-003: spawn_created must add child node before any child edge events."""
    events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-PARENT", "timestamp": "2026-03-01T12:00:00Z"},
        {
            "event_type": "spawn_created",
            "feature": "REQ-F-PARENT",
            "data": {"child_feature": "REQ-F-CHILD", "parent_feature": "REQ-F-PARENT"},
            "timestamp": "2026-03-01T12:01:00Z",
        },
    ]
    graph = project_instance_graph(events)
    ids = [n.feature_id for n in graph.nodes]
    assert "REQ-F-CHILD" in ids, "Child node must be visible immediately after spawn_created"

    child = next(n for n in graph.nodes if n.feature_id == "REQ-F-CHILD")
    assert child.parent_id == "REQ-F-PARENT"
    assert child.status == "pending"
    assert child.zoom_level == 2


def test_spawn_created_child_visible_before_edge_event():
    """T-COMPLY-003: child node exists even with no subsequent edge events for the child."""
    events = [
        {
            "event_type": "spawn_created",
            "feature": "REQ-F-PARENT",
            "data": {"child_feature": "REQ-F-CHILD"},
            "timestamp": "2026-03-01T12:01:00Z",
        },
    ]
    graph = project_instance_graph(events)
    assert any(n.feature_id == "REQ-F-CHILD" for n in graph.nodes)

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


# ── REQ-EVENT-002: Projection Contract ────────────────────────────────────────


_FIXTURE_EVENTS = [
    {"event_type": "feature_spawned", "feature": "REQ-F-A", "timestamp": "2026-03-01T10:00:00Z"},
    {"event_type": "edge_started", "feature": "REQ-F-A", "edge": "design→code", "timestamp": "2026-03-01T10:01:00Z"},
    {"event_type": "iteration_completed", "feature": "REQ-F-A", "edge": "design→code", "delta": 3, "timestamp": "2026-03-01T10:02:00Z"},
    {"event_type": "edge_converged", "feature": "REQ-F-A", "edge": "design→code", "timestamp": "2026-03-01T10:03:00Z"},
    {"event_type": "feature_spawned", "feature": "REQ-F-B", "timestamp": "2026-03-01T10:04:00Z"},
    {"event_type": "edge_started", "feature": "REQ-F-B", "edge": "code↔unit_tests", "timestamp": "2026-03-01T10:05:00Z"},
]


def test_projection_determinism() -> None:
    """Same event stream replayed twice must produce identical output (REQ-EVENT-002 Determinism)."""
    graph1 = project_instance_graph(list(_FIXTURE_EVENTS), topology_version="2.9.0")
    graph2 = project_instance_graph(list(_FIXTURE_EVENTS), topology_version="2.9.0")

    assert len(graph1.nodes) == len(graph2.nodes)
    ids1 = sorted(n.feature_id for n in graph1.nodes)
    ids2 = sorted(n.feature_id for n in graph2.nodes)
    assert ids1 == ids2

    # Statuses must match
    by_id1 = {n.feature_id: n for n in graph1.nodes}
    by_id2 = {n.feature_id: n for n in graph2.nodes}
    for fid in ids1:
        assert by_id1[fid].status == by_id2[fid].status
        assert by_id1[fid].current_edge == by_id2[fid].current_edge
        assert by_id1[fid].delta == by_id2[fid].delta


def test_projection_completeness_replay_to_midpoint() -> None:
    """Replaying to a midpoint returns state at that point (REQ-EVENT-002 Completeness)."""
    # Replay only first 4 events (before REQ-F-B is spawned)
    partial = _FIXTURE_EVENTS[:4]
    graph = project_instance_graph(partial)

    ids = [n.feature_id for n in graph.nodes]
    assert "REQ-F-A" in ids
    assert "REQ-F-B" not in ids

    node_a = next(n for n in graph.nodes if n.feature_id == "REQ-F-A")
    assert "design→code" in node_a.converged_edges


def test_projection_isolation_by_feature() -> None:
    """Each feature node is isolated — one feature's events don't mutate another (REQ-EVENT-002 Isolation)."""
    events = list(_FIXTURE_EVENTS)
    graph = project_instance_graph(events)

    node_a = next(n for n in graph.nodes if n.feature_id == "REQ-F-A")
    node_b = next(n for n in graph.nodes if n.feature_id == "REQ-F-B")

    # REQ-F-A converged on design→code; REQ-F-B did not
    assert "design→code" in node_a.converged_edges
    assert "design→code" not in node_b.converged_edges

    # REQ-F-B is on code↔unit_tests; REQ-F-A is not
    assert node_b.current_edge == "code↔unit_tests"
    assert node_a.current_edge == "design→code"  # last edge_converged sets current_edge


def test_projection_produces_ordered_watermark() -> None:
    """The as_of watermark reflects the timestamp of the last replayed event."""
    graph = project_instance_graph(list(_FIXTURE_EVENTS))
    last_ts = "2026-03-01T10:05:00Z"
    expected = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
    assert graph.as_of == expected


def test_projection_with_empty_stream_is_stable() -> None:
    """Empty event stream must return valid InstanceGraph (not raise)."""
    graph = project_instance_graph([], topology_version="2.9.0")
    summary = summarise_instance_graph(graph)
    assert summary["total_nodes"] == 0
    assert summary["topology_version"] == "2.9.0"


def test_projection_summary_counts_match_nodes() -> None:
    """summarise_instance_graph counts must sum to total_nodes."""
    graph = project_instance_graph(list(_FIXTURE_EVENTS))
    summary = summarise_instance_graph(graph)
    by_status_total = sum(summary["by_status"].values())
    assert by_status_total == summary["total_nodes"]


# ── T-COMPLY-006: Hamiltonian (ADR-S-020) ────────────────────────────────────


_HAMILTONIAN_EVENTS = [
    {"event_type": "feature_spawned", "feature": "REQ-F-H", "timestamp": "2026-03-01T10:00:00Z"},
    {"event_type": "edge_started", "feature": "REQ-F-H", "edge": "design→code", "timestamp": "2026-03-01T10:01:00Z"},
    {"event_type": "iteration_completed", "feature": "REQ-F-H", "edge": "design→code", "delta": 3, "timestamp": "2026-03-01T10:02:00Z"},
    {"event_type": "iteration_completed", "feature": "REQ-F-H", "edge": "design→code", "delta": 2, "timestamp": "2026-03-01T10:03:00Z"},
    {"event_type": "iteration_completed", "feature": "REQ-F-H", "edge": "design→code", "delta": 0, "timestamp": "2026-03-01T10:04:00Z"},
    {"event_type": "edge_converged", "feature": "REQ-F-H", "edge": "design→code", "timestamp": "2026-03-01T10:05:00Z"},
]


def test_hamiltonian_T_accumulates_per_iteration() -> None:
    """T must increment by 1 for each iteration_completed event (ADR-S-020)."""
    graph = project_instance_graph(list(_HAMILTONIAN_EVENTS))
    node = next(n for n in graph.nodes if n.feature_id == "REQ-F-H")
    assert node.hamiltonian_T == 3, f"Expected T=3 after 3 iterations, got {node.hamiltonian_T}"


def test_hamiltonian_V_zero_after_convergence() -> None:
    """V must be 0 after edge_converged (all evaluators passed, delta=0)."""
    graph = project_instance_graph(list(_HAMILTONIAN_EVENTS))
    node = next(n for n in graph.nodes if n.feature_id == "REQ-F-H")
    assert node.hamiltonian_V == 0, f"Expected V=0 after convergence, got {node.hamiltonian_V}"


def test_hamiltonian_H_equals_T_plus_V() -> None:
    """H must equal T + V at all times (ADR-S-020 invariant)."""
    graph = project_instance_graph(list(_HAMILTONIAN_EVENTS))
    node = next(n for n in graph.nodes if n.feature_id == "REQ-F-H")
    assert node.hamiltonian == node.hamiltonian_T + node.hamiltonian_V


def test_hamiltonian_V_tracks_delta() -> None:
    """V must equal the last delta before convergence."""
    # Mid-run events only (no convergence yet)
    events = _HAMILTONIAN_EVENTS[:4]  # includes 2 iteration_completed, last delta=2
    graph = project_instance_graph(list(events))
    node = next(n for n in graph.nodes if n.feature_id == "REQ-F-H")
    assert node.hamiltonian_V == 2, f"Expected V=2 (last delta), got {node.hamiltonian_V}"
    assert node.hamiltonian_T == 2, f"Expected T=2 (2 iterations), got {node.hamiltonian_T}"
    assert node.hamiltonian == 4, f"Expected H=4, got {node.hamiltonian}"


def test_compute_hamiltonian_full_feature() -> None:
    """compute_hamiltonian with no edge filter covers all iterations."""
    T, V, H = compute_hamiltonian(_HAMILTONIAN_EVENTS, "REQ-F-H")
    assert T == 3
    assert V == 0  # converged
    assert H == 3


def test_compute_hamiltonian_single_edge() -> None:
    """compute_hamiltonian with edge filter returns only that edge's T."""
    T, V, H = compute_hamiltonian(_HAMILTONIAN_EVENTS, "REQ-F-H", edge="design→code")
    assert T == 3
    assert V == 0
    assert H == 3


def test_compute_hamiltonian_stalled_feature() -> None:
    """Stalled feature (T grows, V constant) → dH/dt = 1 (ADR-S-020 diagnostic)."""
    stalled_events = [
        {"event_type": "feature_spawned", "feature": "REQ-F-STALL", "timestamp": "2026-03-01T10:00:00Z"},
        {"event_type": "edge_started", "feature": "REQ-F-STALL", "edge": "code↔unit_tests", "timestamp": "2026-03-01T10:01:00Z"},
        {"event_type": "iteration_completed", "feature": "REQ-F-STALL", "edge": "code↔unit_tests", "delta": 2, "timestamp": "2026-03-01T10:02:00Z"},
        {"event_type": "iteration_completed", "feature": "REQ-F-STALL", "edge": "code↔unit_tests", "delta": 2, "timestamp": "2026-03-01T10:03:00Z"},
        {"event_type": "iteration_completed", "feature": "REQ-F-STALL", "edge": "code↔unit_tests", "delta": 2, "timestamp": "2026-03-01T10:04:00Z"},
    ]
    T, V, H = compute_hamiltonian(stalled_events, "REQ-F-STALL")
    assert T == 3   # 3 iterations
    assert V == 2   # delta stuck at 2 (stalled)
    assert H == 5   # H grows → dH/dt > 0 → high-friction (ADR-S-020 diagnostic)


def test_compute_hamiltonian_unknown_feature_returns_zero() -> None:
    """Unknown feature returns (0, 0, 0) — not an error."""
    T, V, H = compute_hamiltonian(_HAMILTONIAN_EVENTS, "REQ-F-UNKNOWN")
    assert T == 0
    assert V == 0
    assert H == 0
