# ADR-CG-010: CONSENSUS Saga as Review-Cycle Projection

**Status**: Accepted
**Date**: 2026-03-09
**Deciders**: Codex Genesis Design Authors
**Requirements**: REQ-F-CONSENSUS-001, REQ-F-CDX-006, REQ-DATA-CDX-002, REQ-BR-CDX-002

---

## Context

The shared spec now gives sufficient methodology-level semantics for multi-party review:

- ADR-S-025 defines CONSENSUS quorum, gating comments, participation floors, vote resets, and typed failure outcomes.
- ADR-S-029 binds `composition_dispatched` to a compiled intermediate.
- ADR-S-030.1 moves converged-gap repair to immutable child lineage.

What the spec still leaves to implementations is the concrete review collection mechanism. The Codex tenant already treats the event log as the authoritative replay surface and already models observers as stateless supervisor-side watchers over the log. We need a local design decision that turns CONSENSUS into a buildable tenant package without introducing a second mutable review-state artifact.

## Decision

Adopt **review-cycle projection** as the Codex tenant binding for the CONSENSUS supervisory saga.

1. Review state is reconstructed from events, not from a mutable session document.
2. The primary key is `(review_id, cycle_id)`, not `review_id` alone.
3. A review cycle begins with `consensus_requested`.
4. Material reset begins a new cycle via `review_reopened`.
5. Observer and relay invocations are stateless and must rehydrate current state before writing.
6. The package is choreographed by local invariants, not by a central review orchestrator.

### Canonical event set

The Codex tenant binds CONSENSUS to the following event vocabulary:

- `consensus_requested`
- `comment_received`
- `comment_dispositioned`
- `vote_cast`
- `review_reopened`
- `consensus_reached`
- `consensus_failed`

`review_closed` is not required as a stored event. Closure is derived from `review_closes_at` plus the current clock unless a tenant later adds an explicit close optimization.

### Projection contract

The tenant SHALL expose replay-derived functions equivalent to:

- `current_cycle(review_id) -> cycle_id`
- `session_state(review_id, cycle_id) -> ordered events`
- `gating_comments(review_id, cycle_id) -> comment set`
- `vote_snapshot(review_id, cycle_id) -> valid votes`
- `quorum_state(review_id, cycle_id, now) -> pass | fail | deferred`

### Safety rule

Every observer trigger must carry enough context to reject stale or misrouted work:

- `observer_id`
- `trigger_reason`
- `review_id`
- `cycle_id`
- `artifact`
- `source_run_id`

If the rehydrated state does not match the trigger context, the observer or relay exits without emitting review mutations.

### Choreography rule

The Codex tenant must not centralize review progression in an imperative `gen-consensus-open` style coordinator. The supervisory saga advances because:

- observers subscribe to review-cycle events,
- relays respond only when their local invariants are satisfied,
- closeout occurs only from replay-derived terminal state.

If a new implementation step requires imperative cross-component sequencing, that is design pressure to surface a missing invariant rather than to grow a controller.

## Rationale

- Preserves the event-first recovery and replay model already used by the Codex runtime.
- Avoids a parallel mutable session artifact that could drift from the event log.
- Handles ADR-S-025 vote reset semantics cleanly by making cycle boundaries explicit.
- Keeps the observer/relay implementation stateless and idempotent.
- Keeps the CONSENSUS package aligned with ADR-S-031's supervisory saga model rather than drifting into imperative orchestration.

## Consequences

### Positive

- CONSENSUS becomes implementable as a tenant package without further spec work.
- Monitor state can be derived from the same replay logic as runtime state.
- Duplicate triggers are easier to suppress because the projection key is explicit.

### Negative

- `review_id` alone is not enough; the tenant must manage cycle IDs explicitly.
- Replay logic becomes part of the runtime surface, not just monitor logic.
- Event schema discipline matters more because review state is fully projection-derived.

## References

- [ADR-S-025-consensus-functor.md](../../../specification/adrs/ADR-S-025-consensus-functor.md)
- [ADR-S-029-the-dispatch-contract.md](../../../specification/adrs/ADR-S-029-the-dispatch-contract.md)
- [ADR-S-030.1-immutable-lineage-supersedes-gap-observation-resume.md](../../../specification/adrs/ADR-S-030.1-immutable-lineage-supersedes-gap-observation-resume.md)
- [ADR-CG-004-event-replay-and-recovery.md](ADR-CG-004-event-replay-and-recovery.md)
- [ADR-011-consciousness-loop-at-every-observer.md](ADR-011-consciousness-loop-at-every-observer.md)
