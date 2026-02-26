# Implements: GENESIS_ENGINE_SPEC §6 (Binding Points)
"""CLI entry point for the genesis engine.

Usage:
    python -m genesis_engine evaluate --edge "code↔unit_tests" --feature "REQ-F-001" --asset src/main.py --provider claude
    python -m genesis_engine run-edge --edge "code↔unit_tests" --feature "REQ-F-001" --asset src/main.py --provider gemini
    python -m genesis_engine providers

Key difference from imp_claude: --provider flag selects the F_P implementation.
Default is 'claude', but any registered provider works. Use --deterministic-only
to skip all F_P checks (free, fast, Level 4 only).
"""

import argparse
import json
import sys
from pathlib import Path

from .config_loader import load_yaml
from .engine import EngineConfig, IterationRecord, iterate_edge, run_edge
from .providers import get_provider, list_providers


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
    """Find project_constraints.yml — try tenant paths then root."""
    candidates = [
        workspace / ".ai-workspace" / "context" / "project_constraints.yml",
        workspace / ".ai-workspace" / "claude" / "context" / "project_constraints.yml",
        workspace / ".ai-workspace" / "gemini" / "context" / "project_constraints.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _find_edge_params(workspace: Path) -> Path:
    """Find edge_params directory."""
    candidates = [
        workspace / ".ai-workspace" / "graph" / "edges",
        workspace / ".ai-workspace" / "edge_params",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _find_profiles(workspace: Path) -> Path:
    """Find profiles directory."""
    candidates = [
        workspace / ".ai-workspace" / "profiles",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _find_graph_topology(workspace: Path) -> Path:
    """Find graph_topology.yml."""
    candidates = [
        workspace / ".ai-workspace" / "graph" / "graph_topology.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _emit_command_error(
    workspace: Path, project: str, command: str, category: str, detail: str
) -> None:
    """Emit a command_error event for failure observability."""
    from .fd_emit import emit_event, make_event

    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    try:
        emit_event(
            events_path,
            make_event(
                "command_error",
                project or workspace.name,
                command=command,
                error_category=category,
                error_detail=detail,
            ),
        )
    except Exception:
        pass


_EDGE_MAP = {
    "code↔unit_tests": "tdd",
    "design→test_cases": "design_tests",
    "design→uat_tests": "bdd",
}


def _load_asset(args: argparse.Namespace, workspace: Path) -> str | None:
    """Load asset content from file or stdin."""
    if args.asset == "-":
        return sys.stdin.read()
    asset_path = Path(args.asset)
    if not asset_path.exists():
        _emit_command_error(
            workspace, "", args.command, "missing_asset", f"Asset not found: {args.asset}"
        )
        print(json.dumps({"error": f"Asset not found: {args.asset}"}), file=sys.stderr)
        return None
    return asset_path.read_text()


def _build_config(args: argparse.Namespace, workspace: Path) -> EngineConfig | None:
    """Build EngineConfig from CLI args."""
    constraints_path = (
        Path(args.constraints) if args.constraints else _find_constraints(workspace)
    )
    if not constraints_path.exists():
        _emit_command_error(
            workspace, "", args.command, "missing_constraints",
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

    # Build F_P provider (the pluggable part)
    provider = None
    det_only = getattr(args, "deterministic_only", False)
    if not det_only:
        provider_name = getattr(args, "provider", "claude")
        try:
            provider_kwargs = {"model": getattr(args, "model", "sonnet")}
            provider = get_provider(provider_name, **provider_kwargs)
        except ValueError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return None

    max_iters = getattr(args, "max_iterations", 1)

    return EngineConfig(
        project_name=constraints.get("project", {}).get("name", workspace.name),
        workspace_path=workspace,
        edge_params_dir=_find_edge_params(workspace),
        profiles_dir=_find_profiles(workspace),
        constraints=constraints,
        graph_topology=graph_topology,
        provider=provider,
        max_iterations_per_edge=max_iters,
        deterministic_only=det_only,
        fd_timeout=getattr(args, "fd_timeout", 120),
    )


def _resolve_edge_config(edge: str, edge_params_dir: Path) -> Path | None:
    """Resolve edge name to config file path."""
    edge_filename = _EDGE_MAP.get(
        edge, edge.replace("→", "_").replace("↔", "_").replace(" ", "")
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


# ── Commands ─────────────────────────────────────────────────────────────


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate an asset against an edge's checklist. Emit Level 4 events."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    asset_content = _load_asset(args, workspace)
    if asset_content is None:
        return 1

    config = _build_config(args, workspace)
    if config is None:
        return 1

    edge_config_path = _resolve_edge_config(args.edge, config.edge_params_dir)
    if edge_config_path is None:
        _emit_command_error(
            workspace, config.project_name, "evaluate",
            "missing_edge_config", f"Edge config not found for: {args.edge}",
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

    formatted = _format_record(record)
    ev = record.evaluation
    passed = sum(1 for c in ev.checks if c.outcome.value == "pass")
    failed = sum(1 for c in ev.checks if c.outcome.value in ("fail", "error"))
    skipped = sum(1 for c in ev.checks if c.outcome.value == "skip")

    output = {
        "edge": args.edge,
        "feature": args.feature,
        "iteration": args.iteration,
        "provider": config.provider.name if config.provider else "none",
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
        "source": "genesis_engine_cli",
    }

    print(json.dumps(output, indent=2))
    return 0 if ev.converged else 1


def cmd_run_edge(args: argparse.Namespace) -> int:
    """Loop on an edge until converge/spawn/budget."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    asset_content = _load_asset(args, workspace)
    if asset_content is None:
        return 1

    config = _build_config(args, workspace)
    if config is None:
        return 1

    profile_path = config.profiles_dir / "standard.yml"
    profile = load_yaml(profile_path) if profile_path.exists() else {}

    records = run_edge(
        edge=args.edge,
        config=config,
        feature_id=args.feature,
        profile=profile,
        asset_content=asset_content,
        context=args.context or "",
    )

    last = records[-1] if records else None
    output = {
        "edge": args.edge,
        "feature": args.feature,
        "provider": config.provider.name if config.provider else "none",
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

    print(json.dumps(output, indent=2))

    if last and (last.evaluation.converged or last.evaluation.spawn_requested):
        return 0
    return 1


def cmd_providers(args: argparse.Namespace) -> int:
    """List available F_P providers."""
    providers = list_providers()
    output = {"providers": providers, "count": len(providers)}
    print(json.dumps(output, indent=2))
    return 0


# ── CLI argument parsing ─────────────────────────────────────────────────


def _add_shared_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by evaluate and run-edge."""
    parser.add_argument(
        "--edge", required=True, help="Edge name (e.g., 'code↔unit_tests')"
    )
    parser.add_argument(
        "--feature", required=True, help="Feature ID (e.g., 'REQ-F-001')"
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
        "--provider",
        default="claude",
        help="F_P provider name (default: claude). Use 'providers' command to list.",
    )
    parser.add_argument(
        "--model", default="sonnet", help="Model for agent checks (default: sonnet)"
    )
    parser.add_argument(
        "--deterministic-only",
        action="store_true",
        help="Only run F_D checks (skip agent and human). Fast, free, Level 4.",
    )
    parser.add_argument(
        "--fd-timeout",
        type=int,
        default=120,
        help="Timeout for deterministic subprocess checks in seconds (default: 120)",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="genesis-engine",
        description="Genesis Engine — LLM-agnostic evaluation with pluggable F_P providers",
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

    # providers subcommand
    subparsers.add_parser(
        "providers",
        help="List available F_P providers",
    )

    args = parser.parse_args()

    if args.command == "evaluate":
        return cmd_evaluate(args)
    elif args.command == "run-edge":
        return cmd_run_edge(args)
    elif args.command == "providers":
        return cmd_providers(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
