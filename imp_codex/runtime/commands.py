# Implements: REQ-F-UX-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Thin executable command stubs for the Codex runtime."""

from __future__ import annotations

from datetime import timedelta
import hashlib
from pathlib import Path
import re
from typing import Iterable

from .behaviors import (
    apply_review_behavior,
    resolve_candidate_artifact_behavior,
    resolve_iteration_evaluation_behavior,
)
from .consensus import (
    VALID_DISPOSITIONS,
    VALID_QUORUMS,
    VALID_RECOVERY_PATHS,
    VALID_VERDICTS,
    current_cycle,
    format_timestamp,
    next_comment_id,
    next_cycle_id,
    next_review_id,
    parse_timestamp,
    payload_for,
    quorum_state,
    review_events,
)
from .events import append_run_event, load_events, utc_now
from .edge_runner import DispatchTarget, run_edge
from .fp_supervisor import scan_pending_fp_runs
from .intents import resolve_affected_features, resolve_named_intent_payload
from .paths import RuntimePaths, bootstrap_workspace, detect_workspace_scope
from .projections import (
    blocked_feature_details,
    compute_context_hash,
    decide_start_action,
    default_feature_document,
    detect_state,
    detect_stuck_features,
    determine_next_edge,
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


INTENT_ID_RE = re.compile(r"^INT-(\d+)$")


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


def _resolve_consensus_roster(roster: Iterable[str] | str) -> list[dict]:
    """Normalize a roster input into ``[{id, type}, ...]`` entries."""

    entries: list[str]
    if isinstance(roster, str):
        entries = [part.strip() for part in roster.split(",")]
    else:
        entries = [str(part).strip() for part in roster]
    normalized: list[dict] = []
    for entry in entries:
        if not entry:
            continue
        if entry.startswith("human:"):
            participant_id = entry.split(":", 1)[1].strip()
            participant_type = "human"
        elif entry.startswith("agent:"):
            participant_id = entry.split(":", 1)[1].strip()
            participant_type = "agent"
        else:
            participant_id = entry
            participant_type = "agent" if entry.startswith("gen-") else "human"
        if not participant_id:
            continue
        normalized.append({"id": participant_id, "type": participant_type})
    if not normalized:
        raise ValueError("roster must not be empty")
    return normalized


def _consensus_cycle_or_raise(paths: RuntimePaths, review_id: str) -> tuple[list, dict]:
    events = load_events(paths.events_file)
    cycle = current_cycle(events, review_id)
    if cycle is None:
        raise FileNotFoundError(f"Review not found: {review_id}")
    return events, cycle


def _payload_facet(event) -> dict:
    return event.raw.get("run", {}).get("facets", {}).get("sdlc:payload", {}) or {}


def _intent_events(paths: RuntimePaths, *, intent_id: str | None = None) -> list:
    events = load_events(paths.events_file)
    selected = []
    for event in events:
        if event.semantic_type != "IntentRaised":
            continue
        payload = _payload_facet(event)
        if intent_id and payload.get("intent_id") != intent_id:
            continue
        selected.append(event)
    return selected


def _handled_intent_pairs(paths: RuntimePaths) -> set[tuple[str, str]]:
    handled: set[tuple[str, str]] = set()
    for event in load_events(paths.events_file):
        if event.semantic_type != "IterationStarted":
            continue
        payload = _payload_facet(event)
        intent_id = str(payload.get("intent_id", "")).strip()
        feature_id = str(payload.get("feature", "")).strip() or (event.feature or "")
        if intent_id and feature_id:
            handled.add((intent_id, feature_id))
    return handled


def _ensure_dispatch_feature(paths: RuntimePaths, feature_id: str) -> tuple[dict, Path]:
    feature_doc, feature_path = load_feature(paths, feature_id)
    if feature_doc is not None:
        return feature_doc, feature_path
    if not feature_id.startswith("REQ-F-"):
        raise FileNotFoundError(f"No feature vector found for dispatch target: {feature_id}")
    default_profile = load_project_constraints(paths).get("project", {}).get("default_profile", "standard")
    feature_doc = default_feature_document(paths, feature_id=feature_id, profile_name=default_profile)
    dump_yaml(feature_path, feature_doc)
    return feature_doc, feature_path


def _context_manifest_template() -> dict:
    return {
        "version": "1.0.0",
        "generated_at": utc_now(),
        "algorithm": "sha256-canonical-v1",
        "aggregate_hash": "pending",
        "entries": [],
    }


def _workspace_rel(paths: RuntimePaths, path: Path) -> str:
    return str(path.relative_to(paths.workspace_root))


def _consensus_cycle_dir(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    cycle_dir = paths.consensus_reviews_dir / review_id / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    return cycle_dir


def _consensus_review_path(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    return _consensus_cycle_dir(paths, review_id, cycle_id) / "review.yml"


def _consensus_comment_path(paths: RuntimePaths, review_id: str, cycle_id: str, comment_id: str) -> Path:
    comments_dir = _consensus_cycle_dir(paths, review_id, cycle_id) / "comments"
    comments_dir.mkdir(parents=True, exist_ok=True)
    return comments_dir / f"{comment_id}.md"


def _consensus_disposition_path(paths: RuntimePaths, review_id: str, cycle_id: str, comment_id: str) -> Path:
    dispositions_dir = _consensus_cycle_dir(paths, review_id, cycle_id) / "dispositions"
    dispositions_dir.mkdir(parents=True, exist_ok=True)
    return dispositions_dir / f"{comment_id}.yml"


def _consensus_vote_path(paths: RuntimePaths, review_id: str, cycle_id: str, participant: str) -> Path:
    votes_dir = _consensus_cycle_dir(paths, review_id, cycle_id) / "votes"
    votes_dir.mkdir(parents=True, exist_ok=True)
    safe_participant = re.sub(r"[^A-Za-z0-9._-]+", "-", participant).strip("-") or "participant"
    return votes_dir / f"{safe_participant}.yml"


def _consensus_outcome_path(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    return _consensus_cycle_dir(paths, review_id, cycle_id) / "outcome.yml"


def _consensus_recovery_path(paths: RuntimePaths, review_id: str, cycle_id: str) -> Path:
    return _consensus_cycle_dir(paths, review_id, cycle_id) / "recovery.yml"


def _write_consensus_review_record(
    paths: RuntimePaths,
    *,
    payload: dict,
    requested_run_id: str | None = None,
    review_path: Path | None = None,
) -> Path:
    path = review_path or _consensus_review_path(paths, payload["review_id"], payload["cycle_id"])
    review_doc = dict(payload)
    review_doc["status"] = "open"
    if requested_run_id:
        review_doc["requested_run_id"] = requested_run_id
    dump_yaml(path, review_doc)
    return path


def _write_consensus_comment_record(
    paths: RuntimePaths,
    *,
    review_id: str,
    cycle_id: str,
    comment_id: str,
    participant: str,
    content: str,
    gating: bool,
    asset_version: str,
    comment_run_id: str | None = None,
    comment_path: Path | None = None,
) -> Path:
    path = comment_path or _consensus_comment_path(paths, review_id, cycle_id, comment_id)
    lines = [
        "# Consensus Comment",
        "",
        f"- review_id: {review_id}",
        f"- cycle_id: {cycle_id}",
        f"- comment_id: {comment_id}",
        f"- participant: {participant}",
        f"- gating: {str(gating).lower()}",
        f"- asset_version: {asset_version}",
    ]
    if comment_run_id:
        lines.append(f"- comment_run_id: {comment_run_id}")
    lines.extend(["", content.strip(), ""])
    path.write_text("\n".join(lines))
    return path


def _write_consensus_disposition_record(
    paths: RuntimePaths,
    *,
    review_id: str,
    cycle_id: str,
    comment_id: str,
    original_participant: str,
    disposition: str,
    rationale: str,
    material_change: bool,
    disposition_run_id: str | None = None,
    disposition_path: Path | None = None,
) -> Path:
    path = disposition_path or _consensus_disposition_path(paths, review_id, cycle_id, comment_id)
    dump_yaml(
        path,
        {
            "review_id": review_id,
            "cycle_id": cycle_id,
            "comment_id": comment_id,
            "original_participant": original_participant,
            "disposition": disposition,
            "rationale": rationale,
            "material_change": material_change,
            "comment_dispositioned_run_id": disposition_run_id,
        },
    )
    return path


def _write_consensus_vote_record(
    paths: RuntimePaths,
    *,
    review_id: str,
    cycle_id: str,
    participant: str,
    verdict: str,
    rationale: str,
    conditions: list[str],
    counts_toward_quorum: bool,
    vote_run_id: str | None = None,
    vote_path: Path | None = None,
) -> Path:
    path = vote_path or _consensus_vote_path(paths, review_id, cycle_id, participant)
    dump_yaml(
        path,
        {
            "review_id": review_id,
            "cycle_id": cycle_id,
            "participant": participant,
            "verdict": verdict,
            "rationale": rationale,
            "conditions": conditions,
            "counts_toward_quorum": counts_toward_quorum,
            "vote_run_id": vote_run_id,
        },
    )
    return path


def _write_consensus_outcome_record(
    paths: RuntimePaths,
    *,
    state: dict,
    terminal_run_id: str | None = None,
    outcome_path: Path | None = None,
) -> Path:
    path = outcome_path or _consensus_outcome_path(paths, state["review_id"], state["cycle_id"])
    outcome_doc = dict(state)
    if terminal_run_id:
        outcome_doc["terminal_run_id"] = terminal_run_id
    dump_yaml(path, outcome_doc)
    return path


def _write_consensus_recovery_record(
    paths: RuntimePaths,
    *,
    review_id: str,
    cycle_id: str,
    path_choice: str,
    rationale: str,
    recovery_run_id: str | None = None,
    recovery_path: Path | None = None,
) -> Path:
    path = recovery_path or _consensus_recovery_path(paths, review_id, cycle_id)
    dump_yaml(
        path,
        {
            "review_id": review_id,
            "cycle_id": cycle_id,
            "path": path_choice,
            "rationale": rationale,
            "recovery_path_selected_run_id": recovery_run_id,
        },
    )
    return path


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


def _payload_value(event, key: str):
    return event.raw.get("run", {}).get("facets", {}).get("sdlc:payload", {}).get(key)


def _next_intent_id(paths: RuntimePaths) -> str:
    max_seq = 0
    for event in load_events(paths.events_file):
        intent_id = _payload_value(event, "intent_id")
        if not intent_id:
            continue
        match = INTENT_ID_RE.fullmatch(str(intent_id))
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f"INT-{max_seq + 1:03d}"


def _emit_composition_dispatch(
    paths: RuntimePaths,
    *,
    project_name: str,
    actor: str,
    feature: str | None,
    edge: str,
    intent_payload: dict,
    causation_id: str,
    correlation_id: str,
    parent_run_id: str,
) -> dict | None:
    if intent_payload.get("requires_spec_change"):
        return None

    composition = dict(intent_payload.get("composition") or {})
    return append_run_event(
        paths.events_file,
        project_name=project_name,
        semantic_type="composition_dispatched",
        actor=actor,
        feature=feature,
        edge=edge,
        payload={
            "intent_id": intent_payload.get("intent_id"),
            "feature": feature,
            "edge": edge,
            "requires_spec_change": False,
            "composition_name": intent_payload.get("composition_name"),
            "composition_expression": intent_payload.get("composition_expression"),
            "composition": composition,
            "vector_type": intent_payload.get("vector_type", "feature"),
            "affected_features": list(intent_payload.get("affected_features") or []),
            "affected_req_keys": list(intent_payload.get("affected_req_keys") or []),
            "intent_vector": intent_payload.get("intent_vector"),
        },
        causation_id=causation_id,
        correlation_id=correlation_id,
        parent_run_id=parent_run_id,
    )


def _default_spec_paths(paths: RuntimePaths) -> list[str]:
    if not paths.specification_dir.exists():
        return []
    return sorted(
        str(path.relative_to(paths.project_root))
        for path in paths.specification_dir.rglob("*.md")
        if path.is_file()
    )


def _hash_relative_paths(project_root: Path, relative_paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    normalized_paths = sorted(set(relative_paths))
    for relative_path in normalized_paths:
        path = (project_root / relative_path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Spec path not found: {relative_path}")
        digest.update(relative_path.encode("utf-8"))
        digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _find_event_by_semantic_and_intent(
    paths: RuntimePaths,
    *,
    semantic_types: set[str],
    intent_id: str,
):
    for event in reversed(load_events(paths.events_file)):
        if event.semantic_type not in semantic_types:
            continue
        if _payload_value(event, "intent_id") == intent_id or _payload_value(event, "trigger_intent") == intent_id:
            return event
    return None


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
    auto: bool = False,
    max_steps: int = 10,
    run_agent: bool = False,
    run_deterministic: bool = False,
    actor: str = "intent-observer",
) -> dict:
    """Detect state and return the next recommended action."""

    paths = RuntimePaths(project_root)
    recovery = {"scanned": 0, "retries_scheduled": 0, "escalations": 0, "gap_events": 0, "manifests": []}
    if paths.workspace_root.exists():
        recovery_result = scan_pending_fp_runs(project_root, actor=actor)
        recovery = {
            "scanned": recovery_result.scanned,
            "retries_scheduled": recovery_result.retries_scheduled,
            "escalations": recovery_result.escalations,
            "gap_events": recovery_result.gap_events,
            "manifests": recovery_result.manifests,
        }
    decision = decide_start_action(paths, feature=feature, edge=edge)
    result = {
        "state": decision.state,
        "action": decision.action,
        "feature": decision.feature,
        "edge": decision.edge,
        "detail": decision.detail,
        "recovery": recovery,
        "health": render_health_summary(paths) if paths.workspace_root.exists() else {},
        "blocked_features": blocked_feature_details(paths) if paths.workspace_root.exists() else [],
    }
    if not auto:
        return result

    paths = bootstrap_workspace(project_root)
    steps = []
    remaining = max(max_steps, 0)

    while remaining > 0:
        dispatch = gen_dispatch_intents(
            project_root,
            actor=actor,
            max_dispatch=remaining,
            run_agent=run_agent,
            run_deterministic=run_deterministic,
        )
        if dispatch["dispatches"]:
            steps.extend(dispatch["dispatches"])
            remaining -= len(dispatch["dispatches"])
            if remaining <= 0:
                break

        decision = decide_start_action(paths, feature=feature, edge=edge)
        if decision.state != "IN_PROGRESS":
            break

        iterate = gen_iterate(
            project_root,
            feature=decision.feature,
            edge=decision.edge,
            actor=actor,
            run_agent=run_agent,
            run_deterministic=run_deterministic,
        )
        steps.append(
            {
                "kind": "iterate",
                "feature": decision.feature,
                "edge": decision.edge,
                "start_run_id": iterate["start_run_id"],
                "completed_run_id": iterate["completed_run_id"],
                "status": iterate["status"],
            }
        )
        remaining -= 1

    final_decision = decide_start_action(paths, feature=feature, edge=edge)
    result.update(
        {
            "state": final_decision.state,
            "action": final_decision.action,
            "feature": final_decision.feature,
            "edge": final_decision.edge,
            "detail": final_decision.detail,
            "auto": True,
            "steps": steps,
            "steps_executed": len(steps),
        }
    )
    return result


def gen_dispatch_intents(
    project_root: Path,
    *,
    intent_id: str | None = None,
    actor: str = "intent-observer",
    max_dispatch: int = 20,
    run_agent: bool = False,
    run_deterministic: bool = False,
) -> dict:
    """Dispatch unactioned intents into the first unconverged edge per feature."""

    paths = bootstrap_workspace(project_root)
    handled_pairs = _handled_intent_pairs(paths)
    dispatches = []

    for intent_event in _intent_events(paths, intent_id=intent_id):
        payload = _payload_facet(intent_event)
        current_intent_id = str(payload.get("intent_id", "")).strip()
        if not current_intent_id:
            continue
        if payload.get("requires_spec_change") is True:
            continue

        scope = resolve_affected_features(
            paths,
            feature=payload.get("feature") or intent_event.feature,
            affected_features=list(payload.get("affected_features") or []),
            affected_req_keys=list(payload.get("affected_req_keys") or []),
        )
        if scope == ["all"]:
            scoped_features = [
                feature_doc.get("feature")
                for feature_doc, _ in iter_features(paths)
                if feature_doc.get("feature") and feature_doc.get("status") != "converged"
            ]
        else:
            scoped_features = scope

        for feature_id in scoped_features:
            if len(dispatches) >= max_dispatch:
                break
            if (current_intent_id, feature_id) in handled_pairs:
                continue

            try:
                feature_doc, _feature_path = _ensure_dispatch_feature(paths, feature_id)
            except FileNotFoundError:
                continue
            dispatch_edge = determine_next_edge(paths, feature_doc)
            if dispatch_edge is None:
                continue

            edge_run = run_edge(
                DispatchTarget(
                    intent_id=current_intent_id,
                    feature_id=feature_id,
                    edge=dispatch_edge,
                    intent_event=intent_event.raw,
                    feature_vector=feature_doc,
                ),
                project_root,
                paths.events_file,
                project=_project_name(paths),
                actor=actor,
                run_agent=run_agent,
                run_deterministic=run_deterministic,
            )
            handled_pairs.add((current_intent_id, feature_id))
            dispatches.append(
                {
                    "kind": "intent_dispatch",
                    "intent_id": current_intent_id,
                    "feature": feature_id,
                    "edge": dispatch_edge,
                    "edge_started_run_id": edge_run.edge_started_run_id,
                    "iteration_start_run_id": edge_run.iteration_start_run_id,
                    "completed_run_id": edge_run.completed_run_id,
                    "convergence_run_id": edge_run.convergence_run_id,
                    "intent_run_id": edge_run.intent_run_id,
                    "status": edge_run.status,
                    "delta": edge_run.delta,
                    "fp_manifest_path": edge_run.fp_manifest_path,
                }
            )
        if len(dispatches) >= max_dispatch:
            break

    status_markdown = _write_status(paths)
    return {
        "intent_id": intent_id,
        "dispatches": dispatches,
        "dispatched_count": len(dispatches),
        "status_markdown": status_markdown,
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
    intent_id: str | None = None,
) -> dict:
    """Execute one minimal iteration and update projections."""

    paths = bootstrap_workspace(project_root, project_name=project_name)
    feature_doc, feature_path = load_feature(paths, feature)
    constraints = load_project_constraints(paths)
    default_profile = constraints.get("project", {}).get("default_profile", "standard")
    profile_name = profile or (feature_doc or {}).get("profile") or default_profile
    required_evaluator_types = _required_evaluator_types(paths, profile_name, edge)
    if feature_doc is None:
        feature_doc = default_feature_document(paths, feature_id=feature, profile_name=profile_name, title=title)

    iteration = next_iteration(feature_doc, edge)
    evaluation = resolve_iteration_evaluation_behavior(
        paths,
        feature=feature,
        edge=edge,
        required_evaluator_types=required_evaluator_types,
        evaluators=evaluators,
        delta=delta,
        converged=converged,
        run_agent=run_agent,
        run_deterministic=run_deterministic,
    )
    evaluator_details = evaluation["evaluator_details"]
    delta = evaluation["delta"]
    converged = evaluation["converged"]
    human_required = evaluation["human_required"]
    evaluator_summary = _summarize_evaluators(evaluator_details, delta=delta, converged=converged)
    timestamp = utc_now()
    context_hash = compute_context_hash(paths, profile_name, feature_doc)
    construct = resolve_candidate_artifact_behavior(paths.project_root, artifact_paths)
    artifact_refs = construct["artifact_refs"]
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
            "intent_id": intent_id,
            "input_hash": context_hash,
            "candidate_artifacts": artifact_refs,
        },
        event_time=timestamp,
    )

    status = evaluation["status"]
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
            "intent_id": intent_id,
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
        feature_doc["disposition"] = "converged"
        if artifact_refs and not feature_doc.get("produced_asset_ref"):
            feature_doc["produced_asset_ref"] = artifact_refs[0]["path"]
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
                "intent_id": intent_id,
            },
            causation_id=completed["run"]["runId"],
            correlation_id=started["run"]["runId"],
            parent_run_id=completed["run"]["runId"],
        )

    stuck = detect_stuck_features(load_events(paths.events_file))
    intent_event = None
    dispatch_event = None
    if not converged and (feature, edge) in stuck:
        intent_payload = resolve_named_intent_payload(
            paths,
            signal_source="test_failure",
            feature=feature,
            edge=edge,
            affected_features=[feature],
            affected_req_keys=[feature],
        )
        intent_payload.update(
            {
                "intent_id": _next_intent_id(paths),
                "requires_spec_change": False,
                "prior_intents": [],
                "edge_context": edge,
            }
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
        dispatch_event = _emit_composition_dispatch(
            paths,
            project_name=project,
            actor=actor,
            feature=feature,
            edge=edge,
            intent_payload=intent_payload,
            causation_id=intent_event["run"]["runId"],
            correlation_id=started["run"]["runId"],
            parent_run_id=intent_event["run"]["runId"],
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
        "dispatch_run_id": dispatch_event["run"]["runId"] if dispatch_event else None,
        "status_markdown": status_markdown,
        "project": project,
        "active_tasks_file": str(paths.active_tasks_file),
        "feature_index_file": str(paths.feature_index_path),
        "evaluator_summary": evaluator_summary,
        "artifact_refs": artifact_refs,
        "behaviors": {
            "construct": construct,
            "evaluate": {
                "behavior": evaluation["behavior"],
                "required_evaluator_types": evaluation["required_evaluator_types"],
                "human_required": evaluation["human_required"],
                "auto_inferred": evaluation["auto_inferred"],
            },
        },
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

    review = apply_review_behavior(
        feature_doc,
        review_edge=review_edge,
        decision=decision,
        feedback=feedback,
        iteration=latest.iteration,
        latest_delta=latest.delta,
        timestamp=utc_now(),
    )
    feature_doc = review["feature_doc"]
    all_pass = review["all_evaluators_pass"]
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
            "iteration": review["iteration"],
            "decision": decision,
            "feedback": feedback,
            "all_evaluators_pass": all_pass,
        },
        causation_id=latest.raw.get("run", {}).get("runId"),
        correlation_id=latest.raw.get("run", {}).get("facets", {}).get("sdlc:universal", {}).get("correlation_id"),
        parent_run_id=latest.raw.get("run", {}).get("runId"),
    )
    review = apply_review_behavior(
        feature_doc,
        review_edge=review_edge,
        decision=decision,
        feedback=feedback,
        iteration=latest.iteration,
        latest_delta=latest.delta,
        timestamp=review_event["eventTime"],
    )
    feature_doc = review["feature_doc"]

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
        "behaviors": {
            "review": {
                "behavior": review["behavior"],
                "converged": review["converged"],
            },
        },
    }


