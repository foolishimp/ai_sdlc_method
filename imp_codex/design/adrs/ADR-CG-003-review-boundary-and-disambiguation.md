# ADR-CG-003: Review Boundary and Spec-First Disambiguation

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-EVAL-003, REQ-CTX-001, REQ-UX-002, REQ-SENSE-005

---

## Context

Codex can modify files through tooling, but AISDLC requires that ambiguity is resolved upstream (intent/spec/design) and human accountability is preserved at boundaries with architectural or governance impact.

We need a consistent review boundary policy for Codex flows.

## Decision

Adopt a **spec-first review boundary**:

1. Prefer disambiguation at intent/spec/design edges before code mutation.
2. Treat runtime observability as a secondary unblock and validation source.
3. Require explicit human approval for:
   - `requirements→design` convergence when mandatory dimensions are unresolved,
   - spec mutations (`spec_modified`) from feedback loops,
   - promotion decisions on human-required edges.
4. Allow autonomous drafting (including sensory proposals), but not autonomous final promotion for human-gated edges.

## Rationale

- Aligns with shared methodology constraints and your project direction (spec/design first).
- Reduces rework caused by coding through unresolved ambiguity.
- Preserves traceable accountability in event history.

## Consequences

### Positive

- Higher design correctness before implementation.
- Clear audit trail for governance and design decisions.

### Negative

- Additional human checkpoints can increase cycle time on some edges.

## References

- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-EVAL-003, REQ-UX-002, REQ-SENSE-005
- [ADR-012-two-command-ux-layer.md](ADR-012-two-command-ux-layer.md)
- [ADR-013-multi-agent-coordination.md](ADR-013-multi-agent-coordination.md)
