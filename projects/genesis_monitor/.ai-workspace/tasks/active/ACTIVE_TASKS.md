# Active Tasks — Genesis Monitor

## Completed (v1.0 — INT-GMON-001/002/003)

| # | Title | Status | Priority |
|---|-------|--------|----------|
| 1 | Write INTENT.md | completed | critical |
| 2 | Derive REQUIREMENTS.md from intent | completed | critical |
| 3 | Derive DESIGN.md from requirements | completed | critical |
| 4 | Implement code from design | completed | critical |
| 5 | Write unit tests | completed | critical |
| 6 | Write UAT/integration tests | completed | critical |

## Active (v2.0 — INT-GMON-004: v2.5 Alignment)

| # | Title | Status | Feature Vector | Priority |
|---|-------|--------|----------------|----------|
| 7 | Update INTENT.md with INT-GMON-004 | completed | - | critical |
| 8 | Update REQUIREMENTS.md (17 new REQs) | completed | - | critical |
| 9 | Update DESIGN.md (models, parsers, projections, routes) | completed | - | critical |
| 10 | Create feature vectors (REQ-F-GMON-002, 003) | completed | - | critical |
| 11 | Implement REQ-F-GMON-002: models + parsers | not_started | REQ-F-GMON-002 | critical |
| 12 | Implement REQ-F-GMON-003: projections + dashboard | not_started | REQ-F-GMON-003 | high |

## Active (v3.1 — INT-GMON-009: Multi-Design Tenant Observability)

| # | Title | Status | Feature Vector | Priority |
|---|-------|--------|----------------|----------|
| 13 | Add INT-GMON-009 to INTENT.md | completed | REQ-F-MTEN-001 | high |
| 14 | Add REQ-F-MTEN-001/002/003 to REQUIREMENTS.md | completed | REQ-F-MTEN-001 | high |
| 15 | Create ADR-004: tenant switching + filter propagation | completed | REQ-F-MTEN-001 | high |
| 16 | Implement design selector nav (project.html) | completed | REQ-F-MTEN-001 | high |
| 17 | Implement HTMX configRequest interceptor (project.html) | completed | REQ-F-MTEN-001 | high |
| 18 | Fix triggerReload() to preserve ?design= in scrubber | completed | REQ-F-MTEN-001 | high |
| 19 | Fix _get_historical_state design-only bug (routes.py) | completed | REQ-F-MTEN-001 | high |
| 20 | Fix PhaseEntry delta_curve kwarg bug (temporal.py) | completed | REQ-F-MTEN-001 | high |
| 21 | Add TestDesignTenancy (6 tests) + multi-tenant fixture events | completed | REQ-F-MTEN-001 | high |
| 22 | Create feature vector REQ-F-MTEN-001.yml | completed | REQ-F-MTEN-001 | medium |

## Active (v3.4 — INT-GMON-006: One-Stop Observability)

| # | Title | Status | Feature Vector | Priority |
|---|-------|--------|----------------|----------|
| 23 | Spawn REQ-F-GMON-004/005/006 from INT-GMON-006 | completed | — | high |
| 24 | REQ-F-GMON-004: intent→requirements CONVERGED | completed | REQ-F-GMON-004 | high |
| 25 | REQ-F-GMON-004: requirements→design CONVERGED | completed | REQ-F-GMON-004 | high |
| 26 | REQ-F-GMON-004: design→code CONVERGED | completed | REQ-F-GMON-004 | high |
| 27 | REQ-F-GMON-004: code↔unit_tests CONVERGED | completed | REQ-F-GMON-004 | high |
| 28 | REQ-F-GMON-005: intent→requirements | pending | REQ-F-GMON-005 | high |
| 29 | REQ-F-GMON-006: intent→requirements | pending | REQ-F-GMON-006 | high |

### REQ-F-GMON-004: intent→requirements CONVERGED
**Date**: 2026-03-07T19:10:30Z
**Iterations**: 1
**Evaluators**: 6/6 checks passed
**Asset**: .ai-workspace/spec/REQUIREMENTS.md (added §28 REQ-F-LINEAGE-001..004, §29 source findings)
**Next edge**: requirements→design

### REQ-F-GMON-004: requirements→design CONVERGED
**Date**: 2026-03-07T20:30:00Z
**Iterations**: 1
**Evaluators**: 5/5 checks passed
**Asset**: design/DESIGN.md (new file — §1 model changes, §2 projection changes, §3 template changes, §4 routes unchanged)
**Key decisions**:
- `spec_inventory(project_root)` — searches `.ai-workspace/spec/REQUIREMENTS.md` then `specification/REQUIREMENTS.md`; returns `set[str]` of `### REQ-F-*` / `### REQ-NFR-*` headings
- `telemetry_scanner(project_root)` — regex `req=["'](REQ-[\w-]+)["']` on `.py` files; same walk scope as code scanner
- `TraceabilityReport` gains: `telemetry_coverage`, `spec_defined_keys`, `orphan_keys`, `uncovered_keys` (all with empty defaults — backward compat)
- `build_traceability_view()` gains per-row: `spec_defined`, `telemetry_files`, `has_telemetry`, `is_orphan`, `is_uncovered`
- Template: 6-column table (added Spec + Telemetry); orphan badge (⚠ yellow), gap badge (◌ red)
- No route changes needed
**Next edge**: design→code

