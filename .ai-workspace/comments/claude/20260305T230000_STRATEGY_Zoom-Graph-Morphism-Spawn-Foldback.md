# STRATEGY: Zoom as Graph Morphism — Spawn and Fold-Back are Zoom In/Out

**Author**: Claude Code
**Date**: 2026-03-05T23:00:00Z
**Addresses**: `PROJECTIONS_AND_INVARIANTS.md`, pre-ADR-026 (variable grain), spawn/fold-back mechanism
**For**: all

## Summary

Zoom in (add new nodes) and zoom out (collapse nodes) are not visualisation operations — they are **structure-preserving transformations on the graph topology** that leave the four primitives invariant. Spawn is zoom in: a node expands into a sub-graph. Fold-back is zoom out: a sub-graph collapses back into its parent. The four primitives apply at every zoom level without modification. The event log records all zoom levels simultaneously via the `parentRunId` causal chain. This is the model's deepest invariant: **self-similarity across scale**.

---

## Zoom In: Expanding a Node into a Sub-Graph

A node N in the graph can be expanded into a sub-graph (N₁ → N₂ → N₃) when the work it represents has internal structure that needs to be made explicit. The sub-graph must preserve N's **interface contract**: same inputs, same outputs, same convergence criterion as seen from N's neighbours.

```
Before zoom in:
  design ──────────────────────── code
             (N: opaque step)

After zoom in:
  design → module_decomposition → basis_projections → code_units → code
             (N expanded into N₁ → N₂ → N₃)
```

The parent graph still sees `design → code`. The zoomed graph sees the sub-steps. Both are valid views. The interface contract is preserved: the input to N₁ is what design produces; the output of N₃ is what code expects.

**Spawn is zoom in.** When an edge traversal discovers that the problem has sub-structure requiring its own convergence loop, it spawns — creating a child feature vector. The child IS the expanded sub-graph. The parent step pauses; the child traverses its own graph; fold-back collapses the result back into the parent's convergence evaluation.

The zoom-in operation does not require a topology change to the parent graph. The parent sees the child as an opaque unit of work (same grain as before). The child sees its own full topology. Both are correct simultaneously.

---

## Zoom Out: Collapsing a Sub-Graph into a Node

The inverse: multiple nodes (N₁ → N₂ → N₃) can be collapsed into a single node N at a coarser grain when the internal structure is irrelevant to the viewer.

```
Before zoom out (SDLC view):
  design → code → unit_tests → uat_tests

After zoom out (business view):
  specification → implementation → verification
  (design folds into spec; code+unit_tests folds into impl; uat into verification)
```

The SDLC view and the business view are both valid. Neither is more "true." The business view is a coarser projection of the same event stream.

**Fold-back is zoom out.** When a spawned child converges, its entire traversal — however many steps, however many iterations — collapses into a single result that the parent step evaluates as one atomic outcome. The parent does not see the child's internal structure; it sees a converged artifact and a delta value. That is zoom out.

---

## The Four Primitives are Scale-Invariant

At every zoom level, the same four primitives apply without modification:

| Zoom level | Graph | Iterate | Evaluators | Spec+Context |
|---|---|---|---|---|
| Project | Full SDLC topology | `/gen-start --auto` | Feature convergence | Project constraints |
| Feature | Feature vector trajectory | `/gen-iterate --edge` | Edge convergence | Edge config + spec |
| Edge traversal | Invoke mandate | F_P construct call | Delta = 0 | Mandate + context |
| Sub-graph (spawn) | Child topology | Child iterate | Child evaluators | Child constraints |
| Iteration | Single LLM call | anthropic.messages.create | F_D checks + F_P eval | Prompt + context |

The model is self-similar: every row is the same structure at a different scale. This is not coincidence — it is the consequence of the four primitives being defined without a scale parameter. `iterate(Asset, Context[], Evaluators) → Asset'` is valid whether Asset is a whole codebase or a single function.

---

## The Event Log Holds All Zoom Levels Simultaneously

The event log doesn't pick a zoom level — it records everything:

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

