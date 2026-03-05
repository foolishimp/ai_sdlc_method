# Active Tasks

*Last Updated: 2026-03-05*
*Methodology: AI SDLC Asset Graph Model v3.0.0-beta.1*

---

## MVP — Wire gen-iterate → Engine (ADR-021)

**Priority**: CRITICAL — blocks dogfood
**Status**: Done — 2026-03-05
**Commit**: `3c18488`
**Release Target**: MVP

**Description**:
`gen-iterate.md` and `python -m genesis evaluate` are disconnected. Normal workflow (`/gen-iterate`) runs the LLM agent path; the engine runs only via manual CLI. Until these are the same invocation the workflow cannot be dogfooded through normal slash commands.

**Tasks**:
1. Add `--mode {interactive|engine|auto}` to `gen-iterate.md` command signature
2. `auto` mode: delegate to engine for `code↔unit_tests` and `design→test_cases`; interactive for all others
3. `engine` mode: call `python -m genesis evaluate` with correct `--edge`, `--feature`, `--asset`, `--constraints`, `--deterministic-only` args
4. Pass through `--fd-timeout` from profile or default
5. Emit result back to slash command output (delta, converged, evaluators summary)
6. Add acceptance test: `/gen-iterate --mode engine` on green project → `converged: true`

**Reference**: `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md`, `imp_claude/code/genesis/__main__.py`

---

## MVP — Emit edge_started + Align Gap Detection (Codex item 3)

**Priority**: HIGH — recovery correctness
**Status**: Done — 2026-03-05
**Commit**: `3c18488`
**Release Target**: MVP

**Description**:
The session-gap recovery scanner in `workspace_state.py` depends on `edge_started` events to detect abandoned iterations. The engine does not emit them. Recovery scanner is broken against real engine runs — it can't distinguish "never started" from "started but crashed".

**Tasks**:
1. Emit `edge_started` event at the top of `run_edge()` in `engine.py` (before first `iterate_edge()` call)
2. Fields: `feature`, `edge`, `iteration: 1`, consistent with `iteration_completed` schema
3. Verify `workspace_state.find_incomplete_edges()` correctly pairs `edge_started` with `edge_converged` / `iteration_completed`
4. Add test: emit `edge_started` then simulate crash → recovery scanner detects the incomplete edge

**Reference**: `imp_claude/code/genesis/engine.py:run_edge()`, `imp_claude/code/genesis/workspace_state.py:find_incomplete_edges()`

---

## MVP — Delete Dead Code (ADR-020 residue)

**Priority**: HIGH — clarity before dogfood
**Status**: Done — 2026-03-05
**Commit**: `ee41f55`
**Release Target**: MVP

**Description**:
`fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py` are dead code. ADR-024 supersedes ADR-020 — the subprocess F_P path (`claude -p`) is gone. Engine routes through `FpFunctor`. REQ-F-FPC-* tags moved to fp_functor.py header.

**Tasks**:
1. ✓ Move `REQ-F-FPC-*` tag comments into fp_functor.py Implements header
2. ✓ Delete `fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py`, `test_fp_subprocess.py`
3. ✓ Rewrite `test_functor_construct.py` — keep only ADR-024 tests
4. ✓ Remove `ConstructResult` from `models.py`
5. ✓ 691 unit tests pass; 55 pre-existing failures (stale path constants, not regressions)

**Reference**: `imp_claude/code/genesis/fp_functor.py`, `imp_claude/tests/test_functor_construct.py`

---

## MVP — F_P Construct via MCP Actor (ADR-023/024)

**Priority**: HIGH — needed for full construct→evaluate loop
**Status**: Stub (`fp_functor._mcp_invoke` raises, always returns `skipped=True`)
**Release Target**: MVP+1 (can dogfood F_D only without this)

**Description**:
Every F_P invocation currently skips — the MCP actor is never reached. F_D evaluation works. Full construct loop (code generation, test writing via actor) requires the MCP transport to fire. This is the ADR-024 core unlock.

**Tasks**:
1. Implement `_mcp_invoke()` in `fp_functor.py` — issue actual `claude_code` MCP tool call with actor prompt
2. Wire `CLAUDE_CODE_SSE_PORT` detection to live invocation (not just skip)
3. Actor writes fold-back result to `.ai-workspace/agents/fp_result_{run_id}.json`
4. `_parse_actor_result()` already correct — reads fold-back, builds `StepResult`
5. Integration test: MCP available + actor completes → `fp_result.converged` populated
6. Budget enforcement: pass `--max-budget-usd` to actor invocation

