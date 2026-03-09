# Active Tasks — ai_sdlc_method

*Updated: 2026-03-09*

---

## Overriding Goal: Shippable 1.0 via GCC Bootstrap Model

Each internal release uses the methodology on itself to build the next version.
Dogfooding is not a test — it is the build process.

### Release Ladder

| Version | Gate | Done when | Status |
|---------|------|-----------|--------|
| **v0.1** | Dogfooding enabled | Interactive agent path works; can iterate on own codebase using the methodology | ✅ **RELEASED** |
| **v0.2** | Engine-core correctness (Claude tenant) | T-001 + T-005 + T-007 + T-008: OL events, runId threading, F_P fold-back contract — deterministic evaluation path correct. Human gate (REQ-EVAL-003) and full MVP assurance deferred to v1.0. | ✅ **RELEASED** |
| **v0.3** | Observability verified | genesis_monitor correctly parses and displays a v0.2 methodology run end-to-end | ✅ **RELEASED** (2026-03-09) |
| **v0.4** | Ecosystem verified | Methodology applied to an external project; converges and all tests pass | ✅ **RELEASED** (2026-03-09) |
| **v1.0** | Assurance | v0.3 + v0.4 both green — product-level confidence, not just unit test confidence | ✅ **RELEASED** (2026-03-09) |

### Current state

| Artifact | Status |
|----------|--------|
| Spec | Complete — ADR-S-001..026 |
| Implementation Requirements | 83 REQ keys |
| Feature Vectors | 15 vectors, 83/83 tagged |
| Tests | 1567 imp_claude + 574 genesis_monitor = 2141 unit passing; 19 e2e monitor + 27 convergence + 5 UAT = 51 e2e |
| Active release | v1.0 — all gates cleared. v1.1 sprint: T-002 ✅ DONE, T-006 ✅ DONE. Remaining: T-004 (FPC audit, design-tier only) |

### Post-1.0 (v1.1 sprint) — ALL COMPLETE (2026-03-09)
T-002 ✅ (context hierarchy — 6-level, manifests, installer), T-003 ✅ (instance graph), T-004 ✅ (FPC audit), T-006 ✅ (H-metric)

### REQ-F-EVOL-001: design→uat_tests CONVERGED
**Date**: 2026-03-08T09:00:00Z
**Iterations**: 1
**Evaluators**: 7/7 checks passed (5 agent, 2 human)
**Asset**: imp_claude/tests/uat/test_uc_evol_001_spec_evolution.feature (20 Gherkin scenarios)
**Next edge**: none — REQ-F-EVOL-001 fully converged across all standard profile edges

---

### Known Spec Inconsistencies (tracked, not blocking)
- **REQ-CTX-002 vs ADR-S-022**: Resolved — REQ-CTX-002 updated 2026-03-07 to 6-level hierarchy matching ADR-S-022. Implementation work in T-COMPLY-002 (v1.1).
- **REQ-EVAL-003 (human gate)**: Critical/Phase 1 in spec but not in v0.2 scope. v0.2 gate is engine-core correctness only. Human gate deferred to v1.0 assurance tier.

---

## Tenant Task Files

| Tenant | Task File | Sprint |
|--------|-----------|--------|
| Claude | [.ai-workspace/claude/tasks/active/ACTIVE_TASKS.md](../../claude/tasks/active/ACTIVE_TASKS.md) | Spec Compliance Refactor (T-COMPLY-001..008) |
| Gemini | (no active sprint) | — |
| Codex | (no active sprint) | — |

---

## Backlog (cross-tenant)

- **Marketplace Observer** (REQ-LIFE-010 variant): Feature vector for per-tenant implementation of ADR-S-024 consensus decision gate — session-start scan, task-boundary gate, ambiguity routing. Evaluate within MVP context before spawning.
- **ADR-S-014**: OTLP/Phoenix — Gemini tenant has an OTLP relay implementation; ratified design ADR missing for all tenants. Claude tenant: no design ADR, no implementation.
- **INTRO-005**: Build Health monitor — needs CI/CD integration
- **ADR cleanup**: Remove historical rationale sections from ADRs that no longer constrain construction — spec drift prevention
- **INT-TRACE-001**: Code annotation pass — 52/83 spec REQ keys have no Implements: tag
- **INT-TRACE-002**: Test annotation pass — 1078 tests with no Validates: REQ-* links
- **INT-TRACE-003**: Orphan fixture key cleanup in command .md files
