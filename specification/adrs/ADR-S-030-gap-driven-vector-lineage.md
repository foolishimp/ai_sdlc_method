# ADR-S-030: Immutable Lineage Rule — Gap-Driven Vector Typing

**Series**: S
**Status**: Proposed
**Date**: 2026-03-09
**Scope**: Vector model refinement — typing and lineage for repair work

--- 

## Context

ADR-S-026 unified vectors into `intent_vector`. However, the typing rule for work discovered against an already-converged feature remained ambiguous (Codex residual finding #2). If a gap (e.g., `missing_telemetry`) is found on `REQ-F-123`, do we re-open the original vector or spawn a new one?

## Decision

### The Immutable Lineage Rule

Converged trajectories are **Immutable**. Once a feature vector reaches `status: converged`, its historical trajectory MUST NOT be modified or reverted.

### Repair Work as Child Intent Vectors

Any work discovered by a gap evaluator against an existing requirement MUST spawn a **NEW** intent vector with the following typing rules:

1.  **source**: `gap`
2.  **parent_vector_id**: The ID of the converged parent feature (e.g., `REQ-F-123`).
3.  **subtype**: `repair_vector` (or `telemetry_vector`, `test_vector` based on gap type).
4.  **resolution_level**: The level where the gap was observed (e.g., `telemetry`, `code`).

### Causal Mapping

The project graph MUST project these as child branches. The repair vector carries its own trajectory and converges independently. The parent feature's lineage facet will eventually include the child's convergence as a "Stability Anchor."

## Consequences

- **Positive**: Preserves event-sourced history. No "state-reversion" side effects. Clear causal audit trail from initial creation to every subsequent repair.
- **Negative**: Increases the number of active intent vectors in large projects.
