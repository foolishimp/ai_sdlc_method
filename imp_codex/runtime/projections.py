"""Replay-derived projections for features, routing, and status."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

import yaml

from .events import NormalizedEvent, load_events, utc_now
from .paths import RuntimePaths, CONFIG_ROOT


def load_yaml(path: Path) -> dict:
    with open(path) as handle:
        documents = [doc for doc in yaml.safe_load_all(handle) if doc is not None]
    merged: dict = {}
    for document in documents:
        merged.update(document)
    return merged


def dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def edge_id(transition: dict) -> str:
    arrow = "↔" if transition.get("edge_type") == "co_evolution" else "→"
    return f"{transition['source']}{arrow}{transition['target']}"


def parse_edge(edge: str) -> tuple[str, str]:
    if "↔" in edge:
        left, right = edge.split("↔", 1)
        return left, right
    left, right = edge.split("→", 1)
    return left, right


def edge_assets(edge: str) -> list[str]:
    source, target = parse_edge(edge)
    if "↔" in edge:
        return [source, target]
    return [target]


def load_graph(paths: RuntimePaths) -> dict:
    graph_path = paths.graph_topology_path if paths.graph_topology_path.exists() else CONFIG_ROOT / "graph_topology.yml"
    return load_yaml(graph_path)


def transition_order(paths: RuntimePaths) -> list[str]:
    return [edge_id(transition) for transition in load_graph(paths).get("transitions", [])]


def load_profile(paths: RuntimePaths, profile_name: str) -> dict:
    profile_path = paths.profiles_dir / f"{profile_name}.yml"
    if not profile_path.exists():
        profile_path = CONFIG_ROOT / "profiles" / f"{profile_name}.yml"
    return load_yaml(profile_path)


def load_project_constraints(paths: RuntimePaths) -> dict:
    if not paths.project_constraints_path.exists():
        return {}
    return load_yaml(paths.project_constraints_path)


def load_feature(paths: RuntimePaths, feature_id: str) -> tuple[dict | None, Path]:
    active_path = paths.active_features_dir / f"{feature_id}.yml"
    if active_path.exists():
        return load_yaml(active_path), active_path
    completed_path = paths.completed_features_dir / f"{feature_id}.yml"
    if completed_path.exists():
        return load_yaml(completed_path), completed_path
    return None, active_path


def iter_features(paths: RuntimePaths) -> list[tuple[dict, Path]]:
    features: list[tuple[dict, Path]] = []
    for directory in (paths.active_features_dir, paths.completed_features_dir):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.yml")):
            features.append((load_yaml(path), path))
    return features


def feature_lookup(paths: RuntimePaths) -> dict[str, dict]:
    """Map feature IDs to their current documents."""

    return {
        feature_doc.get("feature"): feature_doc
        for feature_doc, _ in iter_features(paths)
        if feature_doc.get("feature")
    }


def feature_title(feature_id: str) -> str:
    return feature_id.replace("REQ-F-", "").replace("-", " ").title()


def default_feature_document(
    paths: RuntimePaths,
    *,
    feature_id: str,
    profile_name: str,
    title: str | None = None,
) -> dict:
    template = load_yaml(paths.feature_template_path)
    now = utc_now()
    template["feature"] = feature_id
    template["title"] = title or feature_title(feature_id)
    template["intent"] = template.get("intent", "").replace("{timestamp}", now)
    template["profile"] = profile_name
    template["status"] = "pending"
    template["created"] = now
    template["updated"] = now
    return template


def compute_context_hash(paths: RuntimePaths, profile_name: str, feature_doc: dict | None = None) -> str:
    digest = hashlib.sha256()
    for candidate in (
        paths.graph_topology_path,
        paths.project_constraints_path,
        paths.profiles_dir / f"{profile_name}.yml",
    ):
        if candidate.exists():
            digest.update(candidate.read_bytes())
    if feature_doc:
        digest.update(yaml.safe_dump(feature_doc, sort_keys=True).encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"


def next_iteration(feature_doc: dict, edge: str) -> int:
    asset = edge_assets(edge)[-1]
    return int(feature_doc.get("trajectory", {}).get(asset, {}).get("iteration", 0)) + 1


def update_feature_for_iteration(
    feature_doc: dict,
    *,
    edge: str,
    iteration: int,
    status: str,
    context_hash: str,
    evaluators: dict,
    timestamp: str,
    profile_name: str,
    delta: int,
) -> dict:
    feature_doc = dict(feature_doc)
    feature_doc["updated"] = timestamp
    feature_doc["profile"] = profile_name
    feature_doc["status"] = "in_progress"
    feature_doc.setdefault("trajectory", {})
    for asset in edge_assets(edge):
        trajectory = dict(feature_doc["trajectory"].get(asset, {}))
        if status == "converged":
            trajectory["status"] = "converged"
        elif status == "pending_review":
            trajectory["status"] = "pending_review"
        else:
            trajectory["status"] = "iterating"
        trajectory["iteration"] = iteration
        trajectory.setdefault("started_at", timestamp)
        if status == "converged":
            trajectory["converged_at"] = timestamp
        trajectory["context_hash"] = context_hash
        trajectory["evaluator_results"] = evaluators
        trajectory["delta"] = delta
        feature_doc["trajectory"][asset] = trajectory
    return feature_doc


def edge_is_converged(feature_doc: dict, edge: str) -> bool:
    trajectory = feature_doc.get("trajectory", {})
    return all(trajectory.get(asset, {}).get("status") == "converged" for asset in edge_assets(edge))


def included_edges(profile_doc: dict, graph_doc: dict) -> list[str]:
    includes = profile_doc.get("graph", {}).get("include")
    if includes:
        return list(includes)
    return [edge_id(transition) for transition in graph_doc.get("transitions", [])]


def unresolved_edges(feature_doc: dict, profile_doc: dict, graph_doc: dict) -> list[str]:
    return [edge for edge in included_edges(profile_doc, graph_doc) if not edge_is_converged(feature_doc, edge)]


def feature_is_done(feature_doc: dict, profile_doc: dict, graph_doc: dict) -> bool:
    return not unresolved_edges(feature_doc, profile_doc, graph_doc)


def reached_design_or_later(feature_doc: dict) -> bool:
    trajectory = feature_doc.get("trajectory", {})
    for asset in ("design", "module_decomp", "basis_projections", "code", "unit_tests", "uat_tests"):
        if trajectory.get(asset, {}).get("status") not in (None, "pending"):
            return True
    return False


def _has_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return any(_has_value(item) for item in value)
    if isinstance(value, dict):
        return any(_has_value(item) for item in value.values())
    return value is not None


def unresolved_mandatory_constraints(paths: RuntimePaths, features: Iterable[dict]) -> list[str]:
    graph_doc = load_graph(paths)
    constraints_doc = load_project_constraints(paths)
    values = constraints_doc.get("constraint_dimensions", {})
    if not any(reached_design_or_later(feature) for feature in features):
        return []
    unresolved: list[str] = []
    for name, metadata in graph_doc.get("constraint_dimensions", {}).items():
        if not metadata.get("mandatory"):
            continue
        if not _has_value(values.get(name, {})):
            unresolved.append(name)
    return unresolved


def detect_stuck_features(events: Iterable[NormalizedEvent], threshold: int = 3) -> set[tuple[str, str]]:
    grouped: dict[tuple[str, str], list[NormalizedEvent]] = defaultdict(list)
    for event in events:
        if event.semantic_type != "IterationCompleted" or event.delta is None or event.delta <= 0:
            continue
        if not event.feature or not event.edge:
            continue
        grouped[(event.feature, event.edge)].append(event)
    stuck: set[tuple[str, str]] = set()
    for key, group in grouped.items():
        tail = group[-threshold:]
        if len(tail) < threshold:
            continue
        deltas = {event.delta for event in tail}
        if len(deltas) == 1:
            stuck.add(key)
    return stuck


def detect_corrupted_events(paths: RuntimePaths) -> list[dict]:
    """Return malformed JSONL rows from the event log."""

    if not paths.events_file.exists():
        return []
    corruptions: list[dict] = []
    with open(paths.events_file) as handle:
        for line_no, line in enumerate(handle, 1):
            raw = line.strip()
            if not raw:
                continue
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                corruptions.append({"line": line_no, "raw": raw, "error": str(exc)})
    return corruptions


def detect_missing_feature_vectors(paths: RuntimePaths) -> list[str]:
    """Find feature IDs referenced in events but missing from feature projections."""

    known = set(feature_lookup(paths))
    referenced = {
        event.feature
        for event in load_events(paths.events_file)
        if event.feature
    }
    return sorted(referenced - known)


def detect_orphaned_spawns(paths: RuntimePaths) -> list[dict]:
    """Find child features whose parent feature is missing."""

    known = set(feature_lookup(paths))
    orphans: list[dict] = []
    for feature_doc, _ in iter_features(paths):
        parent = feature_doc.get("parent") or {}
        parent_id = parent.get("feature") if isinstance(parent, dict) else None
        if parent_id and parent_id not in known:
            orphans.append(
                {
                    "feature": feature_doc.get("feature"),
                    "parent": parent_id,
                    "reason": f"parent {parent_id} not found",
                }
            )
    return orphans


def dependency_ids(feature_doc: dict) -> list[str]:
    """Extract dependency feature IDs from a feature document."""

    dependencies = []
    for dependency in feature_doc.get("dependencies", []):
        if isinstance(dependency, str):
            dependencies.append(dependency)
        elif isinstance(dependency, dict) and dependency.get("feature"):
            dependencies.append(dependency["feature"])
    return dependencies


def has_pending_human_review(feature_doc: dict) -> bool:
    """Return true when any trajectory leg is waiting on human review."""

    for edge_data in feature_doc.get("trajectory", {}).values():
        if isinstance(edge_data, dict) and edge_data.get("status") == "pending_review":
            return True
    return False


def pending_review_details(paths: RuntimePaths) -> list[dict]:
    """Return features currently waiting on human approval."""

    latest_review_edge: dict[str, str] = {}
    for event in load_events(paths.events_file):
        if (
            event.semantic_type == "IterationCompleted"
            and event.status == "pending_review"
            and event.feature
            and event.edge
        ):
            latest_review_edge[event.feature] = event.edge

    pending: list[dict] = []
    for feature_id, feature_doc in sorted(feature_lookup(paths).items()):
        if not has_pending_human_review(feature_doc):
            continue
        pending.append(
            {
                "feature": feature_id,
                "edge": latest_review_edge.get(feature_id),
            }
        )
    return pending


def blocked_feature_details(paths: RuntimePaths) -> list[dict]:
    """Return blocked features with dependency or review reasons."""

    features = feature_lookup(paths)
    blocked: list[dict] = []
    for feature_id, feature_doc in sorted(features.items()):
        if feature_doc.get("status") == "converged":
            continue
        reasons = []
        for dependency_id in dependency_ids(feature_doc):
            dependency_doc = features.get(dependency_id)
            if dependency_doc is None or dependency_doc.get("status") != "converged":
                reasons.append(f"dependency {dependency_id} unresolved")
        if has_pending_human_review(feature_doc):
            reasons.append("pending human review")
        if reasons:
            blocked.append({"feature": feature_id, "reasons": reasons})
    return blocked


def compute_aggregated_view(paths: RuntimePaths) -> dict:
    """Aggregate feature and edge counts across the workspace."""

    features = [feature for feature, _ in iter_features(paths)]
    stuck = detect_stuck_features(load_events(paths.events_file))
    stuck_ids = {feature_id for feature_id, _edge in stuck}
    blocked = blocked_feature_details(paths)
    blocked_ids = {item["feature"] for item in blocked}

    converged = 0
    in_progress = 0
    edges_total = 0
    edges_converged = 0
    for feature_doc in features:
        if feature_doc.get("status") == "converged":
            converged += 1
        elif feature_doc.get("feature") in blocked_ids:
            pass
        elif feature_doc.get("feature") in stuck_ids:
            pass
        else:
            in_progress += 1
        for edge_data in feature_doc.get("trajectory", {}).values():
            if not isinstance(edge_data, dict):
                continue
            edges_total += 1
            if edge_data.get("status") == "converged":
                edges_converged += 1
    return {
        "total": len(features),
        "converged": converged,
        "in_progress": in_progress,
        "blocked": len(blocked_ids),
        "stuck": len(stuck_ids),
        "edges_total": edges_total,
        "edges_converged": edges_converged,
    }


def get_unactioned_signals(paths: RuntimePaths) -> list[NormalizedEvent]:
    """Return intent-like signals that have not been acted upon yet."""

    events = load_events(paths.events_file)
    actioned_features = {
        event.feature
        for event in events
        if event.semantic_type in {"SpawnCreated", "ReviewCompleted", "SpecModified"}
    }
    return [
        event
        for event in events
        if event.semantic_type in {"IntentRaised", "intent_raised"}
        and event.feature not in actioned_features
    ]


@dataclass(frozen=True)
class StartDecision:
    state: str
    action: str
    feature: str | None
    edge: str | None
    detail: str


def detect_state(paths: RuntimePaths) -> str:
    if not paths.workspace_root.exists():
        return "UNINITIALISED"
    if not paths.intent_path.exists() or not paths.intent_path.read_text().strip():
        return "NEEDS_INTENT"
    feature_docs = [feature for feature, _ in iter_features(paths)]
    if not feature_docs:
        return "NO_FEATURES"
    active = [feature for feature in feature_docs if feature.get("status") != "converged"]
    if not active:
        return "ALL_CONVERGED"
    if unresolved_mandatory_constraints(paths, active):
        return "NEEDS_CONSTRAINTS"
    if pending_review_details(paths):
        return "PENDING_HUMAN_REVIEW"
    stuck = detect_stuck_features(load_events(paths.events_file))
    if stuck:
        return "STUCK"
    blocked = {item["feature"] for item in blocked_feature_details(paths)}
    if active and all(feature.get("feature") in blocked for feature in active):
        return "ALL_BLOCKED"
    return "IN_PROGRESS"


def select_next_feature(paths: RuntimePaths, explicit_feature: str | None = None) -> dict | None:
    graph_doc = load_graph(paths)
    candidates = []
    for feature_doc, _ in iter_features(paths):
        if feature_doc.get("status") == "converged":
            continue
        if explicit_feature and feature_doc.get("feature") != explicit_feature:
            continue
        profile_doc = load_profile(paths, feature_doc.get("profile", "standard"))
        remaining = unresolved_edges(feature_doc, profile_doc, graph_doc)
        candidates.append((len(remaining), feature_doc.get("feature"), feature_doc, remaining))
    if not candidates and explicit_feature:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def determine_next_edge(paths: RuntimePaths, feature_doc: dict, explicit_edge: str | None = None) -> str | None:
    if explicit_edge:
        return explicit_edge
    graph_doc = load_graph(paths)
    profile_doc = load_profile(paths, feature_doc.get("profile", "standard"))
    unresolved = set(unresolved_edges(feature_doc, profile_doc, graph_doc))
    for edge in transition_order(paths):
        if edge in unresolved:
            return edge
    return None


def decide_start_action(
    paths: RuntimePaths,
    *,
    feature: str | None = None,
    edge: str | None = None,
) -> StartDecision:
    state = detect_state(paths)
    if state == "UNINITIALISED":
        return StartDecision(state=state, action="init", feature=None, edge=None, detail="Workspace missing")
    if state == "NEEDS_INTENT":
        return StartDecision(state=state, action="author_intent", feature=None, edge=None, detail="INTENT.md missing or empty")
    if state == "NO_FEATURES":
        return StartDecision(state=state, action="spawn_feature", feature=None, edge=None, detail="No feature vectors found")
    if state == "NEEDS_CONSTRAINTS":
        missing = unresolved_mandatory_constraints(paths, [doc for doc, _ in iter_features(paths)])
        return StartDecision(state=state, action="resolve_constraints", feature=None, edge=None, detail=", ".join(missing))
    if state == "PENDING_HUMAN_REVIEW":
        pending = pending_review_details(paths)
        first = pending[0] if pending else {"feature": None, "edge": None}
        detail = ", ".join(
            f"{item['feature']}:{item['edge'] or 'pending edge'}"
            for item in pending
        )
        return StartDecision(
            state=state,
            action="review",
            feature=first["feature"],
            edge=first["edge"],
            detail=detail or "Human review required",
        )
    if state == "STUCK":
        stuck = ", ".join(f"{feature_id}:{edge}" for feature_id, edge in sorted(detect_stuck_features(load_events(paths.events_file))))
        return StartDecision(state=state, action="recover_stuck", feature=None, edge=None, detail=stuck or "Repeated identical delta detected")
    if state == "ALL_BLOCKED":
        blocked = blocked_feature_details(paths)
        detail = "; ".join(f"{item['feature']}: {', '.join(item['reasons'])}" for item in blocked)
        return StartDecision(state=state, action="recover_blocked", feature=None, edge=None, detail=detail or "All active features blocked")
    if state == "ALL_CONVERGED":
        return StartDecision(state=state, action="release", feature=None, edge=None, detail="All active features converged")

    feature_doc = select_next_feature(paths, explicit_feature=feature)
    if feature_doc is None:
        return StartDecision(state=state, action="spawn_feature", feature=None, edge=None, detail="No matching active feature")
    selected_edge = determine_next_edge(paths, feature_doc, explicit_edge=edge)
    return StartDecision(
        state=state,
        action="iterate",
        feature=feature_doc.get("feature"),
        edge=selected_edge,
        detail="closest-to-complete",
    )


def render_feature_index(paths: RuntimePaths) -> dict:
    """Render a machine-readable feature index projection."""

    graph_doc = load_graph(paths)
    features = []
    for feature_doc, feature_path in iter_features(paths):
        profile_doc = load_profile(paths, feature_doc.get("profile", "standard"))
        remaining = unresolved_edges(feature_doc, profile_doc, graph_doc)
        features.append(
            {
                "feature": feature_doc.get("feature"),
                "title": feature_doc.get("title"),
                "status": feature_doc.get("status"),
                "profile": feature_doc.get("profile"),
                "next_edge": remaining[0] if remaining else None,
                "remaining_edges": len(remaining),
                "path": str(feature_path.relative_to(paths.workspace_root)),
            }
        )
    return {
        "generated": utc_now(),
        "project": load_project_constraints(paths).get("project", {}).get("name", paths.project_root.name),
        "features": features,
    }


def render_active_tasks_markdown(paths: RuntimePaths) -> str:
    """Render a filtered markdown task log derived from the event stream."""

    events = load_events(paths.events_file)
    decision = decide_start_action(paths)
    lines = [
        "# Active Tasks",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Next Action",
        "",
        f"- State: {decision.state}",
        f"- Action: {decision.action}",
    ]
    if decision.feature and decision.edge:
        lines.append(f"- Target: {decision.feature} on {decision.edge}")

    lines.extend(["", "## Converged Edges", ""])
    converged = [
        event
        for event in events
        if event.semantic_type == "ConvergenceAchieved" and event.feature and event.edge
    ]
    if not converged:
        lines.append("- None")
    for event in converged[-20:]:
        lines.append(
            f"### {event.feature}: {event.edge} CONVERGED\n"
            f"**Date**: {event.event_time}\n"
            f"**Iterations**: {event.iteration or '-'}\n"
            f"**Delta**: {event.delta if event.delta is not None else '-'}\n"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_health_summary(paths: RuntimePaths) -> dict:
    """Compute a lightweight workspace health summary."""

    stuck = detect_stuck_features(load_events(paths.events_file))
    return {
        "corrupted_events": detect_corrupted_events(paths),
        "missing_feature_vectors": detect_missing_feature_vectors(paths),
        "orphaned_spawns": detect_orphaned_spawns(paths),
        "pending_human_review": pending_review_details(paths),
        "stuck_features": [
            {"feature": feature_id, "edge": edge}
            for feature_id, edge in sorted(stuck)
        ],
        "blocked_features": blocked_feature_details(paths),
    }


def render_status_markdown(paths: RuntimePaths) -> str:
    """Render the current markdown status projection."""

    features = [doc for doc, _ in iter_features(paths)]
    graph_doc = load_graph(paths)
    event_counts = Counter(event.semantic_type for event in load_events(paths.events_file))
    decision = decide_start_action(paths)
    rollup = compute_aggregated_view(paths)
    health = render_health_summary(paths)
    signals = get_unactioned_signals(paths)
    lines = [
        f"# Project Status - {load_project_constraints(paths).get('project', {}).get('name', paths.project_root.name)}",
        "",
        f"Generated: {utc_now()}",
        "",
        f"State: {decision.state}",
        "What Start Would Do: "
        + decision.action
        + (f" {decision.feature} on {decision.edge}" if decision.feature and decision.edge else ""),
        "",
        "## Project Rollup",
        "",
        f"- Edges converged: {rollup['edges_converged']}/{rollup['edges_total']}",
        f"- Features: {rollup['converged']} converged, {rollup['in_progress']} in-progress, {rollup['blocked']} blocked, {rollup['stuck']} stuck",
        f"- Signals: {len(signals)} unactioned intent_raised",
        "",
        "## Active Features",
        "",
        "| Feature | Status | Next Edge | Remaining Edges |",
        "|---------|--------|-----------|-----------------|",
    ]
    if not features:
        lines.append("| - | - | - | - |")
    for feature_doc in sorted(features, key=lambda item: item.get("feature", "")):
        profile_doc = load_profile(paths, feature_doc.get("profile", "standard"))
        remaining = unresolved_edges(feature_doc, profile_doc, graph_doc)
        next_edge = remaining[0] if remaining else "-"
        lines.append(
            f"| {feature_doc.get('feature')} | {feature_doc.get('status')} | {next_edge} | {len(remaining)} |"
        )

    lines.extend(["", "## Signals", ""])
    if not signals:
        lines.append("- None")
    for signal in signals:
        lines.append(f"- {signal.feature or '-'}: {signal.semantic_type} ({signal.event_time})")

    lines.extend(["", "## Next Actions", ""])
    if decision.feature and decision.edge:
        lines.append(f"- Iterate {decision.feature} on {decision.edge}")
    else:
        lines.append(f"- {decision.action}")

    lines.extend(
        [
            "",
            "## Process Telemetry",
            "",
            "### Convergence Pattern",
            f"- Total events: {sum(event_counts.values())}",
        ]
    )
    for name in sorted(event_counts):
        lines.append(f"- {name}: {event_counts[name]}")

    lines.extend(
        [
            "",
            "### Workspace Health",
            f"- Corrupted events: {len(health['corrupted_events'])}",
            f"- Missing feature vectors: {len(health['missing_feature_vectors'])}",
            f"- Orphaned spawns: {len(health['orphaned_spawns'])}",
            f"- Pending human review: {len(health['pending_human_review'])}",
            f"- Stuck features: {len(health['stuck_features'])}",
            f"- Blocked features: {len(health['blocked_features'])}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_projections(paths: RuntimePaths) -> dict:
    """Write the core derived views to disk."""

    status_markdown = render_status_markdown(paths)
    paths.status_file.write_text(status_markdown)
    feature_index = render_feature_index(paths)
    dump_yaml(paths.feature_index_path, feature_index)
    active_tasks_markdown = render_active_tasks_markdown(paths)
    paths.active_tasks_file.write_text(active_tasks_markdown)
    return {
        "status_markdown": status_markdown,
        "feature_index": feature_index,
        "active_tasks_markdown": active_tasks_markdown,
    }


__all__ = [
    "StartDecision",
    "compute_context_hash",
    "decide_start_action",
    "default_feature_document",
    "detect_state",
    "detect_stuck_features",
    "determine_next_edge",
    "dump_yaml",
    "edge_assets",
    "edge_id",
    "feature_is_done",
    "feature_lookup",
    "get_unactioned_signals",
    "included_edges",
    "iter_features",
    "load_feature",
    "load_graph",
    "load_profile",
    "load_project_constraints",
    "load_yaml",
    "next_iteration",
    "pending_review_details",
    "render_active_tasks_markdown",
    "render_feature_index",
    "render_health_summary",
    "render_status_markdown",
    "select_next_feature",
    "transition_order",
    "unresolved_edges",
    "update_feature_for_iteration",
    "write_projections",
]