def gen_propose(
    project_root: Path,
    *,
    title: str,
    trigger: str,
    signal_source: str,
    affected_req_keys: Iterable[str],
    feature: str | None = None,
    edge: str = "spec_change",
    vector_type: str = "feature",
    prior_intents: Iterable[str] | None = None,
    spec_paths: Iterable[str] | None = None,
    actor: str = "codex-runtime",
    causation_id: str | None = None,
    correlation_id: str | None = None,
    parent_run_id: str | None = None,
) -> dict:
    """Raise a spec-changing intent and enter it into the draft proposal queue."""

    paths = bootstrap_workspace(project_root)
    project = _project_name(paths)
    req_keys = list(dict.fromkeys(affected_req_keys))
    if not req_keys:
        raise ValueError("affected_req_keys must not be empty")
    affected_features = resolve_affected_features(
        paths,
        feature=feature or req_keys[0],
        affected_req_keys=req_keys,
    )
    spec_paths_list = list(spec_paths or _default_spec_paths(paths))
    baseline_hash = _hash_relative_paths(paths.project_root, spec_paths_list) if spec_paths_list else None
    intent_id = _next_intent_id(paths)
    prior_intents_list = list(prior_intents or [])

    intent_payload = {
        "intent_id": intent_id,
        "feature": feature or req_keys[0],
        "edge": edge,
        "trigger": trigger,
        "delta": title,
        "signal_source": signal_source,
        "severity": "high",
        "vector_type": vector_type,
        "affected_features": affected_features,
        "affected_req_keys": req_keys,
        "prior_intents": prior_intents_list,
        "edge_context": edge,
        "requires_spec_change": True,
        "composition_name": None,
        "composition_expression": None,
        "composition": None,
        "intent_vector": {
            "source": signal_source,
            "parent": {"feature": feature or req_keys[0], "edge": edge},
            "resolution_level": "feature_set" if len(req_keys) > 1 else "feature",
            "composition_expression": None,
            "profile": "standard",
            "status": "proposed",
        },
    }
    intent_event = append_run_event(
        paths.events_file,
        project_name=project,
        semantic_type="intent_raised",
        actor=actor,
        feature=feature or req_keys[0],
        edge=edge,
        payload=intent_payload,
        causation_id=causation_id,
        correlation_id=correlation_id,
        parent_run_id=parent_run_id,
    )
    proposal_event = append_run_event(
        paths.events_file,
        project_name=project,
        semantic_type="feature_proposal",
        actor=actor,
        feature=feature or req_keys[0],
        edge=edge,
        payload={
            "intent_id": intent_id,
            "requires_spec_change": True,
            "title": title,
            "trigger": trigger,
            "signal_source": signal_source,
            "affected_features": affected_features,
            "affected_req_keys": req_keys,
            "spec_paths": spec_paths_list,
            "baseline_hash": baseline_hash,
            "prior_intents": prior_intents_list + [intent_id],
        },
        causation_id=intent_event["run"]["runId"],
        correlation_id=correlation_id or intent_event["run"]["runId"],
        parent_run_id=intent_event["run"]["runId"],
    )
    status_markdown = _write_status(paths)
    return {
        "intent_id": intent_id,
        "intent_run_id": intent_event["run"]["runId"],
        "feature_proposal_run_id": proposal_event["run"]["runId"],
        "spec_paths": spec_paths_list,
        "baseline_hash": baseline_hash,
        "status_markdown": status_markdown,
    }


