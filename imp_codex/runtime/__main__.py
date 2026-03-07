"""CLI wrapper for the minimal executable Codex runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .commands import (
    gen_checkpoint,
    gen_init,
    gen_fold_back,
    gen_gaps,
    gen_iterate,
    gen_release,
    gen_review,
    gen_spawn,
    gen_start,
    gen_status,
    gen_trace,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m imp_codex.runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--project-root", default=".")
    start_parser.add_argument("--feature")
    start_parser.add_argument("--edge")

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--project-root", default=".")
    init_parser.add_argument("--project-name")
    init_parser.add_argument("--default-profile", default="standard")
    init_parser.add_argument("--actor", default="codex-runtime")

    iterate_parser = subparsers.add_parser("iterate")
    iterate_parser.add_argument("--project-root", default=".")
    iterate_parser.add_argument("--feature", required=True)
    iterate_parser.add_argument("--edge", required=True)
    iterate_parser.add_argument("--profile")
    iterate_parser.add_argument("--delta", type=int)
    iterate_parser.add_argument("--converged", action="store_true")
    iterate_parser.add_argument("--run-agent", action="store_true")
    iterate_parser.add_argument("--run-deterministic", action="store_true")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--project-root", default=".")
    status_parser.add_argument("--feature")
    status_parser.add_argument("--health", action="store_true")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--project-root", default=".")
    review_parser.add_argument("--feature", required=True)
    review_parser.add_argument("--edge")
    review_parser.add_argument("--decision", required=True)
    review_parser.add_argument("--feedback", default="")
    review_parser.add_argument("--actor", default="human")

    spawn_parser = subparsers.add_parser("spawn")
    spawn_parser.add_argument("--project-root", default=".")
    spawn_parser.add_argument("--type", dest="vector_type", required=True)
    spawn_parser.add_argument("--parent", required=True)
    spawn_parser.add_argument("--reason", required=True)
    spawn_parser.add_argument("--duration")
    spawn_parser.add_argument("--parent-edge")
    spawn_parser.add_argument("--actor", default="codex-runtime")

    fold_back_parser = subparsers.add_parser("fold-back")
    fold_back_parser.add_argument("--project-root", default=".")
    fold_back_parser.add_argument("--child", required=True)
    fold_back_parser.add_argument("--summary", required=True)
    fold_back_parser.add_argument("--status", default="converged")
    fold_back_parser.add_argument("--actor", default="codex-runtime")

    gaps_parser = subparsers.add_parser("gaps")
    gaps_parser.add_argument("--project-root", default=".")
    gaps_parser.add_argument("--feature")
    gaps_parser.add_argument("--no-intents", action="store_true")
    gaps_parser.add_argument("--actor", default="codex-runtime")

    release_parser = subparsers.add_parser("release")
    release_parser.add_argument("--project-root", default=".")
    release_parser.add_argument("--version", required=True)
    release_parser.add_argument("--dry-run", action="store_true")
    release_parser.add_argument("--actor", default="codex-runtime")

    trace_parser = subparsers.add_parser("trace")
    trace_parser.add_argument("--project-root", default=".")
    trace_parser.add_argument("--req-key", required=True)
    trace_parser.add_argument("--direction", default="both")

    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("--project-root", default=".")
    checkpoint_parser.add_argument("--message", default="")
    checkpoint_parser.add_argument("--actor", default="codex-runtime")

    args = parser.parse_args(argv)
    project_root = Path(args.project_root)

    if args.command == "start":
        result = gen_start(project_root, feature=args.feature, edge=args.edge)
    elif args.command == "init":
        result = gen_init(
            project_root,
            project_name=args.project_name,
            default_profile=args.default_profile,
            actor=args.actor,
        )
    elif args.command == "iterate":
        result = gen_iterate(
            project_root,
            feature=args.feature,
            edge=args.edge,
            profile=args.profile,
            delta=args.delta,
            converged=args.converged,
            run_agent=args.run_agent,
            run_deterministic=args.run_deterministic,
        )
    elif args.command == "review":
        result = gen_review(
            project_root,
            feature=args.feature,
            edge=args.edge,
            decision=args.decision,
            feedback=args.feedback,
            actor=args.actor,
        )
    elif args.command == "spawn":
        result = gen_spawn(
            project_root,
            vector_type=args.vector_type,
            parent=args.parent,
            reason=args.reason,
            duration=args.duration,
            parent_edge=args.parent_edge,
            actor=args.actor,
        )
    elif args.command == "fold-back":
        result = gen_fold_back(
            project_root,
            child=args.child,
            summary=args.summary,
            status=args.status,
            actor=args.actor,
        )
    elif args.command == "gaps":
        result = gen_gaps(
            project_root,
            feature=args.feature,
            emit_intents=not args.no_intents,
            actor=args.actor,
        )
    elif args.command == "release":
        result = gen_release(
            project_root,
            version=args.version,
            dry_run=args.dry_run,
            actor=args.actor,
        )
    elif args.command == "trace":
        result = gen_trace(
            project_root,
            req_key=args.req_key,
            direction=args.direction,
        )
    elif args.command == "checkpoint":
        result = gen_checkpoint(
            project_root,
            message=args.message,
            actor=args.actor,
        )
    else:
        result = gen_status(project_root, feature=args.feature, health=args.health)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
