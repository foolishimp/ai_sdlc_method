# ADR-S-009.1: Intent Vector Schema Extension and Source-of-Truth Clarification

**Series**: S
**Parent**: ADR-S-009 (Feature Vector Lifecycle — Spec vs Trajectory)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolutions 3 and 5

---

## What changes

Two amendments to ADR-S-009.

### Amendment A: Source-of-truth domain split (Resolution 3)

ADR-S-009 Layer 1 (Spec Definition) describes `specification/features/` as the authoritative feature definition. This is correct and confirmed. Adding explicit note:

> **`specification/` files are authoritative artifacts, not event projections.** `spec_modified` events (ADR-S-010) are the audit trail of changes to those files. They do not replace the files as source of truth. If a `spec_modified` event and the current file disagree (hash mismatch), the investigation begins with the file and git history — not by overwriting the file from the event log.

**Monitoring invariant**: a hash mismatch between a `specification/` file and its most recent `spec_modified` event MUST be classified as a **CRITICAL** gap by the sensory system. It triggers an `EVOLVE` cycle to resync the audit trail — either by emitting a corrective `spec_modified` event (if the file change was legitimate but unrecorded) or by reverting the file (if the change was unauthorised). This gap MUST NOT be silently ignored or deferred.

This complements ADR-S-012.1, which scope-limits ADR-S-012's event-first model to the `.ai-workspace/` and code domains.

### Amendment B: Intent vector schema extension (Resolution 5)

`feature_vector` is formally a subtype of `intent_vector` (ADR-S-026 §4):

```
feature_vector = intent_vector where:
  vector_type ∈ {feature}
  source_kind ∈ {abiogenesis, parent_spawn}
  profile     ∈ {full, standard}
```

The `.ai-workspace/features/active/*.yml` schema is extended with the following fields from the intent_vector tuple. All new fields are **optional for existing vectors**; **required for vectors created after this amendment**.

| New field | Type | Notes |
|-----------|------|-------|
| `source_kind` | enum | `abiogenesis \| gap_observation \| parent_spawn` |
| `trigger_event` | string \| null | Event ID that caused this vector; null for abiogenesis |
| `target_asset_type` | string | The asset type this vector produces |
| `composition_expression` | object | `{macro, version, bindings}` per ADR-S-026 §3 |
| `produced_asset_ref` | string \| null | Populated on convergence; null while iterating |
| `disposition` | enum \| null | `converged \| blocked_accepted \| blocked_deferred \| abandoned \| null` |

**Migration**: existing vectors without these fields are treated as:
- `source_kind: abiogenesis` (if no trigger event exists) or `parent_spawn` (if spawned from another vector)
- `trigger_event: null`
- `produced_asset_ref: null` (if still active) or the known asset path (if converged)
- `disposition: null` (if active) or `converged` (if known converged)

The two-layer deployment model (spec definition / workspace trajectory) is **unchanged** — this amendment extends the YAML schema, not the deployment model.

---

## What does not change

- Two-layer deployment model (Layer 1 spec definition, Layer 2 workspace trajectory)
- JOIN semantics (spec JOIN workspace by feature_id)
- Inflate / fold-back operations
- Profile zoom behaviour (poc/spike collapse)
- ORPHAN detection

---

## References

- ADR-S-009 (parent)
- ADR-S-012.1 — companion: scope-limits event-first model to .ai-workspace/
- ADR-S-026 §4 — intent_vector tuple definition
- ADR-S-027 Resolutions 3 and 5