def gen_spec_modify(
    project_root: Path,
    *,
    intent_id: str,
    what_changed: Iterable[str],
    affected_req_keys: Iterable[str] | None = None,
    spec_paths: Iterable[str] | None = None,
    spawned_vectors: Iterable[str] | None = None,
    actor: str = "human",
) -> dict:
    """Record a human-approved specification change for a draft proposal."""

    paths = bootstrap_workspace(project_root)
    proposal_event = _find_event_by_semantic_and_intent(
        paths,
        semantic_types={"FeatureProposal", "feature_proposal"},
        intent_id=intent_id,
    )
    if proposal_event is None:
        raise FileNotFoundError(f"No feature_proposal found for intent {intent_id}")

    proposal_payload = proposal_event.raw.get("run", {}).get("facets", {}).get("sdlc:payload", {})
    if proposal_payload.get("requires_spec_change") is not True:
        raise ValueError(f"feature_proposal for {intent_id} is not marked requires_spec_change=true")

    spec_paths_list = list(spec_paths or proposal_payload.get("spec_paths") or _default_spec_paths(paths))
    baseline_hash = proposal_payload.get("baseline_hash")
    if baseline_hash is None and spec_paths_list:
        baseline_hash = _hash_relative_paths(paths.project_root, spec_paths_list)
    new_hash = _hash_relative_paths(paths.project_root, spec_paths_list) if spec_paths_list else None
    if baseline_hash and new_hash and baseline_hash == new_hash:
        raise ValueError("spec_modified requires a spec file change; current hash matches proposal baseline")

    req_keys = list(dict.fromkeys(affected_req_keys or proposal_payload.get("affected_req_keys") or []))
    affected_features = resolve_affected_features(
        paths,
        feature=proposal_payload.get("feature") or proposal_event.feature,
        affected_features=list(proposal_payload.get("affected_features") or []),
        affected_req_keys=req_keys,
    )
    prior_intents = list(dict.fromkeys(proposal_payload.get("prior_intents") or [intent_id]))
    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="spec_modified",
        actor=actor,
        feature=req_keys[0] if req_keys else proposal_event.feature,
        edge="spec_change",
        payload={
            "trigger_intent": intent_id,
            "intent_id": intent_id,
            "signal_source": proposal_payload.get("signal_source", "source_finding"),
            "what_changed": list(what_changed),
            "affected_features": affected_features,
            "affected_req_keys": req_keys,
            "previous_hash": baseline_hash,
            "new_hash": new_hash,
            "spawned_vectors": list(spawned_vectors or []),
            "prior_intents": prior_intents,
            "spec_paths": spec_paths_list,
        },
        causation_id=proposal_event.raw.get("run", {}).get("runId"),
        correlation_id=proposal_event.raw.get("run", {}).get("facets", {}).get("sdlc:universal", {}).get("correlation_id"),
        parent_run_id=proposal_event.raw.get("run", {}).get("runId"),
    )
    status_markdown = _write_status(paths)
    return {
        "intent_id": intent_id,
        "spec_modified_run_id": event["run"]["runId"],
        "previous_hash": baseline_hash,
        "new_hash": new_hash,
        "spec_paths": spec_paths_list,
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
    child_doc["source_kind"] = "parent_spawn"
    child_doc["parent"] = {
        "feature": parent,
        "edge": trigger_edge,
        "reason": reason,
    }
    child_doc["target_asset_type"] = trigger_edge.split("→")[-1].split("↔")[-1].strip() if trigger_edge else ""
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
    child_doc["trigger_event"] = event["run"]["runId"]
    dump_yaml(child_path, child_doc)
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
    child_doc["disposition"] = "converged" if status == "converged" else "blocked_deferred"
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
            "spec_drift_refs": len(report["spec_drift_refs"]),
            "layer_results": report["layer_results"],
        },
    )

    intent_run_ids = []
    dispatch_run_ids = []
    feature_proposal_run_ids = []
    if emit_intents:
        for cluster_key, reqs in sorted(report["gap_clusters"].items()):
            kind, _domain = cluster_key.split(":", 1)
            severity = "high" if kind == "gap" else "medium"
            intent_payload = resolve_named_intent_payload(
                paths,
                signal_source="gap",
                feature=reqs[0],
                edge="gap_analysis",
                affected_features=[feature] if feature else None,
                affected_req_keys=reqs,
            )
            intent_payload.update(
                {
                    "intent_id": _next_intent_id(paths),
                    "requires_spec_change": False,
                    "prior_intents": [],
                    "edge_context": "gap_analysis",
                }
            )
            intent = append_run_event(
                paths.events_file,
                project_name=project,
                semantic_type="intent_raised",
                actor=actor,
                feature=reqs[0],
                edge="gap_analysis",
                payload={
                    "intent_id": intent_payload["intent_id"],
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
            dispatch = _emit_composition_dispatch(
                paths,
                project_name=project,
                actor=actor,
                feature=reqs[0],
                edge="gap_analysis",
                intent_payload=intent_payload,
                causation_id=intent["run"]["runId"],
                correlation_id=gaps_event["run"]["runId"],
                parent_run_id=intent["run"]["runId"],
            )
            if dispatch is not None:
                dispatch_run_ids.append(dispatch["run"]["runId"])
        for cluster_key, reqs in sorted(report["spec_change_clusters"].items()):
            proposal = gen_propose(
                project_root,
                title=f"Specification update required for {len(reqs)} referenced REQ keys",
                trigger=f"/gen-gaps found {len(reqs)} REQ references missing from specification",
                signal_source="spec_drift",
                affected_req_keys=reqs,
                feature=reqs[0],
                edge="gap_analysis",
                prior_intents=[],
                spec_paths=_default_spec_paths(paths),
                actor=actor,
                causation_id=gaps_event["run"]["runId"],
                correlation_id=gaps_event["run"]["runId"],
                parent_run_id=gaps_event["run"]["runId"],
            )
            intent_run_ids.append(proposal["intent_run_id"])
            feature_proposal_run_ids.append(proposal["feature_proposal_run_id"])

    status_markdown = _write_status(paths)
    return {
        "report": report,
        "gaps_run_id": gaps_event["run"]["runId"],
        "intent_run_ids": intent_run_ids,
        "dispatch_run_ids": dispatch_run_ids,
        "feature_proposal_run_ids": feature_proposal_run_ids,
        "status_markdown": status_markdown,
    }


def gen_consensus_open(
    project_root: Path,
    *,
    artifact: str,
    roster: Iterable[str] | str,
    quorum: str = "majority",
    review_id: str | None = None,
    asset_version: str = "v1",
    min_duration_seconds: int = 0,
    review_closes_in: int = 86400,
    abstention_model: str = "neutral",
    min_participation_ratio: float = 0.5,
    actor: str = "local-user",
    event_time: str | None = None,
) -> dict:
    """Open a new CONSENSUS review cycle."""

    paths = bootstrap_workspace(project_root)
    artifact_path = paths.project_root / artifact
    if not artifact_path.exists() or not artifact_path.is_file():
        raise FileNotFoundError(f"Artifact not found: {artifact}")
    if quorum not in VALID_QUORUMS:
        raise ValueError(f"Unsupported quorum threshold: {quorum}")
    if abstention_model not in {"neutral", "counts_against"}:
        raise ValueError(f"Unsupported abstention model: {abstention_model}")
    if not 0 < min_participation_ratio <= 1:
        raise ValueError("min_participation_ratio must be in (0, 1]")
    if min_duration_seconds < 0 or review_closes_in < 0:
        raise ValueError("review windows must be non-negative")

    events = load_events(paths.events_file)
    participant_roster = _resolve_consensus_roster(roster)
    review_id = review_id or next_review_id(events, artifact)
    if review_events(events, review_id):
        raise ValueError(f"Review already exists: {review_id}")

    published_at = parse_timestamp(event_time or utc_now())
    review_closes_at = published_at + timedelta(seconds=review_closes_in)
    min_close_at = published_at + timedelta(seconds=min_duration_seconds)
    if review_closes_at < min_close_at:
        raise ValueError("review_closes_at must be >= published_at + min_duration_seconds")

    cycle_id = next_cycle_id(events, review_id)
    review_path = _consensus_review_path(paths, review_id, cycle_id)
    payload = {
        "review_id": review_id,
        "cycle_id": cycle_id,
        "asset_id": artifact_path.stem,
        "asset_version": asset_version,
        "artifact": artifact,
        "requested_by": actor,
        "published_at": format_timestamp(published_at),
        "review_closes_at": format_timestamp(review_closes_at),
        "min_duration_seconds": int(min_duration_seconds),
        "participants": participant_roster,
        "quorum": quorum,
        "quorum_threshold": quorum,
        "abstention_model": abstention_model,
        "min_participation_ratio": float(min_participation_ratio),
        "review_ref": _workspace_rel(paths, review_path),
    }
    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="consensus_requested",
        actor=actor,
        feature=artifact_path.stem,
        edge="consensus",
        payload=payload,
        event_time=payload["published_at"],
    )
    _write_consensus_review_record(
        paths,
        payload=payload,
        requested_run_id=event["run"]["runId"],
        review_path=review_path,
    )
    status_markdown = _write_status(paths)
    state = quorum_state(load_events(paths.events_file), review_id, cycle_id, now=payload["published_at"])
    return {
        "review_id": review_id,
        "cycle_id": cycle_id,
        "artifact": artifact,
        "participants": participant_roster,
        "quorum_threshold": quorum,
        "published_at": payload["published_at"],
        "review_closes_at": payload["review_closes_at"],
        "consensus_requested_run_id": event["run"]["runId"],
        "review_path": str(review_path),
        "state": state,
        "status_markdown": status_markdown,
    }


def gen_comment(
    project_root: Path,
    *,
    review_id: str,
    content: str,
    participant: str = "local-user",
    actor: str = "local-user",
    event_time: str | None = None,
) -> dict:
    """Record one review comment for the current consensus cycle."""

    if not content.strip():
        raise ValueError("content must not be empty")

    paths = bootstrap_workspace(project_root)
    events, cycle = _consensus_cycle_or_raise(paths, review_id)
    comment_time = parse_timestamp(event_time or utc_now())
    gating = cycle["terminal_event"] is None and comment_time <= parse_timestamp(cycle["review_closes_at"])
    comment_id = next_comment_id(events, review_id, cycle["cycle_id"])
    comment_path = _consensus_comment_path(paths, review_id, cycle["cycle_id"], comment_id)

    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="comment_received",
        actor=actor,
        feature=cycle["asset_id"],
        edge="consensus",
        payload={
            "review_id": review_id,
            "cycle_id": cycle["cycle_id"],
            "comment_id": comment_id,
            "participant": participant,
            "asset_version": cycle["asset_version"],
            "content": content,
            "content_ref": _workspace_rel(paths, comment_path),
            "gating": gating,
        },
        event_time=format_timestamp(comment_time),
    )
    _write_consensus_comment_record(
        paths,
        review_id=review_id,
        cycle_id=cycle["cycle_id"],
        comment_id=comment_id,
        participant=participant,
        content=content,
        gating=gating,
        asset_version=cycle["asset_version"],
        comment_run_id=event["run"]["runId"],
        comment_path=comment_path,
    )
    status_markdown = _write_status(paths)
    state = quorum_state(load_events(paths.events_file), review_id, cycle["cycle_id"], now=event["eventTime"])
    return {
        "review_id": review_id,
        "cycle_id": cycle["cycle_id"],
        "comment_id": comment_id,
        "gating": gating,
        "comment_run_id": event["run"]["runId"],
        "comment_path": str(comment_path),
        "state": state,
        "status_markdown": status_markdown,
    }


