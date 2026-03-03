# ADR-S-012: Event Stream as the Foundational Medium of the Formal Model

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
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

This ADR was reviewed by both Claude Code and Gemini CLI prior to acceptance. Gemini independently validated each gap against observed problems in `imp_gemini_cloud`: asynchronous Vertex AI batch completions (push context), edges failing due to upstream structural flaws (compensation), and local vs cloud implementation drift (projection contract).

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

All events carry universal fields `{ instance_id, actor, causation_id, correlation_id }` plus their type-specific payload below.

```
# Iteration lifecycle
IterationStarted    { asset_type, edge, context_refs[] }
IterationCompleted  { asset_type, edge, delta }
IterationFailed     { asset_type, edge, reason }

# Convergence
EvaluatorVoted      { evaluator_type, result, evidence }
ConsensusReached    { threshold, votes_for, votes_total, result }
ConvergenceAchieved { asset_type, edge, delta }

# Compensation (saga)
CompensationTriggered { failed_edge, target_edge }
CompensationCompleted { target_edge, restored_projection_hash }

# Context
ContextArrived      { source_type, payload_ref }

# Authorization
TransitionAuthorized { edge, permissions }
TransitionDenied     { edge, reason }
```

Causal chain examples:

```
# Saga compensation chain
IterationFailed(edge: B→C, causation_id: X, correlation_id: ROOT)
  └─ CompensationTriggered(edge: A→B, causation_id: IterationFailed.runId, correlation_id: ROOT)
      └─ CompensationCompleted(edge: A→B, causation_id: CompensationTriggered.runId, correlation_id: ROOT)

# Root event — no parent
IterationStarted(edge: intent→requirements, causation_id: self.runId, correlation_id: self.runId)
  └─ IterationCompleted(causation_id: IterationStarted.runId, correlation_id: IterationStarted.runId)
      └─ IterationStarted(edge: requirements→design, causation_id: IterationCompleted.runId, correlation_id: ROOT)
```

Every event MUST carry three universal fields in addition to its type-specific payload:

| Field | Type | Meaning |
|---|---|---|
| `instance_id` | string | Identifies the workflow instance — scopes projection and multi-tenancy |
| `actor` | string | Identity of the subject that caused the event — human, agent, or system |
| `causation_id` | UUID | `runId` of the immediate parent event that directly triggered this event |
| `correlation_id` | UUID | `runId` of the root event of the entire causal chain (the originating intent or signal) |

`causation_id` maps directly to OpenLineage `ParentRunFacet.run.runId` (ADR-S-011) and MUST be populated on every event. It enables causal graph traversal: "show me everything triggered by event X" without chain-walking. `correlation_id` enables root-cause lookup in O(1): "show me everything caused by intent INT-007" across an arbitrarily deep chain.

For root events (those with no triggering parent — e.g., a user-initiated `IterationStarted` or an external `ContextArrived`), `causation_id = correlation_id = this event's own runId`.

Implementations MUST propagate both IDs through the execution context — analogous to distributed tracing span propagation. Every event emitter receives the current `causation_id` and `correlation_id` from its caller and sets them on the emitted event before the next event in the chain is produced.

All events MUST conform to the OpenLineage schema defined in ADR-S-011.

### Projection as the implementation contract

An implementation is conformant if:

1. It emits the required event taxonomy with required fields
2. It satisfies the three projection invariants (determinism, completeness, isolation)
3. It satisfies the saga invariant
4. Events are append-only — no event is modified or deleted after emission

The implementation MAY store events in a local file, a database, a message queue, or any other durable medium. It MAY project assets eagerly (materialised views) or lazily (replay on demand). These are design decisions, not spec decisions.

This establishes **projection as the conformance contract**: two implementations are spec-equivalent if they produce the same asset projections from the same event streams. A laptop implementation using `events.jsonl` and a cloud implementation using Firestore or DynamoDB streams are equally conformant if they satisfy the four conditions above.

---

## Consequences

**Positive:**

- **Durability is structural.** An append-only event stream is inherently durable. Any implementation that persists events survives process failure by definition — recovery is replay from the last known position. The spec no longer needs to specify recovery separately.

- **Push context is native.** `ContextArrived` events integrate external inputs into the stream without special-casing. Long-running workflows that wait on async external signals (batch completions, human approvals, webhook callbacks) are expressed naturally — `iterate()` suspends until the event arrives.

- **Compensation is formal.** The saga invariant gives implementations a verifiable correctness requirement. Conformance testing can assert: given an `IterationFailed` event, was `CompensationCompleted` emitted before the next `IterationStarted` on the same edge?

- **Any technology is a valid projection.** Files, DynamoDB, Firestore, Kafka, BPMN audit logs — all are event stores. The spec is silent on choice. A cloud-native implementation using EventBridge and Step Functions is as conformant as a laptop implementation using `events.jsonl`.

- **Downstream projections are free.** Audit trails, OpenLineage lineage, SLA monitoring, parallel consensus aggregation, multi-tenancy filtering — all are read-side projections of the same stream. They add no write-side complexity.

- **Multi-instance is trivially supported.** Each workflow instance has an `instance_id`. Projection filters by `instance_id`. N concurrent instances of the same graph are N independent filtered views of a shared stream.

- **Replay performance is manageable.** Implementations SHOULD treat existing checkpoints or snapshots as O(1) starting positions for projection — replay begins from the nearest snapshot, not from the beginning of the stream. This bounds replay cost regardless of stream length. Snapshots are implementation artefacts; the spec does not mandate them, but implementations that store them satisfy the Completeness invariant more efficiently.

**Negative / Trade-offs:**

- **Model complexity increases.** `Asset<Tn> = project(EventStream)` is harder to explain than "asset is a document." The formal model requires a new §Event Stream Substrate section. The executive summary must be updated.

- **Projection performance is implementation-specific.** Lazy replay is simple but slow for long streams without snapshots. Materialised views are fast but require consistency management. The spec is silent; implementations must choose.

- **`actor` is required on every event.** This imposes an authorization model on implementations that previously had none. Lightweight implementations (local laptop, spike profile) must supply an actor identity — `"local-user"` is a valid minimal value.

- **Saga invariant is testable but not free.** Conformance tests must replay event streams and verify the invariant. Implementations must build or adopt event replay infrastructure. This is non-trivial but the scope is bounded: a single method signature change in the engine (`iterate_edge` returns events rather than mutating state directly).

- **Working tree synchronisation.** Implementations that materialise assets as local files must ensure the working tree stays consistent with the event stream. A sync phase after every event append — updating local artifacts to reflect the new projection — prevents state drift between the stream and the file system.

- **Causal ID propagation is disciplined, not automatic.** `causation_id` and `correlation_id` do not self-populate. Implementations must thread both IDs through the execution context — the same discipline as distributed tracing. The cost is low (two UUID fields per event) and the payoff is free causal graph traversal via standard OpenLineage tooling. Lightweight implementations MAY use `"local"` as `correlation_id` for spike/minimal profiles where full chain tracing is not required.

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
- Peer review: `.ai-workspace/comments/claude/20260304T120000_STRATEGY_ADR-S-012-event-stream-formal-model.md`
- Peer review: `.ai-workspace/comments/gemini/20260304T121500_REVIEW_ADR-S-012-event-stream-formal-model.md`
