# ADR-S-029: graph_fragment — The Compiled Dispatch Intermediate

**Series**: S
**Status**: Accepted
**Date**: 2026-03-09
**Supersedes**: ADR-S-027.1 — bound `composition_dispatched` to `edge_sequence`; superseded because `graph_fragment` is strictly richer and correctly named
**Withdrawal Rationale**: ADR-S-027.1 defined the compiled intermediate as an `edge_sequence` — a flat ordered list of edges with params_ref and context_refs. This was correct for execution ordering but omitted two properties the execution layer needs: which asset nodes will be traversed (for validation and display), and which functor category (F_D / F_P / F_H) applies to each edge (for scheduling). Without operator_bindings, the execution layer must re-derive functor assignment from the profile config on every dispatch, making it stateful about Level 3 concerns. ADR-S-029 resolves this. The `edge_sequence` concept survives as the `edges` field within the `graph_fragment`.
**Prior reference**: git tag `adr-deleted/ADR-S-027.1`
**Closes**: Codex residual finding #1 (`20260309T020552`) — execution contract gap on `composition_dispatched`

---

## What changes from ADR-S-027.1

### The compiled intermediate: graph_fragment

A `composition_dispatched` event MUST include a `compiled_to` section containing a **graph_fragment** — the normative Level 5 execution contract produced by compiling a Level 3 named composition.

A graph_fragment consists of three parts:

```
graph_fragment = {
    nodes:             [AssetType],           # ordered list of asset nodes traversed
    edges:             [EdgeRef],             # ordered list of admissible transitions
    operator_bindings: {EdgeRef → Functor}    # F_D | F_P | F_H per edge
}
```

**Canonical shape** on the `composition_dispatched` event:

```yaml
composition_dispatched:
  intent_id: INT-GAP-008
  macro: PLAN
  version: v1
  compiled_to:
    type: graph_fragment
    nodes:
      - requirements
      - feature_decomposition
      - design_recommendations
    edges:
      - edge: requirements→feature_decomposition
        params_ref: edge_params/feature_decomposition.yml
        context_refs:
          - specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md
      - edge: feature_decomposition→design_recommendations
        params_ref: edge_params/design_recommendations.yml
        context_refs: []
    operator_bindings:
      requirements→feature_decomposition: F_P
      feature_decomposition→design_recommendations: F_D
    registry_ref: compositions/PLAN@v1.yml
```

**The execution layer operates on the `graph_fragment` only.** The fact that it originated from a named composition (Level 3) is invisible to the execution layer. Level separation invariant (ADR-S-027 §Invariant 6) is satisfied.

### Why nodes

Explicit node enumeration enables:
1. **Pre-dispatch validation**: can the execution layer produce each node's required schema before starting?
2. **Display**: genesis_monitor knows which assets will be produced before they exist — panels can render pending slots
3. **Dependency checking**: nodes that depend on external assets can be verified at dispatch time, not mid-execution

### Why operator_bindings

Functor assignment baked in at compile time makes the execution layer stateless about Level 3 concerns:

| Functor | Scheduling implication |
|---------|----------------------|
| `F_D` | Run immediately — no external dependencies |
| `F_P` | Requires MCP connection — check availability before dispatching |
| `F_H` | Requires human availability — do not auto-start; queue for gate |

Without operator_bindings, the execution layer must re-derive these from the profile config on every dispatch. With them, the compiler resolves once; the execution layer reads.

### Compilation rules (carried forward from ADR-S-027.1, updated for graph_fragment)

| Situation | Compiled form |
|-----------|--------------|
| Sequential composition | Single `graph_fragment` — one entry per node/edge in order |
| Fan-out (BROADCAST pattern) | Multiple `graph_fragment` blocks, one per target branch — fan-out resolved statically at compile time |
| Conditional branching | Compiler resolves branch at dispatch time using current graph state; compiled graph_fragment is always a flat list — no conditional logic in the intermediate |

The composition compiler is a Level 3 concern. The execution engine never sees conditionals or fan-out patterns — it receives resolved flat fragments.

**Fan-out canonical shape:**

```yaml
compiled_to:
  type: graph_fragment_set       # multiple fragments for BROADCAST
  fragments:
    - branch: feature_decomposition_path
      nodes: [requirements, feature_decomposition]
      edges:
        - edge: requirements→feature_decomposition
          params_ref: edge_params/feature_decomposition.yml
      operator_bindings:
        requirements→feature_decomposition: F_P
    - branch: design_recommendations_path
      nodes: [feature_decomposition, design_recommendations]
      edges:
        - edge: feature_decomposition→design_recommendations
          params_ref: edge_params/design_recommendations.yml
      operator_bindings:
        feature_decomposition→design_recommendations: F_D
  registry_ref: compositions/PLAN@v1.yml
```

### Updated composition_dispatched event fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `intent_id` | string | yes | Intent that triggered this dispatch |
| `macro` | string | yes | Named composition identifier |
| `version` | string | yes | Composition version (matches registry) |
| `compiled_to.type` | enum | yes | `graph_fragment` or `graph_fragment_set` |
| `compiled_to.nodes` | list | yes (single fragment) | Ordered asset node list |
| `compiled_to.edges` | list | yes (single fragment) | Ordered edge refs with params |
| `compiled_to.operator_bindings` | map | yes | EdgeRef → F_D \| F_P \| F_H |
| `compiled_to.fragments` | list | yes (fan-out) | Per-branch graph_fragment list |
| `compiled_to.registry_ref` | string | yes | Source composition file in registry |

---

## What does not change

- Level separation invariant (ADR-S-027 §Invariant 6)
- Five-level stack (ADR-S-026 §1)
- Named compositions themselves (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY)
- Gap type → named composition dispatch table (ADR-S-026 §gap_type_dispatch)
- `requires_spec_change` field on `intent_raised`
- Registry governance rules (per-tenant composition registry, version pinning)
- All other fields on `composition_dispatched` events

---

## References

- ADR-S-027 — Resolution 6: Level 3 compiles to Level 5
- ADR-S-027.1 (superseded) — edge_sequence intermediate — git tag `adr-deleted/ADR-S-027.1`
- ADR-S-026 §3 — Named compositions and their schema
- ADR-S-011 — composition_dispatched OL transport registration (§eventType mapping)
- ADR-S-012 — composition_dispatched semantic registration (§8 Required event taxonomy)
- Codex residual finding #1 (`20260309T020552`): composition_dispatched lacks binding executable intermediate
- Proposal `20260309T120000`: Decision 2 — graph_fragment rationale