def gen_dispose(
    project_root: Path,
    *,
    review_id: str,
    comment_id: str,
    disposition: str,
    rationale: str,
    actor: str = "local-user",
    event_time: str | None = None,
) -> dict:
    """Disposition one gating comment in the active consensus cycle."""

    if disposition not in VALID_DISPOSITIONS:
        raise ValueError(f"Unsupported disposition: {disposition}")
    if not rationale.strip():
        raise ValueError("rationale must not be empty")

    paths = bootstrap_workspace(project_root)
    events, cycle = _consensus_cycle_or_raise(paths, review_id)
    if cycle["terminal_event"] is not None:
        raise ValueError(f"Review cycle is already terminal: {review_id} {cycle['cycle_id']}")

    target_comment = None
    for event in review_events(events, review_id, cycle_id=cycle["cycle_id"]):
        if event.semantic_type != "CommentReceived":
            continue
        payload = payload_for(event)
        if payload.get("comment_id") == comment_id:
            target_comment = payload
            break
    if target_comment is None:
        raise FileNotFoundError(f"Comment not found: {comment_id}")
    if not target_comment.get("gating"):
        raise ValueError(f"Comment is not gating: {comment_id}")
    for event in review_events(events, review_id, cycle_id=cycle["cycle_id"]):
        if event.semantic_type != "CommentDispositioned":
            continue
        if payload_for(event).get("comment_id") == comment_id:
            raise ValueError(f"Comment already dispositioned: {comment_id}")

    disposition_time = format_timestamp(parse_timestamp(event_time or utc_now()))
    disposition_path = _consensus_disposition_path(paths, review_id, cycle["cycle_id"], comment_id)
    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="comment_dispositioned",
        actor=actor,
        feature=cycle["asset_id"],
        edge="consensus",
        payload={
            "review_id": review_id,
            "cycle_id": cycle["cycle_id"],
            "comment_id": comment_id,
            "original_participant": target_comment.get("participant", ""),
            "disposition": disposition,
            "rationale": rationale,
            "response_ref": _workspace_rel(paths, disposition_path),
            "material_change": disposition == "scope_change",
        },
        event_time=disposition_time,
    )
    _write_consensus_disposition_record(
        paths,
        review_id=review_id,
        cycle_id=cycle["cycle_id"],
        comment_id=comment_id,
        original_participant=target_comment.get("participant", ""),
        disposition=disposition,
        rationale=rationale,
        material_change=disposition == "scope_change",
        disposition_run_id=event["run"]["runId"],
        disposition_path=disposition_path,
    )
    spec_event = None
    if disposition == "scope_change":
        spec_event = append_run_event(
            paths.events_file,
            project_name=_project_name(paths),
            semantic_type="spec_modified",
            actor=actor,
            feature=cycle["asset_id"],
            edge="consensus",
            payload={
                "review_id": review_id,
                "cycle_id": cycle["cycle_id"],
                "trigger": "comment_dispositioned scope_change",
                "comment_id": comment_id,
                "rationale": rationale,
            },
            causation_id=event["run"]["runId"],
            correlation_id=event["run"]["runId"],
            parent_run_id=event["run"]["runId"],
            event_time=disposition_time,
        )
    status_markdown = _write_status(paths)
    state = quorum_state(load_events(paths.events_file), review_id, cycle["cycle_id"], now=disposition_time)
    return {
        "review_id": review_id,
        "cycle_id": cycle["cycle_id"],
        "comment_id": comment_id,
        "disposition": disposition,
        "comment_dispositioned_run_id": event["run"]["runId"],
        "spec_modified_run_id": spec_event["run"]["runId"] if spec_event else None,
        "disposition_path": str(disposition_path),
        "state": state,
        "status_markdown": status_markdown,
    }


