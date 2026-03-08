# ADR-S-010.1: feature_proposal — requires_spec_change Invariant

**Series**: S
**Parent**: ADR-S-010 (Event-Sourced Spec Evolution)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolution 2

---

## What changes

ADR-S-010 defines the `feature_proposal` event and the Draft Features Queue. This amendment adds an explicit invariant linking `feature_proposal` to the `requires_spec_change` branch introduced in ADR-S-008.1.

### Amendment to §feature_proposal invariants

Add invariant:

> **`feature_proposal` events are only emitted when `requires_spec_change: true`**. An `intent_raised` event with `requires_spec_change: false` does NOT produce a `feature_proposal`. It produces a `composition_dispatched` event directly. Emitting `feature_proposal` for a gap that does not require a spec change is a pipeline conformance violation.

### Amendment to §The Draft Features Queue

The Draft Features Queue is the observable state of pending `feature_proposal` events that have not yet been promoted or rejected. This amendment clarifies what it contains:

> The Queue contains ONLY proposals that, if approved, will result in a `spec_modified` event. It does not contain dispatchable work items. Dispatchable work items (arising from `requires_spec_change: false` intents) are tracked in the workspace as active intent vectors.

### New field on feature_proposal schema

Add `requires_spec_change: true` as a required field on `feature_proposal` events (always `true` — the field is present to make the classification explicit and auditable):

```json
{
  "event_type": "feature_proposal",
  "data": {
    "requires_spec_change": true,
    ...existing fields...
  }
}
```

---

## What does not change

- `feature_proposal` schema (all existing fields unchanged; one field added)
- Draft Features Queue computation
- Promotion operation (F_H gate)
- Rejection operation
- `spec_modified` schema and invariants
- Causal chain model

---

## References

- ADR-S-010 (parent)
- ADR-S-008.1 — companion: adds requires_spec_change branch to Stage 3
- ADR-S-027 Resolution 2
