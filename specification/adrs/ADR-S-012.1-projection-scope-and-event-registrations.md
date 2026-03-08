# ADR-S-012.1: Projection Scope Limit and Event Type Registrations

**Series**: S
**Parent**: ADR-S-012 (Event Stream as Foundational Medium)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolutions 1 and 3

---

## What changes

Two amendments to ADR-S-012.

### Amendment A: Projection scope (Resolution 3)

ADR-S-012 §Asset redefined as a projection states:

> `Asset<Tn> := project(EventStream[0..n], asset_type, instance_id)`

This applies to `.ai-workspace/` and code domains. It does NOT apply to `specification/`.

**Adding explicit scope rule**:

> **`specification/` files are excluded from the event-first model.** Spec files are authoritative artifacts (ADR-S-001, ADR-S-002). `spec_modified` events (ADR-S-010) are the audit trail of changes to those files — not the substrate from which files are derived. The event-first model (`Asset = project(EventStream)`) applies to:
> - `.ai-workspace/` operational state
> - Code and test artifacts produced by the iterate engine
>
> It does NOT apply to:
> - `specification/core/`, `specification/requirements/`, `specification/features/`, `specification/adrs/`, `specification/verification/`

**Conflict resolution rule** (added to §Projection as the implementation contract):

> If a workspace file and the event log disagree, the event log is authoritative — regenerate the file from the stream.
> If a spec file and a `spec_modified` event disagree (hash mismatch), investigate via the file and git history — the file is authoritative for the spec domain.

### Amendment B: Event type registrations (Resolution 1)

Add the following event types to §Required event taxonomy. These were introduced in ADR-S-025/026 but not registered here.

**CONSENSUS events** (required when CONSENSUS functor is active on an edge):

```
proposal_published    { asset_id, asset_version, roster_size, quorum, min_duration, review_closes_at }
comment_received      { asset_id, participant, gating: bool, disposition: null }
vote_cast             { asset_id, asset_version, participant, verdict, conditions: [] }
asset_version_changed { asset_id, prior_version, new_version, materiality: material|non_material }
consensus_reached     { asset_id, asset_version, approve_ratio, participation_ratio, gating_comments_dispositioned }
consensus_failed      { asset_id, failure_reason, available_paths: [] }
recovery_path_selected { asset_id, path: re_open|narrow_scope|abandon }
```

**Named Composition / Intent Vector events**:

```
composition_dispatched    { intent_id, macro, version, bindings, vector_id }
intent_vector_converged   { vector_id, produced_asset_ref, edge }
intent_vector_blocked     { vector_id, reason, disposition: null }
```

All carry the universal fields `{instance_id, actor, causation_id, correlation_id}`. All conform to ADR-S-011.

---

## What does not change

- The four projection invariants (determinism, completeness, isolation)
- The saga invariant
- All existing required event types
- `iterate()` signature
- Context sources (pull + push)
- Universal fields `{instance_id, actor, causation_id, correlation_id}`

---

## References

- ADR-S-012 (parent)
- ADR-S-009.1 — companion: adds source-of-truth note to spec layer
- ADR-S-011.1 — companion: OL encoding of the same new event types
- ADR-S-025 — CONSENSUS event sources
- ADR-S-026 — Named composition event sources
- ADR-S-027 Resolutions 1 and 3
