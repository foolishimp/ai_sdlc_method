# Implements: REQ-UX-001
"""Pure-function workspace state detection utilities.

These functions operate on filesystem paths (workspace directories) and return
derived state.  No stored state variables — same input always produces same
output.  Designed to become the foundation of the runtime engine once it exists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════
# EVENT UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def load_events(workspace: Path) -> list[dict[str, Any]]:
    """Parse events.jsonl from a workspace, returning list of event dicts.

    Skips blank lines.  Raises ValueError on malformed JSON.
    """
    events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    events: list[dict[str, Any]] = []
    for i, line in enumerate(events_file.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON on line {i} of events.jsonl: {exc}"
            ) from exc
    return events


def get_converged_edges(events: list[dict[str, Any]], feature: str) -> set[str]:
    """Return set of edge names that have ``edge_converged`` events for *feature*."""
    return {
        ev.get("edge", "")
        for ev in events
        if ev.get("event_type") == "edge_converged"
        and ev.get("feature") == feature
    }


def compute_current_delta(
    events: list[dict[str, Any]], feature: str, edge: str,
) -> int | None:
    """Return the most recent delta value for a feature/edge pair, or None."""
    delta: int | None = None
    for ev in events:
        if (
            ev.get("event_type") == "iteration_completed"
            and ev.get("feature") == feature
            and ev.get("edge") == edge
        ):
            d = ev.get("delta")
            if d is not None:
                delta = int(d)
    return delta


def get_iteration_count(
    events: list[dict[str, Any]], feature: str, edge: str,
) -> int:
    """Count iteration_completed events for a feature/edge pair."""
    return sum(
        1
        for ev in events
        if ev.get("event_type") == "iteration_completed"
        and ev.get("feature") == feature
        and ev.get("edge") == edge
    )


# ═══════════════════════════════════════════════════════════════════════
# FEATURE UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def get_active_features(workspace: Path) -> list[dict[str, Any]]:
    """Load all active feature vector YAML files."""
    features_dir = workspace / ".ai-workspace" / "features" / "active"
    if not features_dir.exists():
        return []

    features: list[dict[str, Any]] = []
    for path in sorted(features_dir.glob("*.yml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        if data:
            features.append(data)
    return features


def detect_stuck_features(
    workspace: Path, threshold: int = 3,
) -> list[dict[str, Any]]:
    """Detect features where delta has not decreased for *threshold* consecutive iterations.

    Returns a list of dicts with keys: feature, edge, delta, iterations, reason.
    """
    events = load_events(workspace)
    stuck: list[dict[str, Any]] = []

    # Group iteration events by (feature, edge)
    sequences: dict[tuple[str, str], list[int]] = {}
    for ev in events:
        if ev.get("event_type") != "iteration_completed":
            continue
        feat = ev.get("feature", "")
        edge = ev.get("edge", "")
        delta = ev.get("delta")
        if feat and edge and delta is not None:
            sequences.setdefault((feat, edge), []).append(int(delta))

    for (feat, edge), deltas in sequences.items():
        if len(deltas) < threshold:
            continue
        # Check if the last `threshold` deltas are identical and > 0
        tail = deltas[-threshold:]
        if len(set(tail)) == 1 and tail[0] > 0:
            stuck.append({
                "feature": feat,
                "edge": edge,
                "delta": tail[0],
                "iterations": len(deltas),
                "reason": f"delta={tail[0]} unchanged for {threshold} iterations",
            })

    return stuck


def _has_pending_human_review(
    workspace: Path, feature_id: str, events: list[dict[str, Any]],
) -> bool:
    """Check if a feature has a pending human review.

    Only returns True if the feature vector trajectory explicitly contains
    a "pending_review" status on any edge.  Simply having iterations without
    review events does NOT imply a block — most edges don't require human review.
    """
    features = get_active_features(workspace)
    for fv in features:
        if fv.get("feature") != feature_id:
            continue
        traj = fv.get("trajectory", {})
        for _edge_name, edge_data in traj.items():
            if isinstance(edge_data, dict) and edge_data.get("status") == "pending_review":
                return True
    return False


def _has_blocked_dependency(
    workspace: Path, feature_id: str, events: list[dict[str, Any]],
) -> bool:
    """Check if a feature is blocked by an unconverged dependency (spawn)."""
    features = get_active_features(workspace)
    for fv in features:
        if fv.get("feature") != feature_id:
            continue
        deps = fv.get("dependencies", [])
        for dep in deps:
            dep_id = dep if isinstance(dep, str) else dep.get("feature", "")
            if dep_id:
                dep_converged = get_converged_edges(events, dep_id)
                # If any standard edge is not converged, it's blocking
                if not dep_converged:
                    return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# FEATURE SELECTION & EDGE WALK
# ═══════════════════════════════════════════════════════════════════════

def select_closest_to_complete(
    features: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Select the feature closest to completion (fewest unconverged edges).

    Returns the feature vector dict, or None if no active features.
    """
    best: dict[str, Any] | None = None
    best_remaining = float("inf")

    for fv in features:
        if fv.get("status") == "converged":
            continue
        traj = fv.get("trajectory", {})
        converged_count = sum(
            1 for _k, v in traj.items()
            if isinstance(v, dict) and v.get("status") == "converged"
        )
        total_edges = max(len(traj), 1)
        remaining = total_edges - converged_count
        if remaining < best_remaining:
            best_remaining = remaining
            best = fv

    return best


