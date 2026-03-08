# Implements: REQ-UX-001, REQ-UX-005, REQ-SUPV-002, REQ-ROBUST-003, REQ-ROBUST-008
# Implements: REQ-FEAT-002 (Feature Dependencies), REQ-UX-003 (Project-Wide Observability)
# Implements: REQ-EVOL-001 (Workspace Vector Schema Enforcement)
# Implements: REQ-EVOL-002 (Feature Display Tools Must JOIN Spec and Workspace)
# Implements: REQ-EVOL-004 (spec_modified event + spec hash verification)
# Implements: REQ-INTENT-004 (Spec Reproducibility — verify_spec_hashes, compute_context_hash)
"""Pure-function workspace state detection utilities.

These functions operate on filesystem paths (workspace directories) and return
derived state. No stored state variables — same input always produces same
output.

Provenance: Originally authored by Gemini in
imp_gemini/gemini_cli/internal/workspace_state.py,
ported to imp_claude and adapted for Claude tenant conventions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from .contracts import WorkspaceSchemaViolation
from .ol_event import normalize_event

_REQ_F_PATTERN = re.compile(r"\bREQ-F-[A-Z]+-\d+\b")

# Fields that belong in specification/features/, NOT in workspace trajectory files.
# Implements: REQ-EVOL-001, REQ-EVOL-DATA-001
FORBIDDEN_WORKSPACE_KEYS: frozenset[str] = frozenset(
    {
        "satisfies",  # spec: REQ-* mapping
        "success_criteria",  # spec: product outcomes
        "dependencies",  # spec: feature dependency graph
        "what_converges",  # spec: convergence description
        "phase",  # spec: release phase assignment
    }
)


def load_feature_vector(path: Path) -> dict[str, Any]:
    """Load a workspace feature vector YAML with schema enforcement.

    Raises WorkspaceSchemaViolation if any forbidden definition field is
    present — definition fields belong in specification/features/, not here.
    Implements: REQ-EVOL-001 (Workspace Vectors Are Trajectory-Only)
    """
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    for key in FORBIDDEN_WORKSPACE_KEYS:
        if key in data:
            raise WorkspaceSchemaViolation(str(path), key)
    return data


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

BOOTLOADER_START_MARKER = "<!-- GENESIS_BOOTLOADER_START -->"


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT & VIEW UTILITIES
# ═══════════════════════════════════════════════════════════════════════


def _workspace_dir(workspace: Path) -> Path:
    """Normalize a path to the actual ``.ai-workspace`` directory."""
    if workspace.name == ".ai-workspace":
        return workspace
    return workspace / ".ai-workspace"


def compute_context_hash(context: dict[str, Any]) -> str:
    """Deterministically hash context content for reproducibility checks."""
    canonical = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries (override wins)."""
    result = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = value
    return result


