# ADR-S-017: Variable Grain and Zoom Morphism

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-05
**Scope**: All implementations — grain as invocation parameter, spawn/fold-back semantics, event log projection
**Extends**: ADR-S-015 (transaction model), ADR-S-016 (invocation contract), ADR-S-012 (event stream as formal model)

---

## Context

The specification defines `iterate(Asset, Context[], Evaluators) → Asset'` without a scale parameter. The operation is applied at the edge level in the SDLC graph, but the strategy comments from 2026-03-05 identified that this operation is inherently scale-invariant: the same four primitives apply whether the unit of work is a single LLM call, an edge traversal, a feature vector, or an entire sprint.

Two related questions had not been formally resolved:

1. **What is "grain"?** The `Intent` struct in ADR-S-016 includes a `grain` field, but its semantics were left implicit.
2. **What are spawn and fold-back, structurally?** They were described operationally (spawn = create child feature vector; fold-back = evaluate child result) but not as instances of a general principle.

This ADR resolves both by establishing zoom as a first-class model concept.

---

## Decision

### Grain is a first-class parameter

Every invocation of `iterate()` executes at a declared **grain** — the boundary size that defines what counts as one unit of work. The grain determines:

- Which events are emitted as START/COMPLETE boundaries (vs. sub-events within a boundary)
- What the evaluators check (convergence criterion at this grain)
- What "converged" means (delta = 0 at this grain's evaluator)

Grain is declared in `Intent.grain` (ADR-S-016). Valid grain values include:

```
"iteration"  — single functor invocation (one LLM call or one deterministic check)
"edge"       — full edge traversal (possibly multiple iterations until delta=0)
"feature"    — full feature vector (all edges for one feature)
"sprint"     — multiple features in a planning boundary
```

Custom grains are valid for domain-specific instantiations. The grain names above are reference anchors for the SDLC graph.

### Zoom is a continuous parameter [0.0, 1.0]

The named grains are anchor points on a continuous zoom parameter:

```
zoom = 0.0  →  single node: "this project exists"
zoom = 0.25 →  feature level: N features, each pending/converged
zoom = 0.5  →  edge level: each feature has M edges, each with status
zoom = 0.75 →  iteration level: each edge took K iterations with cost C
zoom = 1.0  →  token level: every LLM call, every tool use, every file write
```

Named profiles (full, standard, poc, spike, hotfix, minimal — from `PROJECTIONS_AND_INVARIANTS.md`) are anchor points on this continuum. They are not the only valid zoom levels.

### Spawn is zoom in; fold-back is zoom out

**Spawn** is the operation that expands a node into a sub-graph. When an edge traversal discovers sub-structure requiring its own convergence loop, it spawns a child unit of work. The child is structurally identical to the parent — same intent format, same event schema, same artifact versioning — but at a finer grain.

```
Before spawn (parent sees):
  design ──────── code
        (opaque step)

After spawn (child sees):
  design → module_decomposition → basis_projections → code_units → code
        (N expanded into N₁ → N₂ → N₃)
```

The parent graph still sees `design → code`. The zoomed sub-graph sees the internal structure. Both are valid simultaneously. The interface contract is preserved: the input to N₁ is what design produces; the output of N₃ is what code expects.

**Fold-back** is the inverse: when the child converges, its entire traversal collapses back into a single result that the parent evaluates as one atomic outcome. The parent does not see the child's internal structure — it sees a converged artifact and a delta value.

Spawn and fold-back are not special mechanisms added to support recursion. They are the natural expression of zoom in/out in a model that is scale-invariant by construction.

### The four primitives are scale-invariant

At every zoom level, the same four primitives apply without modification:

| Zoom level | Graph | Iterate | Evaluators | Spec+Context |
|---|---|---|---|---|
| Project | Full SDLC topology | `/gen-start --auto` | Feature convergence | Project constraints |
| Feature | Feature vector trajectory | `/gen-iterate --edge` | Edge convergence | Edge config + spec |
| Edge traversal | Invoke intent | F_P construct call | Delta = 0 | Intent + context |
| Sub-graph (spawn) | Child topology | Child iterate | Child evaluators | Child constraints |
| Iteration | Single LLM call | anthropic.messages.create | F_D checks + F_P eval | Prompt + context |

Every row is the same structure at a different scale. This is a consequence of the four primitives being defined without a scale parameter. `iterate(Asset, Context[], Evaluators) → Asset'` is valid whether Asset is a whole codebase or a single function.

### The event log holds all zoom levels simultaneously

The event log does not pick a zoom level — it records everything. Any view is derivable by choosing which events to treat as boundaries:

```
parentRunId=null     feature_started      REQ-F-CONV-001
  parentRunId=A      edge_started         design→code
    parentRunId=B    iteration_started    design→code iteration 1
    parentRunId=B    iteration_completed  delta=0.3
    parentRunId=B    iteration_started    design→code iteration 2
      parentRunId=C  spawn_created        REQ-F-CONV-001-module-A
        parentRunId=D edge_started        design→code (child)
        parentRunId=D edge_converged      design→code (child) delta=0
      parentRunId=C  fold_back           REQ-F-CONV-001-module-A converged
    parentRunId=B    iteration_completed  delta=0.0
  parentRunId=A      edge_converged       design→code
feature_converged    REQ-F-CONV-001
```

- **Iteration view**: filter events with `parentRunId=B`
- **Edge view**: filter events with `parentRunId=A`
- **Feature view**: boundaries at `feature_started` / `feature_converged`
- **Spawn sub-graph view**: filter by `parentRunId=C`

The zoom level is a **query parameter on the event log**, not a property of the events themselves.

### Topology extension without model change

Zoom in can create nodes that were not in the original topology — inserting new intermediate nodes between existing ones:

```
Original: requirements → design
Extended: requirements → architecture_spike → interface_contracts → design
```

New nodes are topology configuration (`graph_topology.yml`), not model modification. The four primitives immediately apply to new nodes. The boundary constraint: the extended topology must preserve path connectivity from source to sink. You can add intermediate nodes; you cannot disconnect the graph.

### The deepest invariant

> **At any zoom level, the four primitives apply without modification. A unit of work at zoom Z is structurally identical to a unit of work at zoom Z+1, except for the grain of its boundary and the specificity of its evaluators.**

This means:
- Any agent that can execute one edge traversal can execute any edge traversal at any zoom level.
- Any evaluator that can test convergence at one grain can be adapted to any grain.
- Any event consumer that can project the event log at one zoom can project it at any zoom.
- New domain instantiations inherit zoom in/out for free — it is a property of the model, not of the SDLC configuration.

### Grain is a first-class model parameter, not just implementation detail

The grain determines:

1. Which events are emitted as START/COMPLETE boundaries (ADR-S-015)
2. What `Intent.grain` declares to the functor registry (ADR-S-016)
3. What convergence criterion applies (`delta = 0` at the declared grain)
4. The spawn depth limit: each spawn decrements a depth budget; when exhausted, the step must converge or escalate to F_H

The spawn depth limit in edge_params is the zoom budget: "this edge is allowed to recurse at most N levels deep." Beyond that, it must either converge or escalate to F_H.

---

## Consequences

**Positive:**
- Spawn and fold-back are no longer special cases — they are zoom in/out, deriving their semantics from the model's scale-invariance.
- The event log is a universal substrate: any view at any zoom is derivable from the same event stream without re-running anything.
- Topology extension (new nodes in `graph_topology.yml`) inherits the full model — no model changes required.
- Cross-domain instantiation is possible: a business workflow engine is an instance of the same four primitives at a different grain, sharing the OL event schema.
- The monitor (genesis_monitor) zoom control is a query parameter on the `parentRunId` tree, not a separate data structure.

**Negative / Trade-offs:**
- The `grain` field in `Intent` must be propagated correctly through all invocations. An incorrect grain causes wrong events to be treated as boundaries, making event log projections inconsistent.
- Spawn depth limits must be enforced or the recursion is unbounded. Each implementation must track depth and enforce the limit.
- Variable grain makes the schema more general but also harder to validate — a COMPLETE event is valid at multiple grains depending on context.

---

## Implementation status

| Aspect | imp_claude | imp_gemini |
|---|---|---|
| `Intent.grain` field | ❌ not yet (implicit "edge" everywhere) | ❌ not yet |
| Spawn depth limit | ❌ not yet (manual `/gen-spawn` only) | Partial (depth tracking) |
| Event log zoom query | ❌ monitor uses fixed edge-level view | Partial (parentRunId linked) |
| Topology extension | ✅ `graph_topology.yml` config | ✅ config-based |
| `parentRunId` causal chain | Partial (some events only) | ✅ implemented |

Neither implementation is fully compliant today. This ADR defines the target.

---

## References

- [ADR-S-015](ADR-S-015-unit-of-work-transaction-model.md) — transaction model; START/COMPLETE as grain boundaries; `parentRunId` causal chain
- [ADR-S-016](ADR-S-016-invocation-contract.md) — `Intent.grain` field; functor registry resolves (edge, grain, env) → functor
- [ADR-S-012](ADR-S-012-event-stream-as-formal-model-medium.md) — event stream as the formal model medium; projections
- [PROJECTIONS_AND_INVARIANTS.md](../../specification/core/PROJECTIONS_AND_INVARIANTS.md) — named profiles as grain anchor points; spawn/fold-back mechanics
- Strategy comments (pre-ADR discussion):
  - `.ai-workspace/comments/claude/20260305T220000_STRATEGY_Graph-as-Projection-Universal-Process-Model.md`
  - `.ai-workspace/comments/claude/20260305T230000_STRATEGY_Zoom-Graph-Morphism-Spawn-Foldback.md`
