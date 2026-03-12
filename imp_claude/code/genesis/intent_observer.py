# Implements: REQ-F-DISPATCH-001
# Implements: REQ-F-RUNTIME-001
"""IntentObserver — reads intent_raised events, identifies unhandled intents,
resolves dispatch targets.

The homeostatic loop closing component. Reads the append-only event stream,
finds intent_raised events with no matching edge_started (unhandled), resolves
the target feature+edge from affected_features and feature vector trajectories,
and returns DispatchTarget records for EDGE_RUNNER to execute.

Design decisions:
- "Unhandled" = intent_raised with no edge_started where
    edge_started.data.intent_id == intent.data.intent_id  (OL format)
    OR edge_started.intent_id == intent.intent_id         (flat format)
  Idempotency: once an edge_started is emitted for an intent_id, that intent
  is considered handled.
- Scope resolution: load feature vector YAML from
    .ai-workspace/features/active/{feature_id}.yml
- Topological edge order: load from graph_topology.yml (transitions list)
- Skip edges where trajectory.{edge_key}.status == "converged"
- Profile: load from feature vector's profile field, fall back to "standard"
- affected_features: canonical dispatch field; ["all"] triggers full workspace scan
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .outcome_types import IntentEvent


# ── Profile → edge order maps ─────────────────────────────────────────────────

# Standard profile edge traversal order (v2.9.0)
STANDARD_EDGE_ORDER = [
    "intent→requirements",
    "requirements→feature_decomposition",
    "feature_decomposition→design_recommendations",
    "design_recommendations→design",
    "design→module_decomposition",
    "module_decomposition→basis_projections",
    "basis_projections→code",
    "code↔unit_tests",
    "design→test_cases",
    "design→uat_tests",
]

# Profile name → subset of edges (in traversal order)
PROFILE_EDGE_ORDERS: dict[str, list[str]] = {
    "full": STANDARD_EDGE_ORDER,
    "standard": STANDARD_EDGE_ORDER,
    "poc": [
        "intent→requirements",
        "requirements→feature_decomposition",
        "feature_decomposition→design_recommendations",
        "design→code",
        "code↔unit_tests",
    ],
    "spike": [
        "intent→requirements",
        "design→code",
        "code↔unit_tests",
    ],
    "hotfix": [
        "code↔unit_tests",
    ],
    "minimal": [
        "code↔unit_tests",
    ],
}


@dataclass
class DispatchTarget:
    """A single dispatch unit: one feature + one edge to run EDGE_RUNNER on.

    intent_id     — primary intent (first / canonical; used for backward-compat lookup)
    intent_events — ALL contributing intent_raised events for this (feature, edge) pair.
                    Populated by get_pending_dispatches() when multiple intents are merged.
                    edge_started emits handled_intent_ids from this list to close them all.
    """

    intent_id: str
    feature_id: str
    edge: str
    intent_events: list[dict] = field(default_factory=list)   # replaces intent_event (singular)
    feature_vector: dict = field(default_factory=dict)


# ── Event reading ──────────────────────────────────────────────────────────────


def _read_events(events_path: Path) -> list[dict[str, Any]]:
    """Read events.jsonl, normalising OL and flat formats. Tolerates decode errors."""
    if not events_path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
            events.append(_normalize(raw))
        except (json.JSONDecodeError, Exception):
            continue
    return events


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise an OL RunEvent or flat event to a uniform flat dict.

    Flat events have 'event_type' at the top level.
    OL events have eventType + run.facets.sdlc:event_type.
    """
    if "event_type" in raw:
        return raw  # already flat

    facets = raw.get("run", {}).get("facets", {})
    type_facet = facets.get("sdlc:event_type", {})
    if not type_facet:
        return raw  # unknown format — pass through

    import re as _re

    semantic = type_facet.get("type", "")
    event_type = _re.sub(r"(?<!^)(?=[A-Z])", "_", semantic).lower()

    namespace = raw.get("job", {}).get("namespace", "")
    project = namespace.removeprefix("aisdlc://")

    payload = facets.get("sdlc:payload", {})
    flat: dict[str, Any] = {
        "event_type": event_type,
        "timestamp": raw.get("eventTime", ""),
        "project": project,
    }
    flat.update({k: v for k, v in payload.items() if not k.startswith("_")})

    # Metadata preserved for legacy flat events wrapped in OL
    if "_metadata" in raw and "original_data" in raw["_metadata"]:
        orig = raw["_metadata"]["original_data"]
        for k, v in orig.items():
            if k not in flat:
                flat[k] = v
        # Flatten "data" sub-dict if present
        if "data" in orig and isinstance(orig["data"], dict):
            for k, v in orig["data"].items():
                if k not in flat:
                    flat[k] = v

    return flat


