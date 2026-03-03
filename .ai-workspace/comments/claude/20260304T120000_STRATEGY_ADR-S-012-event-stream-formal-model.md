# STRATEGY: ADR-S-012 — Event Stream as the Foundational Medium of the Formal Model

**Author**: Claude Code
**Date**: 2026-03-04T12:00:00
**Addresses**: Formal model gaps — durability, push context, compensation, implementation-independence
**For**: all

---

## Summary

Proposes making event sourcing fundamental to the formal model itself — not just to spec evolution (ADR-S-010) or schema (ADR-S-011), but to the 4 primitives. Asset becomes a projection of an event stream; iterate() produces events not assets directly; a saga invariant formalises compensation. The result: any conformant implementation is a projection policy over a shared event contract, making technology choice a pure design decision.

---

## ADR Draft

# ADR-S-012: Event Stream as the Foundational Medium of the Formal Model

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Proposed
**Date**: 2026-03-04
**Scope**: `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3 (primitives), §4 (iterate), §5 (evaluators) — foundational model change

---

## Context

The current formal model is **state-centric**: assets are the primary objects, iterate() transitions between them, and events are secondary observations emitted alongside state changes. ADR-S-010 adds event sourcing to the spec evolution pipeline. ADR-S-011 standardises the event schema. Neither changes the formal model itself.

Four structural gaps remain unaddressed:

1. **No durability invariant.** The model says nothing about what happens when a process fails mid-iteration. Asset state is wherever the implementation put it. Recovery is undefined at spec level.

2. **Context is pull-only.** `Context[]` is implicitly a set of readable artifacts the agent consults. The model has no concept of context arriving asynchronously from an external system — a market event, a webhook, a downstream service completing. Long-running workflows require push context.

3. **Fold-back is retry-only.** The current fold-back semantic is: asset did not converge → iterate again. There is no provision for a *completed* asset to be rolled back when a downstream edge fails. Compensation — undoing committed work in a chain — has no formal expression.

4. **No implementation-independence guarantee.** Nothing in the spec says that two conformant implementations must produce equivalent observable behaviour. Each implementation builds its own state representation; there is no shared projection contract.

These gaps are not solvable at the design level without spec-level grounding. An implementation can add a database, a message queue, and a saga library — but without spec invariants, conformance cannot be verified and implementations diverge silently.

The root cause is the same in each case: **the model stores state rather than recording events**. A state-centric model cannot provide durability, push context, compensation, or projection equivalence without layering workarounds. Changing the substrate — making events primary and state derived — resolves all four structurally.

---

## Decision

### Event stream as the medium of the formal model

All primitive operations MUST be expressed as events on an **append-only, ordered event stream**. No operation modifies state directly. State is always derived by projecting the event stream.

This is not a new primitive. The four primitives (Graph, Iterate, Evaluators, Spec+Context) are unchanged. What changes is their substrate: they now operate ON the event stream rather than on mutable state.

### Asset redefined as a projection

```
Asset<Tn> := project(EventStream[0..n], asset_type, instance_id)
```

An asset is not stored. It is derived on demand by replaying the event stream up to position n. Implementations MUST satisfy three projection invariants:

- **Determinism**: `project(S, T, I) = project(S, T, I)` always — same stream, same asset, no randomness
- **Completeness**: every prior state of any asset is reconstructable — `Asset<Tk>` for any k ≤ n
- **Isolation**: projecting instance I never reads or modifies the stream of instance J

The spec does not mandate how projection is implemented — in-memory fold, materialised view, event store query. Any mechanism that satisfies the three invariants is conformant.

### Iterate signature

```
iterate(Asset<Tn>, Context[], Evaluators) → Event+
```

`iterate()` returns one or more events. The engine applies them to the stream. `Asset<Tn+1>` is the projection of the stream after those events are appended. The asset is a consequence of the event, not the direct output of the operation.

### Context sources unified

`Context[]` is extended to include **push context**: events arriving from external sources (external systems, timers, human inputs, parallel evaluator votes). Push context events are appended to the stream like any other event. `iterate()` may suspend — waiting for a required context event to arrive — and resume when it does. The spec does not distinguish pull from push at the model level; both are events in the stream.

### Saga invariant (compensation)

The saga invariant is a spec-level correctness requirement for all multi-edge transitions:

```
Invariant (Saga Consistency):
  For any IterationCompleted(edge: A→B, instance: I) in the stream,
  if IterationFailed(edge: B→C, instance: I) is subsequently appended,
  then CompensationCompleted(edge: A→B, instance: I) MUST appear in the stream
  before any further IterationStarted(edge: A→B, instance: I).
```

Compensation is expressed as compensating events appended to the stream — not as state mutation or rollback. The compensated asset state is the projection of the stream including the compensating events.

Implementations are responsible for defining the compensating event sequence for each edge type. The spec requires the invariant holds; the design binds it to technology (saga orchestration, step functions, process coordinator).

### Required event taxonomy

The following event types are **required** by the spec. Implementations are conformant if and only if they emit these events with the required fields. Technology choice is irrelevant to conformance.

```
# Iteration lifecycle
IterationStarted    { asset_type, edge, instance_id, actor, context_refs[] }
IterationCompleted  { asset_type, edge, instance_id, actor, delta }
IterationFailed     { asset_type, edge, instance_id, actor, reason }

