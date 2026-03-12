# Proxy Decision — module_decomposition→basis_projections (all 7 MVP features)

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T14:50:00Z
**Features**: REQ-F-PROJ-001, REQ-F-NAV-001, REQ-F-UX-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001, REQ-F-CTL-001
**Edge**: module_decomposition→basis_projections
**Gate**: human_approves_projections
**Artifact**: imp_react_vite/design/module_decomp/BASIS_PROJECTIONS.md

## Criterion 1: Projection boundaries are sensible — no confusing scope splits

**Evidence**:
- 30 projections in a 7×14 intersection matrix. No feature touches more than 8 modules — well within acceptable complexity.
- REQ-F-PROJ-001 correctly defines all shared TypeScript types in P-01-API. Later projections (P-04-API, P-05-API, P-06-API, P-07-API) extend WorkspaceApiClient without re-declaring types — correct modular extension pattern.
- P-07-SWH notes REQ-F-CTL-001 adds nothing new to server-write-handler (CTL reuses SUP's write path) — the zero-work projection is explicitly documented rather than silently omitted. This is correct.
- ControlSurface (P-07-FCT) scope is clearly bounded: imports GateActionPanel and AutoModeToggle from feature-supervision via prop types as contracts. Cross-module React import is explicit, not implicit.
- Projection boundaries align with the "coherent unit of developer ownership" criterion.
**Result**: PASS

## Criterion 2: Evaluator contracts match business intent — tests will catch real bugs

**Evidence**:
- All error types are named (ApiError, WriteError, ReadError) — no generic throw/exception. Evaluator contracts will catch missing error handling.
- P-05-SWR (isStuck): success case "returns true when 3 consecutive iteration_completed events for same feature+edge have identical delta" directly matches REQ-F-SUP-004 AC2. A test can verify this with a fixture of 3 identical events.
- P-05-SWH (emitEvent): failure case documented as "lock acquisition timeout → WriteError{code: LOCK_TIMEOUT}" — server returns 503. A test with a pre-held lock will exercise this path.
- P-06-SWR (TraceabilityScanner): "malformed JSONL line → skip, count as readError in result.warnings" — observable side effect (warnings array) is testable.
- P-03-APP (useWorkspacePoller): side effect "on mount: calls refreshAll() immediately then every 30000ms" — testable with vi.useFakeTimers() in Vitest.
- Evaluator contracts across 30 projections all specify at least one success case, one failure/error case, and side effects where applicable.
**Result**: PASS

## Criterion 3: Coverage check passes — no capability gaps or double-counting

**Evidence**:
- Section 3 (Feature Coverage Check) explicitly verifies all 7 features:
  - REQ-F-PROJ-001: 7 projections, union covers workspace CRUD, attention badges, unavailable state, server validation
  - REQ-F-NAV-001: 3 projections, union covers ROUTES constant, NavHandle typed variants, PlaceholderPage dead-link prevention, server nav routes
  - REQ-F-UX-001: 3 projections, union covers FreshnessIndicator 5-state machine, useWorkspacePoller 30s timer, CommandLabel + CMD helper
  - REQ-F-OVR-001: 4 projections, union covers fixed-height grid layout, ChangeHighlighter, overview endpoint, FeatureStatusCounts
  - REQ-F-SUP-001: 5 projections, union covers HumanGateQueue, FeatureList sorted order, GateActionPanel with comment enforcement, isStuck server-side, gate write path
  - REQ-F-EVI-001: 4 projections, union covers TraceabilityTable, EventDetailPanel with line-index NavHandle, GapAnalysisPanel re-run, traceability scan endpoint
  - REQ-F-CTL-001: 2 projections, union covers ControlSurface panel, SpawnFeaturePanel, auto-mode event derivation
- workspaceStore.loadWorkspace built incrementally across P-03-STO→P-04-STO→P-05-STO→P-06-STO with final Promise.all — no duplication, progressive enhancement correctly documented.
- No capability appears in zero projections. No capability owned by two projections.
**Result**: PASS

## Summary

All 3 criteria PASS. 30 projections cover all 7 MVP features with clean boundaries. Evaluator contracts are concrete and testable. Coverage check passes with no gaps or overlaps. The Wave 1-4 construction sequence enables up to 5 parallel agents in Wave 3.

**Result**: APPROVED — all 7 features advance to code↔unit_tests
