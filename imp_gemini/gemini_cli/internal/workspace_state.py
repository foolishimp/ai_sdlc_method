# Implements: REQ-UX-001, REQ-UX-005, REQ-SUPV-002
"""Pure-function workspace state detection utilities.
These functions operate on filesystem paths and return derived state.
"""

import hashlib
import json
import yaml
from pathlib import Path
from typing import Any, Optional, Union

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
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
]

def _workspace_dir(workspace: Path) -> Path:
    if workspace.name == ".ai-workspace":
        return workspace
    return workspace / ".ai-workspace"

def load_events(workspace: Path) -> list[dict[str, Any]]:
    events_file = _workspace_dir(workspace) / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    events = []
    with open(events_file) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
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

def select_next_feature(features: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for f in features:
        if f.get("status") != "converged":
            return f
    return None

def get_next_edge(feature: dict[str, Any]) -> Optional[str]:
    traj = feature.get("trajectory", {})
    for edge in STANDARD_PROFILE_EDGES:
        parts = edge.replace("↔", "→").split("→")
        for p in parts:
            p = p.strip()
            if traj.get(p, {}).get("status") != "converged":
                return edge
    return None

def detect_workspace_state(workspace: Path) -> str:
    ws_dir = _workspace_dir(workspace)
    if not ws_dir.exists():
        return "UNINITIALISED"
    
    # Check for constraints
    constraints_path = ws_dir / "gemini_genesis" / "context" / "project_constraints.yml"
    if not constraints_path.exists():
        constraints_path = ws_dir / "context" / "project_constraints.yml"
    
    if not constraints_path.exists():
        return "NEEDS_CONSTRAINTS"
        
    # Check for intent
    intent_path = workspace / "specification" / "INTENT.md"
    if not intent_path.exists() or intent_path.stat().st_size < 10:
        return "NEEDS_INTENT"
        
    features = get_active_features(workspace)
    if not features:
        return "NO_FEATURES"
        
    if detect_stuck_features(workspace):
        return "STUCK"
        
    all_converged = all(f.get("status") == "converged" for f in features)
    if all_converged:
        return "ALL_CONVERGED"
        
    return "IN_PROGRESS"