def _get_intent_id(event: dict[str, Any]) -> str | None:
    """Extract intent_id from a normalised intent_raised event."""
    # Direct field (flat format or extracted payload)
    if "intent_id" in event:
        return event["intent_id"]
    # Nested in 'data' dict (legacy flat format)
    data = event.get("data", {})
    if isinstance(data, dict) and "intent_id" in data:
        return data["intent_id"]
    return None


def _get_affected_features(event: dict[str, Any]) -> list[str]:
    """Extract affected_features from a normalised intent_raised event."""
    # Direct field
    if "affected_features" in event:
        val = event["affected_features"]
        if isinstance(val, list):
            return val
    # Nested in 'data' dict
    data = event.get("data", {})
    if isinstance(data, dict) and "affected_features" in data:
        val = data["affected_features"]
        if isinstance(val, list):
            return val
    return []


def _get_dispatched_intent_ids(events: list[dict[str, Any]]) -> set[str]:
    """Return set of intent_ids for which edge_started has been emitted.

    Reads both the primary intent_id (backward compat) and the full
    handled_intent_ids list (new — closes all contributing intents so that
    merged multi-intent DispatchTargets do not re-appear as unhandled).
    """
    dispatched: set[str] = set()
    for ev in events:
        if ev.get("event_type") != "edge_started":
            continue
        data = ev.get("data", {}) or {}
        # Primary intent_id (backward compat)
        iid = ev.get("intent_id") or data.get("intent_id")
        if iid:
            dispatched.add(str(iid))
        # All contributing intent_ids (new field)
        all_ids = data.get("handled_intent_ids") or ev.get("handled_intent_ids") or []
        for aid in all_ids:
            if aid:
                dispatched.add(str(aid))
    return dispatched


# ── Public API ─────────────────────────────────────────────────────────────────


def find_unhandled_intents(events_path: Path) -> list[dict[str, Any]]:
    """Read events.jsonl and return intent_raised events with no matching edge_started.

    An intent is "handled" if an edge_started event exists where
    edge_started.intent_id == intent.intent_id.

    Returns the raw normalised event dicts in chronological order.
    """
    events = _read_events(events_path)
    dispatched = _get_dispatched_intent_ids(events)

    unhandled: list[dict[str, Any]] = []
    for ev in events:
        if ev.get("event_type") != "intent_raised":
            continue
        iid = _get_intent_id(ev)
        if iid is None:
            # Intent without an ID — cannot track; skip
            continue
        if iid not in dispatched:
            unhandled.append(ev)
    return unhandled


def _load_feature_vector(workspace_root: Path, feature_id: str) -> dict[str, Any] | None:
    """Load feature vector YAML from .ai-workspace/features/active/{feature_id}.yml.

    Returns None if the file does not exist. Does not raise on load errors —
    returns None instead (caller handles missing gracefully).
    """
    path = workspace_root / ".ai-workspace" / "features" / "active" / f"{feature_id}.yml"
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text()) or {}
        return data
    except Exception:
        return None