# Convergence
EvaluatorVoted      { evaluator_type, actor, result, evidence, instance_id }
ConsensusReached    { threshold, votes_for, votes_total, result, instance_id }
ConvergenceAchieved { asset_type, edge, instance_id, delta }

# Compensation (saga)
CompensationTriggered { failed_edge, target_edge, instance_id }
CompensationCompleted { target_edge, instance_id, restored_projection_hash }

# Context
ContextArrived      { source_type, payload_ref, instance_id }

# Authorization
TransitionAuthorized { actor, edge, instance_id, permissions }
TransitionDenied     { actor, edge, instance_id, reason }
```

Every event MUST carry `instance_id` (identifies the workflow instance), `actor` (identity of the subject — human, agent, or system), and conform to the OpenLineage schema defined in ADR-S-011.

### Projection as the implementation contract

An implementation is conformant if:

1. It emits the required event taxonomy with required fields
2. It satisfies the three projection invariants (determinism, completeness, isolation)
3. It satisfies the saga invariant
4. Events are append-only — no event is modified or deleted after emission

The implementation MAY store events in a local file, a database, a message queue, or any other durable medium. It MAY project assets eagerly (materialised views) or lazily (replay on demand). These are design decisions, not spec decisions.

This establishes **projection as the conformance contract**: two implementations are spec-equivalent if they produce the same asset projections from the same event streams.

---

## Consequences

**Positive:**

- **Durability is structural.** An append-only event stream is inherently durable. Any implementation that persists events survives process failure by definition — recovery is replay. The spec no longer needs to specify recovery separately.

- **Push context is native.** `ContextArrived` events integrate external inputs into the stream without special-casing. Long-running workflows that wait for external events are expressed naturally.

- **Compensation is formal.** The saga invariant gives implementations a verifiable correctness requirement. Conformance testing can assert: given an `IterationFailed` event, was `CompensationCompleted` emitted before the next `IterationStarted` on the same edge?

- **Any technology is a valid projection.** Files, DynamoDB, Kafka, BPMN audit logs — all are event stores. The spec is silent on choice. A cloud-native implementation using EventBridge and Step Functions is as conformant as a laptop implementation using `events.jsonl`.

- **Downstream projections are free.** Audit trails, OpenLineage lineage, SLA monitoring, parallel consensus aggregation, multi-tenancy filtering — all are read-side projections of the same stream. They add no write-side complexity.

- **Multi-instance is trivially supported.** Each workflow instance has an `instance_id`. Projection filters by `instance_id`. N concurrent instances of the same graph are N independent filtered views of a shared stream.

**Negative / Trade-offs:**

- **Model complexity increases.** `Asset<Tn> = project(EventStream)` is harder to explain than "asset is a document." The formal model requires a new §Event Stream Substrate section. The executive summary must be updated.

- **Projection performance is implementation-specific.** Lazy replay is simple but slow for long streams. Materialised views are fast but require consistency management. The spec is silent; implementations must choose.

- **`actor` is required on every event.** This imposes an authorization model on implementations that previously had none. Lightweight implementations (local laptop, spike profile) must supply an actor identity (even if it is just `"local-user"`).

- **Saga invariant is testable but not free.** Conformance tests must replay event streams and verify the invariant. This is specifiable but requires tooling. Implementations must build or adopt event replay infrastructure.

---

## Alternatives Considered

**Leave the model state-centric; add durability and compensation at design level**: Each implementation independently solves durability, push context, and compensation. Rejected — implementations diverge, conformance becomes untestable, and the same problems are solved N times with incompatible interfaces.

**Add compensation as a new primitive (`compensate()`)**: Define a 5th operation alongside `iterate()`. Rejected — compensation is not a new primitive. It is a constrained sequence of events that the saga invariant requires. Adding a primitive overstates the change and complicates the model.

**Event sourcing for homeostasis only (ADR-S-010 scope)**: Keep iterate() state-centric; apply event sourcing only to spec evolution. Rejected — this creates a hybrid model where some operations are event-sourced and others are not. The push context and compensation gaps remain unaddressed. ADR-S-010 is correct as far as it goes; this ADR extends the same principle to the full formal model.

**Require OpenLineage as the event store**: Mandate Marquez or equivalent backend. Rejected — ADR-S-011 already establishes local-first. The event store is a design decision; this ADR defines what goes INTO it, not where it lives.

---

## References

- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — event sourcing applied to spec evolution; this ADR generalises that principle to the full formal model
- [ADR-S-011](ADR-S-011-openlineage-unified-metadata-standard.md) — OpenLineage schema; the event taxonomy defined here MUST conform to that schema
- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — homeostasis pipeline events are a subset of the taxonomy defined here
- `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3, §4, §5 — sections requiring revision per this decision
- `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` — new REQ-EVENT-* series required

---

## Recommended Action

Review the draft above. If accepted, write to `specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md` and update `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3/§4/§5 to reflect the new substrate definition. A new REQ-EVENT-* series should be added to `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` capturing the conformance requirements derived from this ADR.
