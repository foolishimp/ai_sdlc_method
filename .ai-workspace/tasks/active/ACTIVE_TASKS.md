# Active Tasks — ai_sdlc_method

*Updated: 2026-03-10*

---

## Overriding Goal: Shippable 3.0-beta via GCC Bootstrap Model

Genesis is the GCC of AI-augmented software. The installer IS CI/CD (deploys Genesis
to any project). events.jsonl + genesis_monitor IS production telemetry (Genesis
observes itself). CONSENSUS exercises the full evaluator triad (F_D + F_P + F_H).

Each internal release uses the methodology on itself to build the next version.
Dogfooding is not a test — it is the build process.

### Release Ladder

| Version | Gate | Done when | Status |
|---------|------|-----------|--------|
| **v0.1** | Dogfooding enabled | Interactive agent path works; can iterate on own codebase using the methodology | ✅ **RELEASED** |
| **v0.2** | Engine-core correctness (Claude tenant) | T-001 + T-005 + T-007 + T-008: OL events, runId threading, F_P fold-back contract | ✅ **RELEASED** |
| **v0.3** | Observability verified | genesis_monitor correctly parses and displays a v0.2 methodology run end-to-end | ✅ **RELEASED** (2026-03-09) |
| **v0.4** | Ecosystem verified | Methodology applied to an external project; converges and all tests pass | ✅ **RELEASED** (2026-03-09) |
| **v1.0** | Assurance | v0.3 + v0.4 both green — product-level confidence | ✅ **RELEASED** (2026-03-09) |
| **v2.10.0** | Asset Graph Model formalisation | 339 commits: Bootloader, OL events, CONSENSUS, genesis_monitor, multi-tenant parity, executor attribution, 1967 tests | ✅ **RELEASED** (2026-03-10) |
| **v3.0.0-beta.1** | MVP complete | F_P actor dispatch (MCP round-trip) e2e validated — engine can autonomously construct, not just evaluate | 🔴 **IN PROGRESS** |

### MVP Feature Set (v3.0.0-beta.1 gate)

| Feature | Description | Status |
|---------|-------------|--------|
| Spec + Graph topology | ADR-S-001..031, 86 REQ keys, 10-node graph | ✅ done |
| Installer (= CI/CD) | gen-setup.py deploys Genesis to any project | ✅ done |
| Commands (interactive) | 13 /gen-* commands, interactive F_P path | ✅ done |
| Engine — F_D path | Deterministic evaluation, OL events, runId causation | ✅ done |
| Genesis Monitor (= telemetry) | Full observability stack, executor attribution | ✅ done |
| CONSENSUS (F_H gate) | Full evaluator triad — design APPROVED 2026-03-10 | ✅ done |
| **Engine — F_P path** | **Actor dispatch via MCP round-trip, fold-back** | 🔴 **THE GAP** |
| E2E validated | All e2e tests pass (downstream of F_P) | 🔴 blocked on F_P |

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

### REQ-F-TOOL-015: code↔unit_tests CONVERGED
**Date**: 2026-03-10
**Iterations**: 1
**Fix**: Added `# Validates: REQ-TOOL-015` to `imp_claude/tests/uat/test_install_e2e.py:1`
**Effect**: L2 test gap (REQ-TOOL-015) from gen-gaps now closed

---

### REQ-F-INTENT-001: requirements CONVERGED + design CONVERGED
**Date**: 2026-03-10
**Requirements**: REQ-INTENT-002/003/004 — all defined in spec with ACs ✓
**Design**: Covered by ADR-010 (INTENT-004 spec hash), ADR-011 (consciousness loop), ADR-014 (INTENT-002 binding), ADR-015 (INTENT-003 ecosystem sensing) — no new ADR needed
**Next edge**: code↔unit_tests
**What code needs**: `# Implements: REQ-INTENT-002/003/004` tags in relevant modules + `context_hash` actual SHA-256 computation in `config_loader.py`

---

### REQ-F-SCHEMA-DISC-001: code↔unit_tests CONVERGED
**Date**: 2026-03-10
**Iterations**: 2
**Evaluators**: 14/14 required checks passed (1 skipped: type_check — no mypy configured)
**Asset**: imp_claude/tests/test_schema_discovery.py (42 tests, 93% coverage)
**Fixes**: removed unused imports in schema_discovery.py + test file; ruff format applied
**Next edge**: uat_tests (pending — profile: standard; human gate required for UAT)

---

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

## New: REQ-F-INTENT-001 — Intent Composition Layer

**Status**: Pending
**Source**: PROP-001 (approved 2026-03-10)
**Priority**: high

Intent composition layer: REQ-INTENT-002 (compose intents from observations),
REQ-INTENT-003 (deduplication), REQ-INTENT-004 (prioritisation). Blocks Phase 2
consciousness loop — system cannot autonomously generate/compose intent without this.

**Requirements**: REQ-INTENT-002, REQ-INTENT-003, REQ-INTENT-004
**Start with**: `/gen-iterate --edge "requirements→design" --feature "REQ-F-INTENT-001"`

---

## New: REQ-F-TELEM-001 — Telemetry Tagging Phase 1

**Status**: Pending
**Source**: PROP-006 (approved 2026-03-10)
**Priority**: medium

Add `req=` telemetry tags to logging/metrics across engine.py, evaluator execution,
and command execution paths. ~85 REQ keys to tag. Required for Phase 2 homeostasis.

**Requirements**: all implemented REQ keys
**Start with**: `/gen-iterate --edge "code↔unit_tests" --feature "REQ-F-TELEM-001"`

---

## New: REQ-F-TOOL-015 — Tag installer tests with Validates: REQ-TOOL-015

**Status**: Pending
**Source**: PROP-007 (approved 2026-03-10)
**Priority**: medium

1-line fix: add `# Validates: REQ-TOOL-015` to test_install_e2e.py.
REQ-TOOL-015 "Workspace Placement at Project Root" has code but no test tag.

**Requirements**: REQ-TOOL-015
**Start with**: edit `imp_claude/tests/uat/test_install_e2e.py` directly

---

## New: REQ-F-EVOL-NFR-002 — Resolve orphan REQ-EVOL-NFR-002 tag

**Status**: Pending
**Source**: PROP-008 (approved 2026-03-10)
**Priority**: low

REQ-EVOL-NFR-002 in workspace_gradient.py and workspace_state.py not in spec.
Either define it in AISDLC_IMPLEMENTATION_REQUIREMENTS.md or correct tag to REQ-EVOL-005.

**Requirements**: REQ-EVOL-NFR-002
**Start with**: `/gen-iterate --edge "code↔unit_tests" --feature "REQ-F-EVOL-NFR-002"`

---

## Backlog (cross-tenant)

- **Marketplace Observer** (REQ-LIFE-010 variant): Feature vector for per-tenant implementation of ADR-S-024 consensus decision gate — session-start scan, task-boundary gate, ambiguity routing. Evaluate within MVP context before spawning.
- **ADR-S-014**: OTLP/Phoenix — Gemini tenant has an OTLP relay implementation; ratified design ADR missing for all tenants. Claude tenant: no design ADR, no implementation.
- **INTRO-005**: Build Health monitor — needs CI/CD integration
- **ADR cleanup**: Remove historical rationale sections from ADRs that no longer constrain construction — spec drift prevention
- **INT-TRACE-001**: Code annotation pass — 52/83 spec REQ keys have no Implements: tag
- **INT-TRACE-002**: Test annotation pass — 1078 tests with no Validates: REQ-* links
- **INT-TRACE-003**: Orphan fixture key cleanup in command .md files