def _get_active_feature_ids(workspace_root: Path) -> list[str]:
    """Return all feature IDs that have active feature vectors."""
    active_dir = workspace_root / ".ai-workspace" / "features" / "active"
    if not active_dir.exists():
        return []
    return [p.stem for p in sorted(active_dir.glob("*.yml"))]


def _select_edge(feature_vector: dict[str, Any]) -> str | None:
    """Select the first non-converged edge from a feature vector's trajectory.

    Uses the profile to determine edge order, then walks the trajectory to find
    the first edge that is not 'converged'. Returns None if all edges are
    converged or the trajectory is empty.
    """
    profile = feature_vector.get("profile", "standard")
    edge_order = PROFILE_EDGE_ORDERS.get(profile, STANDARD_EDGE_ORDER)

    trajectory = feature_vector.get("trajectory", {}) or {}

    for edge in edge_order:
        # Convert edge to trajectory key format
        edge_key = edge.replace("→", "_").replace("↔", "_").replace(" ", "")
        edge_info = trajectory.get(edge_key) or trajectory.get(edge)
        if edge_info is None:
            # Not yet started — this is the first edge to run
            return edge
        status = edge_info.get("status", "pending") if isinstance(edge_info, dict) else "pending"
        if status != "converged":
            return edge

    return None  # all edges converged


def resolve_dispatch_targets(
    intent_event: dict[str, Any],
    workspace_root: Path,
) -> list[DispatchTarget]:
    """From a single intent_raised event, return list of DispatchTarget.

    Projects the raw event dict to IntentEvent at intake boundary.
    Each DispatchTarget is (intent_id, feature_id, edge) — one per affected feature
    that has a non-converged edge. If affected_features == ["all"], scans all active
    feature vectors.

    Returns empty list if:
    - No intent_id on the event
    - No affected features
    - All affected features are fully converged or have no active vector
    """
    intent_id = _get_intent_id(intent_event)
    if not intent_id:
        return []

    affected = _get_affected_features(intent_event)

    if not affected:
        return []

    # Resolve feature list
    if affected == ["all"]:
        feature_ids = _get_active_feature_ids(workspace_root)
    else:
        feature_ids = affected

    targets: list[DispatchTarget] = []
    for feature_id in feature_ids:
        fv = _load_feature_vector(workspace_root, feature_id)
        if fv is None:
            continue  # no active vector — skip

        edge = _select_edge(fv)
        if edge is None:
            continue  # all edges converged — skip

        targets.append(
            DispatchTarget(
                intent_id=intent_id,
                feature_id=feature_id,
                edge=edge,
                intent_events=[intent_event],   # single event per resolve; merged in get_pending_dispatches
                feature_vector=fv,
            )
        )

    return targets


def get_pending_dispatches(workspace_root: Path) -> list[DispatchTarget]:
    """Full pipeline: find unhandled intents → resolve targets → return all pending.

    Entry point for the dispatch loop. Returns all DispatchTargets ready for
    EDGE_RUNNER to execute.

    Deduplication: one work unit per (feature_id, edge). When multiple intents
    target the same (feature, edge), they are merged into a single DispatchTarget
    that carries ALL contributing intent_events. EDGE_RUNNER then emits
    edge_started with handled_intent_ids listing all of them, so none remain
    unhandled on the next pass (idempotency closure).
    """
    events_path = workspace_root / ".ai-workspace" / "events" / "events.jsonl"
    unhandled = find_unhandled_intents(events_path)

    merged: dict[tuple[str, str], DispatchTarget] = {}

    for intent_event in unhandled:
        targets = resolve_dispatch_targets(intent_event, workspace_root)
        for t in targets:
            key = (t.feature_id, t.edge)
            if key not in merged:
                merged[key] = t
            else:
                # Accumulate contributing events; primary intent_id (first) is kept
                merged[key].intent_events.extend(t.intent_events)

    all_targets = list(merged.values())

    return all_targets