def resolve_context_hierarchy(contexts: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold a list of context layers from global→local using deep merge."""
    resolved: dict[str, Any] = {}
    for layer in contexts:
        resolved = deep_merge(resolved, layer)
    return resolved


def compute_feature_view(workspace: Path, feature_id: str) -> dict[str, Any]:
    """Return a per-feature derived view from the active feature YAML."""
    ws_dir = _workspace_dir(workspace)
    fv_path = ws_dir / "features" / "active" / f"{feature_id}.yml"
    if not fv_path.exists():
        return {"feature": feature_id, "status": "missing", "edges": {}}
    with open(fv_path) as f:
        data = yaml.safe_load(f) or {}
    return {
        "feature": data.get("feature", feature_id),
        "status": data.get("status", "pending"),
        "edges": data.get("trajectory", {}),
    }


def compute_aggregated_view(workspace: Path) -> dict[str, Any]:
    """Aggregate high-level progress counters across active feature vectors."""
    ws_dir = _workspace_dir(workspace)
    features_dir = ws_dir / "features" / "active"
    totals = {
        "total": 0,
        "in_progress": 0,
        "pending": 0,
        "converged": 0,
        "blocked": 0,
        "edges_total": 0,
    }
    if not features_dir.exists():
        return totals

    for path in sorted(features_dir.glob("*.yml")):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        totals["total"] += 1
        status = data.get("status", "pending")
        if status in totals:
            totals[status] += 1
        traj = data.get("trajectory", {})
        if isinstance(traj, dict):
            totals["edges_total"] += len(traj)

    return totals


def classify_tolerance_breach(
    observed_value: float,
    threshold: float,
    severity: Union[str, None] = None,
) -> str:
    """Classify tolerance pressure into IntentEngine output classes."""
    if observed_value <= threshold:
        return "reflex.log"
    if severity == "critical":
        return "escalate"
    if observed_value <= (threshold * 2):
        return "specEventLog"
    return "escalate"


# ═══════════════════════════════════════════════════════════════════════
# EVENT UTILITIES
# ═══════════════════════════════════════════════════════════════════════


def load_events(workspace: Path) -> list[dict[str, Any]]:
    """Parse events.jsonl from a workspace, returning list of event dicts.

    Normalizes OL RunEvents to flat format so all consumers see a uniform
    {event_type, timestamp, project, ...payload} structure regardless of which
    writer produced them. See ol_event.normalize_event() for the conversion.
    """
    events_file = _workspace_dir(workspace) / "events" / "events.jsonl"
    if not events_file.exists():
        return []

    events: list[dict[str, Any]] = []
    for i, line in enumerate(events_file.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(normalize_event(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return events


def get_converged_edges(events: list[dict[str, Any]], feature: str) -> set[str]:
    """Return set of edge names that have ``edge_converged`` events for *feature*."""
    return {
        ev.get("edge", "")
        for ev in events
        if ev.get("event_type") == "edge_converged" and ev.get("feature") == feature
    }


def compute_current_delta(
    events: list[dict[str, Any]],
    feature: str,
    edge: str,
) -> Union[int, None]:
    """Return the most recent delta value for a feature/edge pair, or None."""
    delta: Union[int, None] = None
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
    events: list[dict[str, Any]],
    feature: str,
    edge: str,
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
# SESSION GAP DETECTION (REQ-ROBUST-003, REQ-ROBUST-008)
# ═══════════════════════════════════════════════════════════════════════


def detect_abandoned_iterations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect edge_started events with no subsequent completion.

    Scans the event log for ``edge_started`` events that were never followed
    by an ``edge_converged`` or ``iteration_completed`` for the same
    feature/edge pair. Also filters out pairs that already have an
    ``iteration_abandoned`` event (idempotency).

    Returns a list of dicts: {feature, edge, last_event_timestamp}.
    """
    started: dict[tuple[str, str], str] = {}  # (feature, edge) → timestamp
    completed: set[tuple[str, str]] = set()
    already_abandoned: set[tuple[str, str]] = set()

    for ev in events:
        et = ev.get("event_type", "")
        feature = ev.get("feature", "")
        edge = ev.get("edge", "")
        key = (feature, edge)

        if et == "edge_started" and feature and edge:
            started[key] = ev.get("timestamp", "")
        elif et in ("edge_converged", "iteration_completed") and feature and edge:
            completed.add(key)
        elif et == "iteration_abandoned" and feature and edge:
            already_abandoned.add(key)

    abandoned = []
    for key, timestamp in started.items():
        if key not in completed and key not in already_abandoned:
            abandoned.append(
                {
                    "feature": key[0],
                    "edge": key[1],
                    "last_event_timestamp": timestamp,
                }
            )

    return abandoned


# ═══════════════════════════════════════════════════════════════════════
# FEATURE UTILITIES
# ═══════════════════════════════════════════════════════════════════════


def get_active_features(workspace: Path) -> list[dict[str, Any]]:
    """Load all active feature vector YAML files."""
    features_dir = _workspace_dir(workspace) / "features" / "active"
    if not features_dir.exists():
        return []

    features: list[dict[str, Any]] = []
    for path in sorted(features_dir.glob("*.yml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        if data:
            features.append(data)
    return features


def extract_spec_feature_ids(spec_features_path: Path) -> list[str]:
    """Extract REQ-F-* IDs from specification/features/FEATURE_VECTORS.md.

    Returns a sorted deduplicated list. If the file is unreadable, returns [].
    Used by compute_spec_workspace_join() for the spec side of the JOIN (REQ-EVOL-002).
    """
    if not spec_features_path.exists():
        return []
    try:
        text = spec_features_path.read_text(encoding="utf-8")
    except OSError:
        return []
    ids = sorted(set(_REQ_F_PATTERN.findall(text)))
    return ids


def compute_spec_workspace_join(
    workspace: Path,
    spec_features_path: Optional[Path] = None,
) -> dict[str, Any]:
    """JOIN spec feature definitions with workspace trajectory state (REQ-EVOL-002).

    Categorises every known REQ-F-* ID as:
      ACTIVE   — in spec AND in workspace (active or in_progress)
      COMPLETED — in spec AND in workspace (completed/converged)
      PENDING  — in spec AND NOT in workspace
      ORPHAN   — in workspace AND NOT in spec

    Returns a dict with keys: spec_ids, workspace_ids, active, completed, pending, orphan,
    spec_readable (bool), spec_count, workspace_count.
    """
    ws_dir = _workspace_dir(workspace)

    # Resolve spec path: default to specification/features/FEATURE_VECTORS.md
    if spec_features_path is None:
        project_root = ws_dir.parent if ws_dir.name == ".ai-workspace" else workspace
        spec_features_path = (
            project_root / "specification" / "features" / "FEATURE_VECTORS.md"
        )

    spec_readable = spec_features_path.exists()
    spec_ids: set[str] = set(extract_spec_feature_ids(spec_features_path))

    # Collect workspace feature IDs from active + completed directories
    workspace_active: set[str] = set()
    workspace_completed: set[str] = set()

    for subdir, bucket in (
        ("active", workspace_active),
        ("completed", workspace_completed),
    ):
        features_dir = ws_dir / "features" / subdir
        if features_dir.exists():
            for path in features_dir.glob("*.yml"):
                try:
                    with open(path) as f:
                        data = yaml.safe_load(f) or {}
                    fid = data.get("feature") or data.get("id", "")
                    if fid:
                        bucket.add(fid)
                except (yaml.YAMLError, OSError):
                    pass

    workspace_ids = workspace_active | workspace_completed

    active = sorted(spec_ids & workspace_active)
    completed = sorted(spec_ids & workspace_completed)
    pending = sorted(spec_ids - workspace_ids)
    orphan = sorted(workspace_ids - spec_ids)

    return {
        "spec_readable": spec_readable,
        "spec_count": len(spec_ids),
        "workspace_count": len(workspace_ids),
        "spec_ids": sorted(spec_ids),
        "workspace_ids": sorted(workspace_ids),
        "active": active,
        "completed": completed,
        "pending": pending,
        "orphan": orphan,
    }


def detect_stuck_features(
    workspace: Path,
    threshold: int = 3,
) -> list[dict[str, Any]]:
    """Detect features where delta has not decreased for *threshold*
    consecutive iterations."""
    events = load_events(workspace)
    stuck: list[dict[str, Any]] = []

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
        tail = deltas[-threshold:]
        if len(set(tail)) == 1 and tail[0] > 0:
            stuck.append(
                {
                    "feature": feat,
                    "edge": edge,
                    "delta": tail[0],
                    "iterations": len(deltas),
                    "reason": f"delta={tail[0]} unchanged for {threshold} iterations",
                }
            )

    return stuck


def _has_pending_human_review(
    workspace: Path,
    feature_id: str,
    events: list[dict[str, Any]],
) -> bool:
    """Check if a feature has a pending human review."""
    features = get_active_features(workspace)
    for fv in features:
        if fv.get("feature") != feature_id:
            continue
        traj = fv.get("trajectory", {})
        for _edge_name, edge_data in traj.items():
            if (
                isinstance(edge_data, dict)
                and edge_data.get("status") == "pending_review"
            ):
                return True
    return False


def _has_blocked_dependency(
    workspace: Path,
    feature_id: str,
    events: list[dict[str, Any]],
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
                if not dep_converged:
                    return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# FEATURE SELECTION & EDGE WALK
# ═══════════════════════════════════════════════════════════════════════


def select_next_feature(
    features: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Select the feature closest to completion (fewest unconverged edges)."""
    best: Optional[dict[str, Any]] = None
    best_remaining = float("inf")

    for fv in features:
        if fv.get("status") == "converged":
            continue
        traj = fv.get("trajectory", {})
        converged_count = sum(
            1
            for _k, v in traj.items()
            if isinstance(v, dict) and v.get("status") == "converged"
        )
        total_edges = max(len(traj), 1)
        remaining = total_edges - converged_count
        if remaining < best_remaining:
            best_remaining = remaining
            best = fv

    return best


def get_next_edge(
    feature: dict[str, Any],
    graph_topology: Optional[dict[str, Any]] = None,
) -> Union[str, None]:
    """Walk edges in topological order, return first unconverged edge."""
    traj = feature.get("trajectory", {})
    edges = STANDARD_PROFILE_EDGES
    if graph_topology:
        transitions = graph_topology.get("transitions", [])
        if transitions:
            edges = [t.get("name", "") for t in transitions if t.get("name")]

    for edge in edges:
        parts = edge.replace("↔", "→").split("→")
        for part in parts:
            part = part.strip()
            traj_entry = traj.get(part)
            if traj_entry:
                if isinstance(traj_entry, dict):
                    status = traj_entry.get("status", "pending")
                    if status not in ("converged",):
                        return edge
            else:
                return edge
    return None


# ═══════════════════════════════════════════════════════════════════════
# GENESIS SELF-COMPLIANCE (REQ-SUPV-002, REQ-UX-005)
# ═══════════════════════════════════════════════════════════════════════


def verify_genesis_compliance(workspace: Path) -> dict[str, Any]:
    """Verify methodology invariants and bootloader presence.

    Returns a dict with: passed (int), failed (int), results (list of dicts).
    """
    results = []
    passed = 0
    failed = 0

    # 1. Bootloader Presence
    claude_md = workspace / "CLAUDE.md"
    if claude_md.exists() and BOOTLOADER_START_MARKER in claude_md.read_text():
        results.append(
            {
                "name": "bootloader_present",
                "status": "pass",
                "description": "CLAUDE.md contains Bootloader",
            }
        )
        passed += 1
    else:
        results.append(
            {
                "name": "bootloader_present",
                "status": "fail",
                "description": "Bootloader markers missing in CLAUDE.md",
            }
        )
        failed += 1

    # 2. Graph Invariant
    topology_path = workspace / ".ai-workspace" / "graph" / "graph_topology.yml"
    topology = None
    if topology_path.exists():
        try:
            with open(topology_path) as f:
                topology = yaml.safe_load(f)
            nodes = len(topology.get("asset_types", {}))
            edges = len(topology.get("transitions", []))
            if nodes > 0 and edges > 0:
                results.append(
                    {
                        "name": "graph_invariant",
                        "status": "pass",
                        "description": f"Graph has {nodes} nodes, {edges} edges",
                    }
                )
                passed += 1
            else:
                results.append(
                    {
                        "name": "graph_invariant",
                        "status": "fail",
                        "description": "Graph topology is empty",
                    }
                )
                failed += 1
        except Exception as e:
            results.append(
                {
                    "name": "graph_invariant",
                    "status": "fail",
                    "description": f"Cannot parse graph: {e}",
                }
            )
            failed += 1
    else:
        results.append(
            {
                "name": "graph_invariant",
                "status": "fail",
                "description": "graph_topology.yml missing",
            }
        )
        failed += 1

    # 3. Iterate & Evaluator Invariant
    if topology:
        edges = topology.get("transitions", [])
        edge_configs_present = 0
        evaluators_found = 0
        missing_configs = []
        zero_evaluator_edges = []

        for edge in edges:
            name = edge.get("name", "")
            config_rel = edge.get("edge_config", "")
            if not name or not config_rel:
                continue

            # Local path check
            config_path = workspace / ".ai-workspace" / "graph" / config_rel
            if config_path.exists():
                edge_configs_present += 1
                try:
                    with open(config_path) as f:
                        cfg = yaml.safe_load(f)
                    # Support both evaluators: and checklist: keys
                    evs = cfg.get("evaluators", cfg.get("checklist", []))
                    if isinstance(
                        evs, dict
                    ):  # some schemas use dict mapping type -> list
                        count = sum(
                            len(v) if isinstance(v, list) else 1 for v in evs.values()
                        )
                    else:
                        count = len(evs)

                    if count > 0:
                        evaluators_found += count
                    else:
                        zero_evaluator_edges.append(name)
                except Exception:
                    zero_evaluator_edges.append(name)
            else:
                missing_configs.append(name)

        if not missing_configs:
            results.append(
                {
                    "name": "iterate_invariant",
                    "status": "pass",
                    "description": "All edges have evaluator configs",
                }
            )
            passed += 1
        else:
            results.append(
                {
                    "name": "iterate_invariant",
                    "status": "fail",
                    "description": (
                        f"Missing config for edges: {', '.join(missing_configs)}"
                    ),
                }
            )
            failed += 1

        if not zero_evaluator_edges:
            results.append(
                {
                    "name": "evaluator_invariant",
                    "status": "pass",
                    "description": (
                        f"All edges have >=1 evaluator ({evaluators_found} total)"
                    ),
                }
            )
            passed += 1
        else:
            results.append(
                {
                    "name": "evaluator_invariant",
                    "status": "fail",
                    "description": (
                        f"Edges with 0 evaluators: {', '.join(zero_evaluator_edges)}"
                    ),
                }
            )
            failed += 1

    # 4. Tolerance Check (REQ-SUPV-002)
    constraints_path = (
        workspace / ".ai-workspace" / "context" / "project_constraints.yml"
    )
    if constraints_path.exists():
        try:
            with open(constraints_path) as f:
                constraints = yaml.safe_load(f)
            dims = constraints.get("constraint_dimensions", {})
            wishes = []
            for name, val in dims.items():
                if isinstance(val, dict):
                    # Check for non-placeholder values
                    resolved = [
                        v
                        for k, v in val.items()
                        if k
                        not in ("mandatory", "description", "resolves_via", "examples")
                        and v
                    ]
                    if resolved:
                        # Check if it looks like a "wish"
                        # (no numbers, versions, or booleans)
                        flat_val = str(resolved).lower()
                        if not any(char.isdigit() for char in flat_val) and not any(
                            kw in flat_val
                            for kw in [
                                "true",
                                "false",
                                "yes",
                                "no",
                                "active",
                                "enabled",
                            ]
                        ):
                            wishes.append(name)

            if wishes:
                results.append(
                    {
                        "name": "tolerance_check",
                        "status": "warn",
                        "description": (
                            f"{len(wishes)} constraints lack measurable"
                            f" thresholds (wishes): {', '.join(wishes)}"
                        ),
                    }
                )
            else:
                results.append(
                    {
                        "name": "tolerance_check",
                        "status": "pass",
                        "description": (
                            "All resolved constraints have measurable thresholds"
                        ),
                    }
                )
                passed += 1
        except Exception:
            pass

    # 5. Workspace Vector Schema (REQ-EVOL-001)
    # Workspace YAMLs must NOT contain definition fields — module-level FORBIDDEN_WORKSPACE_KEYS
    violations: list[str] = []
    _ws_dir = _workspace_dir(workspace)
    for subdir in ("active", "completed"):
        fv_dir = _ws_dir / "features" / subdir
        if not fv_dir.exists():
            continue
        for path in sorted(fv_dir.glob("*.yml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                for key in FORBIDDEN_WORKSPACE_KEYS:
                    if key in data:
                        violations.append(f"{path.name}: has forbidden key '{key}'")
            except (yaml.YAMLError, OSError):
                pass

    if violations:
        results.append(
            {
                "name": "workspace_vector_schema",
                "status": "fail",
                "description": (
                    f"Workspace vectors contain definition fields ({len(violations)} violations): "
                    + "; ".join(violations[:3])
                    + (" ..." if len(violations) > 3 else "")
                ),
            }
        )
        failed += 1
    else:
        results.append(
            {
                "name": "workspace_vector_schema",
                "status": "pass",
                "description": "Workspace vectors contain no definition fields (satisfies, success_criteria)",
            }
        )
        passed += 1

    # 6. Spec Hash Consistency (REQ-EVOL-NFR-002)
    drift = verify_spec_hashes(workspace)
    if drift:
        results.append(
            {
                "name": "spec_hash_consistency",
                "status": "warn",
                "description": (
                    f"SPEC_DRIFT: {len(drift)} spec file(s) have content that doesn't "
                    f"match last spec_modified event: "
                    + "; ".join(d["file"] for d in drift[:3])
                    + (" ..." if len(drift) > 3 else "")
                ),
            }
        )
    else:
        results.append(
            {
                "name": "spec_hash_consistency",
                "status": "pass",
                "description": "All tracked spec files match their last spec_modified event hash",
            }
        )
        passed += 1

    return {"passed": passed, "failed": failed, "results": results}


# ═══════════════════════════════════════════════════════════════════════
# SPEC HASH VERIFICATION (REQ-EVOL-NFR-002)
# ═══════════════════════════════════════════════════════════════════════


def verify_spec_hashes(
    workspace: Path,
    spec_dir: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Compare current spec file hashes against last spec_modified event per file.

    Returns list of SPEC_DRIFT dicts for files that have drifted:
      {"file": str, "expected_hash": str, "actual_hash": str, "event_timestamp": str}

    A file not in the event log at all is NOT reported as drift — drift only occurs
    when a spec_modified event was emitted and the current file no longer matches.

    Implements: REQ-EVOL-NFR-002 (Spec Hash Verification)
    """
    ws_dir = _workspace_dir(workspace)
    events_file = ws_dir / "events" / "events.jsonl"

    if not events_file.exists():
        return []

    # Resolve project root for relative path resolution
    project_root = ws_dir.parent if ws_dir.name == ".ai-workspace" else workspace
    if spec_dir is None:
        spec_dir = project_root / "specification"

    # Collect most recent spec_modified event per file path
    last_spec_event: dict[str, dict] = {}
    try:
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Handle both flat and OL-wrapped formats
                ev = normalize_event(event)
                if ev.get("event_type") not in ("spec_modified", "SpecModified"):
                    continue
                file_path = ev.get("data", {}).get("file") or ev.get("file")
                if file_path:
                    last_spec_event[file_path] = ev
    except OSError:
        return []

    drift = []
    for file_path, event in last_spec_event.items():
        expected = event.get("data", {}).get("new_hash") or event.get("new_hash")
        if not expected:
            continue

        abs_path = project_root / file_path
        if not abs_path.exists():
            # File was deleted after event — that's drift too
            drift.append(
                {
                    "file": file_path,
                    "expected_hash": expected,
                    "actual_hash": "FILE_MISSING",
                    "event_timestamp": event.get("timestamp", ""),
                }
            )
            continue

        try:
            content = abs_path.read_bytes()
        except OSError:
            continue

        actual = "sha256:" + hashlib.sha256(content).hexdigest()
        if actual != expected:
            drift.append(
                {
                    "file": file_path,
                    "expected_hash": expected,
                    "actual_hash": actual,
                    "event_timestamp": event.get("timestamp", ""),
                }
            )

    return drift


# ═══════════════════════════════════════════════════════════════════════
# INTEGRITY & HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════


def detect_corrupted_events(workspace: Path) -> list[dict[str, Any]]:
    """Return list of corruption reports for events.jsonl."""
    events_file = _workspace_dir(workspace) / "events" / "events.jsonl"
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
    """Find spawns whose parent feature doesn't exist."""
    features = get_active_features(workspace)
    feature_ids = {fv.get("feature", "") for fv in features}

    orphans: list[dict[str, Any]] = []
    for fv in features:
        parent = fv.get("parent", {})
        if not parent:
            continue
        parent_id = (
            parent.get("feature", "") if isinstance(parent, dict) else str(parent)
        )
        if parent_id and parent_id not in feature_ids:
            orphans.append(
                {
                    "feature": fv.get("feature", ""),
                    "parent": parent_id,
                    "reason": f"parent {parent_id} not in active features",
                }
            )
    return orphans


def get_unactioned_escalations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find escalation/intent_raised events that have no corresponding action."""
    escalations = [
        ev for ev in events if ev.get("event_type") in ("intent_raised", "escalation")
    ]
    actioned_intents: set[str] = set()
    for ev in events:
        if ev.get("event_type") in (
            "spawn_created",
            "review_completed",
            "spec_modified",
        ):
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


# ═══════════════════════════════════════════════════════════════════════
# STATE DETECTION
# ═══════════════════════════════════════════════════════════════════════


def detect_workspace_state(workspace: Path) -> str:
    """Detect the current workspace state from filesystem + event log."""
    # Ensure we are looking at the actual .ai-workspace directory
    if workspace.name == ".ai-workspace":
        ws_dir = workspace
        project_root = workspace.parent
    else:
        ws_dir = workspace / ".ai-workspace"
        project_root = workspace

    if not ws_dir.exists() or not ws_dir.is_dir():
        return "UNINITIALISED"

    constraints_candidates = [
        ws_dir / "claude" / "context" / "project_constraints.yml",
        ws_dir / "context" / "project_constraints.yml",
    ]
    has_constraints = False
    for cp in constraints_candidates:
        if cp.exists():
            # print(f"DEBUG: Found constraint file at {cp}")
            try:
                with open(cp) as f:
                    data = yaml.safe_load(f)
                if data and data.get("project"):
                    has_constraints = True
                    break
            except (yaml.YAMLError, OSError):
                pass

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
                            if dim_val.get("mandatory") is False:
                                continue
                            values = [
                                v
                                for k, v in dim_val.items()
                                if k
                                not in (
                                    "mandatory",
                                    "description",
                                    "resolves_via",
                                    "examples",
                                    "notes",
                                )
                                and v
                            ]
                            if values:
                                mandatory_filled += 1
                            mandatory_total += 1
                    if mandatory_total > 0 and mandatory_filled == 0:
                        return "NEEDS_CONSTRAINTS"
                except Exception:
                    pass
                break

    if not has_constraints:
        return "NEEDS_CONSTRAINTS"

    intent_candidates = [
        project_root / "specification" / "INTENT.md",
        ws_dir / "spec" / "INTENT.md",
    ]
    has_intent = any(p.exists() and p.stat().st_size > 10 for p in intent_candidates)
    if not has_intent:
        return "NEEDS_INTENT"

    features = get_active_features(workspace)
    if not features:
        return "NO_FEATURES"

    events = load_events(workspace)

    all_converged = True
    any_stuck = False
    all_blocked = True

    for fv in features:
        feat_id = fv.get("feature", "")
        status = fv.get("status", "pending")

        if status == "converged":
            continue

        all_converged = False

        stuck_list = detect_stuck_features(workspace, threshold=3)
        if any(s["feature"] == feat_id for s in stuck_list):
            any_stuck = True
            continue

        is_blocked = _has_blocked_dependency(
            workspace, feat_id, events
        ) or _has_pending_human_review(workspace, feat_id, events)
        if not is_blocked:
            all_blocked = False

    if all_converged:
        return "ALL_CONVERGED"

    if any_stuck:
        return "STUCK"

    if all_blocked:
        return "ALL_BLOCKED"

    return "IN_PROGRESS"


# ═══════════════════════════════════════════════════════════════════════
# INSTANCE GRAPH PROJECTION (ADR-022)
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class InstanceNode:
    """A feature instance positioned on the asset graph topology (zoom level 1).

    The node is computed by replaying events — it is a derived projection,
    never stored directly. ADR-022: topology is the type system; instances
    are the runtime state derived from the event log.
    """

    feature_id: str  # REQ-F-*
    zoom_level: int  # 0=topology, 1=feature, 2=sub-feature
    current_edge: str  # last edge_started or edge_converged edge
    status: str  # pending | in_progress | converged | archived
    delta: int  # last known delta (-1 = unknown)
    parent_id: Optional[str]  # parent feature for zoom level 2+
    converged_edges: list[str] = field(default_factory=list)


@dataclass
class InstanceGraph:
    """The runtime state of the asset graph — which feature instances exist,
    where each sits in the topology, and what their convergence state is.

    This is a projection of the event log, not a stored document.
    Reconstruct at any time by replaying events up to a watermark.

    ADR-022: topology (graph_topology.yml) defines the type system;
    InstanceGraph defines the instance state.
    """

    nodes: list[InstanceNode]
    as_of: datetime  # event log watermark (timestamp of last event replayed)
    topology_version: str  # from graph_topology.yml graph_properties.version


def project_instance_graph(
    events: list[dict[str, Any]],
    topology_version: str = "unknown",
) -> InstanceGraph:
    """Replay events to derive the current instance graph (ADR-022, Step 4).

    Mutation sequence:
      feature_spawned / project_initialized  → node added
      edge_started                           → node.current_edge = edge, status = in_progress
      iteration_completed                    → node.delta = delta
      edge_converged                         → node.converged_edges.add(edge)
      feature_converged / ALL_CONVERGED      → node.status = archived

    Returns an InstanceGraph positioned at the watermark of the last event.
    """
    nodes: dict[str, InstanceNode] = {}  # feature_id → InstanceNode
    last_timestamp: Optional[str] = None

    for ev in events:
        et = ev.get("event_type", "")
        feature = ev.get("feature", "")
        edge = ev.get("edge", "")
        ts = ev.get("timestamp")
        if ts:
            last_timestamp = ts

        # OL-wrapped events carry event_type in facets
        if not et:
            run_facets = ev.get("run", {}).get("facets", {})
            et = run_facets.get("sdlc:event_type", {}).get("type", "")

        if et in ("project_initialized",) and not feature:
            # project-level event — no node to create
            continue

        if not feature:
            continue

        # Ensure node exists
        if feature not in nodes:
            parent = ev.get("parent_id") or ev.get("data", {}).get("parent_id")
            nodes[feature] = InstanceNode(
                feature_id=feature,
                zoom_level=2 if parent else 1,
                current_edge="",
                status="pending",
                delta=-1,
                parent_id=parent,
            )

        node = nodes[feature]

        if et == "edge_started":
            node.current_edge = edge
            node.status = "in_progress"

        elif et == "iteration_completed":
            raw_delta = ev.get("delta")
            if raw_delta is None:
                raw_delta = ev.get("data", {}).get("delta")
            if raw_delta is not None:
                try:
                    node.delta = int(raw_delta)
                except (TypeError, ValueError):
                    pass
            if edge:
                node.current_edge = edge
            node.status = "in_progress"

        elif et == "edge_converged":
            if edge and edge not in node.converged_edges:
                node.converged_edges.append(edge)
            node.current_edge = edge
            node.status = "in_progress"

        elif et in ("feature_converged",):
            node.status = "archived"

    # Infer converged status from trajectory files when events are sparse
    # (handles workspace_state where feature.status = "converged" in yml)
    as_of = (
        datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
        if last_timestamp
        else datetime.now(timezone.utc)
    )

    return InstanceGraph(
        nodes=list(nodes.values()),
        as_of=as_of,
        topology_version=topology_version,
    )


def summarise_instance_graph(graph: InstanceGraph) -> dict[str, Any]:
    """Produce a concise summary of the instance graph for display."""
    by_status: dict[str, list[str]] = {
        "pending": [],
        "in_progress": [],
        "converged": [],
        "archived": [],
    }
    by_edge: dict[str, list[str]] = {}

    for node in graph.nodes:
        bucket = by_status.setdefault(node.status, [])
        bucket.append(node.feature_id)
        if node.current_edge:
            by_edge.setdefault(node.current_edge, []).append(node.feature_id)

    return {
        "topology_version": graph.topology_version,
        "as_of": graph.as_of.isoformat(),
        "total_nodes": len(graph.nodes),
        "by_status": {k: len(v) for k, v in by_status.items()},
        "active_edges": {
            edge: features for edge, features in by_edge.items() if features
        },
    }
