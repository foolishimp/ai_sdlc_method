# ADR-S-026.2: gap_observation as feature_vector source_kind

**Series**: S
**Parent**: ADR-S-026 (Named Compositions, Five-Level Stack, Intent Vector Envelope)
**Status**: Accepted
**Date**: 2026-03-09
**Supersedes**: ADR-S-026.1 — restricted feature_vector source_kind to {abiogenesis, parent_spawn}, which was too narrow; gap-driven repair work on an existing spec-defined feature resumes that feature's trajectory and is a legitimate third origin that is not creation and not spawning
**Withdrawal Rationale**: ADR-S-026.1's subtype table defined feature_vector with source_kind ∈ {abiogenesis, parent_spawn}. This excluded the common case where a gap is discovered against an existing converged REQ-F-* feature — the gap closure work belongs to that feature's vector (it resumes it), not to a new vector. Forcing implementers to choose between misclassifying as abiogenesis or creating an orphan discovery_vector would cause tenant drift across implementations.
**Prior reference**: git tag `adr-deleted/ADR-S-026.1`

---

## What changes from ADR-S-026.1

### Amendment A carries forward unchanged

`requires_spec_change` field on composition expressions and the classification guidance table are unchanged. See ADR-S-026.1 §Amendment A for the full schema — it is fully carried forward here. The dispatch table extension (`missing_telemetry` gap type) also carries forward.

### Amendment B: vector subtype table — gap_observation added to feature_vector

The `feature_vector` subtype definition is updated:

```
feature_vector   = intent_vector where vector_type = feature,
                                       source_kind ∈ {abiogenesis, parent_spawn, gap_observation},
                                       profile ∈ {full, standard, hotfix, minimal}
```

Changes from ADR-S-026.1:
- `source_kind`: added `gap_observation`
- `profile`: expanded from `{full, standard}` to `{full, standard, hotfix, minimal}` — emergency and trivial feature work must be representable

All other subtype definitions carry forward unchanged:

```
discovery_vector = intent_vector where vector_type = discovery,
                                       source_kind = gap_observation

spike_vector     = intent_vector where vector_type = spike,
                                       source_kind ∈ {abiogenesis, gap_observation}

poc_vector       = intent_vector where vector_type = poc,
                                       source_kind ∈ {abiogenesis, parent_spawn}

hotfix_vector    = intent_vector where vector_type = hotfix,
                                       source_kind = gap_observation
```

### Routing rule for gap_observation on feature_vector

When `source_kind: gap_observation` on a `feature_vector`:

1. **The vector MUST reference an existing spec-defined `REQ-F-*` key.** It is resuming an existing feature trajectory, not creating a new feature.

2. **The existing feature vector's `status` transitions to `iterating`** on the relevant edge. The gap-observation `intent_raised` event becomes the `trigger_event` for that resumption.

3. **A new feature vector is not created.** Gap work on an existing `REQ-F-*` key does not generate a new feature_id.

The rule for distinguishing when to create a new vector vs resume existing:

| Gap situation | Correct action |
|--------------|----------------|
| Gap against existing `REQ-F-*` | Resume existing feature_vector with `source_kind: gap_observation` |
| Gap requiring a new `REQ-F-*` | `feature_proposal → spec_modified → new feature_vector` with `source_kind: abiogenesis` |

This gives a sharp rule: if no spec-defined `REQ-F-*` key exists for the gap, the gap is a spec gap — it requires `requires_spec_change: true` and must go through the `feature_proposal → F_H gate → spec_modified` path before any vector exists to resume.

---

## What does not change

- Amendment A: `requires_spec_change` field, classification guidance table, dispatch table
- Five-level stack (Levels 1–5)
- Named compositions (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY) and their definitions
- Intent vector tuple fields (ADR-S-026 §4.1)
- Project convergence vocabulary (quiescent, converged, bounded)
- Composition library governance rules
- Open questions OQ-1, OQ-2, OQ-3

---

## References

- ADR-S-026 (parent)
- ADR-S-026.1 (superseded) — git tag `adr-deleted/ADR-S-026.1`
- ADR-S-008.1 — requires_spec_change branch to Stage 3
- ADR-S-009.1 — vector subtype schema to workspace YAML
- ADR-S-010.1 — feature_proposal only emitted when requires_spec_change: true
- ADR-S-027 Resolutions 2 and 5
- Codex REVIEW `20260309T020552` Finding 2: gap-driven vector typing on existing REQ keys
- Codex REVIEW `20260309T020752` §Q5: gap_observation watch item (profile constraint too narrow)
- Claude marketplace response `20260309T030000`: gap_observation as third source_kind for feature_vector