def gen_vote(
    project_root: Path,
    *,
    review_id: str,
    verdict: str,
    participant: str = "local-user",
    rationale: str = "",
    conditions: Iterable[str] | None = None,
    actor: str = "local-user",
    event_time: str | None = None,
    gating: bool = False,
) -> dict:
    """Cast a vote in the active consensus cycle."""

    if verdict not in VALID_VERDICTS:
        raise ValueError(f"Unsupported verdict: {verdict}")

    paths = bootstrap_workspace(project_root)
    events, cycle = _consensus_cycle_or_raise(paths, review_id)
    if cycle["terminal_event"] is not None:
        raise ValueError(f"Review cycle is already terminal: {review_id} {cycle['cycle_id']}")

    vote_time = parse_timestamp(event_time or utc_now())
    if vote_time > parse_timestamp(cycle["review_closes_at"]):
        raise ValueError("Review window is closed; reopen the cycle before casting a vote")
    roster_ids = {participant_entry["id"] for participant_entry in cycle["participants"]}
    in_roster = participant in roster_ids
    conditions_list = list(conditions or [])
    vote_path = _consensus_vote_path(paths, review_id, cycle["cycle_id"], participant)

    vote_event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="vote_cast",
        actor=actor,
        feature=cycle["asset_id"],
        edge="consensus",
        payload={
            "review_id": review_id,
            "cycle_id": cycle["cycle_id"],
            "participant": participant,
            "asset_version": cycle["asset_version"],
            "verdict": verdict,
            "rationale": rationale,
            "conditions": conditions_list,
            "counts_toward_quorum": in_roster,
            "vote_ref": _workspace_rel(paths, vote_path),
        },
        event_time=format_timestamp(vote_time),
    )
    _write_consensus_vote_record(
        paths,
        review_id=review_id,
        cycle_id=cycle["cycle_id"],
        participant=participant,
        verdict=verdict,
        rationale=rationale,
        conditions=conditions_list,
        counts_toward_quorum=in_roster,
        vote_run_id=vote_event["run"]["runId"],
        vote_path=vote_path,
    )
    comment_event = None
    comment_path = None
    if gating and rationale.strip():
        comment_id = next_comment_id(load_events(paths.events_file), review_id, cycle["cycle_id"])
        comment_path = _consensus_comment_path(paths, review_id, cycle["cycle_id"], comment_id)
        comment_event = append_run_event(
            paths.events_file,
            project_name=_project_name(paths),
            semantic_type="comment_received",
            actor=actor,
            feature=cycle["asset_id"],
            edge="consensus",
            payload={
                "review_id": review_id,
                "cycle_id": cycle["cycle_id"],
                "comment_id": comment_id,
                "participant": participant,
                "asset_version": cycle["asset_version"],
                "content": rationale,
                "content_ref": _workspace_rel(paths, comment_path),
                "gating": True,
            },
            causation_id=vote_event["run"]["runId"],
            correlation_id=vote_event["run"]["runId"],
            parent_run_id=vote_event["run"]["runId"],
            event_time=format_timestamp(vote_time),
        )
        _write_consensus_comment_record(
            paths,
            review_id=review_id,
            cycle_id=cycle["cycle_id"],
            comment_id=comment_id,
            participant=participant,
            content=rationale,
            gating=True,
            asset_version=cycle["asset_version"],
            comment_run_id=comment_event["run"]["runId"],
            comment_path=comment_path,
        )
    status_markdown = _write_status(paths)
    state = quorum_state(load_events(paths.events_file), review_id, cycle["cycle_id"], now=vote_event["eventTime"])
    return {
        "review_id": review_id,
        "cycle_id": cycle["cycle_id"],
        "participant": participant,
        "verdict": verdict,
        "counts_toward_quorum": in_roster,
        "vote_run_id": vote_event["run"]["runId"],
        "vote_path": str(vote_path),
        "comment_run_id": comment_event["run"]["runId"] if comment_event else None,
        "comment_path": str(comment_path) if comment_path else None,
        "state": state,
        "status_markdown": status_markdown,
    }


