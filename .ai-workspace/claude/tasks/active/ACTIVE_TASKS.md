# Active Tasks — imp_claude (Claude Code tenant)

*Updated: 2026-03-09*
*Overriding goal: [.ai-workspace/tasks/active/ACTIVE_TASKS.md](../../../tasks/active/ACTIVE_TASKS.md)*

---

## SPRINT: Shippable 1.0

**Scope**: Gate 1 only — T-001 + T-007. Gates 2/3/4 are cross-tenant assurance tasks.
**Principle**: Pre-release — no stubs, no legacy paths, no deprecated markers. Migrate or remove.
**No new ADRs** — all decisions already written.

### 1.0 Tasks (Gate 1) — engine complete + robustness tier 1

```
T-COMPLY-001 (event contract)   ✅ DONE — OL emit path, RunState contract
T-COMPLY-005 (transactions)     ✅ DONE — runId threading, input_hash, causation chain
T-COMPLY-007 (stub removal)     ✅ DONE — fold-back contract, FpActorResultMissing
T-COMPLY-008 (actor dispatch)   ✅ DONE — gen-iterate.md: manifest scan + MCP dispatch + status tracking, 10 spec tests
```

### 1.1 Tasks (post-1.0)

```
T-COMPLY-002 (context)          ←── 6-level hierarchy (REQ-CTX-002 spec updated 2026-03-07; implement in config_loader.py)
T-COMPLY-003 (instance graph)   ✅ DONE — profile-coverage derivation + spawn_created child node, 5 tests (2026-03-09)
T-COMPLY-004 (FPC audit)        ←── design-tier tag audit only (no shared spec changes)
T-COMPLY-006 (H-metric)         ✅ DONE — compute_hamiltonian() + InstanceNode.hamiltonian + gen-status H column (2026-03-09)
```

---

### T-COMPLY-001: Event Contract — engine.py → ol_event.py, delete fd_emit.py

**ADRs**: ADR-S-011, ADR-S-012
**Blocks**: T-COMPLY-005, T-COMPLY-006, T-COMPLY-007, T-COMPLY-008
**Files**: `imp_claude/code/genesis/engine.py`, `imp_claude/code/genesis/ol_event.py`, `imp_claude/code/genesis/fd_emit.py`, `imp_claude/tests/test_event_taxonomy.py`, `imp_claude/tests/test_integration_uat.py`

Engine emits flat records via `fd_emit`. `ol_event.py` is side-car. Two bugs: wrong emit path; `IterationCompleted` maps `COMPLETE` instead of `OTHER`.

1. Fix `ol_event.py` — `IterationCompleted` → `RunState.OTHER`; `EdgeConverged` → `RunState.COMPLETE`
2. Replace all `fd_emit.emit_event()` calls in `engine.py` with `ol_event` constructors
3. Wire `iterate_edge()` to emit `IterationStarted` (OL) at start of each pass
4. Wire `run_edge()` to emit `EdgeConverged` (OL) on convergence
5. **Delete `fd_emit.py`** — no deprecation marker
6. Update `test_event_taxonomy.py` — assert ADR-S-011 RunState contract
7. Remove the 3-format normalization shim from `test_integration_uat.py` — OL-native only
8. Search all `fd_emit` imports; remove

---

### T-COMPLY-002: Context Hierarchy — rebase to ADR-S-022 / ADR-027

**ADRs**: ADR-S-022, ADR-027
**Files**: `imp_claude/code/genesis/config_loader.py`, `imp_claude/code/installers/gen-setup.py`, `imp_claude/tests/test_config_loader.py`

Current 4-level `global → org → team → project` is wrong per ADR-S-022. Missing: `context_sources` resolution, lineage manifest, `context_hash` on iteration events.

1. Update `config_loader.py` merge order: `methodology → org → policy → domain → prior → project`
2. Add `context_sources` resolution from feature vector YAML
3. Create `.ai-workspace/context/{scope}/` directory structure on workspace init
4. Generate `context_manifest.yml` — sorted file list + SHA-256 per file, aggregate hash
5. Emit `context_hash` on each `IterationCompleted` OL event
6. Update installer — build lineage dirs on `project_initialized`; include provenance payload
7. Update `test_config_loader.py` — assert 6-level hierarchy; remove old 4-level assertions

---

### T-COMPLY-003: Instance Graph Lifecycle — ADR-S-021

**ADRs**: ADR-S-021, ADR-022
**Files**: `imp_claude/code/genesis/workspace_state.py`, `imp_claude/code/genesis/fd_spawn.py`, `imp_claude/tests/test_instance_graph.py`

Two bugs: archives on `feature_converged` event (spec derives from profile coverage); spawn child node created implicitly from later edge events (should be created from `spawn_created`).

1. Replace `feature_converged` archival check with: `converged_edges ⊇ active_profile_edges → terminal`
2. Create child node from `spawn_created.child_feature` immediately
3. Update `test_instance_graph.py` — assert profile-coverage derivation; remove `feature_converged` terminal assertions
4. Add test: spawn event → child node immediately visible before any child edge event

---

### T-COMPLY-004: F_P Functor Implement-Tag Audit (design-tier only)

**ADRs**: none needed
**Files**: `imp_claude/code/genesis/fp_functor.py`

