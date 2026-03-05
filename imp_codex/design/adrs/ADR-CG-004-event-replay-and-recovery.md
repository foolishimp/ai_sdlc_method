# ADR-CG-004: Event Replay and Recovery Strategy

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-LIFE-005, REQ-LIFE-007, REQ-TOOL-008

---

## Context

AISDLC treats `.ai-workspace/events/events.jsonl` as the source of truth; projections such as STATUS and feature files are derived views. Codex workflows need deterministic recovery after interruption and safe projection regeneration.

## Decision

Use **event replay as canonical recovery**, aligned to the OpenLineage transaction model:

1. `events.jsonl` is append-only and authoritative; canonical write schema is OpenLineage RunEvent (ADR-S-011).
2. STATUS and feature trajectories are re-derived from events when stale or missing.
3. Recovery scan is `runId`-based transaction detection: any `START` with no terminal `COMPLETE|FAIL|ABORT` is an open transaction (ADR-S-015).
4. For open transactions, compare current filesystem hashes to the `sdlc:inputManifest` captured at `START`; emit `gap_detected` when uncommitted writes are found.
5. Checkpoints are immutable snapshots that accelerate restore but do not supersede event history.
6. Recovery tooling (`/gen-checkpoint` + replay workflows) supports:
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

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md) §7.5
- [ADR-S-011-openlineage-unified-metadata-standard.md](../../../specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md)
- [ADR-S-012-event-stream-as-formal-model-medium.md](../../../specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md)
- [ADR-S-015-unit-of-work-transaction-model.md](../../../specification/adrs/ADR-S-015-unit-of-work-transaction-model.md)
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §1.5
- [ADR-010-spec-reproducibility.md](ADR-010-spec-reproducibility.md)
