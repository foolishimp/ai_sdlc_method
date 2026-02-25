# Recovery Plan: Gemini Multi-Tenant Violation Remediation

**Created**: 2026-02-26
**Author**: Claude (imp_claude owner)
**Status**: PLANNED
**Trigger**: Gemini sessions authored 6 commits modifying imp_claude/ in violation of multi-tenant isolation (CLAUDE.md: "Each coder owns its imp_<name>/ folder exclusively")

## Context

Between 2026-02-25 01:42 and 09:08, Gemini sessions committed changes to `imp_claude/` across 6 commits (`c1587ad`, `d5c1d40`, `8bf0c0d`, `2536e8d`, `2dd53bf`, `99ef163`). An additional uncommitted rewrite of `__main__.py` and `engine.py` exists in the working tree.

Architectural evaluation found ~70% of changes are sound and address real gaps. This plan surgically keeps good work, fixes cross-tenant contamination, and restores architectural integrity.

---

## Phase 1: Discard Uncommitted Changes

- [ ] **P1.1** Discard uncommitted diff in `imp_claude/code/genisis/__main__.py`
- [ ] **P1.2** Discard uncommitted diff in `imp_claude/code/genisis/engine.py`
- [ ] **P1.3** Verify: `git diff -- imp_claude/` shows no changes

**Rationale**: The uncommitted rewrite is unstable and untested. The committed versions are the baseline for further work.

---

## Phase 2: Delete Dead Code

- [ ] **P2.1** Delete `imp_claude/code/genisis/state.py` (41 lines, no imports, redundant with fd_emit + workspace_state)
- [ ] **P2.2** Verify: `grep -r "from .state import\|from genisis.state import" imp_claude/` returns nothing

**Rationale**: `state.py` duplicates `fd_emit.emit_event()` and is never imported. Gemini prototyping artifact.

---

## Phase 3: Fix Cross-Tenant References in workspace_state.py

- [ ] **P3.1** Change bootloader marker search from `GEMINI.md` to `CLAUDE.md`
- [ ] **P3.2** Audit all path constants for `gemini_genesis/` references — replace with `claude/` or generic tenant path
- [ ] **P3.3** Review Python syntax: convert `str | None` to `Optional[str]` if Claude codebase uses older convention (check existing files for convention)
- [ ] **P3.4** Add module docstring crediting origin: "Ported from imp_gemini workspace_state.py, adapted for Claude tenant"

**Rationale**: workspace_state.py was copied verbatim from Gemini's tenant. It contains Gemini-specific path assumptions and bootloader markers.

---

## Phase 4: Decouple Spawn from Engine Loop

- [ ] **P4.1** Remove spawn detection block from `engine.py:iterate_edge()` (lines ~198-220)
- [ ] **P4.2** Move spawn decision into `__main__.py:cmd_run_edge()` — engine returns `IterationRecord`, CLI decides spawn
- [ ] **P4.3** Verify `engine.py` has no imports from `fd_spawn`
- [ ] **P4.4** Update `engine.py` docstring to clarify: "Engine evaluates convergence. Spawn decisions are orchestrator responsibility."

**Rationale**: Claude's design principle (ADR-019) is that the engine computes delta; the orchestrator decides what to do. Spawn detection is a lifecycle decision, not an evaluation concern. Gemini coupled them; Claude separates them.

---

## Phase 5: Validate Spawn Infrastructure

- [ ] **P5.1** Review `fd_spawn.py` — confirm no cross-tenant path assumptions
- [ ] **P5.2** Move hardcoded `_VECTOR_TYPE_PROFILES` mapping to `graph_topology.yml` or a dedicated config
- [ ] **P5.3** Move hardcoded `_VECTOR_TYPE_TIMEBOXES` to config
- [ ] **P5.4** Add YAML schema validation for child vectors before marking `pending`
- [ ] **P5.5** Verify `models.py` spawn dataclasses (SpawnRequest, SpawnResult, FoldBackResult) are clean

**Rationale**: fd_spawn.py addresses REQ-LIFE-001 (Recursive Spawn) — real value. But hardcoded mappings violate Claude's config-driven design principle.

---

## Phase 6: Validate Config and Hook Changes

