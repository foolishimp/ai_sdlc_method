"""Thin executable command stubs for the Codex runtime."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from .events import append_run_event, load_events, utc_now
from .evaluators import run_agent_checks, run_deterministic_checks
from .intents import resolve_named_intent_payload
from .paths import RuntimePaths, bootstrap_workspace, detect_workspace_scope
from .projections import (
    blocked_feature_details,
    compute_context_hash,
    decide_start_action,
    default_feature_document,
    detect_state,
    detect_stuck_features,
    dump_yaml,
    feature_is_done,
    iter_features,
    load_feature,
    load_graph,
    load_profile,
    load_project_constraints,
    next_iteration,
    render_health_summary,
    update_feature_for_iteration,
    write_projections,
)
from .traceability import (
    build_checkpoint_snapshot,
    build_context_manifest,
    build_gap_report,
    build_release_manifest,
    build_trace_report,
    current_git_ref,
)


def _summarize_evaluators(evaluators: Iterable[dict] | None, *, delta: int, converged: bool) -> dict:
    details = list(evaluators or [])
    if not details:
        details = [
            {
                "name": "stub_execution",
                "type": "agent",
                "result": "pass" if converged else "fail",
                "required": True,
            }
        ]
    normalized = []
    for detail in details:
        item = dict(detail)
        if "result" not in item and "outcome" in item:
            item["result"] = item["outcome"]
        item.setdefault("required", True)
        normalized.append(item)
    return {
        "passed": sum(1 for item in normalized if item["result"] == "pass"),
        "failed": sum(1 for item in normalized if item["result"] == "fail"),
        "skipped": sum(1 for item in normalized if item["result"] == "skip"),
        "pending": sum(1 for item in normalized if item["result"] == "pending"),
        "total": len(normalized),
        "details": normalized,
        "delta": delta,
    }


def _project_name(paths: RuntimePaths, fallback: str | None = None) -> str:
    constraints = load_project_constraints(paths)
    return constraints.get("project", {}).get("name") or fallback or paths.project_root.name


def _write_status(paths: RuntimePaths) -> str:
    return write_projections(paths)["status_markdown"]


def _context_manifest_template() -> dict:
    return {
        "version": "1.0.0",
        "generated_at": utc_now(),
        "algorithm": "sha256-canonical-v1",
        "aggregate_hash": "pending",
        "entries": [],
    }


def _intent_placeholder(project_name: str) -> str:
    return "\n".join(
        [
            "# Project Intent",
            "",
            f"**Project**: {project_name}",
            f"**Date**: {utc_now()}",
            "**Status**: Draft",
            "",
            "---",
            "",
            f"## INT-001: {project_name} Initial Intent",
            "",
            "### Problem / Opportunity",
            "",
            "{Describe the problem or opportunity here}",
            "",
            "### Expected Outcomes",
            "",
            "- [ ] Outcome 1",
            "- [ ] Outcome 2",
            "",
            "### Constraints",
            "",
            "- Constraint 1",
            "",
            "---",
            "",
            "## Next Steps",
            "",
            "1. Refine this intent with stakeholders",
            '2. Run `/gen-iterate --edge "intent→requirements"` to generate REQ-* keys',
            "3. Review and approve requirements",
            "",
        ]
    )


def _adr_template() -> str:
    return "\n".join(
        [
            "# ADR-000: Template",
            "",
            "**Status**: Template (copy and rename to create new ADR)",
            f"**Date**: {utc_now()}",
            "",
            "## Context",
            "",
            "{What forces are at play? What problem or decision are we facing?}",
            "",
            "## Decision",
            "",
            "We will {describe decision here}.",
            "",
            "## Rationale",
            "",
            "{Why this option? What tradeoffs are accepted?}",
            "",
        ]
    )


def _configured_mandatory_dimensions(paths: RuntimePaths) -> int:
    graph_doc = load_graph(paths)
    constraints = load_project_constraints(paths).get("constraint_dimensions", {})
    configured = 0
    for name, metadata in graph_doc.get("constraint_dimensions", {}).items():
        if not metadata.get("mandatory"):
            continue
        if constraints.get(name):
            configured += 1
    return configured


def _artifact_refs(project_root: Path, artifact_paths: Iterable[str] | None) -> list[dict]:
    project_root = project_root.resolve()
    refs: list[dict] = []
    for raw_path in artifact_paths or []:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (project_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(f"Candidate artifact not found: {raw_path}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        try:
            display_path = str(candidate.relative_to(project_root))
        except ValueError:
            display_path = str(candidate)
        refs.append(
            {
                "path": display_path,
                "sha256": f"sha256:{digest}",
                "bytes": candidate.stat().st_size,
            }
        )
    return refs


def _latest_iteration_event(paths: RuntimePaths, feature: str, edge: str | None = None):
    events = load_events(paths.events_file)
    candidates = [
        event
        for event in events
        if event.feature == feature
        and event.semantic_type == "IterationCompleted"
        and (edge is None or event.edge == edge)
    ]
    return candidates[-1] if candidates else None


def _current_edge_for_feature(paths: RuntimePaths, feature_doc: dict) -> str | None:
    latest = None
    for event in load_events(paths.events_file):
        if event.feature == feature_doc.get("feature") and event.edge:
            latest = event.edge
    return latest or decide_start_action(paths, feature=feature_doc.get("feature")).edge


def _required_evaluator_types(paths: RuntimePaths, profile_name: str, edge: str) -> list[str]:
    profile_doc = load_profile(paths, profile_name)
    evaluators = profile_doc.get("evaluators", {})
    override = evaluators.get("overrides", {}).get(edge, {})
    if isinstance(override, dict) and override.get("evaluators"):
        return list(override["evaluators"])
    return list(evaluators.get("default", []))


def gen_start(
    project_root: Path,
    *,
    feature: str | None = None,
    edge: str | None = None,
) -> dict:
    """Detect state and return the next recommended action."""

    paths = RuntimePaths(project_root)
    decision = decide_start_action(paths, feature=feature, edge=edge)
    return {
        "state": decision.state,
        "action": decision.action,
        "feature": decision.feature,
        "edge": decision.edge,
        "detail": decision.detail,
        "health": render_health_summary(paths) if paths.workspace_root.exists() else {},
        "blocked_features": blocked_feature_details(paths) if paths.workspace_root.exists() else [],
    }


def gen_init(
    project_root: Path,
    *,
    project_name: str | None = None,
    default_profile: str = "standard",
    actor: str = "codex-runtime",
) -> dict:
    """Explicitly scaffold the Codex workspace and emit project_initialized."""

    scope_info = detect_workspace_scope(project_root)
    paths = bootstrap_workspace(project_root, project_name=project_name, default_profile=default_profile)
    project = _project_name(paths, fallback=project_name)

    if not paths.context_manifest_path.exists():
        dump_yaml(paths.context_manifest_path, _context_manifest_template())

    paths.specification_dir.mkdir(parents=True, exist_ok=True)
    if not paths.intent_path.exists():
        paths.intent_path.write_text(_intent_placeholder(project))

    adr_template_path = paths.project_root / "imp_codex" / "design" / "adrs" / "ADR-000-template.md"
    adr_template_path.parent.mkdir(parents=True, exist_ok=True)
    if not adr_template_path.exists():
        adr_template_path.write_text(_adr_template())

    projections = write_projections(paths)
    existing_init = next(
        (
            event
            for event in load_events(paths.events_file)
            if event.semantic_type == "ProjectInitialized"
        ),
        None,
    )
    init_event = None
    if existing_init is None:
        constraints = load_project_constraints(paths)
        graph_doc = load_graph(paths)
        tools_detected = sorted(
            name
            for name, metadata in constraints.get("tools", {}).items()
            if metadata.get("command")
        )
        init_event = append_run_event(
            paths.events_file,
            project_name=project,
            semantic_type="project_initialized",
            actor=actor,
            feature="project",
            edge="init",
            payload={
                "language": constraints.get("language", {}).get("primary", "unknown"),
                "tools_detected": tools_detected,
                "constraint_dimensions_configured": _configured_mandatory_dimensions(paths),
                "asset_types": len(graph_doc.get("asset_types", {})),
                "transitions": len(graph_doc.get("transitions", [])),
                "workspace_scope": scope_info["scope"],
                "workspace_scope_warning": bool(scope_info["warning"]),
            },
        )
        projections = write_projections(paths)

    warnings = [scope_info["warning"]] if scope_info["warning"] else []
    return {
        "workspace_root": str(paths.workspace_root),
        "workspace_scope": scope_info["scope"],
        "warnings": warnings,
        "recommended_project_root": str(scope_info["recommended_project_root"]),
        "project_constraints": str(paths.project_constraints_path),
        "context_manifest": str(paths.context_manifest_path),
        "intent_path": str(paths.intent_path),
        "adr_template": str(adr_template_path),
        "status_file": str(paths.status_file),
        "feature_index_file": str(paths.feature_index_path),
        "active_tasks_file": str(paths.active_tasks_file),
        "status_markdown": projections["status_markdown"],
        "init_run_id": init_event["run"]["runId"] if init_event else existing_init.raw.get("run", {}).get("runId"),
    }


def gen_status(project_root: Path, *, feature: str | None = None, health: bool = False) -> dict:
    """Render and persist the current status projection."""

    paths = RuntimePaths(project_root)
    state = detect_state(paths)
    status_markdown = ""
    if paths.workspace_root.exists():
        status_markdown = _write_status(paths)
    features = []
    if paths.workspace_root.exists():
        features = [doc.get("feature") for doc, _ in iter_features(paths)]
    return {
        "state": state,
        "feature": feature,
        "status_file": str(paths.status_file),
        "status_markdown": status_markdown,
        "features": features,
        "health": render_health_summary(paths) if health and paths.workspace_root.exists() else {},
        "active_tasks_file": str(paths.active_tasks_file),
        "feature_index_file": str(paths.feature_index_path),
    }


def gen_trace(
    project_root: Path,
    *,
    req_key: str,
    direction: str = "both",
) -> dict:
    """Reconstruct a cross-artifact trace for one requirement key."""

    if direction not in {"forward", "backward", "both"}:
        raise ValueError(f"Unsupported trace direction: {direction}")
    paths = bootstrap_workspace(project_root)
    report = build_trace_report(paths, req_key, direction=direction)
    return report


def gen_iterate(
    project_root: Path,
    *,
    feature: str,
    edge: str,
    profile: str | None = None,
    title: str | None = None,
    project_name: str | None = None,
    delta: int | None = None,
    converged: bool | None = None,
    evaluators: Iterable[dict] | None = None,
    artifact_paths: Iterable[str] | None = None,
    run_agent: bool = False,
    run_deterministic: bool = False,
    actor: str = "codex-runtime",
) -> dict:
    """Execute one minimal iteration and update projections."""

    paths = bootstrap_workspace(project_root, project_name=project_name)
    feature_doc, feature_path = load_feature(paths, feature)
    constraints = load_project_constraints(paths)
    default_profile = constraints.get("project", {}).get("default_profile", "standard")
    profile_name = profile or (feature_doc or {}).get("profile") or default_profile
    required_evaluator_types = _required_evaluator_types(paths, profile_name, edge)
    human_required = "human" in required_evaluator_types
    if feature_doc is None:
        feature_doc = default_feature_document(paths, feature_id=feature, profile_name=profile_name, title=title)

    iteration = next_iteration(feature_doc, edge)
    auto_infer_evaluators = (
        evaluators is None
        and delta is None
        and converged is None
        and not run_agent
        and not run_deterministic
    )
    if evaluators is None and (run_agent or run_deterministic or auto_infer_evaluators):
        evaluator_details = []
        if run_agent or (auto_infer_evaluators and "agent" in required_evaluator_types):
            evaluator_details.extend(run_agent_checks(paths, edge, feature=feature))
        if run_deterministic or (auto_infer_evaluators and "deterministic" in required_evaluator_types):
            evaluator_details.extend(run_deterministic_checks(paths, edge))
        if evaluator_details:
            evaluators = evaluator_details
            delta = sum(
                1 for item in evaluator_details
                if item.get("required") and item.get("result") == "fail"
            )
            if converged is None:
                converged = delta == 0
    if converged is None:
        converged = delta == 0 if delta is not None else False
    if delta is None:
        delta = 0 if converged else 1
    evaluator_details = list(evaluators or [])
    if human_required and delta == 0 and not any(item.get("type") == "human" for item in evaluator_details):
        evaluator_details.append(
            {
                "name": "human_review",
                "type": "human",
                "result": "pending",
                "required": True,
            }
        )
        converged = False
    evaluator_summary = _summarize_evaluators(evaluator_details, delta=delta, converged=converged)
    timestamp = utc_now()
    context_hash = compute_context_hash(paths, profile_name, feature_doc)
    artifact_refs = _artifact_refs(paths.project_root, artifact_paths)
    project = _project_name(paths, fallback=project_name)

    started = append_run_event(
        paths.events_file,
        project_name=project,
        semantic_type="IterationStarted",
        actor=actor,
        feature=feature,
        edge=edge,
        payload={
            "feature": feature,
            "edge": edge,
            "iteration": iteration,
            "input_hash": context_hash,
            "candidate_artifacts": artifact_refs,
        },
        event_time=timestamp,
    )

    status = "pending_review" if human_required and delta == 0 else ("converged" if converged else "iterating")
    completed = append_run_event(
        paths.events_file,
        project_name=project,
        semantic_type="IterationCompleted",
        actor=actor,
        feature=feature,
        edge=edge,
        payload={
            "feature": feature,
            "edge": edge,
            "iteration": iteration,
            "delta": delta,
            "status": status,
            "profile": profile_name,
            "context_hash": context_hash,
            "vector_type": feature_doc.get("vector_type", "feature"),
            "evaluators": evaluator_summary,
            "candidate_artifacts": artifact_refs,
        },
        causation_id=started["run"]["runId"],
        correlation_id=started["run"]["runId"],
        parent_run_id=started["run"]["runId"],
    )

    feature_doc = update_feature_for_iteration(
        feature_doc,
        edge=edge,
        iteration=iteration,
        status=status,
        context_hash=context_hash,
        evaluators=evaluator_summary,
        timestamp=timestamp,
        profile_name=profile_name,
        delta=delta,
        artifact_refs=artifact_refs,
    )

    graph_doc = load_graph(paths)
    profile_doc = load_profile(paths, profile_name)
    if status == "converged" and feature_is_done(feature_doc, profile_doc, graph_doc):
        feature_doc["status"] = "converged"
        completed_path = paths.completed_features_dir / feature_path.name
        dump_yaml(completed_path, feature_doc)
        if feature_path.exists() and feature_path != completed_path:
            feature_path.unlink(missing_ok=True)
        feature_path = completed_path
    else:
        dump_yaml(paths.active_features_dir / feature_path.name, feature_doc)
        feature_path = paths.active_features_dir / feature_path.name

    convergence_event = None
    if status == "converged":
        convergence_event = append_run_event(
            paths.events_file,
            project_name=project,
            semantic_type="ConvergenceAchieved",
            actor=actor,
            feature=feature,
            edge=edge,
            payload={
                "feature": feature,
                "edge": edge,
                "iteration": iteration,
                "delta": delta,
                "status": "converged",
            },
            causation_id=completed["run"]["runId"],
            correlation_id=started["run"]["runId"],
            parent_run_id=completed["run"]["runId"],
        )

    stuck = detect_stuck_features(load_events(paths.events_file))
    intent_event = None
    if not converged and (feature, edge) in stuck:
        intent_payload = resolve_named_intent_payload(
            paths,
            signal_source="test_failure",
            feature=feature,
            edge=edge,
            affected_req_keys=[feature],
        )
        intent_event = append_run_event(
            paths.events_file,
            project_name=project,
            semantic_type="intent_raised",
            actor=actor,
            feature=feature,
            edge=edge,
            payload={
                "feature": feature,
                "edge": edge,
                "iteration": iteration,
                "signal_source": "test_failure",
                "delta": delta,
                "trigger": f"{edge} delta={delta} unchanged for 3 iterations",
                "severity": "medium",
                **intent_payload,
            },
            causation_id=completed["run"]["runId"],
            correlation_id=started["run"]["runId"],
            parent_run_id=completed["run"]["runId"],
        )

    status_markdown = _write_status(paths)
    return {
        "feature": feature,
        "edge": edge,
        "iteration": iteration,
        "delta": delta,
        "converged": status == "converged",
        "status": status,
        "feature_path": str(feature_path),
        "status_file": str(paths.status_file),
        "events_file": str(paths.events_file),
        "start_run_id": started["run"]["runId"],
        "completed_run_id": completed["run"]["runId"],
        "convergence_run_id": convergence_event["run"]["runId"] if convergence_event else None,
        "intent_run_id": intent_event["run"]["runId"] if intent_event else None,
        "status_markdown": status_markdown,
        "project": project,
        "active_tasks_file": str(paths.active_tasks_file),
        "feature_index_file": str(paths.feature_index_path),
        "evaluator_summary": evaluator_summary,
        "artifact_refs": artifact_refs,
    }


def gen_checkpoint(
    project_root: Path,
    *,
    message: str = "",
    actor: str = "codex-runtime",
) -> dict:
    """Create a reproducible workspace checkpoint and emit an event."""

    paths = bootstrap_workspace(project_root)
    manifest = build_context_manifest(paths)
    dump_yaml(paths.context_manifest_path, manifest)

    git_ref = current_git_ref(paths.project_root)
    snapshot = build_checkpoint_snapshot(
        paths,
        context_hash=manifest["aggregate_hash"],
        message=message or "Checkpoint created",
        git_ref=git_ref,
    )
    timestamp_token = snapshot["timestamp"].replace(":", "").replace("-", "").replace(".", "")
    snapshot_path = paths.snapshots_dir / f"snapshot-{timestamp_token}.yml"
    dump_yaml(snapshot_path, snapshot)

    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="checkpoint_created",
        actor=actor,
        feature="checkpoint",
        edge="checkpoint",
        payload={
            "context_hash": manifest["aggregate_hash"],
            "feature_count": len(snapshot["feature_states"]),
            "git_ref": git_ref,
            "message": snapshot["message"],
            "snapshot_path": str(snapshot_path.relative_to(paths.project_root)),
        },
    )
    status_markdown = _write_status(paths)
    return {
        "context_manifest_path": str(paths.context_manifest_path),
        "context_hash": manifest["aggregate_hash"],
        "snapshot": snapshot,
        "snapshot_path": str(snapshot_path),
        "checkpoint_run_id": event["run"]["runId"],
        "status_markdown": status_markdown,
    }


def gen_review(
    project_root: Path,
    *,
    feature: str,
    edge: str | None = None,
    decision: str,
    feedback: str = "",
    actor: str = "human",
) -> dict:
    """Record a human review decision for the current feature edge."""

    paths = RuntimePaths(project_root)
    if decision not in {"approved", "rejected", "refined"}:
        raise ValueError(f"Unsupported review decision: {decision}")
    feature_doc, feature_path = load_feature(paths, feature)
    if feature_doc is None:
        raise FileNotFoundError(f"Feature not found: {feature}")
    review_edge = edge or _current_edge_for_feature(paths, feature_doc)
    latest = _latest_iteration_event(paths, feature, review_edge)
    if latest is None:
        raise ValueError(f"No iteration to review for {feature} on {review_edge}")

    all_pass = latest.delta == 0 and decision == "approved"
    review_event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="review_completed",
        actor=actor,
        feature=feature,
        edge=review_edge,
        payload={
            "feature": feature,
            "edge": review_edge,
            "iteration": latest.iteration,
            "decision": decision,
            "feedback": feedback,
            "all_evaluators_pass": all_pass,
        },
        causation_id=latest.raw.get("run", {}).get("runId"),
        correlation_id=latest.raw.get("run", {}).get("facets", {}).get("sdlc:universal", {}).get("correlation_id"),
        parent_run_id=latest.raw.get("run", {}).get("runId"),
    )

    for asset in review_edge.replace("↔", "→").split("→"):
        asset = asset.strip()
        trajectory = dict(feature_doc.get("trajectory", {}).get(asset, {}))
        trajectory["human_review"] = {
            "decision": decision,
            "feedback": feedback,
            "timestamp": review_event["eventTime"],
        }
        if decision == "approved" and all_pass:
            trajectory["status"] = "converged"
            trajectory["converged_at"] = review_event["eventTime"]
        elif decision == "rejected":
            trajectory["status"] = "iterating"
        elif decision == "refined":
            trajectory["status"] = "pending_review"
        feature_doc["trajectory"][asset] = trajectory

    if decision == "approved" and all_pass:
        profile_doc = load_profile(paths, feature_doc.get("profile", "standard"))
        graph_doc = load_graph(paths)
        if feature_is_done(feature_doc, profile_doc, graph_doc):
            feature_doc["status"] = "converged"
            destination = paths.completed_features_dir / feature_path.name
            dump_yaml(destination, feature_doc)
            if feature_path.exists() and feature_path != destination:
                feature_path.unlink(missing_ok=True)
            feature_path = destination
        else:
            dump_yaml(feature_path, feature_doc)
        append_run_event(
            paths.events_file,
            project_name=_project_name(paths),
            semantic_type="ConvergenceAchieved",
            actor=actor,
            feature=feature,
            edge=review_edge,
            payload={
                "feature": feature,
                "edge": review_edge,
                "iteration": latest.iteration,
                "delta": 0,
                "status": "converged",
            },
            causation_id=review_event["run"]["runId"],
            correlation_id=latest.raw.get("run", {}).get("facets", {}).get("sdlc:universal", {}).get("correlation_id"),
            parent_run_id=review_event["run"]["runId"],
        )
    else:
        dump_yaml(feature_path, feature_doc)

    status_markdown = _write_status(paths)
    return {
        "feature": feature,
        "edge": review_edge,
        "decision": decision,
        "all_evaluators_pass": all_pass,
        "review_run_id": review_event["run"]["runId"],
        "feature_path": str(feature_path),
        "status_markdown": status_markdown,
    }


def gen_spawn(
    project_root: Path,
    *,
    vector_type: str,
    parent: str,
    reason: str,
    duration: str | None = None,
    parent_edge: str | None = None,
    actor: str = "codex-runtime",
) -> dict:
    """Spawn a child feature vector and optionally block the parent edge."""

    paths = bootstrap_workspace(project_root)
    parent_doc, parent_path = load_feature(paths, parent)
    if parent_doc is None:
        raise FileNotFoundError(f"Parent feature not found: {parent}")
    if parent_doc.get("status") == "converged":
        raise ValueError(f"Cannot spawn child from converged parent: {parent}")

    profile_map = {
        "discovery": ("minimal", None),
        "spike": ("spike", "1 week"),
        "poc": ("poc", "3 weeks"),
        "hotfix": ("hotfix", "4 hours"),
    }
    if vector_type not in profile_map:
        raise ValueError(f"Unsupported vector type: {vector_type}")
    profile_name, default_duration = profile_map[vector_type]
    profile_doc = load_profile(paths, profile_name)
    prefix_map = {
        "discovery": "DISC",
        "spike": "SPIKE",
        "poc": "POC",
        "hotfix": "HOTFIX",
    }
    existing_ids = {doc.get("feature") for doc, _ in iter_features(paths)}
    seq = 1
    child_id = ""
    prefix = prefix_map[vector_type]
    while True:
        child_id = f"REQ-F-{prefix}-{seq:03d}"
        if child_id not in existing_ids:
            break
        seq += 1

    trigger_edge = parent_edge or _current_edge_for_feature(paths, parent_doc) or decide_start_action(paths, feature=parent).edge
    child_doc = default_feature_document(paths, feature_id=child_id, profile_name=profile_name, title=reason[:80])
    child_doc["vector_type"] = vector_type
    child_doc["parent"] = {
        "feature": parent,
        "edge": trigger_edge,
        "reason": reason,
    }
    child_doc["time_box"]["enabled"] = True
    child_doc["time_box"]["duration"] = duration or profile_doc.get("iteration", {}).get("time_box", {}).get("duration") or default_duration
    child_doc["time_box"]["started"] = utc_now()
    child_doc["time_box"]["check_in"] = profile_doc.get("iteration", {}).get("time_box", {}).get("check_in", "none")
    child_doc["time_box"]["on_expiry"] = profile_doc.get("iteration", {}).get("time_box", {}).get("on_expiry", "fold_back")
    child_path = paths.active_features_dir / f"{child_id}.yml"
    dump_yaml(child_path, child_doc)

    parent_doc.setdefault("children", [])
    parent_doc["children"].append(
        {
            "feature": child_id,
            "vector_type": vector_type,
            "status": "pending",
            "fold_back_status": "pending",
            "fold_back_payload": "",
        }
    )
    if trigger_edge:
        for asset in trigger_edge.replace("↔", "→").split("→"):
            asset = asset.strip()
            trajectory = dict(parent_doc.get("trajectory", {}).get(asset, {}))
            trajectory["status"] = "blocked"
            trajectory["blocked_by"] = child_id
            parent_doc["trajectory"][asset] = trajectory
        parent_doc["status"] = "blocked"
    dump_yaml(parent_path, parent_doc)

    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="spawn_created",
        actor=actor,
        feature=parent,
        edge=trigger_edge,
        payload={
            "parent": parent,
            "child": child_id,
            "vector_type": vector_type,
            "reason": reason,
            "time_box": child_doc["time_box"]["duration"],
            "profile": profile_name,
            "triggered_at_edge": trigger_edge,
        },
    )
    status_markdown = _write_status(paths)
    return {
        "parent": parent,
        "child": child_id,
        "profile": profile_name,
        "duration": child_doc["time_box"]["duration"],
        "spawn_run_id": event["run"]["runId"],
        "child_path": str(child_path),
        "status_markdown": status_markdown,
    }


def gen_fold_back(
    project_root: Path,
    *,
    child: str,
    summary: str,
    status: str = "converged",
    actor: str = "codex-runtime",
) -> dict:
    """Fold a child vector back into its parent context."""

    paths = RuntimePaths(project_root)
    child_doc, child_path = load_feature(paths, child)
    if child_doc is None:
        raise FileNotFoundError(f"Child feature not found: {child}")
    parent_id = child_doc.get("parent", {}).get("feature")
    if not parent_id:
        raise ValueError(f"Child feature has no parent: {child}")
    parent_doc, parent_path = load_feature(paths, parent_id)
    if parent_doc is None:
        raise FileNotFoundError(f"Parent feature not found: {parent_id}")

    fold_back_dir = paths.features_root / "fold-back"
    fold_back_dir.mkdir(parents=True, exist_ok=True)
    payload_path = fold_back_dir / f"{child}.md"
    payload_path.write_text(summary.strip() + "\n")

    child_doc["status"] = "converged" if status == "converged" else "time_box_expired"
    terminal_child_path = paths.completed_features_dir / child_path.name
    dump_yaml(terminal_child_path, child_doc)
    if child_path.exists() and child_path != terminal_child_path:
        child_path.unlink(missing_ok=True)
    child_path = terminal_child_path

    for child_entry in parent_doc.get("children", []):
        if child_entry.get("feature") == child:
            child_entry["status"] = child_doc["status"]
            child_entry["fold_back_status"] = "folded_back"
            child_entry["fold_back_payload"] = str(payload_path.relative_to(paths.workspace_root))
    parent_doc.setdefault("context", {})
    parent_doc["context"].setdefault("fold_backs", [])
    parent_doc["context"]["fold_backs"].append(
        {
            "feature": child,
            "status": child_doc["status"],
            "summary_path": str(payload_path.relative_to(paths.workspace_root)),
        }
    )
    blocking_edge = child_doc.get("parent", {}).get("edge")
    if blocking_edge:
        for asset in blocking_edge.replace("↔", "→").split("→"):
            asset = asset.strip()
            trajectory = dict(parent_doc.get("trajectory", {}).get(asset, {}))
            if trajectory.get("blocked_by") == child:
                trajectory.pop("blocked_by", None)
                trajectory["status"] = "iterating"
            parent_doc["trajectory"][asset] = trajectory
        if parent_doc.get("status") == "blocked":
            parent_doc["status"] = "in_progress"
    dump_yaml(parent_path, parent_doc)

    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="spawn_folded_back",
        actor=actor,
        feature=parent_id,
        edge=blocking_edge,
        payload={
            "parent": parent_id,
            "child": child,
            "fold_back_status": status,
            "payload_path": str(payload_path.relative_to(paths.workspace_root)),
        },
    )
    status_markdown = _write_status(paths)
    return {
        "parent": parent_id,
        "child": child,
        "payload_path": str(payload_path),
        "fold_back_run_id": event["run"]["runId"],
        "status_markdown": status_markdown,
    }


def gen_gaps(
    project_root: Path,
    *,
    feature: str | None = None,
    emit_intents: bool = True,
    actor: str = "codex-runtime",
) -> dict:
    """Run traceability validation and emit gap events."""

    paths = bootstrap_workspace(project_root)
    report = build_gap_report(paths, feature=feature)
    project = _project_name(paths)
    gaps_event = append_run_event(
        paths.events_file,
        project_name=project,
        semantic_type="gaps_validated",
        actor=actor,
        feature=feature or "all",
        edge="gap_analysis",
        payload={
            "layers_run": [1, 2, 3],
            "feature": feature or "all",
            "total_req_keys": report["total_req_keys"],
            "full_coverage": len(report["full_coverage"]),
            "partial_coverage": len(report["partial_coverage"]),
            "no_coverage": len(report["no_coverage"]),
            "test_gaps": len(report["test_gaps"]),
            "telemetry_gaps": len(report["telemetry_gaps"]),
            "layer_results": report["layer_results"],
        },
    )

    intent_run_ids = []
    if emit_intents:
        for cluster_key, reqs in sorted(report["gap_clusters"].items()):
            kind, _domain = cluster_key.split(":", 1)
            severity = "high" if kind == "gap" else "medium"
            intent_payload = resolve_named_intent_payload(
                paths,
                signal_source="gap",
                feature=reqs[0],
                edge="gap_analysis",
                affected_req_keys=reqs,
            )
            intent = append_run_event(
                paths.events_file,
                project_name=project,
                semantic_type="intent_raised",
                actor=actor,
                feature=reqs[0],
                edge="gap_analysis",
                payload={
                    "intent_id": f"INT-{len(intent_run_ids) + 1:03d}",
                    "trigger": f"/gen-gaps found {len(reqs)} uncovered REQ keys",
                    "delta": f"{len(reqs)} REQ keys without coverage",
                    "signal_source": "gap",
                    "vector_type": "feature",
                    "affected_req_keys": reqs,
                    "prior_intents": [],
                    "edge_context": "gap_analysis",
                    "severity": severity,
                    **intent_payload,
                },
                causation_id=gaps_event["run"]["runId"],
                correlation_id=gaps_event["run"]["runId"],
                parent_run_id=gaps_event["run"]["runId"],
            )
            intent_run_ids.append(intent["run"]["runId"])

    status_markdown = _write_status(paths)
    return {
        "report": report,
        "gaps_run_id": gaps_event["run"]["runId"],
        "intent_run_ids": intent_run_ids,
        "status_markdown": status_markdown,
    }


def gen_release(
    project_root: Path,
    *,
    version: str,
    dry_run: bool = False,
    actor: str = "codex-runtime",
) -> dict:
    """Create a release manifest and optionally emit a release event."""

    paths = bootstrap_workspace(project_root)
    gap_report = build_gap_report(paths)
    manifest = build_release_manifest(paths, version, gap_report)
    release_dir = paths.project_root / "docs" / "releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = release_dir / f"release-{version}.yml"
    dump_yaml(manifest_path, manifest)

    event = None
    if not dry_run:
        total = gap_report["total_req_keys"]
        coverage_pct = int((len(gap_report["full_coverage"]) / total) * 100) if total else 0
        event = append_run_event(
            paths.events_file,
            project_name=_project_name(paths),
            semantic_type="release_created",
            actor=actor,
            feature="release",
            edge="release",
            payload={
                "version": version,
                "features_included": len(manifest["features_included"]),
                "coverage_pct": coverage_pct,
                "known_gaps": len(manifest["known_gaps"]),
                "context_hash": manifest["context_hash"],
                "git_tag": f"v{version}",
            },
        )
        _write_status(paths)

    return {
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "release_run_id": event["run"]["runId"] if event else None,
        "dry_run": dry_run,
    }


__all__ = [
    "gen_checkpoint",
    "gen_init",
    "gen_fold_back",
    "gen_gaps",
    "gen_iterate",
    "gen_release",
    "gen_review",
    "gen_start",
    "gen_status",
    "gen_spawn",
    "gen_trace",
]