def gen_consensus_status(
    project_root: Path,
    *,
    review_id: str,
    cycle_id: str | None = None,
    now: str | None = None,
) -> dict:
    """Project current consensus review state without mutating it."""

    paths = bootstrap_workspace(project_root)
    state = quorum_state(load_events(paths.events_file), review_id, cycle_id, now=now)
    return state


def gen_consensus_close(
    project_root: Path,
    *,
    review_id: str,
    cycle_id: str | None = None,
    actor: str = "consensus-closeout",
    event_time: str | None = None,
) -> dict:
    """Emit the terminal consensus outcome for a review if projection is terminal."""

    paths = bootstrap_workspace(project_root)
    close_time = event_time or utc_now()
    state = quorum_state(load_events(paths.events_file), review_id, cycle_id, now=close_time)
    if state["terminal_run_id"] is not None:
        return {
            "review_id": review_id,
            "cycle_id": state["cycle_id"],
            "outcome": state["outcome"],
            "emitted": False,
            "terminal_run_id": state["terminal_run_id"],
            "state": state,
        }
    if state["outcome"] == "deferred":
        return {
            "review_id": review_id,
            "cycle_id": state["cycle_id"],
            "outcome": "deferred",
            "emitted": False,
            "terminal_run_id": None,
            "state": state,
        }

    semantic_type = "consensus_reached" if state["outcome"] == "passed" else "consensus_failed"
    outcome_path = _consensus_outcome_path(paths, state["review_id"], state["cycle_id"])
    payload = {
        "review_id": state["review_id"],
        "cycle_id": state["cycle_id"],
        "asset_id": state["asset_id"],
        "asset_version": state["asset_version"],
        "approve_votes": state["approve_votes"],
        "reject_votes": state["reject_votes"],
        "abstain_votes": state["abstain_votes"],
        "non_response_count": state["non_response_count"],
        "approve_ratio": state["approve_ratio"],
        "participation_ratio": state["participation_ratio"],
        "available_paths": state["available_paths"],
        "outcome_ref": _workspace_rel(paths, outcome_path),
    }
    if semantic_type == "consensus_reached":
        payload["gating_comments_total"] = state["gating_comments_total"]
        payload["gating_comments_dispositioned"] = state["gating_comments_dispositioned"]
    else:
        payload["failure_reason"] = state["failure_reason"]
        payload["gating_comments_undispositioned"] = len(state["gating_comments_remaining"])

    event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type=semantic_type,
        actor=actor,
        feature=state["asset_id"],
        edge="consensus",
        payload=payload,
        event_time=close_time,
    )
    status_markdown = _write_status(paths)
    state = quorum_state(load_events(paths.events_file), review_id, state["cycle_id"], now=close_time)
    _write_consensus_outcome_record(
        paths,
        state=state,
        terminal_run_id=event["run"]["runId"],
        outcome_path=outcome_path,
    )
    return {
        "review_id": review_id,
        "cycle_id": state["cycle_id"],
        "outcome": state["outcome"],
        "emitted": True,
        "terminal_run_id": event["run"]["runId"],
        "outcome_path": str(outcome_path),
        "state": state,
        "status_markdown": status_markdown,
    }


