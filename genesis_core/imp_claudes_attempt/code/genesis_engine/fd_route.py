# Implements: GENESIS_ENGINE_SPEC §3.4 (Profile Selection)
"""F_D route — profile lookup and next edge selection."""

from pathlib import Path

from .models import RouteResult


def select_profile(feature_type: str, profiles_dir: Path) -> str:
    """Map a vector type to a profile name."""
    type_to_profile = {
        "feature": "standard",
        "discovery": "poc",
        "spike": "spike",
        "poc": "poc",
        "hotfix": "hotfix",
    }
    profile_name = type_to_profile.get(feature_type.lower(), "standard")

    profile_path = profiles_dir / f"{profile_name}.yml"
    if not profile_path.exists():
        profile_name = "standard"

    return profile_name


def select_next_edge(
    feature_trajectory: dict,
    graph_topology: dict,
    profile: dict,
) -> RouteResult:
    """Return the next unconverged edge to traverse."""
    profile_name = profile.get("profile", "unknown")
    graph = profile.get("graph", {})
    include_edges = graph.get("include", [])
    optional_edges = graph.get("optional", [])

    if include_edges == "all":
        transitions = graph_topology.get("transitions", [])
        include_edges = []
        for t in transitions:
            source = t.get("source", "")
            target = t.get("target", "")
            if source and target:
                sep = "↔" if t.get("edge_type") == "co_evolution" else "→"
                include_edges.append(f"{source}{sep}{target}")
            elif t.get("edge"):
                include_edges.append(t["edge"])
    if not isinstance(include_edges, list):
        include_edges = []
    if not isinstance(optional_edges, list):
        optional_edges = []

    all_edges = include_edges + optional_edges
    trajectory = feature_trajectory.get("trajectory", {})

    for edge in include_edges:
        edge_status = _edge_status(edge, trajectory)
        if edge_status != "converged":
            return RouteResult(
                selected_edge=edge,
                reason=f"First unconverged required edge (status: {edge_status})",
                profile=profile_name,
                candidates=all_edges,
            )

    for edge in optional_edges:
        edge_status = _edge_status(edge, trajectory)
        if edge_status == "iterating":
            return RouteResult(
                selected_edge=edge,
                reason=f"In-progress optional edge (status: {edge_status})",
                profile=profile_name,
                candidates=all_edges,
            )

    return RouteResult(
        selected_edge="",
        reason="All edges converged",
        profile=profile_name,
        candidates=all_edges,
    )


def _edge_status(edge: str, trajectory: dict) -> str:
    key = edge.replace("→", "_").replace("↔", "_").replace(" ", "")
    entry = trajectory.get(key, {})
    if isinstance(entry, dict):
        return entry.get("status", "pending")
    return "pending"