**Reference**: `imp_claude/code/genesis/fp_functor.py:119`, ADR-024, ADR-023

---

## Resolved: fp_functor skipped consistency (Codex item 6)

**Status**: Done — 2026-03-05
**Commit**: pending

`fp_functor.py` error path (MCP available, fold-back file missing) returned `skipped=False, delta=-1` — contradictory semantics that mislead the orchestrator into treating "actor not yet complete" as a hard failure. Fixed to `skipped=True`: delta=-1 is the sentinel for "no measurement taken", orchestrator correctly ignores it.

---

## Resolved: ADR-024 MVP — F_P MCP Actor Contracts

**Status**: Done — 2026-03-05
**Commit**: `a7e6bfd feat(adr-024): F_P MCP actor contracts — REQ-ROBUST-002 + REQ-ITER-001`

`contracts.py`, `functor.py`, `fp_functor.py` written. Engine is purely F_D. Agent checks always SKIP. FpFunctor returns skipped StepResult when MCP unavailable; reads fold-back result when `CLAUDE_CODE_SSE_PORT` set. 143 tests pass.

---

## Resolved: Actor Model Review (gates v3.0)

**Status**: Done — ADR-017
**Resolution**: Functor composition — F_D / F_P / F_H, natural transformation η, valence-tuned escalation.

---

## Post-MVP: Consciousness Loop Stage 2+3

**Priority**: High
**Status**: Not Started
**Release Target**: 3.0
**Triggered by**: Gemini comparison review (2026-03-03) + `/gen-gaps` INT-GAPS-001..004

**Description**:
Loop stops at Stage 1 (`intent_raised`). Stages 2 (Affect Triage → `feature_proposal` event) and 3 (Human Gate → `/gen-review-proposal`) not implemented. Overlaps REQ-F-EVOL-001.

**Tasks**:
1. Add `feature_proposal`, `feature_proposal_dismissed` event types to `fd_emit.py` + `ol_event.py`
2. Add `feature_proposal` emission to `/gen-gaps` Stage 6
3. Create `/gen-review-proposal` command (list | approve | dismiss)
4. Approval path: append to `specification/features/FEATURE_VECTORS.md`, emit `spec_modified` with hashes, inflate workspace trajectory
5. Test coverage

**Reference**: ADR-011 confirmed gap; ADR-S-008 Stage 2+3; REQ-F-EVOL-001

---

## Post-MVP: Spec Evolution Pipeline (REQ-F-EVOL-001)

**Priority**: High
**Status**: Not Started
**Release Target**: 3.1

**Tasks**:
1. Enforce workspace vector schema (trajectory fields only — no `satisfies`) — REQ-EVOL-001
2. JOIN display in `gen-status`: ACTIVE / PENDING / ORPHAN across spec + workspace — REQ-EVOL-002
3. `spec_modified` event on any `specification/` change (post-commit hook or equivalent) — REQ-EVOL-004
4. `feature_proposal` event type + Draft Queue surfaced in `gen-status` — REQ-EVOL-003, REQ-EVOL-005
5. Add `# Implements: REQ-EVOL-*` tags throughout

**Depends On**: Consciousness Loop Stage 2+3 (shared event types)

---

## Post-MVP: Event Stream Contract (REQ-F-EVENT-001)

**Priority**: Medium
**Status**: Not Started
**Release Target**: 3.1

**Tasks**:
1. Add `IterationStarted`, `EvaluatorVoted`, `ConsensusReached`, `ContextArrived` to `ol_event.py` `_OL_EVENT_TYPE` — REQ-EVENT-003
2. Emit `IterationStarted` at top of `iterate_edge()` in `engine.py` — REQ-EVENT-003
3. Saga compensation: `CompensationTriggered` / `CompensationCompleted` events — REQ-EVENT-004
4. Verify projection contract (determinism, completeness, isolation) — REQ-EVENT-002
5. Write ADR-025: pragmatic exception for `asset_content: str` vs full event-sourced projection

---

## Post-MVP: Topology / Profile Disagreement (Codex item 7)

**Priority**: Medium
**Status**: Needs Decision
**Release Target**: 3.0
**Source**: Codex matrix item 7 + Gemini tournament strategy (2026-03-05/06)

**Description**:
`graph_topology.yml` contains `module_decomposition` and `basis_projections` nodes but standard profiles walk `design → code` directly, skipping them. Two sub-issues:

1. **Node-insertion gap**: the standard execution path doesn't traverse the full topology. Either the nodes are wrong (remove them) or the profile is wrong (add them to the walk).
2. **Tournament sub-graph**: Gemini/Codex dialogue produced `parallel_spawn → tournament_arbitration → tournament_merge` as explicit topology nodes (v2.9.0). Gemini implemented this in their tenant. Before Claude adopts, it needs **ADR-S-018** (tournament sub-graph spec ADR) ratified at the spec level — topology extensions are shared schema, not tenant-local.

**Tasks**:
1. Audit standard profile walk against topology nodes — identify which nodes are actually traversed
2. Decide: remove unused nodes or add them to the standard profile walk
3. Write ADR-S-018: tournament sub-graph pattern (parallel_spawn, tournament_arbitration, tournament_merge, tournament_commit), OL `run.facets.parent` causal links, merge provenance fields
4. After ADR-S-018 ratified: update Claude's `graph_topology.yml` and add feature vectors for tournament nodes

**Reference**: `imp_claude/code/.claude-plugin/plugins/genesis/config/graph_topology.yml`, Gemini `20260306T123000_STRATEGY_TOURNAMENT-TOPOLOGY-REFINEMENT.md`, Codex `20260305T152022_REVIEW_Tournament-Pattern_Node-vs-Edge-Modeling.md`

---

## Post-MVP: ADR-S-012 Decision (ADR-025)

**Priority**: Medium — design decision, one paragraph
**Status**: Needs Decision
**Release Target**: 3.0

**Description**:
ADR-S-012 mandates `iterate() → Event+` (assets as event projections). Engine passes `asset_content: str`. Write ADR-025 to formally record the pragmatic exception and define the 3.x migration path.

**Effort**: Write ADR-025 — ~1 page. No code change.

---

## Post-MVP: Functor Execution Model Config (ADR-017)

**Priority**: Medium
**Status**: Not Started
**Release Target**: 3.0

**Tasks**:
1. Add `mode` (headless | interactive | auto) and `valence` (high | medium | low) to `project_constraints.yml`
2. Add `valence` field to feature vector affect schema
3. Annotate edge configs with starting-functor comments
4. Integration tests for escalation paths (η_D→P and η_P→H)

---

## In Progress: Instance Graph from Events (ADR-022)

**Priority**: Medium
**Status**: Partially Complete — 2026-03-03
**Release Target**: 3.1

**Remaining**:
4. Add `project_instance_graph(events) → InstanceGraph` — full event replay projection
5. Add zoom level 1 overlay to `graph.py`
6. Add topology version check to `on-session-start.sh`

---

## Backlog

- **ADR-S-014**: OTLP/Phoenix — no design ADR, no implementation in imp_claude
- **ADR-013 Inbox staging**: `edge_claim`/`claim_rejected`, Markov parallelism (REQ-COORD-004/005)
- **Task #37**: Ecosystem E(t) as Feedback Loop Edge (Low)
- **Task #34**: Propagate Insights Back to Ontology (Low)

---

## Known Pre-existing Test Failures (not regressions)

55 tests in `test_spec_validation.py` / `test_integration_uat.py` / `test_methodology_bdd.py` reference `specification/AI_SDLC_ASSET_GRAPH_MODEL.md` (old path — moved to `specification/core/`). Fix: update path constants in `imp_claude/tests/conftest.py`.

---

## Current State (2026-03-05)

| Artifact | Status |
|----------|--------|
| Spec (Asset Graph Model) | Complete — 4 primitives, 17 spec ADRs |
| Implementation Requirements | 83 requirements (REQ-EVOL + REQ-EVENT added 2026-03-05) |
| Feature Vectors | 14 vectors, 83/83 covered (v1.9.0) |
| Claude Design (ADRs 008-024) | 17 ADRs; ADR-025 (event-sourced exception) pending |
| Claude Code | Engine CLI + contracts/functor/fp_functor (ADR-024 MVP) |
| Tests | 729 unit passing; 143 engine/functor; 55 stale path failures |
| Gemini Design | Complete (ADRs GG-001-008) |
| Codex Design | Complete (ADR-CG-001) |

**Gap analysis**: `.ai-workspace/comments/claude/` (pending — write after tasks updated)

---

## Recovery Commands

```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git log --oneline -5                             # Recent commits
PYTHONPATH=imp_claude/code python -m pytest imp_claude/tests/ -q \
  --ignore=imp_claude/tests/e2e --ignore=imp_claude/tests/uat -p no:warnings 2>&1 | tail -5
```