def gen_consensus_recover(
    project_root: Path,
    *,
    review_id: str,
    path: str,
    rationale: str = "",
    review_closes_in: int = 86400,
    actor: str = "local-user",
    event_time: str | None = None,
) -> dict:
    """Select and execute one recovery path for a failed consensus cycle."""

    if path not in VALID_RECOVERY_PATHS:
        raise ValueError(f"Unsupported recovery path: {path}")

    paths = bootstrap_workspace(project_root)
    recovery_time = event_time or utc_now()
    state = quorum_state(load_events(paths.events_file), review_id, now=recovery_time)
    if state["terminal_run_id"] is None or state["outcome"] != "failed":
        raise ValueError(f"Review is not in a recoverable failed state: {review_id}")
    if path not in state["available_paths"]:
        raise ValueError(f"Recovery path {path} is not available for {state['failure_reason']}")
    for event in review_events(load_events(paths.events_file), review_id, cycle_id=state["cycle_id"]):
        if event.semantic_type == "RecoveryPathSelected":
            raise ValueError(f"Recovery path already selected for {review_id} {state['cycle_id']}")

    recovery_path = _consensus_recovery_path(paths, review_id, state["cycle_id"])
    selection_event = append_run_event(
        paths.events_file,
        project_name=_project_name(paths),
        semantic_type="recovery_path_selected",
        actor=actor,
        feature=state["asset_id"],
        edge="consensus",
        payload={
            "review_id": review_id,
            "cycle_id": state["cycle_id"],
            "asset_id": state["asset_id"],
            "path": path,
            "rationale": rationale,
            "recovery_ref": _workspace_rel(paths, recovery_path),
        },
        event_time=recovery_time,
    )
    _write_consensus_recovery_record(
        paths,
        review_id=review_id,
        cycle_id=state["cycle_id"],
        path_choice=path,
        rationale=rationale,
        recovery_run_id=selection_event["run"]["runId"],
        recovery_path=recovery_path,
    )

    reopened = None
    reopened_review_path = None
    if path == "re_open":
        events = load_events(paths.events_file)
        next_cycle = next_cycle_id(events, review_id)
        cycle = current_cycle(events, review_id)
        reopened_review_path = _consensus_review_path(paths, review_id, next_cycle)
        reopened = append_run_event(
            paths.events_file,
            project_name=_project_name(paths),
            semantic_type="review_reopened",
            actor=actor,
            feature=state["asset_id"],
            edge="consensus",
            payload={
                "review_id": review_id,
                "prior_cycle_id": state["cycle_id"],
                "cycle_id": next_cycle,
                "reason": rationale or path,
                "asset_id": state["asset_id"],
                "asset_version": state["asset_version"],
                "artifact": cycle["artifact"] if cycle else "",
                "reopened_by": actor,
                "published_at": recovery_time,
                "review_closes_at": format_timestamp(parse_timestamp(recovery_time) + timedelta(seconds=review_closes_in)),
                "min_duration_seconds": cycle["min_duration_seconds"] if cycle else 0,
                "participants": cycle["participants"] if cycle else [],
                "quorum": cycle["quorum_threshold"] if cycle else "majority",
                "quorum_threshold": cycle["quorum_threshold"] if cycle else "majority",
                "abstention_model": cycle["abstention_model"] if cycle else "neutral",
                "min_participation_ratio": cycle["min_participation_ratio"] if cycle else 0.5,
                "review_ref": _workspace_rel(paths, reopened_review_path),
            },
            causation_id=selection_event["run"]["runId"],
            correlation_id=selection_event["run"]["runId"],
            parent_run_id=selection_event["run"]["runId"],
            event_time=recovery_time,
        )
        _write_consensus_review_record(
            paths,
            payload=payload_for(load_events(paths.events_file)[-1]),
            requested_run_id=reopened["run"]["runId"],
            review_path=reopened_review_path,
        )
    status_markdown = _write_status(paths)
    return {
        "review_id": review_id,
        "path": path,
        "recovery_path_selected_run_id": selection_event["run"]["runId"],
        "review_reopened_run_id": reopened["run"]["runId"] if reopened else None,
        "recovery_path": str(recovery_path),
        "reopened_review_path": str(reopened_review_path) if reopened_review_path else None,
        "state": quorum_state(load_events(paths.events_file), review_id, now=recovery_time),
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
    "gen_comment",
    "gen_consensus_close",
    "gen_consensus_open",
    "gen_consensus_recover",
    "gen_consensus_status",
    "gen_dispatch_intents",
    "gen_dispose",
    "gen_init",
    "gen_fold_back",
    "gen_gaps",
    "gen_iterate",
    "gen_propose",
    "gen_release",
    "gen_review",
    "gen_spec_modify",
    "gen_start",
    "gen_status",
    "gen_spawn",
    "gen_trace",
    "gen_vote",
]