def walk_topological_edges(
    traj: dict[str, Any],
    profile_edges: list[str] | None = None,
) -> str | None:
    """Walk edges in topological order, return first unconverged edge.

    *profile_edges* is the ordered list of edges from the profile.
    If not provided, uses STANDARD_PROFILE_EDGES.
    """
    edges = profile_edges or STANDARD_PROFILE_EDGES
    # Normalise edge names → trajectory keys
    for edge in edges:
        # edge name may contain → or ↔; trajectory keys are the target asset name
        parts = edge.replace("↔", "→").split("→")
        for part in parts:
            part = part.strip()
            traj_entry = traj.get(part)
            if isinstance(traj_entry, dict):
                status = traj_entry.get("status", "pending")
                if status not in ("converged",):
                    return edge
            else:
                # Not yet started — this is the next edge
                return edge
    return None  # all converged


# ═══════════════════════════════════════════════════════════════════════
# INTEGRITY & HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════

def detect_corrupted_events(workspace: Path) -> list[dict[str, Any]]:
    """Return list of corruption reports for events.jsonl.

    Each report: {line: int, raw: str, error: str}.
    """
    events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    corruptions: list[dict[str, Any]] = []
    for i, line in enumerate(events_file.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            json.loads(stripped)
        except json.JSONDecodeError as exc:
            corruptions.append({"line": i, "raw": stripped, "error": str(exc)})
    return corruptions


def detect_orphaned_spawns(workspace: Path) -> list[dict[str, Any]]:
    """Find spawns whose parent feature doesn't exist.

    Returns list of dicts: {feature: str, parent: str, reason: str}.
    """
    features = get_active_features(workspace)
    feature_ids = {fv.get("feature", "") for fv in features}

    orphans: list[dict[str, Any]] = []
    for fv in features:
        parent = fv.get("parent", {})
        if not parent:
            continue
        parent_id = parent.get("feature", "") if isinstance(parent, dict) else str(parent)
        if parent_id and parent_id not in feature_ids:
            orphans.append({
                "feature": fv.get("feature", ""),
                "parent": parent_id,
                "reason": f"parent {parent_id} not in active features",
            })
    return orphans


def detect_missing_feature_vectors(workspace: Path) -> list[str]:
    """Find feature IDs referenced in events but without a vector file.

    Returns list of missing feature IDs.
    """
    events = load_events(workspace)
    features = get_active_features(workspace)
    feature_ids = {fv.get("feature", "") for fv in features}

    referenced: set[str] = set()
    for ev in events:
        feat = ev.get("feature", "")
        if feat:
            referenced.add(feat)

    return sorted(referenced - feature_ids - {""})


def detect_circular_dependencies(workspace: Path) -> list[list[str]]:
    """Detect circular dependency chains among features.

    Returns list of cycles, each a list of feature IDs forming the cycle.
    """
    features = get_active_features(workspace)
    # Build adjacency: feature → set of dependency features
    deps: dict[str, set[str]] = {}
    for fv in features:
        fid = fv.get("feature", "")
        dep_list = fv.get("dependencies", [])
        dep_ids: set[str] = set()
        for dep in dep_list:
            did = dep if isinstance(dep, str) else dep.get("feature", "")
            if did:
                dep_ids.add(did)
        deps[fid] = dep_ids

    # DFS cycle detection
    visited: set[str] = set()
    rec_stack: set[str] = set()
    cycles: list[list[str]] = []

    def _dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        for nbr in deps.get(node, set()):
            if nbr not in visited:
                _dfs(nbr, path)
            elif nbr in rec_stack:
                # Found cycle — extract it
                idx = path.index(nbr)
                cycles.append(path[idx:] + [nbr])
        path.pop()
        rec_stack.discard(node)

    for fid in deps:
        if fid not in visited:
            _dfs(fid, [])

    return cycles


# ═══════════════════════════════════════════════════════════════════════
# FEATURE VIEWS
# ═══════════════════════════════════════════════════════════════════════

def compute_feature_view(
    workspace: Path, feature_id: str,
) -> dict[str, Any]:
    """Compute a cross-artifact view for a single feature.

    Returns: {feature, status, edges: {edge_name: {status, iterations, delta}}}.
    """
    features = get_active_features(workspace)
    events = load_events(workspace)

    fv_data: dict[str, Any] | None = None
    for fv in features:
        if fv.get("feature") == feature_id:
            fv_data = fv
            break
    if fv_data is None:
        return {"feature": feature_id, "status": "not_found", "edges": {}}

    edges_view: dict[str, dict[str, Any]] = {}
    traj = fv_data.get("trajectory", {})
    for edge_name, edge_data in traj.items():
        if not isinstance(edge_data, dict):
            continue
        edge_status = edge_data.get("status", "pending")
        iters = edge_data.get("iteration", 0)
        delta = edge_data.get("delta")
        edges_view[edge_name] = {
            "status": edge_status,
            "iterations": iters,
            "delta": delta,
        }

    return {
        "feature": feature_id,
        "status": fv_data.get("status", "pending"),
        "edges": edges_view,
    }


def compute_aggregated_view(
    workspace: Path,
) -> dict[str, Any]:
    """Compute aggregated view across all features.

    Returns: {total, converged, in_progress, blocked, stuck,
              edges_converged, edges_total}.
    """
    features = get_active_features(workspace)
    events = load_events(workspace)

    total = len(features)
    converged = 0
    in_progress = 0
    blocked = 0
    edges_converged = 0
    edges_total = 0

    stuck_list = detect_stuck_features(workspace)
    stuck_ids = {s["feature"] for s in stuck_list}

    for fv in features:
        fid = fv.get("feature", "")
        status = fv.get("status", "pending")
        traj = fv.get("trajectory", {})

        for _k, v in traj.items():
            if isinstance(v, dict):
                edges_total += 1
                if v.get("status") == "converged":
                    edges_converged += 1

        if status == "converged":
            converged += 1
        elif fid in stuck_ids:
            pass  # counted separately
        elif (
            _has_blocked_dependency(workspace, fid, events)
            or _has_pending_human_review(workspace, fid, events)
        ):
            blocked += 1
        else:
            in_progress += 1

    return {
        "total": total,
        "converged": converged,
        "in_progress": in_progress,
        "blocked": blocked,
        "stuck": len(stuck_list),
        "edges_converged": edges_converged,
        "edges_total": edges_total,
    }


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT HIERARCHY
# ═══════════════════════════════════════════════════════════════════════

def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts; *override* values win on conflict."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def resolve_context_hierarchy(
    levels: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve a context hierarchy by deep-merging levels in order.

    Each level is a dict.  Later levels override earlier ones.
    """
    result: dict[str, Any] = {}
    for level in levels:
        result = deep_merge(result, level)
    return result


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT HASHING / REPRODUCIBILITY
# ═══════════════════════════════════════════════════════════════════════

def compute_context_hash(context: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash of a context dict.

    Uses sorted JSON serialisation for determinism.
    """
    canonical = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# ESCALATION / SIGNAL TRACKING
# ═══════════════════════════════════════════════════════════════════════

def get_unactioned_escalations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find escalation/intent_raised events that have no corresponding action.

    An escalation is 'actioned' if a spawn_created, review_completed, or
    spec_modified event references the same intent_id or feature.
    """
    escalations = [
        ev for ev in events
        if ev.get("event_type") in ("intent_raised", "escalation")
    ]
    actioned_intents: set[str] = set()
    for ev in events:
        if ev.get("event_type") in ("spawn_created", "review_completed", "spec_modified"):
            iid = ev.get("intent_id", "") or ev.get("data", {}).get("intent_id", "")
            if iid:
                actioned_intents.add(iid)

    unactioned: list[dict[str, Any]] = []
    for esc in escalations:
        iid = esc.get("intent_id", "") or esc.get("data", {}).get("intent_id", "")
        if iid and iid not in actioned_intents:
            unactioned.append(esc)
        elif not iid:
            unactioned.append(esc)

    return unactioned


def classify_tolerance_breach(
    monitor_value: float | int,
    threshold: float | int,
    *,
    severity: str = "warning",
) -> str:
    """Classify a tolerance breach into one of three IntentEngine output types.

    Returns: "reflex.log", "specEventLog", or "escalate".
    """
    if monitor_value <= threshold:
        return "reflex.log"
    ratio = monitor_value / max(threshold, 1)
    if severity == "critical" or ratio > 2.0:
        return "escalate"
    return "specEventLog"


# ═══════════════════════════════════════════════════════════════════════
# GRAPH ZOOM OPERATIONS
# ═══════════════════════════════════════════════════════════════════════

def zoom_in_edge(
    edge_name: str,
    graph_topology: dict[str, Any],
) -> list[dict[str, Any]]:
    """Expand a single edge into sub-edges from graph topology.

    Returns list of sub-transition dicts.  If no sub-edges defined,
    returns the original edge as a single-element list.
    """
    transitions = graph_topology.get("transitions", [])
    # Find the transition
    for t in transitions:
        if t.get("name") == edge_name:
            sub = t.get("sub_edges", t.get("sub_transitions", []))
            if sub:
                return sub
            return [t]
    return []


def zoom_out_edges(
    sub_edges: list[str],
    graph_topology: dict[str, Any],
) -> str | None:
    """Collapse sub-edges back to their parent edge name.

    Returns the parent transition name, or None if not found.
    """
    transitions = graph_topology.get("transitions", [])
    for t in transitions:
        subs = t.get("sub_edges", t.get("sub_transitions", []))
        if subs:
            sub_names = {s.get("name", s) if isinstance(s, dict) else s for s in subs}
            if set(sub_edges).issubset(sub_names):
                return t.get("name")
    return None


def zoom_preserves_invariants(
    original_edge: dict[str, Any],
    sub_edges: list[dict[str, Any]],
) -> bool:
    """Verify that zoom operation preserves graph invariants.

    Invariants: directed, typed source/target, evaluators defined.
    """
    for sub in sub_edges:
        if not isinstance(sub, dict):
            continue
        # Must have source and target (directed)
        if "source" not in sub and "target" not in sub:
            if "name" not in sub:
                return False
        # Evaluators must be defined (or inherited)
        if "evaluators" not in sub and "evaluators" not in original_edge:
            return False
    return True


# ═══════════════════════════════════════════════════════════════════════
# EVENT RECONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════

def reconstruct_feature_state(
    events: list[dict[str, Any]], feature_id: str,
) -> dict[str, Any]:
    """Reconstruct feature vector state from events alone.

    Returns a dict with: {feature, status, trajectory: {edge: {status, iterations, delta}}}.
    """
    traj: dict[str, dict[str, Any]] = {}
    converged_edges: set[str] = set()

    for ev in events:
        if ev.get("feature") != feature_id:
            continue
        etype = ev.get("event_type", "")
        edge = ev.get("edge", "")

        if etype == "edge_started" and edge:
            if edge not in traj:
                traj[edge] = {"status": "iterating", "iterations": 0, "delta": None}

        elif etype == "iteration_completed" and edge:
            if edge not in traj:
                traj[edge] = {"status": "iterating", "iterations": 0, "delta": None}
            traj[edge]["iterations"] = ev.get("iteration", traj[edge]["iterations"])
            traj[edge]["delta"] = ev.get("delta")
            traj[edge]["status"] = "iterating"

        elif etype == "edge_converged" and edge:
            if edge not in traj:
                traj[edge] = {"status": "converged", "iterations": 0, "delta": 0}
            traj[edge]["status"] = "converged"
            traj[edge]["delta"] = 0
            converged_edges.add(edge)

    all_converged = len(traj) > 0 and all(
        e.get("status") == "converged" for e in traj.values()
    )
    status = "converged" if all_converged else "in_progress"

    return {"feature": feature_id, "status": status, "trajectory": traj}


# ═══════════════════════════════════════════════════════════════════════
# STATE DETECTION — THE CORE FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def detect_workspace_state(workspace: Path) -> str:
    """Detect the current workspace state from filesystem + event log.

    Returns one of: UNINITIALISED, NEEDS_CONSTRAINTS, NEEDS_INTENT,
    NO_FEATURES, IN_PROGRESS, ALL_CONVERGED, STUCK, ALL_BLOCKED.

    This function is pure — it reads only, never writes.
    Same workspace contents always produce the same result.
    """
    ws_dir = workspace / ".ai-workspace"

    # 1. No .ai-workspace → UNINITIALISED
    if not ws_dir.exists():
        return "UNINITIALISED"

    # 2. Check for project constraints
    constraints_candidates = [
        ws_dir / "bedrock" / "context" / "project_constraints.yml",
        ws_dir / "context" / "project_constraints.yml",
    ]
    has_constraints = False
    for cp in constraints_candidates:
        if cp.exists():
            try:
                with open(cp) as f:
                    data = yaml.safe_load(f)
                if data and data.get("project"):
                    has_constraints = True
                    break
            except (yaml.YAMLError, OSError):
                pass

    # Check mandatory constraint dimensions
    if has_constraints:
        for cp in constraints_candidates:
            if cp.exists():
                try:
                    with open(cp) as f:
                        data = yaml.safe_load(f)
                    dims = data.get("constraint_dimensions", {})
                    mandatory_filled = 0
                    mandatory_total = 0
                    for _name, dim_val in dims.items():
                        if isinstance(dim_val, dict):
                            # Check if it has meaningful content (not all empty)
                            values = [
                                v for k, v in dim_val.items()
                                if k not in ("mandatory", "description", "resolves_via", "examples", "notes")
                                and v
                            ]
                            if values:
                                mandatory_filled += 1
                            mandatory_total += 1
                    if mandatory_total > 0 and mandatory_filled == 0:
                        return "NEEDS_CONSTRAINTS"
                except (yaml.YAMLError, OSError):
                    pass
                break

    if not has_constraints:
        return "NEEDS_CONSTRAINTS"

    # 3. Check for intent
    intent_candidates = [
        workspace / "specification" / "INTENT.md",
        ws_dir / "spec" / "INTENT.md",
    ]
    has_intent = any(
        p.exists() and p.stat().st_size > 10
        for p in intent_candidates
    )
    if not has_intent:
        return "NEEDS_INTENT"

    # 4. Check for active features
    features = get_active_features(workspace)
    if not features:
        return "NO_FEATURES"

    # 5. Load events for feature analysis
    events = load_events(workspace)

    # 6. Check if all features are converged
    all_converged = True
    any_stuck = False
    all_blocked = True

    for fv in features:
        feat_id = fv.get("feature", "")
        status = fv.get("status", "pending")

        if status == "converged":
            continue

        all_converged = False

        # Check if stuck
        stuck_list = detect_stuck_features(workspace, threshold=3)
        if any(s["feature"] == feat_id for s in stuck_list):
            any_stuck = True
            continue

        # Check if blocked (dependency or pending review)
        is_blocked = (
            _has_blocked_dependency(workspace, feat_id, events)
            or _has_pending_human_review(workspace, feat_id, events)
        )
        if not is_blocked:
            all_blocked = False

    if all_converged:
        return "ALL_CONVERGED"

    if any_stuck:
        return "STUCK"

    if all_blocked:
        return "ALL_BLOCKED"

    return "IN_PROGRESS"
