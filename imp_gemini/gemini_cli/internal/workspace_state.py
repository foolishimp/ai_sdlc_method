# Implements: REQ-UX-001, REQ-UX-005, REQ-SUPV-001, REQ-SUPV-002, REQ-ROBUST-003, REQ-ROBUST-008
# Implements: REQ-FEAT-002 (Feature Dependencies), REQ-UX-003 (Project-Wide Observability)
# Implements: REQ-EVOL-001 (Workspace Vector Schema Enforcement)
# Implements: REQ-EVOL-002 (Feature Display Tools Must JOIN Spec and Workspace)
# Implements: REQ-EVOL-004 (spec_modified event + spec hash verification)
# Implements: REQ-INTENT-004 (Spec Reproducibility \u2014 verify_spec_hashes, compute_context_hash)
"""Pure-function workspace state detection utilities.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union, List, Dict

import yaml

# Add relative import for normalize_event
from ..engine.ol_event import normalize_event
from ..engine.models import InstanceNode

WORKSPACE_STATES = (
    "UNINITIALISED",
    "NEEDS_CONSTRAINTS",
    "NEEDS_INTENT",
    "NO_FEATURES",
    "IN_PROGRESS",
    "ALL_CONVERGED",
    "STUCK",
    "ALL_BLOCKED",
)

STANDARD_PROFILE_EDGES = [
    "intent\u2192requirements",
    "requirements\u2192feature_decomp",
    "feature_decomp\u2192design",
    "design\u2192module_decomp",
    "module_decomp\u2192basis_proj",
    "basis_proj\u2192code",
    "code\u2192unit_tests",
]

BOOTLOADER_START_MARKER = "<!-- GENESIS_BOOTLOADER_START -->"

def _workspace_dir(workspace: Path) -> Path:
    if workspace.name == ".ai-workspace":
        return workspace
    return workspace / ".ai-workspace"

def load_events(workspace: Path) -> list[dict[str, Any]]:
    events_file = _workspace_dir(workspace) / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    events: list[dict[str, Any]] = []
    with open(events_file) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(normalize_event(json.loads(line)))
                except:
                    continue
    return events

def get_active_features(workspace: Path) -> list[dict[str, Any]]:
    features_dir = _workspace_dir(workspace) / "features" / "active"
    if not features_dir.exists():
        return []
    features = []
    for path in sorted(features_dir.glob("*.yml")):
        with open(path) as f:
            data = yaml.safe_load(f)
            if data:
                features.append(data)
    return features

def detect_stuck_features(workspace: Path, threshold: int = 3) -> list[dict[str, Any]]:
    events = load_events(workspace)
    sequences = {}
    stuck = []
    for ev in events:
        if ev.get("event_type") == "iteration_completed":
            feat, edge, delta = ev.get("feature"), ev.get("edge"), ev.get("delta")
            if feat and edge and delta is not None:
                sequences.setdefault((feat, edge), []).append(int(delta))
    for (feat, edge), deltas in sequences.items():
        if len(deltas) >= threshold:
            tail = deltas[-threshold:]
            if len(set(tail)) == 1 and tail[0] > 0:
                stuck.append({"feature": feat, "edge": edge})
    return stuck

def verify_spec_hashes(workspace: Path) -> list[dict[str, Any]]:
    ws_dir = _workspace_dir(workspace)
    events_file = ws_dir / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    project_root = ws_dir.parent if ws_dir.name == ".ai-workspace" else workspace
    
    last_spec_event: dict[str, dict] = {}
    events = load_events(workspace)
    for ev in events:
        if ev.get("event_type") in ("spec_modified", "SpecModified"):
            file_path = ev.get("file") or ev.get("data", {}).get("file")
            if not file_path:
                # check payload if it was normalized
                file_path = ev.get("file")
            if file_path:
                last_spec_event[file_path] = ev

    drift = []
    for file_path, event in last_spec_event.items():
        expected = event.get("new_hash")
        if not expected: continue

        abs_path = project_root / file_path
        if not abs_path.exists():
            drift.append({"file": file_path, "expected_hash": expected, "actual_hash": "FILE_MISSING"})
            continue

        actual = "sha256:" + hashlib.sha256(abs_path.read_bytes()).hexdigest()
        if actual != expected:
            drift.append({"file": file_path, "expected_hash": expected, "actual_hash": actual})

    return drift

def verify_genesis_compliance(workspace: Path) -> dict[str, Any]:
    results = []
    passed = 0
    failed = 0

    # 1. Bootloader
    gemini_md = workspace / "GEMINI.md"
    if gemini_md.exists() and BOOTLOADER_START_MARKER in gemini_md.read_text():
        results.append({"name": "bootloader_present", "status": "pass"})
        passed += 1
    else:
        results.append({"name": "bootloader_present", "status": "fail"})
        failed += 1

    # 2. Graph Invariant
    topo_path = _workspace_dir(workspace) / "graph" / "graph_topology.yml"
    if topo_path.exists():
        results.append({"name": "graph_invariant", "status": "pass"})
        passed += 1
    else:
        results.append({"name": "graph_invariant", "status": "fail"})
        failed += 1

    # 3. Spec Hash
    drift = verify_spec_hashes(workspace)
    if not drift:
        results.append({"name": "spec_hash_consistency", "status": "pass"})
        passed += 1
    else:
        results.append({"name": "spec_hash_consistency", "status": "warn"})

    return {"passed": passed, "failed": failed, "results": results}

@dataclass
class InstanceGraph:
    nodes: list[InstanceNode]
    as_of: datetime
    topology_version: str = "3.0.0"

def project_instance_graph(events: list[dict[str, Any]], topology_version: str = "3.0.0", active_profile_edges: Optional[list[str]] = None) -> InstanceGraph:
    nodes: dict[str, InstanceNode] = {}
    last_ts = None

    for ev in events:
        et = ev.get("event_type")
        # Support both flat and OL formats if needed, though normalize_event should have handled it
        feature = ev.get("feature")
        edge = ev.get("edge")
        ts = ev.get("timestamp")
        if ts: last_ts = ts

        if et == "spawn_created" or et == "feature_spawned":
            # OL format has child_feature in data or payload
            child_feature = ev.get("child_feature") or ev.get("data", {}).get("child_feature") or ev.get("feature")
            parent_feature = ev.get("parent_feature") or ev.get("data", {}).get("parent_feature")
            if child_feature and child_feature not in nodes:
                nodes[child_feature] = InstanceNode(
                    feature_id=child_feature,
                    zoom_level=2 if parent_feature else 1,
                    current_edge="",
                    status="pending",
                    delta=-1,
                    parent_id=parent_feature
                )
            continue

        if not feature: continue

        if feature not in nodes:
            nodes[feature] = InstanceNode(
                feature_id=feature,
                zoom_level=1,
                current_edge="",
                status="pending",
                delta=-1
            )

        node = nodes[feature]
        if et == "edge_started":
            node.current_edge = edge
            node.status = "in_progress"
        elif et == "iteration_completed":
            node.current_edge = edge # ensure it's set
            node.delta = int(ev.get("delta", -1))
            node.hamiltonian_T += 1
            node.hamiltonian_V = max(0, node.delta)
            node.status = "in_progress"
        elif et == "edge_converged":
            node.current_edge = edge
            if edge not in node.converged_edges:
                node.converged_edges.append(edge)
            node.hamiltonian_V = 0
            node.status = "in_progress"
            
            # Check for full convergence if profile is known
            if active_profile_edges:
                if all(e in node.converged_edges for e in active_profile_edges):
                    node.status = "converged"
        elif et == "feature_converged":
            node.status = "archived"

    as_of = datetime.fromisoformat(last_ts.replace("Z", "+00:00")) if last_ts else datetime.now(timezone.utc)
    return InstanceGraph(nodes=list(nodes.values()), as_of=as_of, topology_version=topology_version)

def summarise_instance_graph(graph: InstanceGraph) -> dict[str, Any]:
    by_status = {}
    for n in graph.nodes:
        by_status[n.status] = by_status.get(n.status, 0) + 1
    
    return {
        "total_nodes": len(graph.nodes),
        "as_of": graph.as_of.isoformat(),
        "topology_version": graph.topology_version,
        "by_status": by_status
    }

def compute_hamiltonian(events: list[dict[str, Any]], feature_id: str, edge: Optional[str] = None) -> tuple[int, int, int]:
    T = 0
    V = 0
    converged = False
    
    for ev in events:
        if ev.get("feature") != feature_id:
            continue
            
        if edge and ev.get("edge") != edge:
            continue
            
        et = ev.get("event_type")
        if et == "iteration_completed":
            T += 1
            V = int(ev.get("delta", 0))
            converged = False
        elif et == "edge_converged":
            V = 0
            converged = True
            
    return T, V, T + V

def select_next_feature(features: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for f in features:
        if f.get("status") != "converged":
            return f
    return None

def get_next_edge(feature: dict[str, Any]) -> Optional[str]:
    traj = feature.get("trajectory", {})
    for edge in STANDARD_PROFILE_EDGES:
        edge_entry = traj.get(edge, {})
        status_str = edge_entry.get("status") if isinstance(edge_entry, dict) else edge_entry
        if status_str == "converged":
            continue
            
        parts = re.split(r"->|\u2192|\u2194", edge)
        target = parts[-1].strip()
        target_entry = traj.get(target, {})
        target_status = target_entry.get("status") if isinstance(target_entry, dict) else target_entry
        if target_status != "converged":
            return edge
    return None

def detect_workspace_state(workspace: Path) -> str:
    ws_dir = _workspace_dir(workspace)
    if not ws_dir.exists():
        return "UNINITIALISED"
    
    # Check for constraints
    constraints_path = ws_dir / "context" / "project_constraints.yml"
    if not constraints_path or not constraints_path.exists():
        # Try design tenant dirs
        design_tenants = [d.name for d in ws_dir.iterdir() if d.is_dir() and (d.name.endswith("_genesis") or d.name == "gemini")]
        for dt in design_tenants:
            paths = [
                ws_dir / dt / "context" / "project_constraints.yml",
                ws_dir / dt / "project_constraints.yml"
            ]
            for p in paths:
                if p.exists():
                    constraints_path = p
                    break
            if constraints_path and constraints_path.exists():
                break
    
    if not constraints_path or not constraints_path.exists():
        return "NEEDS_CONSTRAINTS"
        
    # Check for intent
    intent_paths = [
        workspace / "specification" / "INTENT.md",
        ws_dir / "spec" / "INTENT.md"
    ]
    intent_found = False
    for p in intent_paths:
        if p.exists() and p.stat().st_size > 10:
            intent_found = True
            break
            
    if not intent_found:
        return "NEEDS_INTENT"
        
    features = get_active_features(workspace)
    if not features:
        return "NO_FEATURES"
        
    if detect_stuck_features(workspace):
        return "STUCK"
        
    # Simple check for ALL_BLOCKED (all unconverged features have blocked edges)
    all_blocked = True
    all_converged = True
    for f in features:
        if f.get("status") != "converged":
            all_converged = False
            # Check if current edge is blocked
            traj = f.get("trajectory", {})
            # This is a bit simplified
            any_edge_open = False
            for edge in STANDARD_PROFILE_EDGES:
                entry = traj.get(edge, {})
                status = entry.get("status") if isinstance(entry, dict) else entry
                if status not in ("converged", "blocked"):
                    any_edge_open = True
                    break
            if any_edge_open:
                all_blocked = False
                break
    
    if all_converged: return "ALL_CONVERGED"
    if all_blocked: return "ALL_BLOCKED"
        
    return "IN_PROGRESS"
