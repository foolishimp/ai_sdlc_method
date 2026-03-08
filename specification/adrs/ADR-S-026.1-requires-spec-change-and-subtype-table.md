# ADR-S-026.1: requires_spec_change Field and Vector Subtype Table

**Series**: S
**Parent**: ADR-S-026 (Named Compositions, Five-Level Stack, Intent Vector Envelope)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolutions 2 and 5

---

## What changes

Two amendments to ADR-S-026.

### Amendment A: requires_spec_change field on composition expressions (Resolution 2)

ADR-S-026 §3 defines the typed composition expression emitted by `gap.intent`. Add `requires_spec_change` as a required field:

```json
{
  "event_type": "intent_raised",
  "intent_id": "INT-DATA-003",
  "requires_spec_change": false,
  "composition": {
    "macro": "SCHEMA_DISCOVERY",
    "version": "v1",
    "bindings": {
      "dataset": "data/raw/transactions.parquet",
      "notebook": "jupyter://dev-env",
      "review": "F_H"
    }
  },
  "vector_type": "discovery",
  "gap_type": "missing_schema",
  "triggered_by": "data_pipeline→data_contract edge — no schema_document found"
}
```

**Classification guidance** (how the gap evaluator sets this field):

| `gap_type` | `requires_spec_change` | Reason |
|-----------|----------------------|--------|
| `missing_schema` | false | Existing spec covers data contracts; gap is implementation |
| `missing_requirements` | true | No spec coverage exists; new requirements needed |
| `missing_design` | false | Requirements exist; gap is design/code |
| `unknown_risk` | false | POC within existing scope |
| `unknown_domain` | true | New domain not in spec scope |
| `spec_drift` | true | Spec must be updated to reflect reality |
| `missing_consensus` | true | Governance change required |

Note: this table is a starting point. Implementations may extend it. The classification is always a judgment call by the gap evaluator — the table is guidance, not an exhaustive rule.

**Dispatch table update**: add `missing_telemetry` gap type (identified in ADR-S-027 as missing):

| Gap type | Named composition | requires_spec_change |
|----------|------------------|---------------------|
| `missing_telemetry` | BUILD(code + req_tags) | false |

### Amendment B: Vector subtype table (Resolution 5)

Add to ADR-S-026 §4 (Intent Vector as Orchestration Envelope) the formal subtype mappings:

```
feature_vector   = intent_vector where vector_type = feature,
                                       source_kind ∈ {abiogenesis, parent_spawn},
                                       profile ∈ {full, standard}

discovery_vector = intent_vector where vector_type = discovery,
                                       source_kind = gap_observation

spike_vector     = intent_vector where vector_type = spike,
                                       source_kind ∈ {abiogenesis, gap_observation}

poc_vector       = intent_vector where vector_type = poc,
                                       source_kind ∈ {abiogenesis, parent_spawn}

hotfix_vector    = intent_vector where vector_type = hotfix,
                                       source_kind = gap_observation
```

ADR-S-009's `feature_vector` two-layer model maps to intent_vector tuple fields as documented in ADR-S-009.1.

---

## What does not change

- Five-level stack (Levels 1–5)
- Named compositions (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY) and their definitions
- Gap type → named composition dispatch table (extended above; not replaced)
- Intent vector tuple fields (ADR-S-026 §4.1)
- Three source_kinds (abiogenesis, gap_observation, parent_spawn)
- Project convergence vocabulary (quiescent, converged, bounded)
- Composition library governance rules
- Open questions OQ-1, OQ-2, OQ-3

---

## References

- ADR-S-026 (parent)
- ADR-S-008.1 — companion: adds requires_spec_change branch to Stage 3
- ADR-S-009.1 — companion: adds vector subtype schema to workspace YAML
- ADR-S-010.1 — companion: adds invariant that feature_proposal only emitted when requires_spec_change: true
- ADR-S-027 Resolutions 2 and 5