**Scope clarification** (Codex review 2026-03-07): `fp_functor.py` currently declares `Implements: REQ-ROBUST-001, REQ-ROBUST-002, REQ-ITER-001`. These are valid shared spec keys. There are no `REQ-F-FPC-*` keys — the original task description was stale. This task is design-tier documentation cleanup only; no shared spec anchoring required.

1. Verify all `Implements:` tags in `fp_functor.py` resolve to existing spec keys (REQ-ROBUST-*, REQ-ITER-*)
2. Add any missing design-tier ADR references to the file header (Claude implementation ADRs only)
3. Update `REQ-F-ROBUST-001` feature YAML — `status: converged` if currently stale
4. No changes to `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` or `FEATURE_VECTORS.md` required

---

### T-COMPLY-005: ADR-S-015 Transaction Model

**ADRs**: ADR-S-015, ADR-S-016
**Depends on**: T-COMPLY-001
**Files**: `imp_claude/code/genesis/engine.py`, `imp_claude/code/genesis/__main__.py`, `imp_claude/code/genesis/workspace_state.py`, `imp_claude/code/genesis/contracts.py`

Engine emits start/complete without `runId`, no input manifest, no output hashes. Recovery uses `edge_started` heuristics, not manifest comparison.

1. Generate `runId` (UUID) at edge START; thread through COMPLETE/FAIL/ABORT events
2. Compute `input_manifest` at START — hash source asset file set (path + SHA-256 per file)
3. Populate `output_artifacts` at COMPLETE from `StepResult.artifacts`
4. Rewrite `__main__.py` recovery — read open transaction START events, extract `input_manifest`, compare to current filesystem; ABORT on mismatch
5. Add `runId` to `contracts.py` `StepResult`
6. Tests: open transaction + crash → recovery reads manifest → correct ABORT or RESUME

---

### T-COMPLY-006: H-Metric — workspace_state.py + gen-status

**ADRs**: ADR-S-020, ADR-028
**Depends on**: T-COMPLY-001, T-COMPLY-003
**Files**: `imp_claude/code/genesis/workspace_state.py`, `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md`

V (delta) computed. H = T + V not computed. `gen-status` has no H column.

1. Add `compute_hamiltonian(events, feature, edge) → H` to `workspace_state.py`
2. Derive T from delta curve in `iteration_completed` events for this feature+edge
3. Store H on instance graph node per active edge
4. Add H column to `gen-status` default view: `feature | edge | iter | δ | H`
5. Tests: monotonically decreasing delta → T > 0; stalled → T = 0; H = T + V in all cases

---

### T-COMPLY-007: F_P Stub Removal — Fold-Back File is the Contract

**ADRs**: ADR-023, ADR-024, ADR-021
**Depends on**: T-COMPLY-001
**Files**: `imp_claude/code/genesis/fp_functor.py`, `imp_claude/design/adrs/ADR-024-recursive-actor-model.md`, `imp_claude/design/adrs/ADR-021-dual-mode-traverse.md`

`_mcp_invoke()` returns `skipped=True` when fold-back file absent. Fold-back file mechanism is the correct transport-agnostic contract — the engine is not responsible for launching the actor.

1. Remove stub language and `skipped=True` fallback from `fp_functor.py`
2. Missing fold-back file → raise `FpActorResultMissing` — caller is responsible for actor execution
3. Update ADR-024 §3 and ADR-021 §4 — fold-back file is the accepted invocation protocol; remove "future MCP call" language
4. Update tests — remove `skipped=True` on missing file assertions; assert `FpActorResultMissing`
5. Document: engine is transport-agnostic; actor launch (MCP, CLI, any) is the caller's concern

---

### T-COMPLY-008: F_P Fold-Back Contract — gen-iterate Actor Dispatch

**ADRs**: ADR-023, ADR-024
**Depends on**: T-COMPLY-007
**Status**: Engine side COMPLETE (2026-03-07). LLM-layer side pending.
**Files**: `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md`

**Architecture clarification** (ADR-023: no subprocess, no `claude -p`, ever):
The Python engine CANNOT issue MCP tool calls — MCP is the LLM layer's capability. The fold-back file IS the accepted invocation protocol:

```
ENGINE:     writes fp_intent_{run_id}.json → .ai-workspace/agents/
LLM LAYER:  reads manifest → invokes actor via MCP tool call → actor writes fp_result_{run_id}.json
ENGINE:     reads fp_result on next iteration
```

Engine side (T-008 DONE): `_mcp_invoke()` writes intent manifest, checks for result, raises `FpActorResultMissing` if absent. `FpActorResultMissing` is the observable signal to the LLM layer.

LLM-layer side (this task): Update `gen-iterate.md` to implement the dispatch loop:

1. After each engine iteration, check `.ai-workspace/agents/` for pending `fp_intent_*.json` manifests
2. For each pending manifest (status = "pending"): invoke `claude_code` MCP tool with the actor prompt
3. Actor writes `fp_result_{run_id}.json` → mark manifest status = "dispatched"
4. Re-run engine — it reads fold-back and continues
5. Document: actor self-evaluates against F_D checklist, writes `converged + delta + artifacts + spawns`
6. Test: unit test confirms gen-iterate processes pending manifests before re-invoking engine
