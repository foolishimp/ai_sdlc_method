# Active Tasks — ai_sdlc_method

*Updated: 2026-03-07*

---

## Overriding Goal: Spec-Compliant MVP

Bring the Claude Code implementation into full compliance with the accepted spec
(ADR-S-001..022) before any further feature work. The target is a runtime that
does what the spec says, with no stubs, no legacy parallel paths, and no
deprecated markers.

**Definition of done**: All 8 T-COMPLY tasks resolved. Tests green. No fd_emit
references. No skipped=True fallback in the F_P path. Event taxonomy matches
ADR-S-011 RunState contract. Context merge matches ADR-S-022 6-level hierarchy.

**Current state**:

| Artifact | Status |
|----------|--------|
| Spec | Complete — ADR-S-001..022, 4 primitives, Hamiltonian, Tournament, Sensory |
| Implementation Requirements | 83 REQ keys |
| Feature Vectors | 16 vectors, 83/83 tagged |
| Tests | 1078 unit passing |
| Compliance | 8 open T-COMPLY tasks (see Claude tenant below) |

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