- [ ] **P6.1** Review affect correction in `evaluator_defaults.yml` — Gemini was half-right: affect is NOT an evaluator type (spec §4.3 line 466 confirms), but affect IS still a processing phase (Reflex → Affect → Conscious). Gemini removed it as a phase, which is wrong. Additionally, affect is part of the IntentEngine input tuple: `IntentEngine(intent + affect)` (§4.6.1) — it gives "emotion" (urgency, severity, priority) to outgoing intents. Validate that evaluator_defaults.yml preserves all three roles: (a) processing phase, (b) valence vector on gap findings, (c) intent tuple component.
- [ ] **P6.2** Review `on-session-start.sh` abandoned iteration detection — confirm REQ-SUPV-003 compliance
- [ ] **P6.3** Review `on-stop-check-protocol.sh` edge-specific filtering fix — confirm correctness
- [ ] **P6.4** Review `graph_topology.yml` version bump (2.6.0 → 2.8.0) — confirm alignment with spec version

**Rationale**: The hook changes fix real bugs (edge filtering, abandoned iteration detection). The affect correction needs careful review — Gemini correctly identified that affect is not an evaluator type, but incorrectly stripped its role as a processing phase and missed its role as the emotional component of the intent tuple (§4.6.1).

---

## Phase 7: Validate Test Additions

- [ ] **P7.1** Run `test_functor_spawn.py` (26 tests) — confirm all pass
- [ ] **P7.2** Run `test_functor_complex.py` (23 tests) — confirm all pass
- [ ] **P7.3** Review conftest helpers (`scaffold_green_project`, `scaffold_broken_project`) — confirm no cross-tenant assumptions
- [ ] **P7.4** Run full test suite: `pytest imp_claude/tests/ -v` — confirm no regressions

**Rationale**: Tests are valid and fill real coverage gaps. Must pass after Phase 1-6 changes.

---

## Phase 8: Run Full Regression

- [ ] **P8.1** Run `pytest imp_claude/tests/ -v --tb=short` — all tests pass
- [ ] **P8.2** Run engine dogfood: `PYTHONPATH=imp_claude/code python -m genisis evaluate --edge "code↔unit_tests" --feature "REQ-F-ENGINE-001" --asset imp_claude/code/genisis/engine.py --deterministic-only --fd-timeout 120`
- [ ] **P8.3** Verify delta=0 (engine converges on own codebase)
- [ ] **P8.4** Verify events emitted to `.ai-workspace/events/events.jsonl`

**Rationale**: Final gate. Engine must still converge on its own codebase after remediation.

---

## Decision Log

| Component | Decision | Rationale |
|-----------|----------|-----------|
| `workspace_state.py` | KEEP + FIX | Real value (state detection), fix tenant references |
| `fd_spawn.py` | KEEP + FIX | Addresses REQ-LIFE-001, move hardcoded values to config |
| `models.py` spawn types | KEEP | Clean dataclass contracts |
| `state.py` | DELETE | Dead code, zero imports |
| `engine.py` spawn coupling | REFACTOR | Violates ADR-019 separation of concerns |
| `engine.py` config extensions | KEEP | `deterministic_only`, `fd_timeout` are useful |
| `__main__.py` helpers | KEEP | DRY refactoring is correct |
| `__main__.py` uncommitted | DISCARD | Unstable, untested |
| `cmd_run_edge` | KEEP | Needed for automated traversal |
| Affect correction | PARTIAL REVERT | Gemini right: affect ≠ evaluator type. Gemini wrong: affect IS still a processing phase + intent tuple component (§4.6.1). Restore phase role and intent emotion. |
| Hook bug fixes | KEEP | Real bugs fixed |
| Comparison reports | KEEP | Documentation only |
| Test additions | KEEP | Valid tests, real coverage |
| Conftest helpers | KEEP | Enable fast deterministic testing |
| Design doc v1 purge | KEEP | Forward-looking is correct |

---

## Acceptance Criteria

1. `git diff -- imp_claude/` clean (no uncommitted changes)
2. `state.py` deleted
3. `workspace_state.py` references only Claude-tenant paths
4. `engine.py` has no spawn imports or spawn detection code
5. Spawn decision lives in `__main__.py` orchestrator
6. All hardcoded spawn mappings moved to config
7. Full test suite passes
8. Engine dogfood delta=0

---

## Prevention

After remediation, enforce multi-tenant isolation:

1. Add pre-commit hook checking: commits from imp_gemini sessions must not touch imp_claude/
2. Document in CLAUDE.md: "Contributions from other tenants require review and re-implementation by the owning tenant"
3. Consider git CODEOWNERS file mapping imp_claude/ to Claude sessions
