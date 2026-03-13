# Implements: REQ-ITER-001 (Universal Iterate), REQ-SUPV-003 (Failure Observability), REQ-ROBUST-008 (Session Gap Detection)
"""CLI entry point for the genesis engine.

Usage:
    python -m genesis evaluate --edge "code\u2194unit_tests" --feature "REQ-F-ENGINE-001" --asset path/to/file.py
    python -m genesis run-edge --edge "code\u2194unit_tests" --feature "REQ-F-CALC-001" --asset src/calc.py --max-iterations 5
    python -m genesis construct --edge "intent\u2192requirements" --feature "REQ-F-AUTH-001" --asset spec/INTENT.md --output artifacts/req.md

evaluate: single iteration via iterate_edge() \u2014 same Level 4 events as before.
run-edge: loop until converge/spawn/budget via run_edge() \u2014 enables CLI spawn.
construct: construct + evaluate in one call \u2014 F_P builds, F_D gates (ADR-020).

The engine evaluates an asset against an edge's checklist and emits Level 4 events.
The LLM agent calls this for cross-validation (ADR-019).
"""

import argparse
import json
import sys
from pathlib import Path

from .config_loader import load_yaml
from .engine import EngineConfig, IterationRecord, iterate_edge, run_edge


def _find_workspace(start: Path) -> Path:
    """Walk up from start to find a directory containing .ai-workspace/."""
    current = start.resolve()
    for _ in range(10):
        if (current / ".ai-workspace").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start.resolve()


