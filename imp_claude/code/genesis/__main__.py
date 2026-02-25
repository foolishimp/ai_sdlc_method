# Implements: REQ-ITER-001 (Universal Iterate), REQ-SUPV-003 (Failure Observability)
"""CLI entry point for the genesis engine.

Usage:
    python -m genesis evaluate --edge "code↔unit_tests" --feature "REQ-F-ENGINE-001" --asset path/to/file.py
    python -m genesis evaluate --edge "code↔unit_tests" --feature "REQ-F-ENGINE-001" --asset - < file.py

The engine evaluates an asset against an edge's checklist and emits Level 4 events.
The LLM agent calls this for cross-validation (ADR-019).
"""

import argparse
import json
import sys
from pathlib import Path

from .config_loader import load_yaml
from .engine import EngineConfig


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
        workspace / ".ai-workspace" / "claude" / "context" / "project_constraints.yml",
        workspace / ".ai-workspace" / "context" / "project_constraints.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # return first even if missing — error will be clear


def _find_edge_params(workspace: Path) -> Path:
    """Find edge_params directory — try workspace then plugin."""
    candidates = [
        workspace / ".ai-workspace" / "graph" / "edges",
        workspace
        / "imp_claude"
        / "code"
        / ".claude-plugin"
        / "plugins"
        / "genesis"
        / "config"
        / "edge_params",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _find_profiles(workspace: Path) -> Path:
    """Find profiles directory — try workspace then plugin."""
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


def _emit_command_error(workspace: Path, project: str, command: str, category: str, detail: str) -> None:
    """Emit a command_error event for REQ-SUPV-003 failure observability."""
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
        pass  # Observation failure must not block error reporting


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate an asset against an edge's checklist. Emit Level 4 events."""
    workspace = Path(args.workspace) if args.workspace else _find_workspace(Path.cwd())

    # Load asset content
    if args.asset == "-":
        asset_content = sys.stdin.read()
    else:
        asset_path = Path(args.asset)
        if not asset_path.exists():
            _emit_command_error(workspace, "", "evaluate", "missing_asset", f"Asset not found: {args.asset}")
            print(
                json.dumps({"error": f"Asset not found: {args.asset}"}), file=sys.stderr
            )
            return 1
        asset_content = asset_path.read_text()

    # Load constraints
    constraints_path = (
        Path(args.constraints) if args.constraints else _find_constraints(workspace)
    )
    if not constraints_path.exists():
        _emit_command_error(workspace, "", "evaluate", "missing_constraints", f"Constraints not found: {constraints_path}")
        print(
            json.dumps({"error": f"Constraints not found: {constraints_path}"}),
            file=sys.stderr,
        )
        return 1
    constraints = load_yaml(constraints_path)

    # Load graph topology
    topo_path = _find_graph_topology(workspace)
    graph_topology = load_yaml(topo_path) if topo_path.exists() else {}

    # Build engine config
    config = EngineConfig(
        project_name=constraints.get("project", {}).get("name", workspace.name),
        workspace_path=workspace,
        edge_params_dir=_find_edge_params(workspace),
        profiles_dir=_find_profiles(workspace),
        constraints=constraints,
        graph_topology=graph_topology,
        model=args.model,
        max_iterations_per_edge=1,  # CLI runs one iteration at a time
        claude_timeout=args.timeout,
    )

    # Load edge config
    edge = args.edge
    edge_params_dir = config.edge_params_dir
    edge_map = {
        "code↔unit_tests": "tdd",
        "design→test_cases": "design_tests",
        "design→uat_tests": "bdd",
    }
    edge_filename = edge_map.get(
        edge, edge.replace("→", "_").replace("↔", "_").replace(" ", "")
    )
    edge_config_path = edge_params_dir / f"{edge_filename}.yml"

    if not edge_config_path.exists():
        _emit_command_error(workspace, config.project_name, "evaluate", "missing_edge_config", f"Edge config not found: {edge_config_path}")
        print(
            json.dumps({"error": f"Edge config not found: {edge_config_path}"}),
            file=sys.stderr,
        )
        return 1

    edge_config = load_yaml(edge_config_path)

    # Determine check filter
    run_agent = not args.deterministic_only

    # Run one iteration
    from .config_loader import resolve_checklist
    from .fd_evaluate import run_check as fd_run_check
    from .fp_evaluate import run_check as fp_run_check
    from .fd_emit import emit_event, make_event
    from .models import CheckOutcome, CheckResult

    checks = resolve_checklist(edge_config, constraints)
    results: list[CheckResult] = []
    escalations: list[str] = []

    for check in checks:
        if check.check_type == "deterministic":
            cr = fd_run_check(check, workspace, timeout=args.fd_timeout)
        elif check.check_type == "agent":
            if run_agent:
                cr = fp_run_check(
                    check,
                    asset_content=asset_content,
                    context=args.context or "",
                    model=config.model,
                    timeout=config.claude_timeout,
                )
            else:
                cr = CheckResult(
                    name=check.name,
                    outcome=CheckOutcome.SKIP,
                    required=check.required,
                    check_type=check.check_type,
                    functional_unit=check.functional_unit,
                    message="Skipped: --deterministic-only mode",
                )
        elif check.check_type == "human":
            cr = CheckResult(
                name=check.name,
                outcome=CheckOutcome.SKIP,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message="Skipped: human check (CLI mode)",
            )
        else:
            cr = CheckResult(
                name=check.name,
                outcome=CheckOutcome.SKIP,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Skipped: unknown check type '{check.check_type}'",
            )

        results.append(cr)

        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR):
            if cr.check_type == "deterministic":
                escalations.append(f"η_D→P: {cr.name}")
            elif cr.check_type == "agent":
                escalations.append(f"η_P→H: {cr.name}")

    # Compute delta
    delta = sum(
        1
        for cr in results
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )
    converged = delta == 0

    # Emit Level 4 event
    events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    check_details = [
        {
            "name": cr.name,
            "type": cr.check_type,
            "outcome": cr.outcome.value,
            "required": cr.required,
            "message": cr.message[:200] if cr.message else "",
        }
        for cr in results
    ]

    passed = sum(1 for cr in results if cr.outcome == CheckOutcome.PASS)
    failed = sum(
        1 for cr in results if cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )
    skipped = sum(1 for cr in results if cr.outcome == CheckOutcome.SKIP)

    emit_event(
        events_path,
        make_event(
            "iteration_completed",
            config.project_name,
            feature=args.feature,
            edge=edge,
            iteration=args.iteration,
            delta=delta,
            status="converged" if converged else "iterating",
            evaluators={
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "total": len(results),
                "details": check_details,
            },
            checks=check_details,
            escalations=escalations,
            source="engine_cli",
        ),
    )

    if converged:
        emit_event(
            events_path,
            make_event(
                "edge_converged",
                config.project_name,
                feature=args.feature,
                edge=edge,
                iteration=args.iteration,
                convergence_type="standard",
            ),
        )

    # Output JSON result
    output = {
        "edge": edge,
        "feature": args.feature,
        "iteration": args.iteration,
        "delta": delta,
        "converged": converged,
        "evaluators": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(results),
        },
        "checks": check_details,
        "escalations": escalations,
        "event_emitted": True,
        "source": "engine_cli",
    }

    print(json.dumps(output, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="genesis",
        description="Genesis F_D engine — deterministic evaluation with Level 4 events",
    )
    subparsers = parser.add_subparsers(dest="command")

    # evaluate subcommand
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an asset against an edge's checklist",
    )
    eval_parser.add_argument(
        "--edge", required=True, help="Edge name (e.g., 'code↔unit_tests')"
    )
    eval_parser.add_argument(
        "--feature", required=True, help="Feature ID (e.g., 'REQ-F-ENGINE-001')"
    )
    eval_parser.add_argument(
        "--asset", required=True, help="Path to asset file, or '-' for stdin"
    )
    eval_parser.add_argument(
        "--workspace", default=None, help="Workspace root (auto-detected if omitted)"
    )
    eval_parser.add_argument(
        "--constraints", default=None, help="Path to project_constraints.yml"
    )
    eval_parser.add_argument("--context", default="", help="Additional context string")
    eval_parser.add_argument(
        "--model", default="sonnet", help="Model for agent checks (default: sonnet)"
    )
    eval_parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout for agent checks in seconds"
    )
    eval_parser.add_argument(
        "--iteration", type=int, default=1, help="Iteration number for event"
    )
    eval_parser.add_argument(
        "--deterministic-only",
        action="store_true",
        help="Only run F_D checks (skip agent and human). Fast, free, Level 4.",
    )
    eval_parser.add_argument(
        "--fd-timeout",
        type=int,
        default=120,
        help="Timeout for deterministic subprocess checks in seconds (default: 120)",
    )

    args = parser.parse_args()

    if args.command == "evaluate":
        return cmd_evaluate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
