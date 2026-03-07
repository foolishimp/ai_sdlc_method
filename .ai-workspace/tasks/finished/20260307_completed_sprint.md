# Completed Tasks — Sprint to 2026-03-07

Archived from ACTIVE_TASKS.md. History in git. See commits referenced below.

---

## MVP — Wire gen-iterate → Engine (ADR-021)
**Done**: 2026-03-05 | **Commit**: `3c18488`
`gen-iterate.md` gained `--mode {interactive|engine|auto}`. Engine delegated for `code↔unit_tests` and `design→test_cases`.

## MVP — Emit edge_started + Align Gap Detection
**Done**: 2026-03-05 | **Commit**: `3c18488`
`run_edge()` emits `edge_started` before first iterate pass. Recovery scanner correctly pairs with `edge_converged`.

## MVP — Delete Dead Code (ADR-020 residue)
**Done**: 2026-03-05 | **Commit**: `ee41f55`
Deleted `fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py`, `test_fp_subprocess.py`. `REQ-F-FPC-*` tags migrated to `fp_functor.py` header.

## Resolved: fp_functor skipped consistency
**Done**: 2026-03-05
Error path returned `skipped=False, delta=-1`. Fixed to `skipped=True`.

## ADR-024 MVP — F_P MCP Actor Contracts
**Done**: 2026-03-05 | **Commit**: `a7e6bfd`
`contracts.py`, `functor.py`, `fp_functor.py` written. 143 tests pass.

## Actor Model Review (gates v3.0)
**Done**: ADR-017
Functor composition — F_D / F_P / F_H, natural transformation η, valence-tuned escalation.

## Consciousness Loop Stage 2+3
**Done**: 2026-03-07
`feature_proposal`, `feature_proposal_dismissed` events. `/gen-review-proposal` command. Approval path emits `spec_modified` with hashes.

## Spec Evolution Pipeline (REQ-F-EVOL-001)
**Done**: 2026-03-07 | **Commits**: `7c4bfda`, `0cd8357`, `d799006`, `c5fea45`, `b9d0a7c`
Workspace vector schema enforcement, JOIN display, spec_modified post-commit hook, feature_proposal queue.

## Event Stream Contract (REQ-F-EVENT-001)
**Done**: 2026-03-07 | **Commits**: `06e6c15`, `b9d0a7c`, `cc07366`, `6917c7f`, `e565f10`
Full OL event taxonomy in `ol_event.py`. `IterationStarted` emitted. Saga compensation events. ADR-025 (asset_content exception).

## Topology / Profile Disagreement
**Done**: 2026-03-07
Standard profile walk audited. ADR-S-018 written: tournament sub-graph pattern (parallel_spawn, tournament_arbitration, tournament_merge, tournament_commit).

## ADR-026 — Minimal Installer Footprint
**Done**: 2026-03-07
Permanent installer footprint: 3 operations. `/gen-start` UNINITIALISED handler owns lazy scaffolding. `/gen-init` demoted to power-user escape hatch.

## ADR-S-012 Decision (ADR-025)
**Done**: 2026-03-07 | **Commit**: `e565f10`
Pragmatic exception for `asset_content: str`. Defines 3.x migration path.

## Functor Execution Model Config (ADR-017)
**Done**: 2026-03-07 | **Commit**: `6ad072b`
`mode` and `valence` in `project_constraints.yml`. Edge configs annotated with starting-functor comments.

## Instance Graph from Events (ADR-022)
**Done**: 2026-03-07 | **Commit**: `3c6f9d0`
`project_instance_graph(events) → InstanceGraph`. Topology version check in session-start hook.

## ADR-013 Inbox Staging Serialiser (REQ-COORD-002/005)
**Done**: 2026-03-07 | **Commits**: `91c0596`
`serialiser.py`, `role_authority.py`. 55 tests. `agent_roles.yml` wired.

## REQ-CTX-002 Context Hierarchy (4-level)
**Done**: 2026-03-07 | **Commit**: `c4c35f1`
`deep_merge()`, `merge_contexts()`, `load_context_hierarchy()`. 46 tests.
**Note**: Superseded by T-COMPLY-002 — must be rebased to 6-level per ADR-S-022.

## REQ-EVAL-003 Human Accountability
**Done**: 2026-03-07 | **Commit**: `9133713`
`human_audit.py`. Attribution guard. 33 tests.

## Fix Orphan TOURNAMENT vector
**Done**: 2026-03-07 | **Commit**: `bba2af8`
`REQ-F-TOURNAMENT-001` added to spec. Feature count updated 15 → 16.

## Fix Pre-existing Test Failures (path restructure)
**Done**: 2026-03-07
55 tests updated to `specification/core/` paths. Requirement counts corrected to 83.
