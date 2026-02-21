# ADR-CG-005: Sensory Service Operating Modes for Codex

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005

---

## Context

Codex interaction is often task-scoped and foreground. The methodology requires continuous sensing semantics (interoceptive + exteroceptive) and review-gated proposal flow.

## Decision

Support two Codex-compatible sensory modes with identical event contracts:

1. **Foreground mode**: sensing pipeline runs during `aisdlc-start` and `aisdlc-status --health`.
2. **Background mode**: optional watcher process runs independent of active Codex turns.

Both modes emit the same sensory and triage events (`interoceptive_signal`, `exteroceptive_signal`, `affect_triage`, `draft_proposal`) and enforce the same review boundary before spec or code promotion.

## Rationale

- Matches Codex usage patterns while preserving methodology semantics.
- Keeps operational flexibility for solo and team workflows.

## Consequences

### Positive

- No semantic divergence between interactive and background monitoring.
- Easier rollout: foreground first, background optional.

### Negative

- Background mode introduces operational management overhead.

## References

- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-SENSE-001..005
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5.4
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §1.8
