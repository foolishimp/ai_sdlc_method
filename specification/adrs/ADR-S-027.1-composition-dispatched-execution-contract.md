# ADR-S-027.1: composition_dispatched Execution Contract

**Series**: S
**Parent**: ADR-S-027 (Specification Consolidation — Authority Boundaries)
**Status**: Accepted
**Date**: 2026-03-09
**Closes**: ADR-S-027 open finding — Level 3 → Level 5 execution gap (Codex `20260309T020752` §Q4, `20260309T020552` Finding 1)

---

## What changes

ADR-S-027 Resolution 6 states: "Named compositions (Level 3) compile to graph topology (Level 5). No implementation executes Level 3 directly." It did not bind what the compiled artifact is. This ADR binds it.

### The compiled intermediate: edge_sequence

A `composition_dispatched` event MUST include a `compiled_to` section containing an **edge_sequence** — an ordered list of Level 5 edge references with bound parameters, derived from expanding the named composition against the current graph topology.

Canonical shape:

```yaml
composition_dispatched:
  intent_id: INT-GAP-008
  macro: PLAN
  version: v1
  compiled_to:
    type: edge_sequence
    edges:
      - edge: requirements→feature_decomposition
        params_ref: edge_params/feature_decomposition.yml
        context_refs:
          - specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md
      - edge: feature_decomposition→design_recommendations
        params_ref: edge_params/design_recommendations.yml
        context_refs: []
    registry_ref: compositions/PLAN@v1.yml
```

**The execution layer operates on the `edge_sequence` only.** The fact that it originated from a named composition (Level 3) is invisible to the execution layer. Level separation invariant (ADR-S-027 §Invariant 6) is satisfied.

### Compilation rules

| Situation | Compiled form |
|-----------|--------------|
| Sequential composition | Flat `edge_sequence` — one entry per edge in order |
| Fan-out (BROADCAST pattern) | Multiple `edge_sequence` blocks, one per target branch — compilation resolves the fan-out statically |
| Conditional branching | The composition compiler resolves the branch at dispatch time using current graph state; the compiled edge_sequence is always a flat list — no conditional logic in the intermediate |

The composition compiler is a Level 3 concern. The execution engine never sees conditionals or fan-out patterns — it receives resolved flat sequences.

### composition_dispatched event update

Add `compiled_to` as a required field on `composition_dispatched` events (registered in ADR-S-011.1 and ADR-S-012.1):

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `intent_id` | string | yes | Intent that triggered this dispatch |
| `macro` | string | yes | Named composition identifier |
| `version` | string | yes | Composition version (matches registry) |
| `compiled_to.type` | enum | yes | Always `edge_sequence` |
| `compiled_to.edges` | list | yes | Ordered list of Level 5 edge refs with params |
| `compiled_to.registry_ref` | string | yes | Source composition file in registry |

---

## What does not change

- Level separation invariant (ADR-S-027 §Invariant 6)
- Five-level stack (ADR-S-026 §1)
- Named compositions themselves (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY)
- Gap type → named composition dispatch table (ADR-S-026.1)
- `requires_spec_change` field on `intent_raised` (ADR-S-026.1)
- Registry governance rules (per-tenant composition registry, version pinning)
- All other fields on `composition_dispatched` events

---

## References

- ADR-S-027 (parent) — Resolution 6: Level 3 compiles to Level 5
- ADR-S-026 §3 — Named compositions and their schema
- ADR-S-011.1 — composition_dispatched OL transport registration
- ADR-S-012.1 — composition_dispatched semantic registration
- Codex REVIEW `20260309T020552` Finding 1: composition_dispatched lacks binding executable intermediate
- Codex REVIEW `20260309T020752` §Q4: follow-on ADR recommended for composition execution contract
- Claude marketplace proposal `20260309T030000`: edge_sequence as compiled intermediate
