# ADR-CG-004: Event Replay and Recovery Strategy

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-LIFE-005, REQ-LIFE-007, REQ-TOOL-008

---

## Context

AISDLC treats `.ai-workspace/events/events.jsonl` as the source of truth; projections such as STATUS and feature files are derived views. Codex workflows need deterministic recovery after interruption and safe projection regeneration.

## Decision

Use **event replay as canonical recovery**:

1. `events.jsonl` is append-only and authoritative.
2. STATUS and feature trajectories are re-derived from events when stale or missing.
3. Checkpoints are immutable snapshots that accelerate restore but do not supersede event history.
4. Recovery tooling (`aisdlc_restore`) supports:
   - checkpoint restore for fast continuity,
   - full event replay for authoritative reconstruction.

## Rationale

- Maintains consistency with methodology event-sourcing model.
- Supports deterministic reconstruction across Codex sessions.
- Avoids state drift from manual projection edits.

## Consequences

### Positive

- Resilient workflow recovery with auditable provenance.
- Clear separation between source-of-truth and projections.

### Negative

- Requires strict discipline to keep event schemas stable.

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §7.5
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §1.5
- [ADR-010-spec-reproducibility.md](ADR-010-spec-reproducibility.md)
