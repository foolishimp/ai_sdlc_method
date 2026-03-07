# Active Tasks — ai_sdlc_method

*Updated: 2026-03-07*

---

## Overriding Goal: Shippable 1.0 via GCC Bootstrap Model

Each internal release uses the methodology on itself to build the next version.
Dogfooding is not a test — it is the build process.

### Release Ladder

| Version | Gate | Done when | Status |
|---------|------|-----------|--------|
| **v0.1** | Dogfooding enabled | Interactive agent path works; can iterate on own codebase using the methodology | ✅ **RELEASED** |
| **v0.2** | Runtime correct | T-001 + T-005 + T-007 + T-008: OL events, transaction model, F_P engine complete | ❌ open |
| **v0.3** | Observability verified | genesis_monitor correctly parses and displays a v0.2 methodology run end-to-end | ❌ open |
| **v0.4** | Ecosystem verified | Methodology applied to an external project; converges and all tests pass | ❌ open |
| **v1.0** | Assurance | v0.3 + v0.4 both green — product-level confidence, not just unit test confidence | ❌ open |

### Current state

| Artifact | Status |
|----------|--------|
| Spec | Complete — ADR-S-001..024 |
| Implementation Requirements | 83 REQ keys |
| Feature Vectors | 16 vectors, 83/83 tagged |
| Tests | 1078 unit passing |
| Active release | v0.1 — next target v0.2 |

### Post-1.0 (v1.1 sprint)
T-002 (context hierarchy), T-003 (instance graph), T-004 (FPC anchoring), T-006 (H-metric)

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
- **ADR-S-014**: OTLP/Phoenix — no design ADR, no implementation in any tenant
- **INTRO-005**: Build Health monitor — needs CI/CD integration
- **ADR cleanup**: Remove historical rationale sections from ADRs that no longer constrain construction — spec drift prevention
- **INT-TRACE-001**: Code annotation pass — 52/83 spec REQ keys have no Implements: tag
- **INT-TRACE-002**: Test annotation pass — 1078 tests with no Validates: REQ-* links
- **INT-TRACE-003**: Orphan fixture key cleanup in command .md files
