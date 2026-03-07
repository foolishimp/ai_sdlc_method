# Active Tasks — imp_claude (Claude Code tenant)

*Updated: 2026-03-07*
*Overriding goal: [.ai-workspace/tasks/active/ACTIVE_TASKS.md](../../../tasks/active/ACTIVE_TASKS.md)*

---

## SPRINT: Spec Compliance Refactor

**Source**: Codex 20260307T165215 + Gemini 20260307T193000 gap reviews
**Principle**: Pre-release — no stubs, no legacy paths, no deprecated markers. Migrate or remove.
**No new ADRs** — all decisions already written.

### Sequencing

```
T-COMPLY-001 (event contract)   ←── start here, blocks 005/006/007/008
T-COMPLY-002 (context)          ←── parallel
T-COMPLY-003 (instance graph)   ←── parallel, blocks 006
T-COMPLY-004 (FPC anchoring)    ←── parallel, no dependencies

T-COMPLY-005 (transactions)     ←── after 001
T-COMPLY-006 (H-metric)         ←── after 001 + 003
T-COMPLY-007 (stub removal)     ←── after 001
T-COMPLY-008 (MCP actor)        ←── after 007
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

### T-COMPLY-004: Anchor REQ-F-FPC-* Keys in Spec

**ADRs**: none needed
**Files**: `imp_claude/code/genesis/fp_functor.py`, `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`, `specification/features/FEATURE_VECTORS.md`

11 `REQ-F-FPC-*` keys in `fp_functor.py` are real working code with no spec anchor. Every `Implements:` tag must resolve to a spec requirement.

1. Read `fp_functor.py` — extract all 11 `REQ-F-FPC-*` keys with descriptions
2. Add formal requirements to `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` — new `§ F_P Functor Construct` section
3. Update `FEATURE_VECTORS.md` — add FPC keys to `REQ-F-FP-001` requirements list
4. Update spec summary table (coverage counts)
5. Update `REQ-F-ROBUST-001` feature YAML — `status: converged` (currently stale `in_progress`)

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

### T-COMPLY-008: F_P Construct via MCP Actor (ADR-023/024)

**ADRs**: ADR-023, ADR-024
**Depends on**: T-COMPLY-007
**Files**: `imp_claude/code/genesis/fp_functor.py`

With stub removed (T-COMPLY-007), the actual MCP actor invocation needs implementing to close the construct loop.

1. Implement `_mcp_invoke()` — issue `claude_code` MCP tool call with actor prompt
2. Wire `CLAUDE_CODE_SSE_PORT` detection to live invocation
3. Actor writes fold-back to `.ai-workspace/agents/fp_result_{run_id}.json`
4. `_parse_actor_result()` already reads fold-back correctly — verify it handles `runId` from T-COMPLY-005
5. Integration test: MCP available + actor completes → `fp_result.converged` populated
6. Budget enforcement: pass `--max-budget-usd` to actor invocation
