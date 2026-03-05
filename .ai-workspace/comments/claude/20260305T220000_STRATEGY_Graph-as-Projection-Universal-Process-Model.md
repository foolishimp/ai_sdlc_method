# STRATEGY: Graph as Projection — Universal Process Model with Variable Boundary Grain

**Author**: Claude Code
**Date**: 2026-03-05T22:00:00Z
**Addresses**: Asset Graph Model (specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md §1), pre-ADR-025, pre-ADR-026
**For**: all

## Summary

The four primitives (Graph, Iterate, Evaluators, Spec+Context) are not SDLC-specific. They are a general model for any process flow that produces artifacts, evaluates them against constraints, and converges. Different process flows — SDLC, business approval, CI/CD, data pipelines — are not different systems. They are different **boundary drawings** over the same underlying event stream, each selecting a different grain at which a "unit of work" is defined. The event log is the master; every domain view is a projection. This is a general principle, not a methodology feature.

---

## The Spec Already Says This

From `AI_SDLC_ASSET_GRAPH_MODEL.md`:

> "The graph is not universal. The SDLC graph is one domain-specific instantiation. The four primitives are universal; the graph is parameterised."

The unit-of-work comment (21:00) extended this: the event log is the WAL, each step is a transaction, the fractal structure enables recursion at any depth. This comment completes the generalization: **the event log is domain-agnostic; the domain graph is a projection with a chosen boundary grain.**

---

## The Master Traversal

At the finest grain, every operation is an event. No boundaries are drawn. The event stream is a complete record of all work:

```
lLM_call_started        (fine grain — individual inference)
file_write              (fine grain — filesystem side effect)
test_run_started        (fine grain — subprocess)
test_run_completed      (fine grain — result)
edge_traversal_started  (medium grain — methodology unit)
edge_traversal_complete (medium grain — methodology unit)
feature_converged       (coarse grain — business unit)
release_approved        (very coarse — governance unit)
```

All of these are events on the same stream. None of them inherently defines "the" unit of work. The unit of work is defined by where you draw the boundary.

---

## Views as Boundary Drawings

Different process frameworks draw different boundaries over the same event stream:

| View | Boundary start | Boundary end | Unit of work |
|---|---|---|---|
| **SDLC (this project)** | `edge_started` | `edge_converged` | edge traversal |
| **Feature delivery** | `feature_started` | `feature_converged` | feature vector |
| **Sprint/milestone** | `sprint_started` | `sprint_completed` | sprint |
| **CI/CD pipeline** | `commit_pushed` | `deployment_verified` | pipeline run |
| **Business approval** | `proposal_submitted` | `approval_granted` | approval workflow |
| **Data pipeline** | `job_started` | `job_completed` | batch job |

Each view:
1. Selects which events mark the boundary (START/COMPLETE criteria)
2. Aggregates events within a boundary into a single step record
3. Defines what "converged" means at that grain
4. Has its own evaluators appropriate to the boundary

The four primitives parameterise to each view. The event log is shared. The state derivation is view-specific.

---

## Overlaying Views on the Same Graph

The interesting property: views can be **overlaid**. The same work is simultaneously visible at multiple grains. A feature delivery view contains SDLC edge traversal views contains iteration views. They are not separate systems — they are different zoom levels on the same event stream.

```
Feature delivery view:
  REQ-F-CONV-001  [pending → converged]
    │
    ├─ SDLC edge view:
    │    design→code      [START ... COMPLETE]
    │    code↔unit_tests  [START ... COMPLETE]
    │
    └─ Iteration view:
         iteration_1  [LLM call + F_D checks + delta=0.3]
         iteration_2  [LLM call + F_D checks + delta=0.0]
```

Each view is a valid "graph" in the model's sense — a topology of typed assets with admissible transitions. The SDLC graph and the feature delivery graph and the CI/CD graph are all instantiations of the same four primitives, at different grains, sharing the same event log.

This is what the spec calls "projections" (`PROJECTIONS_AND_INVARIANTS.md`) — but generalised beyond methodology profiles to cross-domain process views.

---

## Variable Boundary Grain for Different Automation Contexts

The user insight: automated process flows may have **different acceptable boundary grains** than human-supervised ones.

A fully automated CI/CD pipeline is comfortable with fine-grain boundaries: every test run is a unit of work, every deployment is a unit, recovery is automatic at each grain.

A human approval workflow needs coarser boundaries: the unit of work is an approval cycle, not an individual file write. The human only sees and acts at the coarse grain; everything below it is machinery.

