"""CLI wrapper for the minimal executable Codex runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .commands import (
    gen_comment,
    gen_consensus_close,
    gen_consensus_open,
    gen_consensus_recover,
    gen_consensus_status,
    gen_dispatch_intents,
    gen_dispose,
    gen_checkpoint,
    gen_init,
    gen_fold_back,
    gen_gaps,
    gen_iterate,
    gen_propose,
    gen_release,
    gen_review,
    gen_spec_modify,
    gen_spawn,
    gen_start,
    gen_status,
    gen_trace,
    gen_vote,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m imp_codex.runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--project-root", default=".")
    start_parser.add_argument("--feature")
    start_parser.add_argument("--edge")
    start_parser.add_argument("--auto", action="store_true")
    start_parser.add_argument("--max-steps", type=int, default=10)
    start_parser.add_argument("--run-agent", action="store_true")
    start_parser.add_argument("--run-deterministic", action="store_true")
    start_parser.add_argument("--actor", default="intent-observer")

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
    iterate_parser.add_argument("--artifact-path", action="append", default=[])
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

    propose_parser = subparsers.add_parser("propose")
    propose_parser.add_argument("--project-root", default=".")
    propose_parser.add_argument("--title", required=True)
    propose_parser.add_argument("--trigger", required=True)
    propose_parser.add_argument("--signal-source", required=True)
    propose_parser.add_argument("--affected-req-key", action="append", dest="affected_req_keys", required=True, default=[])
    propose_parser.add_argument("--feature")
    propose_parser.add_argument("--edge", default="spec_change")
    propose_parser.add_argument("--vector-type", default="feature")
    propose_parser.add_argument("--prior-intent", action="append", dest="prior_intents", default=[])
    propose_parser.add_argument("--spec-path", action="append", dest="spec_paths", default=[])
    propose_parser.add_argument("--actor", default="codex-runtime")

    spec_modify_parser = subparsers.add_parser("spec-modify")
    spec_modify_parser.add_argument("--project-root", default=".")
    spec_modify_parser.add_argument("--intent-id", required=True)
    spec_modify_parser.add_argument("--what-changed", action="append", required=True, default=[])
    spec_modify_parser.add_argument("--affected-req-key", action="append", dest="affected_req_keys", default=[])
    spec_modify_parser.add_argument("--spec-path", action="append", dest="spec_paths", default=[])
    spec_modify_parser.add_argument("--spawned-vector", action="append", dest="spawned_vectors", default=[])
    spec_modify_parser.add_argument("--actor", default="human")

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

    dispatch_parser = subparsers.add_parser("dispatch-intents")
    dispatch_parser.add_argument("--project-root", default=".")
    dispatch_parser.add_argument("--intent-id")
    dispatch_parser.add_argument("--max-dispatch", type=int, default=20)
    dispatch_parser.add_argument("--run-agent", action="store_true")
    dispatch_parser.add_argument("--run-deterministic", action="store_true")
    dispatch_parser.add_argument("--actor", default="intent-observer")

    consensus_open_parser = subparsers.add_parser("consensus-open")
    consensus_open_parser.add_argument("--project-root", default=".")
    consensus_open_parser.add_argument("--artifact", required=True)
    consensus_open_parser.add_argument("--roster", required=True)
    consensus_open_parser.add_argument("--quorum", default="majority")
    consensus_open_parser.add_argument("--review-id")
    consensus_open_parser.add_argument("--asset-version", default="v1")
    consensus_open_parser.add_argument("--min-duration-seconds", type=int, default=0)
    consensus_open_parser.add_argument("--review-closes-in", type=int, default=86400)
    consensus_open_parser.add_argument("--abstention-model", default="neutral")
    consensus_open_parser.add_argument("--min-participation-ratio", type=float, default=0.5)
    consensus_open_parser.add_argument("--actor", default="local-user")

    comment_parser = subparsers.add_parser("comment")
    comment_parser.add_argument("--project-root", default=".")
    comment_parser.add_argument("--review-id", required=True)
    comment_parser.add_argument("--content", required=True)
    comment_parser.add_argument("--participant", default="local-user")
    comment_parser.add_argument("--actor", default="local-user")

    dispose_parser = subparsers.add_parser("dispose")
    dispose_parser.add_argument("--project-root", default=".")
    dispose_parser.add_argument("--review-id", required=True)
    dispose_parser.add_argument("--comment-id", required=True)
    dispose_parser.add_argument("--disposition", required=True)
    dispose_parser.add_argument("--rationale", required=True)
    dispose_parser.add_argument("--actor", default="local-user")

    vote_parser = subparsers.add_parser("vote")
    vote_parser.add_argument("--project-root", default=".")
    vote_parser.add_argument("--review-id", required=True)
    vote_parser.add_argument("--verdict", required=True)
    vote_parser.add_argument("--participant", default="local-user")
    vote_parser.add_argument("--rationale", default="")
    vote_parser.add_argument("--condition", action="append", dest="conditions", default=[])
    vote_parser.add_argument("--gating", action="store_true")
    vote_parser.add_argument("--actor", default="local-user")

    consensus_status_parser = subparsers.add_parser("consensus-status")
    consensus_status_parser.add_argument("--project-root", default=".")
    consensus_status_parser.add_argument("--review-id", required=True)
    consensus_status_parser.add_argument("--cycle-id")

    consensus_close_parser = subparsers.add_parser("consensus-close")
    consensus_close_parser.add_argument("--project-root", default=".")
    consensus_close_parser.add_argument("--review-id", required=True)
    consensus_close_parser.add_argument("--cycle-id")
    consensus_close_parser.add_argument("--actor", default="consensus-closeout")

    consensus_recover_parser = subparsers.add_parser("consensus-recover")
    consensus_recover_parser.add_argument("--project-root", default=".")
    consensus_recover_parser.add_argument("--review-id", required=True)
    consensus_recover_parser.add_argument("--path", required=True)
    consensus_recover_parser.add_argument("--rationale", default="")
    consensus_recover_parser.add_argument("--review-closes-in", type=int, default=86400)
    consensus_recover_parser.add_argument("--actor", default="local-user")

    args = parser.parse_args(argv)
    project_root = Path(args.project_root)

    if args.command == "start":
        result = gen_start(
            project_root,
            feature=args.feature,
            edge=args.edge,
            auto=args.auto,
            max_steps=args.max_steps,
            run_agent=args.run_agent,
            run_deterministic=args.run_deterministic,
            actor=args.actor,
        )
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
            artifact_paths=args.artifact_path,
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
    elif args.command == "propose":
        result = gen_propose(
            project_root,
            title=args.title,
            trigger=args.trigger,
            signal_source=args.signal_source,
            affected_req_keys=args.affected_req_keys,
            feature=args.feature,
            edge=args.edge,
            vector_type=args.vector_type,
            prior_intents=args.prior_intents,
            spec_paths=args.spec_paths,
            actor=args.actor,
        )
    elif args.command == "spec-modify":
        result = gen_spec_modify(
            project_root,
            intent_id=args.intent_id,
            what_changed=args.what_changed,
            affected_req_keys=args.affected_req_keys,
            spec_paths=args.spec_paths,
            spawned_vectors=args.spawned_vectors,
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
    elif args.command == "dispatch-intents":
        result = gen_dispatch_intents(
            project_root,
            intent_id=args.intent_id,
            actor=args.actor,
            max_dispatch=args.max_dispatch,
            run_agent=args.run_agent,
            run_deterministic=args.run_deterministic,
        )
    elif args.command == "consensus-open":
        result = gen_consensus_open(
            project_root,
            artifact=args.artifact,
            roster=args.roster,
            quorum=args.quorum,
            review_id=args.review_id,
            asset_version=args.asset_version,
            min_duration_seconds=args.min_duration_seconds,
            review_closes_in=args.review_closes_in,
            abstention_model=args.abstention_model,
            min_participation_ratio=args.min_participation_ratio,
            actor=args.actor,
        )
    elif args.command == "comment":
        result = gen_comment(
            project_root,
            review_id=args.review_id,
            content=args.content,
            participant=args.participant,
            actor=args.actor,
        )
    elif args.command == "dispose":
        result = gen_dispose(
            project_root,
            review_id=args.review_id,
            comment_id=args.comment_id,
            disposition=args.disposition,
            rationale=args.rationale,
            actor=args.actor,
        )
    elif args.command == "vote":
        result = gen_vote(
            project_root,
            review_id=args.review_id,
            verdict=args.verdict,
            participant=args.participant,
            rationale=args.rationale,
            conditions=args.conditions,
            gating=args.gating,
            actor=args.actor,
        )
    elif args.command == "consensus-status":
        result = gen_consensus_status(
            project_root,
            review_id=args.review_id,
            cycle_id=args.cycle_id,
        )
    elif args.command == "consensus-close":
        result = gen_consensus_close(
            project_root,
            review_id=args.review_id,
            cycle_id=args.cycle_id,
            actor=args.actor,
        )
    elif args.command == "consensus-recover":
        result = gen_consensus_recover(
            project_root,
            review_id=args.review_id,
            path=args.path,
            rationale=args.rationale,
            review_closes_in=args.review_closes_in,
            actor=args.actor,
        )
    else:
        result = gen_status(project_root, feature=args.feature, health=args.health)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
