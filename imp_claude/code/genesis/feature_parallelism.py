# Implements: REQ-COORD-004 (Markov-Aligned Parallelism)
"""Feature parallelism — inner product computation for safe multi-agent routing.

The inner product of two feature vectors is the count of shared modules they
depend on. Features with zero inner product (orthogonal) have no shared modules
and may be executed in parallel by independent agents with no coordination.
Features with non-zero inner product share modules; shared modules must be
built before both features diverge.

Reference: Asset Graph Model §6.7 (Basis Projections — orthogonal projections
execute in parallel), §11.1 (Inner product — shared modules determine
coordination need).

The feature_module_map is the n-n mapping produced by module_decomposition:
    {
        "REQ-F-AUTH-001": ["auth.py", "models.py", "utils.py"],
        "REQ-F-API-001":  ["api.py",  "models.py"],
        "REQ-F-CLI-001":  ["cli.py",  "commands.py"],
    }

inner_product(REQ-F-AUTH-001, REQ-F-API-001)  = 1  (shared: models.py)
inner_product(REQ-F-AUTH-001, REQ-F-CLI-001)  = 0  (no shared modules)
"""

from __future__ import annotations

from typing import Any


# ═══════════════════════════════════════════════════════════════════════
# INNER PRODUCT
# ═══════════════════════════════════════════════════════════════════════


def compute_inner_product(
    feature_a: str,
    feature_b: str,
    feature_module_map: dict[str, list[str]],
) -> int:
    """Count the shared modules between feature_a and feature_b.

    Returns 0 (orthogonal) if either feature is absent from the map.
    Returns the number of modules that appear in both feature vectors.
    """
    mods_a = set(feature_module_map.get(feature_a, []))
    mods_b = set(feature_module_map.get(feature_b, []))
    return len(mods_a & mods_b)


def is_orthogonal(
    feature_a: str,
    feature_b: str,
    feature_module_map: dict[str, list[str]],
) -> bool:
    """Return True if the two features share zero modules (safe to parallelise)."""
    return compute_inner_product(feature_a, feature_b, feature_module_map) == 0


def shared_modules(
    feature_a: str,
    feature_b: str,
    feature_module_map: dict[str, list[str]],
) -> list[str]:
    """Return the list of modules shared between feature_a and feature_b."""
    mods_a = set(feature_module_map.get(feature_a, []))
    mods_b = set(feature_module_map.get(feature_b, []))
    return sorted(mods_a & mods_b)


# ═══════════════════════════════════════════════════════════════════════
# PARALLELISM GROUPS
# ═══════════════════════════════════════════════════════════════════════


def compute_parallelism_matrix(
    features: list[str],
    feature_module_map: dict[str, list[str]],
) -> dict[tuple[str, str], int]:
    """Compute the inner product matrix for all feature pairs.

    Returns: {(feature_a, feature_b): inner_product} for all a < b pairs
    (upper triangle only — symmetric).
    """
    matrix: dict[tuple[str, str], int] = {}
    for i, fa in enumerate(features):
        for fb in features[i + 1 :]:
            ip = compute_inner_product(fa, fb, feature_module_map)
            matrix[(fa, fb)] = ip
    return matrix


def find_orthogonal_groups(
    features: list[str],
    feature_module_map: dict[str, list[str]],
) -> list[list[str]]:
    """Partition features into groups of mutually orthogonal features.

    Features within a group share zero modules with each other and may
    be safely executed in parallel. Uses a greedy graph colouring approach:
    each group is an independent set in the shared-module conflict graph.

    Returns list of groups (each group is a list of feature IDs), with
    the largest groups first.
    """
    # Build conflict edges: features that share at least one module
    conflicts: dict[str, set[str]] = {f: set() for f in features}
    for i, fa in enumerate(features):
        for fb in features[i + 1 :]:
            if not is_orthogonal(fa, fb, feature_module_map):
                conflicts[fa].add(fb)
                conflicts[fb].add(fa)

    # Greedy partition into independent sets (graph colouring)
    unassigned = list(features)
    groups: list[list[str]] = []

    while unassigned:
        group: list[str] = []
        blocked: set[str] = set()
        remaining: list[str] = []

        for feature in unassigned:
            if feature in blocked:
                remaining.append(feature)
                continue
            group.append(feature)
            # Block all features that conflict with this one
            blocked.update(conflicts[feature])

        groups.append(group)
        unassigned = remaining

    # Sort groups by size (largest first)
    groups.sort(key=len, reverse=True)
    return groups


def get_parallelism_advice(
    features: list[str],
    feature_module_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Return per-pair parallelism advice for all feature pairs.

    Returns list of advice dicts:
        {
            "feature_a": str,
            "feature_b": str,
            "inner_product": int,
            "is_orthogonal": bool,
            "advice": "parallel_safe" | "sequential_recommended",
            "shared_modules": list[str],   # only if non-orthogonal
        }
    """
    advice: list[dict[str, Any]] = []
    for i, fa in enumerate(features):
        for fb in features[i + 1 :]:
            ip = compute_inner_product(fa, fb, feature_module_map)
            orthogonal = ip == 0
            entry: dict[str, Any] = {
                "feature_a": fa,
                "feature_b": fb,
                "inner_product": ip,
                "is_orthogonal": orthogonal,
                "advice": "parallel_safe" if orthogonal else "sequential_recommended",
            }
            if not orthogonal:
                entry["shared_modules"] = shared_modules(fa, fb, feature_module_map)
            advice.append(entry)
    return advice


# ═══════════════════════════════════════════════════════════════════════
# AGENT ROUTING
# ═══════════════════════════════════════════════════════════════════════


def route_features_to_agents(
    features: list[str],
    available_agents: list[str],
    feature_module_map: dict[str, list[str]],
) -> dict[str, Any]:
    """Assign features to agents respecting orthogonality constraints.

    Strategy:
    1. Compute parallelism groups (orthogonal sets)
    2. If there are enough agents, assign each group to a different agent
    3. If there are more features than agents, pack groups round-robin
    4. Emit a warning for any non-orthogonal assignment

    Returns:
        {
            "assignments": {agent_id: [feature_ids]},
            "warnings": [{"agent_id", "feature_a", "feature_b", "shared_modules"}],
            "groups": [[feature_ids]],  # orthogonal groups computed
        }
    """
    groups = find_orthogonal_groups(features, feature_module_map)

    # Assign groups to agents round-robin
    assignments: dict[str, list[str]] = {a: [] for a in available_agents}
    warnings: list[dict[str, Any]] = []

    if not available_agents:
        return {"assignments": {}, "warnings": [], "groups": groups}

    for idx, group in enumerate(groups):
        agent = available_agents[idx % len(available_agents)]
        assignments[agent].extend(group)

    # Detect non-orthogonal within the same agent's assignment
    for agent, agent_features in assignments.items():
        for i, fa in enumerate(agent_features):
            for fb in agent_features[i + 1 :]:
                if not is_orthogonal(fa, fb, feature_module_map):
                    warnings.append(
                        {
                            "agent_id": agent,
                            "feature_a": fa,
                            "feature_b": fb,
                            "inner_product": compute_inner_product(
                                fa, fb, feature_module_map
                            ),
                            "shared_modules": shared_modules(
                                fa, fb, feature_module_map
                            ),
                            "advice": "build shared modules before diverging",
                        }
                    )

    return {"assignments": assignments, "warnings": warnings, "groups": groups}
