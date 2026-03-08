# STRATEGY: PLAN — The Universal Intermediary Functor

**Author**: Claude Code
**Date**: 2026-03-08T10:00:00Z
**Addresses**: Graph topology reorganisation — PLAN as the repeating structure between all asset transitions
**For**: all

---

## The Insight

The reason higher-order functors were introduced was not CONSENSUS per se — it was to see the **repeating structure** across the graph that was being re-invented at each edge. CONSENSUS is a governance gate that sits at specific high-stakes transitions. The more fundamental recurring structure is **PLAN**.

Between every major asset transition, the same four-operation sequence occurs:

```
1. Decompose  — break source asset into atomic buildable units
2. Evaluate   — assess each unit (feasibility, risk, unknowns, assumptions)
3. Order      — dependency DAG + topological sort + critical path
4. Rank       — priority assignment (MVP/deferred, value/cost, risk-first)
```

This produces a **work order** — the ordered, dependency-respecting plan for constructing the next asset type.

The graph is not a flat sequence of direct asset→asset transitions. It is:

```
asset_T → PLAN(asset_T) → work_order → BUILD(work_order) → asset_T+1
```

Or more compactly, since PLAN is so universal:

```
intent → PLAN → requirements → PLAN → design → PLAN → code ↔ tests
```

---

## What PLAN Is

**Type signature**:
```
PLAN : 1 → 1    (source asset in → work order for next asset type out)
```

The work order is itself an asset — it has structure, evaluators, and convergence criteria. It carries:
- `units[]` — the atomic buildable elements (features, modules, tasks, etc.)
- `dep_dag` — dependency graph over units (Mermaid DAG + adjacency list)
- `build_order` — topological sort of dep_dag
- `ranked_units` — priority-ordered units (MVP scope, risk ordering)
- `deferred_units` — explicitly out of scope with rationale

**Sub-operations (parameterised per asset type)**:

| Sub-operation | requirements PLAN | design PLAN | code PLAN |
|--------------|------------------|-------------|-----------|
| Decompose    | REQ-F-* keys → features | features → modules/components | modules → functions/classes |
| Evaluate     | feasibility, scope risk | architectural risk, tech fit | complexity, test surface |
| Order        | feature dep DAG | module dep DAG | call graph / layer deps |
| Rank         | MVP / business value | architectural stability | implementation priority |

The sub-operations are the same. What varies is the **category of unit** being decomposed and the **evaluation criteria** applied. This is a parameterisation, not a different functor.

---

## The Corrected Graph Topology

The current graph has `feature_decomposition` and `design_recommendations` as named nodes — but these are both PLAN instances. The corrected topology with PLAN made explicit:

```
intent
  → CONSENSUS (governance profile only — multi-stakeholder gate before spec promotion)
  → PLAN (decompose intent into requirements units, order by priority)
  → requirements
  → PLAN (decompose requirements into design units, order by coherence)
  → design
  → PLAN (decompose design into code units, order by dependency/risk)
  → code ↔ unit_tests [BUILD]
  → uat_tests
  → cicd
  → running_system → telemetry → new_intent
```

**Where CONSENSUS appears**: Only at transitions where multi-stakeholder approval is required before the work order can be promoted. For a standard feature, CONSENSUS is absent — the PLAN output goes to a single F_H review (one human approves the work order). For governance-level changes (ADR acceptance, spec modification, methodology release), CONSENSUS gates before PLAN runs.

**Profiles**:
```
full:      intent → CONSENSUS → PLAN → req → PLAN → design → PLAN → code ↔ tests
standard:  intent → PLAN → req → PLAN → design → PLAN → code ↔ tests
poc:       intent → PLAN → design → code ↔ tests    (requirements folded in)
hotfix:    code ↔ tests                              (direct, no PLAN)
```

---

## Why This Matters for Minimising Code

The reason PLAN matters is exactly what was stated: **build from atomic composable building blocks, minimise code, minimise duplication**.

Without PLAN as a named functor:
- Every edge in the graph has its own edge_params file defining decompose/order/rank steps
- The logic is repeated across `requirements_feature_decomp.yml`, `feature_decomp_design_rec.yml`, and whatever the code planning edge would be called
- Each re-invention introduces inconsistency and accumulates maintenance cost

With PLAN as a named functor:
- One PLAN implementation with parameterised unit category and evaluation criteria
- All three planning stages (req/design/code) share the same core logic
- The edge_params files become **parameterisation files** for PLAN, not re-implementations
- New asset transitions (e.g., design→infrastructure, code→deployment) inherit PLAN automatically
- The composition compiler can expand PLAN into the correct graph fragment given the asset type

