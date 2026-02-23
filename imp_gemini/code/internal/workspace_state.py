# Implements: REQ-UX-001
import json
import hashlib
from pathlib import Path
from typing import Any
import yaml

# Constants
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

def load_events(workspace_root: Path) -> list[dict[str, Any]]:
    events_file = workspace_root / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    events: list[dict[str, Any]] = []
    with open(events_file, "r") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events

def get_active_features(workspace_root: Path) -> list[dict[str, Any]]:
    features_dir = workspace_root / "features" / "active"
    if not features_dir.exists():
        return []

    features: list[dict[str, Any]] = []
    for path in sorted(features_dir.glob("*.yml")):
        with open(path, "r") as f:
            try:
                content = f.read()
                if content.startswith("---"):
                    content = content[3:]
                data = yaml.safe_load(content)
                if data:
                    features.append(data)
            except Exception:
                continue
    return features

def detect_stuck_features(workspace_root: Path, threshold: int = 3) -> list[dict[str, Any]]:
    events = load_events(workspace_root)
    sequences: dict[tuple[str, str], list[int]] = {}
    for ev in events:
        if ev.get("event_type") != "iteration_completed":
            continue
        feat = ev.get("feature", "")
        edge = ev.get("edge", "")
        delta = ev.get("delta")
        if feat and edge and delta is not None:
            sequences.setdefault((feat, edge), []).append(int(delta))

    stuck: list[dict[str, Any]] = []
    for (feat, edge), deltas in sequences.items():
        if len(deltas) >= threshold:
            tail = deltas[-threshold:]
            if len(set(tail)) == 1 and tail[0] > 0:
                stuck.append({
                    "feature": feat,
                    "edge": edge,
                    "delta": tail[0],
                    "iterations": len(deltas),
                })
    return stuck

def detect_workspace_state(project_root: Path) -> str:
    workspace_root = project_root / ".ai-workspace"
    if not workspace_root.exists():
        return "UNINITIALISED"

    # NEEDS_CONSTRAINTS check
    constraints_file = workspace_root / "gemini_genesis" / "project_constraints.yml"
    if not constraints_file.exists():
        # Fallback to templates/defaults if needed, but for now strict
        return "NEEDS_CONSTRAINTS"

    # NEEDS_INTENT check
    # In imp_gemini, tree shows spec/INTENT.md
    intent_file = workspace_root / "spec" / "INTENT.md"
    if not intent_file.exists() or intent_file.stat().st_size < 10:
        return "NEEDS_INTENT"

    features = get_active_features(workspace_root)
    if not features:
        return "NO_FEATURES"

    stuck_features = detect_stuck_features(workspace_root)
    if stuck_features:
        return "STUCK"

    all_converged = True
    for fv in features:
        if fv.get("status") != "converged":
            all_converged = False
            break
    
    if all_converged:
        return "ALL_CONVERGED"

    return "IN_PROGRESS"

def select_next_feature(features: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not features:
        return None
    
    # Closest-to-complete
    def count_converged(feat):
        traj = feat.get("trajectory", {})
        return sum(1 for p in traj.values() if isinstance(p, dict) and p.get("status") == "converged")
    
    sorted_features = sorted(features, key=count_converged, reverse=True)
    for feat in sorted_features:
        if feat.get("status") != "converged":
            return feat
    return None

def get_next_edge(feature: dict[str, Any], topology: dict[str, Any]) -> str | None:
    traj = feature.get("trajectory", {})
    # Use topology to find the first unconverged edge
    transitions = topology.get("transitions", [])
    for t in transitions:
        target = t.get("target")
        if traj.get(target, {}).get("status") != "converged":
            return f"{t.get('source')}→{t.get('target')}"
    return None

def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts; *override* values win on conflict."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result

def resolve_context_hierarchy(levels: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve a context hierarchy by deep-merging levels in order."""
    result: dict[str, Any] = {}
    for level in levels:
        result = deep_merge(result, level)
    return result

def compute_context_hash(context: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash of a context dict."""
    canonical = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
