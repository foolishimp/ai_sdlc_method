"""Decision Queue Engine — ranks actionable items for a Genesis project.

Examines feature vectors, the event stream, and gap analysis results to produce
a prioritised queue of items the practitioner should act on next.
All operations are pure read-only (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-QUEUE-001
# Implements: REQ-F-QUEUE-002
# Implements: REQ-F-QUEUE-003
# Implements: REQ-F-API-004
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

_SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

_ITERATING_STATUSES: frozenset[str] = frozenset({"iterating", "in_progress"})
_DONE_STATUSES: frozenset[str] = frozenset(
    {"converged", "blocked", "blocked_deferred", "abandoned", "error"}
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _feature_id(feature: dict) -> str:
    return feature.get("feature_id") or feature.get("id", "")


def _iter_events_for(events: list[dict], feature_id: str) -> list[dict]:
    return [
        e
        for e in events
        if e.get("event_type") == "iteration_completed" and e.get("feature_id") == feature_id
    ]


def _current_edge(events: list[dict], feature_id: str) -> str | None:
    """Return the most recent in-progress edge for *feature_id*."""
    started: dict[str, bool] = {}  # edge → converged?
    for ev in events:
        if ev.get("feature_id") != feature_id:
            continue
        ev_type = ev.get("event_type", "")
        edge = ev.get("edge", "")
        if not edge:
            continue
        if ev_type == "edge_started":
            started[edge] = False
        elif ev_type == "edge_converged":
            started[edge] = True

    # Return the last edge that has not converged
    for edge, converged in reversed(list(started.items())):
        if not converged:
            return edge
    return None


def _pending_edge_count(events: list[dict], feature_id: str) -> int:
    """Count how many edges for *feature_id* have been started but not converged."""
    edge_state: dict[str, bool] = {}
    for ev in events:
        if ev.get("feature_id") != feature_id:
            continue
        ev_type = ev.get("event_type", "")
        edge = ev.get("edge", "")
        if not edge:
            continue
        if ev_type == "edge_started":
            edge_state[edge] = False
        elif ev_type == "edge_converged":
            edge_state[edge] = True
    return sum(1 for converged in edge_state.values() if not converged)


def _is_stuck(iter_events: list[dict]) -> bool:
    """Return True if the last 3 iteration_completed deltas are identical."""
    if len(iter_events) < 3:
        return False
    deltas = [int(e.get("delta") or 0) for e in iter_events[-3:]]
    return len(set(deltas)) == 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def command_for_item(
    item_type: str,
    feature_id: str | None,
    edge: str | None,
    gap_keys: list[str],
) -> str:
    """Generate the appropriate genesis command for a queue item.

    Args:
        item_type: One of ``STUCK``, ``BLOCKED``, ``GAP_CLUSTER``, ``IN_PROGRESS``.
        feature_id: Feature identifier (used for STUCK / BLOCKED / IN_PROGRESS).
        edge: Current edge name (used for STUCK / BLOCKED / IN_PROGRESS).
        gap_keys: REQ keys in a gap cluster (used for GAP_CLUSTER).

    Returns:
        A genesis command string.
    """
    if item_type == "GAP_CLUSTER":
        return "/gen-gaps"
    if feature_id and edge:
        return f'/gen-iterate --edge "{edge}" --feature "{feature_id}"'
    if feature_id:
        return f'/gen-iterate --feature "{feature_id}"'
    return "/gen-gaps"


def build_item_detail(
    item_type: str,
    feature_dict: dict,
    events: list[dict],
    gap_keys: list[str],
) -> dict:
    """Build the detail payload for a queue item.

    Args:
        item_type: One of ``STUCK``, ``BLOCKED``, ``GAP_CLUSTER``, ``IN_PROGRESS``.
        feature_dict: Parsed feature YAML dict (may be empty for GAP_CLUSTER).
        events: Full event list for the workspace.
        gap_keys: REQ keys in this gap cluster (GAP_CLUSTER only).

    Returns:
        Dict conforming to :class:`~genesis_nav.models.schemas.QueueItemDetail`.
    """
    fid = _feature_id(feature_dict)
    iter_evs = _iter_events_for(events, fid) if fid else []
    last3_deltas = [int(e.get("delta") or 0) for e in iter_evs[-3:]]
    current_delta = last3_deltas[-1] if last3_deltas else None

    if item_type == "STUCK":
        return {
            "reason": f"Delta has not changed for the last {len(last3_deltas)} iterations.",
            "delta": current_delta,
            "failing_checks": [],
            "expected_outcome": "Delta decreases after next iterate() call.",
            "gap_keys": [],
            "iteration_history": last3_deltas,
        }
    if item_type == "BLOCKED":
        return {
            "reason": "Feature is explicitly marked 'blocked' in its YAML.",
            "delta": current_delta,
            "failing_checks": [],
            "expected_outcome": "Human resolves blocker; feature status updated to 'in_progress'.",
            "gap_keys": [],
            "iteration_history": last3_deltas,
        }
    if item_type == "GAP_CLUSTER":
        return {
            "reason": f"{len(gap_keys)} REQ key(s) lack code or test annotations.",
            "delta": None,
            "failing_checks": [],
            "expected_outcome": "All REQ keys in cluster are tagged in code and tests.",
            "gap_keys": gap_keys,
            "iteration_history": [],
        }
    # IN_PROGRESS
    return {
        "reason": "Feature is actively iterating.",
        "delta": current_delta,
        "failing_checks": [],
        "expected_outcome": "Delta converges to 0 on this edge.",
        "gap_keys": [],
        "iteration_history": last3_deltas,
    }


def build_queue_items(
    features: list[dict],
    events: list[dict],
    gaps: dict,
) -> list[dict]:
    """Build a ranked list of decision queue items.

    Priority order: STUCK (critical) > BLOCKED (high) > GAP_CLUSTER (medium) > IN_PROGRESS (low).
    Within the same severity, higher delta → listed first (more work remaining = more urgent).

    Args:
        features: List of feature dicts (from feature_reader).
        events: Full event list for the workspace.
        gaps: GapReport dict as returned by ``analyze_gaps()``.

    Returns:
        Sorted list of queue item dicts conforming to
        :class:`~genesis_nav.models.schemas.QueueItem`.
        Returns a single "healthy" item when no issues are detected.
    """
    items: list[dict] = []

    # --- STUCK and BLOCKED ---
    stuck_fids: set[str] = set()
    blocked_fids: set[str] = set()

    for feature in features:
        fid = _feature_id(feature)
        status = feature.get("status", "")

        iter_evs = _iter_events_for(events, fid)
        edge = _current_edge(events, fid)

        if status not in _DONE_STATUSES and _is_stuck(iter_evs):
            stuck_fids.add(fid)
            detail = build_item_detail("STUCK", feature, events, [])
            items.append(
                {
                    "type": "STUCK",
                    "severity": "critical",
                    "feature_id": fid,
                    "description": (
                        f"Feature {fid} stalled — delta unchanged for last 3 iterations"
                    ),
                    "command": command_for_item("STUCK", fid, edge, []),
                    "detail": detail,
                    "_sort_delta": detail["delta"] or 0,
                }
            )

        if status == "blocked":
            blocked_fids.add(fid)
            detail = build_item_detail("BLOCKED", feature, events, [])
            items.append(
                {
                    "type": "BLOCKED",
                    "severity": "high",
                    "feature_id": fid,
                    "description": f"Feature {fid} is blocked",
                    "command": command_for_item("BLOCKED", fid, edge, []),
                    "detail": detail,
                    "_sort_delta": detail["delta"] or 0,
                }
            )

    # --- GAP_CLUSTER ---
    all_gap_keys: list[str] = []
    for layer_key in ("layer_1", "layer_2"):
        layer = gaps.get(layer_key, {})
        for gap in layer.get("gaps", []):
            key = gap.get("req_key", "")
            if key and key not in all_gap_keys:
                all_gap_keys.append(key)

    # Group by domain prefix (everything before the trailing -NNN digit part)
    clusters: dict[str, list[str]] = {}
    for key in all_gap_keys:
        parts = key.rsplit("-", 1)
        prefix = parts[0] if len(parts) == 2 and parts[1].isdigit() else key
        clusters.setdefault(prefix, []).append(key)

    for prefix, cluster_keys in sorted(clusters.items()):
        detail = build_item_detail("GAP_CLUSTER", {}, [], cluster_keys)
        items.append(
            {
                "type": "GAP_CLUSTER",
                "severity": "medium",
                "feature_id": None,
                "description": (
                    f"Gap cluster: {prefix}-* ({len(cluster_keys)} uncovered REQ key(s))"
                ),
                "command": command_for_item("GAP_CLUSTER", None, None, cluster_keys),
                "detail": detail,
                "_sort_delta": 0,
            }
        )

    # --- IN_PROGRESS ---
    for feature in features:
        fid = _feature_id(feature)
        if fid in stuck_fids or fid in blocked_fids:
            continue
        status = feature.get("status", "")
        if status not in _ITERATING_STATUSES:
            continue
        edge = _current_edge(events, fid)
        pending = _pending_edge_count(events, fid)
        detail = build_item_detail("IN_PROGRESS", feature, events, [])
        items.append(
            {
                "type": "IN_PROGRESS",
                "severity": "low",
                "feature_id": fid,
                "description": f"Feature {fid} iterating — {pending} pending edge(s)",
                "command": command_for_item("IN_PROGRESS", fid, edge, []),
                "detail": detail,
                "_sort_delta": detail["delta"] or 0,
            }
        )

    if not items:
        return [
            {
                "type": "healthy",
                "severity": "info",
                "feature_id": None,
                "description": "No blockers detected — project is healthy.",
                "command": "",
                "detail": {
                    "reason": "All features are converged or quiescent.",
                    "delta": None,
                    "failing_checks": [],
                    "expected_outcome": "",
                    "gap_keys": [],
                    "iteration_history": [],
                },
            }
        ]

    # Sort: by severity tier, then by descending delta (more urgent first)
    items.sort(key=lambda i: (_SEVERITY_ORDER.get(i["severity"], 99), -(i["_sort_delta"])))

    # Strip internal sort key before returning
    for item in items:
        item.pop("_sort_delta", None)

    return items