An AI agent working autonomously operates at an intermediate grain: the edge traversal is the unit (coarse enough for the agent to have meaningful autonomy; fine enough for the engine to intervene if convergence fails).

**The key property that makes this work**: the evaluators are defined per-boundary, not globally. A CI/CD evaluator asks "did the deployment succeed?" A methodology evaluator asks "does delta = 0 on this edge?" A business evaluator asks "did the approver sign off?" Each grain has its own convergence criterion.

The engine doesn't need to know which view is "correct" — it executes at whatever grain the invoking context declares, emits events at that grain, and the event log carries all of them simultaneously.

---

## The General Principle

```
Any process that:
  (a) produces artifacts
  (b) evaluates them against constraints
  (c) converges when constraints are satisfied

...is an instantiation of:
  Graph       = topology of artifact types + admissible transitions
  Iterate     = T(Asset_n, Context[]) → Asset_{n+1}
  Evaluators  = convergence test at the chosen boundary grain
  Spec+Context = the constraint surface

...with:
  Event log   = the shared ledger across all grains and domains
  Grain       = the chosen boundary for a unit of work in this context
  View        = a projection of the event log at a specific grain
```

The SDLC methodology is one instantiation. A business workflow engine is another. A data pipeline orchestrator is another. They share the model, the event schema (OL is already domain-agnostic), and the four primitives. They differ in the graph topology, the evaluators, and the chosen grain.

---

## Implications

### 1. The event schema must be grain-agnostic

The OL schema (ADR-S-011) is already grain-agnostic — it uses `job.name` for the operation name, which can be an edge name, a pipeline stage, or a business process step. The `sdlc:*` facets should be renamed or generalised to `process:*` if the model is to be domain-agnostic.

Or: keep `sdlc:*` for the SDLC view, and allow other views to define their own facet namespaces over the same OL event stream. The OL schema explicitly supports this — custom facets are the extensibility mechanism.

### 2. The invocation contract is grain-parameterised

The `Intent` in pre-ADR-024 needs a `grain` field:

```python
@dataclass
class Intent:
    graph_id: str        # which graph topology
    edge: str            # which transition in that graph
    feature: str         # which unit at this grain
    grain: str           # "iteration" | "edge" | "feature" | "sprint" | custom
    constraints: dict
    context: list[Asset]
```

The grain determines what START/COMPLETE events are emitted, what the evaluators check, and what "converged" means.

### 3. Spawn is grain-crossing recursion

When a unit of work at one grain spawns a sub-unit, it may cross grain boundaries: a feature-grain unit spawning an edge-grain sub-unit. The spawn event records the grain transition. Fold-back returns the result to the parent grain.

This is the fractal property stated precisely: recursion can cross grains as well as staying within a grain. A business approval workflow can spawn an SDLC feature delivery as a sub-unit. The event log records both, linked by `parentRunId`.

### 4. The genesis_monitor is a multi-grain projection engine

The monitor should be able to render any registered view over the shared event log — not just the SDLC view. Different "dashboards" are different boundary drawings over the same stream. This is the ADR-022 instance graph generalised: not just "show the SDLC feature×edge matrix" but "show any registered view at any grain."

---

## Where This Sits in the Spec

This is a generalisation of `PROJECTIONS_AND_INVARIANTS.md`, which defines profiles (full, standard, poc, spike, hotfix, minimal) as different views of the SDLC graph. The insight here extends that: profiles vary the evaluators and convergence criteria within the SDLC domain. The variable grain principle varies the boundary itself, enabling cross-domain views over the same event log.

This suggests a spec update: `PROJECTIONS_AND_INVARIANTS.md` §2 "Profiles" should be followed by a §3 "Grain and Domain Projection" that captures this principle. The SDLC profiles are one instantiation of a more general projection mechanism.

## Recommended Action

**For the record** (no immediate implementation required):

1. **pre-ADR-026**: "Variable boundary grain as a first-class model parameter." Documents the general principle and its implications for the event schema, invocation contract, and monitor.

2. **Spec update**: Add §3 "Grain and Domain Projection" to `PROJECTIONS_AND_INVARIANTS.md`. The four primitives are universal; the grain is a parameterisation of the boundary; the event log is the shared substrate for all grains and domains.

3. **Rename `sdlc:*` facets to `process:*`** (long-term, non-breaking): makes the OL schema domain-agnostic while keeping SDLC-specific facets as a domain extension.

This is a "thinking out loud" comment — not a blocking decision. The current implementation is correct at the SDLC grain. This generalisation is a future direction worth preserving so it's available to any agent — or any domain — that wants to instantiate the model.
