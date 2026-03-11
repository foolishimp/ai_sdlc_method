"""State computation from feature vectors and event streams.

Derives project-level lifecycle state from feature data, and per-feature
Hamiltonian metrics from events.  All operations are pure (read-only,
no side-effects — REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-STAT-002
# Implements: REQ-F-STAT-004
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

_ITERATING_STATUSES: frozenset[str] = frozenset({"iterating", "in_progress"})
_EXCLUDED_FROM_REQUIRED: frozenset[str] = frozenset({"blocked_deferred", "abandoned", "error"})


def compute_project_state(features: list[dict]) -> str:
    """Derive the project lifecycle state from all feature vectors.

    State priority (highest to lowest):

    1. **ITERATING** — any feature has status ``"iterating"`` or ``"in_progress"``.
    2. **CONVERGED** — all *required* features (excluding ``blocked_deferred``,
       ``abandoned``, ``error``) have status ``"converged"``.
    3. **BOUNDED** — nothing iterating; every ``blocked`` feature has an
       explicit ``disposition`` value.
    4. **QUIESCENT** — nothing iterating; at least one ``blocked`` feature
       lacks a ``disposition``.
    5. **uninitialized** — no features at all.

    Args:
        features: List of feature dicts as returned by
            :func:`~genesis_nav.readers.feature_reader.read_features`.

    Returns:
        One of ``"ITERATING"``, ``"QUIESCENT"``, ``"CONVERGED"``,
        ``"BOUNDED"``, ``"uninitialized"``.
    """
    if not features:
        return "uninitialized"

    # 1. ITERATING — highest priority
    for feat in features:
        if feat.get("status") in _ITERATING_STATUSES:
            return "ITERATING"

    # 2. CONVERGED — all required features done
    required = [f for f in features if f.get("status") not in _EXCLUDED_FROM_REQUIRED]
    if required and all(f.get("status") == "converged" for f in required):
        return "CONVERGED"

    # 3. BOUNDED vs QUIESCENT — based on blocked feature dispositions
    blocked = [f for f in features if f.get("status") == "blocked"]
    if blocked:
        all_disposed = all(bool(f.get("disposition")) for f in blocked)
        return "BOUNDED" if all_disposed else "QUIESCENT"

    # Default — workspace active but no clear forward state
    return "QUIESCENT"


def compute_hamiltonian(events: list[dict], feature_id: str) -> dict:
    """Compute the Hamiltonian metrics for a single feature.

    The Hamiltonian ``H = T + V`` where:

    - **T** — total number of ``iteration_completed`` events for this feature.
    - **V** — ``delta`` from the most recent ``iteration_completed`` event;
      set to ``0`` if an ``edge_converged`` event for the same feature
      follows in the stream.
    - **H** — ``T + V`` (monotonically increasing when converging).
    - **flat** — ``True`` when the last 3 ``V`` values are identical,
      indicating H is growing but V is not improving (possible stall).

    Args:
        events: Full event list for the workspace, in file order.
        feature_id: Feature identifier to filter on.

    Returns:
        Dict with keys ``H`` (int), ``T`` (int), ``V`` (int), ``flat`` (bool).
    """
    # Collect (original_index, event) pairs for iteration_completed events
    # Events may use "feature" or "feature_id" depending on emitter
    def _fid(e: dict) -> str:
        return e.get("feature_id") or e.get("feature") or ""

    feature_iterations: list[tuple[int, dict]] = [
        (i, e)
        for i, e in enumerate(events)
        if e.get("event_type") == "iteration_completed" and _fid(e) == feature_id
    ]

    T = len(feature_iterations)
    V = 0

    if feature_iterations:
        last_idx, last_ev = feature_iterations[-1]
        raw_v = int(last_ev.get("delta") or 0)

        # V → 0 if an edge_converged for this feature follows in the stream
        subsequent = events[last_idx + 1 :]
        edge_converged_follows = any(
            e.get("event_type") == "edge_converged" and e.get("feature_id") == feature_id
            for e in subsequent
        )
        V = 0 if edge_converged_follows else raw_v

    H = T + V

    # flat: last 3 V values (delta fields) are identical — stall indicator
    v_history = [int(e.get("delta") or 0) for _, e in feature_iterations[-3:]]
    flat = len(v_history) >= 3 and len(set(v_history)) == 1

    return {"H": H, "T": T, "V": V, "flat": flat}


def build_feature_detail(feature_dict: dict, events: list[dict]) -> dict:
    """Combine a feature YAML dict with computed Hamiltonian and trajectory.

    Derives the per-edge trajectory by replaying the event stream for the
    given feature.  Events examined: ``edge_started``, ``iteration_completed``,
    ``edge_converged``.

    Args:
        feature_dict: Parsed YAML dict for one feature vector.  Must contain
            ``feature_id`` (or ``id``) — all other fields are optional.
        events: Full event list for the workspace, in file order.

    Returns:
        Dict compatible with
        :class:`~genesis_nav.models.schemas.FeatureDetail` containing
        ``feature_id``, ``title``, ``status``, ``current_edge``, ``delta``,
        ``hamiltonian``, ``trajectory`` (list of edge dicts), and ``error``.
    """
    feature_id: str = feature_dict.get("feature_id") or feature_dict.get("id", "")

    # --- Build per-edge trajectory from events ---
    # edge_map preserves insertion order (Python 3.7+)
    edge_map: dict[str, dict] = {}

    for ev in events:
        if (ev.get("feature_id") or ev.get("feature") or "") != feature_id:
            continue
        ev_type = ev.get("event_type", "")
        edge = ev.get("edge", "")
        if not edge:
            continue

        if edge not in edge_map:
            edge_map[edge] = {
                "edge": edge,
                "status": "in_progress",
                "iteration": 0,
                "delta": 0,
                "started_at": None,
                "converged_at": None,
            }

        if ev_type == "edge_started":
            edge_map[edge]["started_at"] = ev.get("timestamp")
        elif ev_type == "iteration_completed":
            edge_map[edge]["iteration"] += 1
            edge_map[edge]["delta"] = int(ev.get("delta") or 0)
        elif ev_type == "edge_converged":
            edge_map[edge]["status"] = "converged"
            edge_map[edge]["converged_at"] = ev.get("timestamp")
            edge_map[edge]["delta"] = 0

    trajectory = list(edge_map.values())

    # current_edge: last in-progress edge in trajectory
    current_edge: str | None = None
    for edge_info in reversed(trajectory):
        if edge_info["status"] != "converged":
            current_edge = edge_info["edge"]
            break

    hamiltonian = compute_hamiltonian(events, feature_id)

    return {
        "feature_id": feature_id,
        "title": feature_dict.get("title", feature_id),
        "status": feature_dict.get("status", "unknown"),
        "current_edge": current_edge,
        "delta": hamiltonian["V"],
        "hamiltonian": hamiltonian,
        "trajectory": trajectory,
        "error": feature_dict.get("error"),
    }