def _find_constraints(workspace: Path) -> Path:
    """Find project_constraints.yml \u2014 try tenant paths then root."""
    candidates = [
        workspace / ".ai-workspace" / "claude" / "context" / "project_constraints.yml",
        workspace / ".ai-workspace" / "context" / "project_constraints.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # return first even if missing \u2014 error will be clear


def _find_edge_params(workspace: Path) -> Path:
    """Find edge_params directory.

    Search order:
    1. .ai-workspace/graph/edge_params/         - project-local (highest priority)
    2. .ai-workspace/graph/edges/               - legacy alias
    3. genesis/config/edge_params/ (pkg-local)  - installed by gen-setup.py alongside engine
    4. ../.claude-plugin/.../edge_params/       - source dev tree (imp_claude/code/)
    5. workspace/imp_claude/.../edge_params/    - monorepo root fallback
    """
    _pkg_dir = Path(__file__).resolve().parent  # genesis/ package dir
    _module_root = _pkg_dir.parent              # imp_claude/code or .genesis
    candidates = [
        workspace / ".ai-workspace" / "graph" / "edge_params",
        workspace / ".ai-workspace" / "graph" / "edges",
        _pkg_dir / "config" / "edge_params",
        _module_root / ".claude-plugin" / "plugins" / "genesis" / "config" / "edge_params",
        workspace / "imp_claude" / "code" / ".claude-plugin" / "plugins" / "genesis" / "config" / "edge_params",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _find_profiles(workspace: Path) -> Path:
    """Find profiles directory \u2014 try workspace then plugin."""
    candidates = [
        workspace / ".ai-workspace" / "profiles",
        workspace
        / "imp_claude"
        / "code"
        / ".claude-plugin"
        / "plugins"
        / "genesis"
        / "config"
        / "profiles",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _find_graph_topology(workspace: Path) -> Path:
    """Find graph_topology.yml."""
    candidates = [
        workspace / ".ai-workspace" / "graph" / "graph_topology.yml",
        workspace
        / "imp_claude"
        / "code"
        / ".claude-plugin"
        / "plugins"
        / "genesis"
        / "config"
        / "graph_topology.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _emit_command_error(
    workspace: Path, project: str, command: str, category: str, detail: str
) -> None:
    """Emit a command_error event for REQ-SUPV-003 failure observability."""
    from .ol_event import emit_ol_event, make_ol_event

    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    try:
        emit_ol_event(
            events_path,
            make_ol_event(
                "CommandError",
                command,
                project or workspace.name,
                workspace.name,
                "genesis-cli",
                payload={
                    "command": command,
                    "error_category": category,
                    "error_detail": detail,
                },
            ),
        )
    except Exception:
        pass  # Observation failure must not block error reporting


def _check_session_gaps(workspace: Path, project: str) -> None:
    """Detect and emit events for abandoned iterations (REQ-ROBUST-008).

    Scans the event log for edge_started events with no subsequent completion.
    Emits iteration_abandoned events for each detected gap. Idempotent.
    """
    from .ol_event import emit_ol_event, make_ol_event
    from .workspace_state import detect_abandoned_iterations, load_events

    events = load_events(workspace)
    abandoned = detect_abandoned_iterations(events)

    if not abandoned:
        return

    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    for gap in abandoned:
        try:
            emit_ol_event(
                events_path,
                make_ol_event(
                    "IterationAbandoned",
                    gap["edge"],
                    project,
                    gap["feature"],
                    "genesis-cli",
                    payload={
                        "feature": gap["feature"],
                        "edge": gap["edge"],
                        "last_event_timestamp": gap["last_event_timestamp"],
                    },
                ),
            )
        except Exception:
            pass  # Observation failure must not block engine startup

    print(
        f"genesis: detected {len(abandoned)} abandoned iteration(s) from prior session",
        file=sys.stderr,
    )


# \u2500\u2500 Shared helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


_EDGE_MAP = {
    "code\u2194unit_tests": "tdd",
    "design\u2192test_cases": "design_tests",
    "design\u2192uat_tests": "bdd",
}


def _load_asset(args: argparse.Namespace, workspace: Path) -> str | None:
    """Load asset content from file or stdin. Returns None on error."""
    if args.asset == "-":
        return sys.stdin.read()
    asset_path = Path(args.asset)
    if not asset_path.exists():
        _emit_command_error(
            workspace,
            "",
            args.command,
            "missing_asset",
            f"Asset not found: {args.asset}",
        )
        print(json.dumps({"error": f"Asset not found: {args.asset}"}), file=sys.stderr)
        return None
    return asset_path.read_text()


def _build_config(args: argparse.Namespace, workspace: Path) -> EngineConfig | None:
    """Build EngineConfig from CLI args. Returns None on error."""
    constraints_path = (
        Path(args.constraints) if args.constraints else _find_constraints(workspace)
    )
    if not constraints_path.exists():
        _emit_command_error(
            workspace,
            "",
            args.command,
            "missing_constraints",
            f"Constraints not found: {constraints_path}",
        )
        print(
            json.dumps({"error": f"Constraints not found: {constraints_path}"}),
            file=sys.stderr,
        )
        return None
    constraints = load_yaml(constraints_path)

    topo_path = _find_graph_topology(workspace)
    graph_topology = load_yaml(topo_path) if topo_path.exists() else {}

    max_iters = getattr(args, "max_iterations", 1)

    return EngineConfig(
        project_name=constraints.get("project", {}).get("name", workspace.name),
        workspace_path=workspace,
        edge_params_dir=_find_edge_params(workspace),
        profiles_dir=_find_profiles(workspace),
        constraints=constraints,
        graph_topology=graph_topology,
        model=args.model,
        max_iterations_per_edge=max_iters,
        claude_timeout=getattr(args, "timeout", 300),
        deterministic_only=getattr(args, "deterministic_only", False),
        fd_timeout=getattr(args, "fd_timeout", 120),
        stall_timeout=getattr(args, "stall_timeout", 60),
        budget_usd=getattr(args, "budget_usd", 2.0),
    )


def _resolve_edge_config(edge: str, edge_params_dir: Path) -> Path | None:
    """Resolve edge name to config file path. Returns None if not found."""
    edge_filename = _EDGE_MAP.get(
        edge, edge.replace("\u2192", "_").replace("\u2194", "_").replace(" ", "")
    )
    edge_config_path = edge_params_dir / f"{edge_filename}.yml"
    if edge_config_path.exists():
        return edge_config_path
    return None


def _format_record(record: IterationRecord) -> dict:
    """Format an IterationRecord as a JSON-serializable dict."""
    ev = record.evaluation
    return {
        "iteration": record.iteration,
        "delta": ev.delta,
        "converged": ev.converged,
        "spawn_requested": ev.spawn_requested,
        "checks": [
            {
                "name": c.name,
                "type": c.check_type,
                "outcome": c.outcome.value,
                "required": c.required,
                "message": c.message[:200] if c.message else "",
            }
            for c in ev.checks
        ],
        "escalations": ev.escalations,
    }


# \u2500\u2500 Commands \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate an asset against an edge's checklist. Emit Level 4 events."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    asset_content = _load_asset(args, workspace)
    if asset_content is None:
        return 1

    config = _build_config(args, workspace)
    if config is None:
        return 1

    _check_session_gaps(workspace, config.project_name)

    edge_config_path = _resolve_edge_config(args.edge, config.edge_params_dir)
    if edge_config_path is None:
        _emit_command_error(
            workspace,
            config.project_name,
            "evaluate",
            "missing_edge_config",
            f"Edge config not found for: {args.edge}",
        )
        print(
            json.dumps({"error": f"Edge config not found for: {args.edge}"}),
            file=sys.stderr,
        )
        return 1

    edge_config = load_yaml(edge_config_path)

    record = iterate_edge(
        edge=args.edge,
        edge_config=edge_config,
        config=config,
        feature_id=args.feature,
        asset_content=asset_content,
        context=args.context or "",
        iteration=args.iteration,
    )

    # Build output \u2014 preserve the same schema callers expect
    formatted = _format_record(record)
    ev = record.evaluation
    passed = sum(1 for c in ev.checks if c.outcome.value == "pass")
    failed = sum(1 for c in ev.checks if c.outcome.value in ("fail", "error"))
    skipped = sum(1 for c in ev.checks if c.outcome.value == "skip")

    output = {
        "edge": args.edge,
        "feature": args.feature,
        "iteration": args.iteration,
        "delta": ev.delta,
        "converged": ev.converged,
        "evaluators": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(ev.checks),
        },
        "checks": formatted["checks"],
        "escalations": ev.escalations,
        "event_emitted": record.event_emitted,
        "source": "engine_cli",
    }

    print(json.dumps(output, indent=2))
    return 0 if ev.converged else 1


def cmd_run_edge(args: argparse.Namespace) -> int:
    """Loop on an edge until converge/spawn/budget. Enables CLI spawn."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    asset_content = _load_asset(args, workspace)
    if asset_content is None:
        return 1

    config = _build_config(args, workspace)
    if config is None:
        return 1

    _check_session_gaps(workspace, config.project_name)

    construct = getattr(args, "construct", False)
    output_file = Path(args.output) if getattr(args, "output", None) else None

    # run_edge does its own edge config file lookup
    profile_path = config.profiles_dir / "standard.yml"
    profile = load_yaml(profile_path) if profile_path.exists() else {}

    records = run_edge(
        edge=args.edge,
        config=config,
        feature_id=args.feature,
        profile=profile,
        asset_content=asset_content,
        context=args.context or "",
        construct=construct,
        output_path=output_file,
    )

    last = records[-1] if records else None
    output = {
        "edge": args.edge,
        "feature": args.feature,
        "total_iterations": len(records),
        "final_delta": last.evaluation.delta if last else -1,
        "converged": last.evaluation.converged if last else False,
        "spawn_requested": last.evaluation.spawn_requested if last else "",
        "iterations": [_format_record(r) for r in records],
    }

    if last and last.evaluation.spawn_requested:
        child_id = last.evaluation.spawn_requested
        output["child_path"] = str(
            config.workspace_path
            / ".ai-workspace"
            / "features"
            / "active"
            / f"{child_id}.yml"
        )

    if last and last.fp_result and not last.fp_result.audit.skipped:
        fp = last.fp_result
        output["fp_actor"] = {
            "transport": fp.audit.transport,
            "converged": fp.converged,
            "cost_usd": fp.cost_usd,
            "duration_ms": fp.duration_ms,
            "artifacts": len(fp.artifacts),
        }

    print(json.dumps(output, indent=2))

    if last and (last.evaluation.converged or last.evaluation.spawn_requested):
        return 0
    return 1


def cmd_construct(args: argparse.Namespace) -> int:
    """Construct + evaluate in one call. F_P builds, F_D gates (ADR-020)."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    asset_content = _load_asset(args, workspace)
    if asset_content is None:
        return 1

    config = _build_config(args, workspace)
    if config is None:
        return 1

    _check_session_gaps(workspace, config.project_name)

    output_file = Path(args.output) if args.output else None

    edge_config_path = _resolve_edge_config(args.edge, config.edge_params_dir)
    if edge_config_path is None:
        _emit_command_error(
            workspace,
            config.project_name,
            "construct",
            "missing_edge_config",
            f"Edge config not found for: {args.edge}",
        )
        print(
            json.dumps({"error": f"Edge config not found for: {args.edge}"}),
            file=sys.stderr,
        )
        return 1

    edge_config = load_yaml(edge_config_path)

    record = iterate_edge(
        edge=args.edge,
        edge_config=edge_config,
        config=config,
        feature_id=args.feature,
        asset_content=asset_content,
        context=args.context or "",
        iteration=args.iteration,
        construct=True,
        output_path=output_file,
    )

    # Build output
    formatted = _format_record(record)
    ev = record.evaluation
    passed = sum(1 for c in ev.checks if c.outcome.value == "pass")
    failed = sum(1 for c in ev.checks if c.outcome.value in ("fail", "error"))
    skipped = sum(1 for c in ev.checks if c.outcome.value == "skip")

    output = {
        "edge": args.edge,
        "feature": args.feature,
        "iteration": args.iteration,
        "delta": ev.delta,
        "converged": ev.converged,
        "evaluators": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(ev.checks),
        },
        "checks": formatted["checks"],
        "escalations": ev.escalations,
        "event_emitted": record.event_emitted,
        "source": "engine_cli",
    }

    if record.fp_result and not record.fp_result.audit.skipped:
        fp = record.fp_result
        output["fp_actor"] = {
            "transport": fp.audit.transport,
            "converged": fp.converged,
            "cost_usd": fp.cost_usd,
            "duration_ms": fp.duration_ms,
            "artifacts": len(fp.artifacts),
        }
        if output_file:
            output["output_path"] = str(output_file)

    print(json.dumps(output, indent=2))
    return 0 if ev.converged else 1




# ── start subcommand ──────────────────────────────────────────────
# Implements: ADR-032 (skills as dispatch surfaces)
# This is the engine-side of the F_P dispatch loop.
# Exit codes:
#   0 — converged or nothing to do
#   2 — fp_dispatched: MCP actor needed; manifest path in JSON stdout
#   3 — fh_required: human gate; surfaces to user
#   1 — error


def cmd_start(args: argparse.Namespace) -> int:
    """State-driven start: find work → run_edge → signal when F_P actor needed.

    This is the engine half of the dispatch loop (ADR-032).
    The skill (gen-iterate / gen-start) is the MCP half — it calls this,
    reads exit code 2, dispatches the actor, then calls this again.
    """
    try:
        import yaml as _yaml
    except ImportError:
        print(json.dumps({"status": "error", "error": "PyYAML required"}))
        return 1

    from .intent_observer import (
        DispatchTarget,
        _get_active_feature_ids,
        _load_feature_vector,
        _select_edge,
        get_pending_dispatches,
    )
    from .edge_runner import run_edge as _run_edge

    workspace = _find_workspace(
        Path(args.workspace) if getattr(args, "workspace", None) else Path.cwd()
    )
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"

    # Project name
    project_name = workspace.name
    constraints_path = _find_constraints(workspace)
    if constraints_path.exists():
        try:
            c = _yaml.safe_load(constraints_path.read_text()) or {}
            pn = c.get("project_name") or (c.get("project") or {}).get("name")
            if pn:
                project_name = pn
        except Exception:
            pass

    # --- Find targets ---------------------------------------------------------
    # 1. Pending intents first (homeostatic loop)
    targets = get_pending_dispatches(workspace)

    # 2. If none, direct feature selection
    if not targets:
        feature_arg = getattr(args, "feature", None)
        edge_arg = getattr(args, "edge", None)
        if feature_arg:
            fv = _load_feature_vector(workspace, feature_arg)
            if fv:
                edge = edge_arg or _select_edge(fv)
                if edge:
                    targets = [DispatchTarget(
                        intent_id="manual",
                        feature_id=feature_arg,
                        edge=edge,
                        feature_vector=fv,
                    )]
        else:
            for fid in _get_active_feature_ids(workspace):
                fv = _load_feature_vector(workspace, fid)
                if not fv:
                    continue
                edge = _select_edge(fv)
                if edge:
                    targets.append(DispatchTarget(
                        intent_id="auto",
                        feature_id=fid,
                        edge=edge,
                        feature_vector=fv,
                    ))

    if not targets:
        print(json.dumps({"status": "nothing_to_do",
                          "message": "No active features with unconverged edges"}))
        return 0

    # --- Process targets ------------------------------------------------------
    auto = getattr(args, "auto", False)

    for target in targets:
        result = _run_edge(
            target=target,
            workspace_root=workspace,
            events_path=events_path,
            project_name=project_name,
        )

        out: dict = {
            "status": result.status,
            "feature": result.feature_id,
            "edge": result.edge,
            "delta": result.delta,
            "iterations": result.iterations,
            "events": result.events_emitted,
        }

        if result.status == "fp_dispatched":
            # Signal to skill: MCP actor needed. Manifest path in output.
            out["fp_manifest_path"] = result.fp_manifest_path
            print(json.dumps(out))
            return 2  # skill reads this, dispatches actor, calls us again

        if result.status == "fh_required":
            out["message"] = "Human gate required — awaiting F_H approval"
            print(json.dumps(out))
            return 3  # skill surfaces gate to user

        if result.status == "evaluator_error":
            out["message"] = f"Evaluator infrastructure error: {result.evaluator_error}"
            print(json.dumps(out))
            return 1

        # converged or stuck
        print(json.dumps(out))

        if result.status == "converged":
            _update_trajectory(workspace, target.feature_id, target.edge, _yaml)

        if result.status != "converged" and not auto:
            return 1

    return 0


def _update_trajectory(workspace: Path, feature_id: str, edge: str, yaml_mod) -> None:
    """Write-back convergence to the feature vector YAML projection.

    The event stream is the source of truth. The feature vector YAML is a
    derived projection. This write-back keeps _select_edge() from re-selecting
    already-converged edges on the next call.
    """
    import datetime
    fv_path = workspace / ".ai-workspace" / "features" / "active" / f"{feature_id}.yml"
    if not fv_path.exists():
        return
    try:
        fv = yaml_mod.safe_load(fv_path.read_text()) or {}
        traj = fv.setdefault("trajectory", {})
        # Trajectory key = target node name (after → or ↔)
        import re as _re
        edge_key = _re.split(r"[→↔]", edge)[-1].strip()
        traj[edge_key] = {
            "status": "converged",
            "converged_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        fv_path.write_text(yaml_mod.dump(fv, default_flow_style=False, allow_unicode=True))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(f"trajectory write-back failed: {exc}")


# ── context subcommand ────────────────────────────────────────────


def cmd_context(args: argparse.Namespace) -> int:
    """Print workspace state for /gen-genesis session bootstrap.

    Reads active feature vectors, recent events, and pending proposals.
    Outputs clean text — no ad-hoc Python required in the command definition.
    """
    import glob

    try:
        import yaml
    except ImportError:
        print("error: PyYAML required (pip install pyyaml)", file=sys.stderr)
        return 1

    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())
    ws = workspace / ".ai-workspace"

    # ── Project name ───────────────────────────────────────────────────────────────────────────
    project_name = workspace.name
    constraints_path = ws / "context" / "project_constraints.yml"
    if constraints_path.exists():
        try:
            c = yaml.safe_load(constraints_path.read_text()) or {}
            project_name = (c.get("project") or {}).get("name") or project_name
        except Exception:
            pass

    # ── Active features ─────────────────────────────────────────────────────────────────────
    EDGE_ORDER = [
        "intent", "requirements", "feature_decomposition",
        "design", "code", "unit_tests", "uat_tests", "cicd",
    ]
    features = []
    for fpath in sorted(glob.glob(str(ws / "features" / "active" / "*.yml"))):
        try:
            d = yaml.safe_load(open(fpath).read())
            if not isinstance(d, dict):
                continue
            fid = d.get("feature", Path(fpath).stem)
            title = d.get("title", "")
            status = d.get("status", "")
            traj = d.get("trajectory") or {}
            current_edge = None
            for edge in EDGE_ORDER:
                entry = traj.get(edge)
                if entry is None:
                    continue
                edge_status = entry.get("status") if isinstance(entry, dict) else str(entry)
                if edge_status != "converged":
                    current_edge = edge
                    break
            # Top-level status is authoritative — a feature marked converged
            # may still have individual edges at "pending" (e.g. uat deferred).
            resolved_edge = "all_converged" if status == "converged" else (current_edge or "all_converged")
            features.append({
                "id": fid, "title": title,
                "status": status,
                "current_edge": resolved_edge,
            })
        except Exception as e:
            print(f"  [warn] skipped {Path(fpath).name}: {e}", file=sys.stderr)

    # ── Completed / events / proposals ──────────────────────────────────────────
    completed = list(glob.glob(str(ws / "features" / "completed" / "*.yml")))

    events_path = ws / "events" / "events.jsonl"
    recent_events: list[str] = []
    if events_path.exists():
        lines = events_path.read_text().splitlines()
        for line in reversed(lines[-20:]):
            try:
                e = json.loads(line)
                recent_events.append(e.get("event_type", ""))
                if len(recent_events) >= 5:
                    break
            except Exception:
                pass
        recent_events.reverse()

    proposals = []
    for ppath in sorted(glob.glob(str(ws / "reviews" / "pending" / "PROP-*.yml"))):
        try:
            p = yaml.safe_load(open(ppath).read()) or {}
            if p.get("status") == "draft":
                proposals.append({
                    "id": p.get("proposal_id", Path(ppath).stem),
                    "severity": p.get("severity", ""),
                    "title": (p.get("title") or "")[:60],
                })
        except Exception:
            pass

    # ── Derive state ─────────────────────────────────────────────────────────────────────────
    total = len(features)
    converged_count = sum(1 for f in features if f["status"] == "converged")
    in_progress = [f for f in features if f["current_edge"] != "all_converged"]
    if in_progress:
        state = "IN_PROGRESS"
    elif converged_count == total and total > 0:
        state = "ALL_CONVERGED"
    else:
        state = "UNKNOWN"

    # ── Output ───────────────────────────────────────────────────────────────────────────────
    print(f"project:     {project_name}")
    print(f"state:       {state}")
    print(f"features:    {converged_count}/{total} converged"
          + (f", {len(in_progress)} in-progress" if in_progress else ""))
    print(f"completed:   {len(completed)}")
    if recent_events:
        print(f"last_events: {', '.join(recent_events)}")
    print()
    if in_progress:
        print("in_progress:")
        for f in in_progress:
            print(f"  {f['id']:<30}  edge={f['current_edge']}  \"{f['title'][:45]}\"")
        print()
    if proposals:
        print("proposals (draft):")
        for p in proposals:
            print(f"  {p['id']}  {p['severity']:<8}  {p['title']}")
        print()
    if not in_progress and not proposals:
        print("ready: all features converged, no pending proposals")
    return 0

# \u2500\u2500 Shared CLI args \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _add_shared_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by evaluate and run-edge."""
    parser.add_argument(
        "--edge", required=True, help="Edge name (e.g., 'code\u2194unit_tests')"
    )
    parser.add_argument(
        "--feature", required=True, help="Feature ID (e.g., 'REQ-F-ENGINE-001')"
    )
    parser.add_argument(
        "--asset", required=True, help="Path to asset file, or '-' for stdin"
    )
    parser.add_argument(
        "--workspace", default=None, help="Workspace root (auto-detected if omitted)"
    )
    parser.add_argument(
        "--constraints", default=None, help="Path to project_constraints.yml"
    )
    parser.add_argument("--context", default="", help="Additional context string")
    parser.add_argument(
        "--model", default="sonnet", help="Model for agent checks (default: sonnet)"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout for agent checks in seconds"
    )
    parser.add_argument(
        "--deterministic-only",
        action="store_true",
        help="Only run F_D checks (skip agent and human). Fast, free, Level 4.",
    )
    parser.add_argument(
        "--fd-timeout",
        type=int,
        default=60,
        help=(
            "Stall timeout for F_D subprocess checks in seconds (default: 60). "
            "Kills the subprocess if it produces NO output for this many seconds. "
            "NOT a wall-clock timeout — a healthy slow process (e.g. long test suite) "
            "will run to completion. Wall ceiling = stall_timeout × 20."
        ),
    )
    parser.add_argument(
        "--stall-timeout",
        type=int,
        default=60,
        help="Stall detection timeout for F_P calls in seconds (default: 60, 0=disable)",
    )
    parser.add_argument(
        "--budget-usd",
        type=float,
        default=2.0,
        dest="budget_usd",
        help="Max spend per construct invocation in USD (default: 2.0)",
    )


def main() -> int:
    # Configure structured logging so req= telemetry tags appear in stderr
    # when the engine is run as a subprocess (not just via caplog in tests).
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        prog="genesis",
        description="Genesis F_D engine \u2014 deterministic evaluation with Level 4 events",
    )
    subparsers = parser.add_subparsers(dest="command")

    # evaluate subcommand
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an asset against an edge's checklist (single iteration)",
    )
    _add_shared_args(eval_parser)
    eval_parser.add_argument(
        "--iteration", type=int, default=1, help="Iteration number for event"
    )

    # run-edge subcommand
    run_parser = subparsers.add_parser(
        "run-edge",
        help="Loop on edge until converge/spawn/budget",
    )
    _add_shared_args(run_parser)
    run_parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations before stopping (default: 10)",
    )
    run_parser.add_argument(
        "--construct",
        action="store_true",
        help="Enable F_P construct before evaluate (ADR-020)",
    )
    run_parser.add_argument(
        "--output",
        default=None,
        help="Path to write constructed artifact",
    )

    # construct subcommand (ADR-020)
    construct_parser = subparsers.add_parser(
        "construct",
        help="Construct artifact + evaluate in one call (F_P builds, F_D gates)",
    )
    _add_shared_args(construct_parser)
    construct_parser.add_argument(
        "--iteration", type=int, default=1, help="Iteration number for event"
    )
    construct_parser.add_argument(
        "--output",
        default=None,
        help="Path to write constructed artifact",
    )

    # context subcommand — session bootstrap for /gen-genesis
    context_parser = subparsers.add_parser(
        "context",
        help="Print workspace state for session bootstrap (/gen-genesis)",
    )
    context_parser.add_argument(
        "--workspace", default=None, help="Workspace root (auto-detected if omitted)"
    )

    # start subcommand — ADR-032 dispatch surface entry point
    start_parser = subparsers.add_parser(
        "start",
        help="State-driven start: find work, run edge_runner, signal when F_P needed",
    )
    start_parser.add_argument("--workspace", default=None, help="Workspace root (auto-detected)")
    start_parser.add_argument("--feature", default=None, help="Override feature selection")
    start_parser.add_argument("--edge", default=None, help="Override edge selection")
    start_parser.add_argument("--auto", action="store_true", help="Loop through all pending targets")
    start_parser.add_argument("--human-proxy", action="store_true", dest="human_proxy",
                              help="Act as F_H proxy at human gates (requires --auto)")

    args = parser.parse_args()

    if args.command == "evaluate":
        return cmd_evaluate(args)
    elif args.command == "run-edge":
        return cmd_run_edge(args)
    elif args.command == "construct":
        return cmd_construct(args)
    elif args.command == "context":
        return cmd_context(args)
    elif args.command == "start":
        return cmd_start(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