Any view is derivable by choosing which events to treat as boundaries:
- **Iteration view**: boundaries at `iteration_started` / `iteration_completed`
- **Edge view**: boundaries at `edge_started` / `edge_converged`
- **Feature view**: boundaries at `feature_started` / `feature_converged`
- **Spawn sub-graph view**: filter by `parentRunId=C`, render that sub-tree

The zoom level is a **query parameter on the event log**, not a property of the events themselves.

---

## Zoom as a Continuous Parameter, Not Discrete Levels

The spec (`PROJECTIONS_AND_INVARIANTS.md`) defines named profiles (full, standard, poc, spike, hotfix, minimal) as discrete zoom anchors. The underlying parameter is continuous — you can zoom to any grain, not just the named ones.

```
zoom = 0.0  →  single node: "this project exists"
zoom = 0.25 →  feature level: "N features, each pending/converged"
zoom = 0.5  →  edge level: "each feature has M edges, each with status"
zoom = 0.75 →  iteration level: "each edge took K iterations with cost C"
zoom = 1.0  →  token level: "every LLM call, every tool use, every file write"
```

Named profiles are anchor points on this continuum — not the only valid zoom levels. A CI/CD system might zoom to 0.6 (test-run level). A business dashboard might zoom to 0.3 (milestone level). An LLM cost audit might zoom to 0.9 (per-call level).

The four primitives apply at every point on this continuum. The evaluators and convergence criteria are what change — not the model.

---

## Creating New Nodes: Topology Extension Without Model Change

Zoom in can also create nodes that weren't in the original topology definition — not just expanding existing nodes, but inserting new intermediate nodes between existing ones.

```
Original topology:   requirements → design
Extended topology:   requirements → architecture_spike → interface_contracts → design
```

The new nodes (architecture_spike, interface_contracts) are valid asset types parameterised by the graph config. They don't require a model change — they require a topology config change (graph_topology.yml). The four primitives immediately apply to the new nodes. The event log records traversals of the new edges. The evaluators for the new nodes are defined in edge_params/.

This is the extension mechanism: the model is fixed; the topology is parameterised; new nodes are topology configuration, not model modification.

The boundary constraint: the extended topology must preserve **path connectivity** from the original graph's source to sink. You can add intermediate nodes; you cannot disconnect the graph. And any zoom-out that collapses the extended region must produce an output consistent with the original edge's contract.

---

## Implications for Implementation

**Graph topology as a runtime parameter, not compile-time constant**: `graph_topology.yml` is already this — a config file, not hardcoded. Zoom in is "load a more detailed graph_topology for this sub-problem." Zoom out is "query the event log at a coarser granularity."

**The genesis_monitor zoom control**: The ADR-022 instance graph comment mentioned zoom levels 0, 1, 2. This comment makes that precise: the monitor's zoom slider is a query parameter on the `parentRunId` event tree. At zoom 0: show feature nodes only. At zoom 1: expand to edge nodes. At zoom 2: expand to iteration nodes. The event log supports all three without re-running anything.

**Spawn depth limit as zoom budget**: Each spawn goes one level deeper. Unbounded recursion is zoom to 1.0 (token level) — impractical. The spawn depth limit in edge_params is the zoom budget: "this edge is allowed to recurse at most N levels deep." Beyond that, it must either converge or escalate to F_H (human).

**The invocation contract's `grain` field** (pre-ADR-024) is the zoom level at which this unit of work is executing. It determines which events are emitted as START/COMPLETE boundaries and which are emitted as sub-events within a boundary.

---

## The Deepest Invariant

The model's self-similarity across scale is its most powerful property and its most important invariant:

> **At any zoom level, the four primitives apply without modification. A unit of work at zoom Z is structurally identical to a unit of work at zoom Z+1, except for the grain of its boundary and the specificity of its evaluators.**

This means:
- Any agent that can execute one edge traversal can execute any edge traversal at any zoom level.
- Any evaluator that can test convergence at one grain can be adapted to any grain.
- Any event consumer that can project the event log at one zoom can project it at any zoom.
- Any new domain instantiation inherits zoom in/out for free — it's a property of the model, not of the SDLC configuration.

Spawn and fold-back are not special mechanisms added to support recursion. They are the natural expression of zoom in/out in a model that is already self-similar at every scale.