**Composition cost is real** — each PLAN invocation is an intermediate artifact with its own convergence cycle. But because PLAN is consistent, that cost is **predictable and uniform** across all transitions. The human evaluator knows what to expect at every PLAN gate. The tooling knows what to emit. The event log has the same PLAN-phase events at every transition.

---

## PLAN and the Homeostatic Loop

The homeostasis view is:

```
telemetry → intent → PLAN → work_order → BUILD → asset_T+1 → ... → telemetry
```

PLAN is where the system decides **what to build next** given the current state. In the homeostatic interpretation:
- The source asset is the observation (what exists)
- PLAN is the evaluation (what is the delta between current and target?)
- The work order is the corrective intent (what work closes the delta?)
- BUILD executes the corrective intent

CONSENSUS sits at the boundary where the **corrective intent itself** requires multi-stakeholder agreement — where the delta is large enough or the stakes are high enough that one human's judgment is insufficient. This is specifically the intent→requirements boundary for governance-level changes (spec modifications, methodology evolution), and specific release gates in the `full` profile.

For everything else (normal feature work), PLAN + single F_H review is sufficient.

---

## Proposed Update to Functor Library

PLAN should be added to `HIGHER_ORDER_FUNCTORS.md` as a primary functor — arguably the most frequently used one in practice. It sits above BUILD in importance for the methodology's day-to-day operation.

**Updated functor library (9 functors)**:

```
PLAN       : 1 → 1    (source asset → work order — universal intermediary)
BROADCAST  : 1 → N    (fan-out)
FOLD       : N → 1    (fan-in)
BUILD      : 2 → 2    (co-evolution with feedback)
CONSENSUS  : (1+N)→1  (multi-stakeholder F_H gate)
REVIEW     : 1 → 1    (single-evaluator gate)
DISCOVERY  : 1 → 1    (question-answered convergence)
RATIFY     : 1 → 1    (stability promotion)
EVOLVE     : 1 → 1    (versioned re-entry)
```

PLAN is the universal intermediary. The graph topology as a repeating unit:

```
asset_T → [CONSENSUS?] → PLAN → asset_T+1
```

BUILD is the execution functor (code ↔ tests co-evolution). PLAN is the planning functor (decompose → order → rank). They are complementary: PLAN decides what to build; BUILD builds it.

---

## Graph Topology Simplification

The current graph_topology.yml has `feature_decomposition` and `design_recommendations` as distinct node types. Under the PLAN functor model, these collapse:

- `feature_decomposition` = `PLAN(requirements)` — planning stage for requirements→design transition
- `design_recommendations` = `PLAN(design_rec)` — planning stage for requirements→design transition (sub-step)

These two should merge into a single `PLAN` node type with a single edge_params template that is parameterised by the asset type being planned. The graph topology becomes:

```
intent → plan_req → requirements → plan_design → design → plan_code → code ↔ tests
```

Where `plan_req`, `plan_design`, `plan_code` are all instances of the PLAN functor with different parameter bindings — not different node types.

**Implementation implication**: The `requirements_feature_decomp.yml` and `feature_decomp_design_rec.yml` edge_params files become parameterisation variants of a single `plan.yml` template. Shared checklist, shared output structure (units/dep_dag/build_order/ranked_units/deferred_units), different unit categories and evaluation criteria.

---

## Open Questions for Reviewers

1. **PLAN sub-operation granularity**: Should decompose/evaluate/order/rank be four separate micro-iterations, or one compound iteration? The argument for compound: the four steps are tightly coupled — you can't rank without ordering, can't order without evaluating. The argument for separate: observability (you can see where planning stalled) and spawning (a complex decomposition might spawn a DISCOVERY vector). Current proposal: compound, with the four steps as internal structure of a single PLAN iteration.

2. **PLAN output as a stable asset**: Should the work order be a stable asset (evaluated by F_H before proceeding) or an intermediate artifact that is immediately consumed by the next construction phase? Current proposal: stable asset with F_H gate — the work order is where the human makes the scope/priority decision. This is where BUILD order decisions are made; they deserve human review.

3. **Parameterisation mechanism**: How does PLAN know what kind of units to decompose into? Options: (a) edge_params binding (the parameterisation lives in the edge config file); (b) asset type annotation (the source asset carries its type, PLAN dispatches accordingly). Edge_params binding is cleaner — the graph topology already carries this information.
