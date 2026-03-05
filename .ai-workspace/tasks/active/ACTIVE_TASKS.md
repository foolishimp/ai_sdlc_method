# Active Tasks

*Last Updated: 2026-03-05*
*Methodology: AI SDLC Asset Graph Model v3.0.0-beta.1*

---

## MVP — Wire gen-iterate → Engine (ADR-021)

**Priority**: CRITICAL — blocks dogfood
**Status**: Not Started
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

## MVP — Delete Dead Code (ADR-020 residue)

**Priority**: HIGH — clarity before dogfood
**Status**: Not Started
**Release Target**: MVP

**Description**:
`fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py` are dead code. ADR-024 supersedes ADR-020 — the subprocess F_P path (`claude -p`) is gone. Engine routes through `FpFunctor`. These files persist only to anchor `REQ-F-FPC-*` tags.

**Tasks**:
1. Move `REQ-F-FPC-*` tag comments into `DESIGN_REQUIREMENTS.md` §1 as historical anchors (design-tier, not code-tier)
2. Delete `fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py`
3. Verify no remaining imports reference these files
4. Run test suite — confirm 729 unit tests still pass

**Reference**: `imp_claude/code/genesis/fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py`

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
