# Implements: REQ-F-DASH-002
"""Generate Mermaid graph diagrams from topology and status data."""

import re

from genesis_monitor.models import GraphTopology, StatusReport
from genesis_monitor.models.core import FeatureVector

# Optional sub-graph nodes: only render when they have actual activity.
# When dormant (no events, no feature trajectory coverage) they clutter the diagram.
_OPTIONAL_NODES = {"parallel_spawn", "tournament_arbitration", "tournament_merge"}


def _sanitize_node_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.replace(" ", "_")).strip("_")


def _extract_target_node(edge_name: str) -> str:
    parts = re.split(r"[→↔]", edge_name)
    return _sanitize_node_id(parts[-1].strip())


def _active_nodes_from_features(features: list[FeatureVector] | None) -> set[str]:
    """Return node IDs that appear in any feature vector trajectory."""
    active: set[str] = set()
    if not features:
        return active
    for fv in features:
        for edge_key in fv.trajectory:
            active.add(_sanitize_node_id(edge_key))
    return active


def build_graph_mermaid(
    topology: GraphTopology | None,
    status: StatusReport | None,
    features: list[FeatureVector] | None = None,
) -> str:
    if not topology or not topology.asset_types:
        return _default_graph(status, features)

    # Determine which optional nodes have real activity
    active_from_features = _active_nodes_from_features(features)
    active_from_status: set[str] = set()
    if status:
        for entry in status.phase_summary:
            active_from_status.add(_extract_target_node(entry.edge))
    all_active = active_from_features | active_from_status

    # Only include optional nodes when they have actual activity
    visible_nodes: set[str] = set()
    for at in topology.asset_types:
        node_id = _sanitize_node_id(at.name)
        if node_id in _OPTIONAL_NODES and node_id not in all_active:
            continue  # dormant — skip
        visible_nodes.add(node_id)

    lines = ["graph LR"]

    # Emit node declarations
    for at in topology.asset_types:
        node_id = _sanitize_node_id(at.name)
        if node_id not in visible_nodes:
            continue
        label = at.name.replace("_", " ").title()
        lines.append(f"    {node_id}[{label}]")

    # Emit only transitions where both endpoints are visible
    for t in topology.transitions:
        src = _sanitize_node_id(t.source)
        tgt = _sanitize_node_id(t.target)
        if src in visible_nodes and tgt in visible_nodes:
            lines.append(f"    {src} --> {tgt}")

    # Convergence colouring — seed from STATUS.md
    converged_nodes: set[str] = set()
    progress_nodes: set[str] = set()

    if status:
        for entry in status.phase_summary:
            node_name = _extract_target_node(entry.edge)
            if entry.status == "converged":
                converged_nodes.add(node_name)
            elif entry.status == "in_progress":
                progress_nodes.add(node_name)

    # Augment from feature vector trajectories (catches pre-code edges like
    # design_recommendations that STATUS.md may not cover)
    if features:
        for fv in features:
            for edge_key, traj in fv.trajectory.items():
                node_id = _sanitize_node_id(edge_key)
                if traj.status == "converged":
                    converged_nodes.add(node_id)
                    progress_nodes.discard(node_id)
                elif traj.status in ("iterating", "in_progress") and node_id not in converged_nodes:
                    progress_nodes.add(node_id)

    converged_nodes &= visible_nodes
    progress_nodes &= visible_nodes

    if converged_nodes:
        lines.append("    classDef done fill:#4caf50,stroke:#388e3c,color:#fff")
        for n in sorted(converged_nodes):
            lines.append(f"    class {n} done")
    if progress_nodes:
        lines.append("    classDef active fill:#ff9800,stroke:#f57c00,color:#fff")
        for n in sorted(progress_nodes):
            lines.append(f"    class {n} active")

    # Tournament nodes get distinct styling when visible (they have activity)
    active_tournament = _OPTIONAL_NODES & visible_nodes
    if active_tournament:
        lines.append("    classDef tournament fill:#e1f5fe,stroke:#01579b,stroke-dasharray: 5 5")
        for n in sorted(active_tournament):
            lines.append(f"    class {n} tournament")

    return "\n".join(lines)


def _default_graph(status: StatusReport | None, features: list[FeatureVector] | None = None) -> str:
    nodes = ["intent", "requirements", "design", "code", "unit_tests", "uat_tests"]
    labels = ["Intent", "Requirements", "Design", "Code", "Unit Tests", "UAT Tests"]
    valid_nodes = set(nodes)
    lines = ["graph LR"]
    for nid, label in zip(nodes, labels):
        lines.append(f"    {nid}[{label}]")
    for i in range(len(nodes) - 1):
        lines.append(f"    {nodes[i]} --> {nodes[i + 1]}")
    if status:
        converged: set[str] = set()
        active: set[str] = set()
        for entry in status.phase_summary:
            target = _extract_target_node(entry.edge)
            if entry.status == "converged":
                converged.add(target)
            elif entry.status == "in_progress":
                active.add(target)
        converged &= valid_nodes
        active &= valid_nodes
        if converged:
            lines.append("    classDef done fill:#4caf50,stroke:#388e3c,color:#fff")
            for n in sorted(converged):
                lines.append(f"    class {n} done")
        if active:
            lines.append("    classDef active fill:#ff9800,stroke:#f57c00,color:#fff")
            for n in sorted(active):
                lines.append(f"    class {n} active")
    return "\n".join(lines)