### REQ-F-GMON-004: code↔unit_tests CONVERGED
**Date**: 2026-03-07T20:48:00Z
**Iterations**: 1 (with 2 code fixes before convergence)
**Evaluators**: 379/379 tests pass
**Fixes applied (code, not tests)**:
1. `models/events.py`: Removed premature v2.9 entries (`manual_commit`, `transaction_aborted`) from `EVENT_TYPE_MAP` — count was 30 vs spec-contractual 28
2. `parsers/events.py`: Fixed `ABORT` branch to be conditional — `iteration_abandoned` was incorrectly mapped to `transaction_aborted`; pattern now consistent with `COMPLETE` and `FAIL` branches
**Checklist**: tests_pass=✅ req_tags_in_code=✅ req_tags_in_tests=✅ test_quality=✅ code_quality=✅
**Feature status**: **CONVERGED** (all 4 edges: requirements, design, code, unit_tests)

---

## Active (v3.5 — INT-GMON-010: Event Trail Graph Visualization)

| # | Title | Status | Feature Vector | Priority |
|---|-------|--------|----------------|----------|
| 30 | Spawn REQ-F-GVIZ-001 from INT-GMON-010 | completed | REQ-F-GVIZ-001 | high |
| 31 | REQ-F-GVIZ-001: requirements CONVERGED | completed | REQ-F-GVIZ-001 | high |
| 32 | REQ-F-GVIZ-001: design CONVERGED (ADR-007) | completed | REQ-F-GVIZ-001 | high |
| 33 | REQ-F-GVIZ-001: code↔unit_tests CONVERGED | completed | REQ-F-GVIZ-001 | high |

### REQ-F-GVIZ-001: All Edges CONVERGED
**Date**: 2026-03-08T01:00:00Z
**Iterations**: 1 (delta=0 first pass)
**Evaluators**: 463/463 tests pass
**Assets**:
- `design/adrs/ADR-007-d3-event-trail-graph.md` — D3.js v7 technology binding
- `server/routes.py` — `_build_graph_data()` helper + `GET /timeline/graph-data` route
- `templates/timeline.html` — D3.js graph section + legend + interaction handlers
- `tests/test_event_index.py` — 20 new tests (TestGraphDataRoute×9, TestBuildGraphDataHelper×5, TestParseEdgeNodes×6)
**Key decisions (ADR-007)**:
- D3.js v7 from CDN (no build step, satisfies REQ-NFR-001 no-framework constraint)
- JSON endpoint: server computes data, D3 renders SVG client-side
- Fixed horizontal node layout (canonical SDLC order), quadratic Bezier arcs
- Arc encoding: weight=log1p(iters)×2+1, colour=feature, opacity=recency, dash=status
- Node encoding: size=log1p(runs), fill=health, pulse=in_progress
- Interaction: arc/node click → filter bar + row de-emphasis (no page reload)
**Feature status**: **CONVERGED** (all 4 edges: requirements, design, code, unit_tests)

## Active (v3.6 — Executor Attribution)

| # | Title | Status | Feature Vector | Priority |
|---|-------|--------|----------------|----------|
| 34 | REQ-F-EXEC-001: design_recommendations CONVERGED | completed | REQ-F-EXEC-001 | high |
| 35 | REQ-F-EXEC-001: design (ADR-009) CONVERGED | completed | REQ-F-EXEC-001 | high |
| 36 | REQ-F-EXEC-001: code CONVERGED | completed | REQ-F-EXEC-001 | high |
| 37 | REQ-F-EXEC-001: unit_tests CONVERGED | completed | REQ-F-EXEC-001 | high |

### REQ-F-EXEC-001: All Edges CONVERGED
**Date**: 2026-03-09T19:15:00Z
**Iterations**: 1 per edge (delta=0 first pass)
**Evaluators**: 19 new tests pass (593/593 total)
**Assets**:
- `specification/design/EXEC_DESIGN_RECOMMENDATIONS.md` — 4 design ADRs
- `imp_fastapi/design/adrs/ADR-009-executor-attribution.md` — implementation ADR
- `models/events.py` — `Event.executor` + `Event.emission` fields
- `parsers/events.py` — `_infer_executor()` — OL-format→engine, flat→claude, explicit wins
- `projections/edge_runs.py` — `EdgeRun.executor/emission` + `_close_run()` fallback walk
- `models/core.py` — `EdgeConvergence.executor` field
- `projections/convergence.py` — capture executor from edge_converged event
- `server/routes.py` — `arc_style` field in run dicts for D3
- `templates/base.html` — CSS badge + arc classes (ADR-009)
- `templates/fragments/_convergence.html` — Executor badge column
- `templates/timeline.html` — executor-based dashArray + arc class + legend
- `tests/test_executor_attribution.py` — 19 tests (4 classes)
**Key decisions (ADR-009)**:
- `executor`/`emission` on `Event` base class (not subtypes) — all projections access uniformly
- Inference: `eventType` present → engine; `event_type` only → claude; explicit wins
- Arc: CSS `stroke-dasharray` via class — solid/dashed/dotted-amber; no JS library changes
- Badge: 4 CSS classes matching arc visual language (engine=green, claude=blue, retro=amber, unknown=grey)
**Feature status**: **CONVERGED** (all 5 edges)

---

## Dependency Graph

```
REQ-F-GMON-002 (models + parsers)
    └──► REQ-F-GMON-003 (projections + dashboard)

INT-GMON-009 (multi-tenant)
    └──► REQ-F-MTEN-001 (filter + selector + propagation) — CONVERGED

INT-GMON-006 (one-stop observability)
    ├──► REQ-F-GMON-004 (4-col lineage + telemetry scanner) — CONVERGED ✅
    ├──► REQ-F-GMON-005 (CQRS workspace hierarchy) — pending
    └──► REQ-F-GMON-006 (STATUS.md panel) — pending
```

REQ-F-GMON-002 must converge before REQ-F-GMON-003 can begin code iteration.
