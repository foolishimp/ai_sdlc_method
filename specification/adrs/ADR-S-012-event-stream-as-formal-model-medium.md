# ADR-S-012: Event Stream as the Foundational Medium of the Formal Model

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-04
**Revised**: 2026-03-14 (incorporates ADR-S-012.1; adds event-time semantics and gate-stream consistency)
**Supersedes**: ADR-S-012.1 (projection scope and event registrations — folded in)
**Scope**: `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3–§5 — foundational model

---

## Context

The original formal model was **state-centric**: assets are the primary objects, iterate() transitions between them, events are secondary observations. Four structural gaps drove the change to an event-first substrate:

1. **No durability invariant** — recovery from mid-iteration failure was undefined at spec level
2. **Context is pull-only** — no formal expression for async external signals (webhooks, batch completions, human approvals)
3. **Fold-back is retry-only** — no compensation semantic for rolling back committed work when a downstream edge fails
4. **No projection equivalence guarantee** — two conformant implementations could produce different observable behaviour

All four are resolved structurally by making events primary and state derived.

---

## Decision

### 1. Event stream as the substrate

All primitive operations MUST be expressed as events on an **append-only, ordered event stream**. No operation modifies state directly. State is always derived by projecting the event stream.

The four primitives (Graph, Iterate, Evaluators, Spec+Context) are unchanged. What changes is their substrate: they now operate ON the event stream rather than on mutable state.

### 2. Asset redefined as a projection

```
Asset<Tn> := project(EventStream[0..n], asset_type, instance_id)
```

An asset is not stored. It is derived on demand by replaying the event stream up to position n. Implementations MUST satisfy three projection invariants:

- **Determinism**: `project(S, T, I) = project(S, T, I)` always — same stream, same asset, no randomness
- **Completeness**: every prior state of any asset is reconstructable — `Asset<Tk>` for any k ≤ n
- **Isolation**: projecting instance I never reads or modifies the stream of instance J

**Projection scope**: The event-first model applies to `.ai-workspace/` operational state and code/test artifacts produced by the iterate engine. It does NOT apply to `specification/` files. Spec files (`specification/core/`, `specification/requirements/`, `specification/features/`, `specification/adrs/`, `specification/verification/`) are authoritative artifacts; `spec_modified` events (ADR-S-010) are their audit trail, not their substrate.

**Conflict resolution**: If a workspace file and the event log disagree, the event log is authoritative — regenerate the file from the stream. If a spec file and a `spec_modified` event disagree (hash mismatch), the file and git history are authoritative for the spec domain.

### 3. Iterate signature

```
iterate(Asset<Tn>, Context[], Evaluators) → Event+
```

`iterate()` returns one or more events. The engine appends them to the stream. `Asset<Tn+1>` is the projection of the stream after those events are appended — a consequence of the event, not the direct output.

`Context[]` includes **push context**: events arriving asynchronously from external sources (external systems, timers, human inputs, evaluator votes). Push context events are appended to the stream like any other event. `iterate()` may suspend waiting for a required context event and resume when it arrives. Pull and push are both events; the model does not distinguish them.

### 4. Event-time semantics

**`event_time` is append-assigned and non-overridable by the caller.** It is the timestamp of the log entry, set by the event log writer at the moment of append. A caller MUST NOT supply a historical timestamp to make a later entry masquerade as an earlier one.

Events MAY carry additional domain time fields (`effective_at`, `completed_at`, `observed_at`) describing the business nature of the underlying fact. These fields do not change the append order or the `event_time` of the log entry.

**Prohibited acts** (non-conformant regardless of intent):
- Appending a log entry with a forged earlier `event_time`
- Using a late trace or review artifact to impersonate a missing earlier control decision

### 5. Control surface and trace surface

The event stream has two distinct surfaces:

**Control surface** — authoritative, gate-moving events in the canonical log. These govern causality: what the system decided, and when. Control events must be truthful, append-time-stamped, and emitted at the moment the decision is made.

**Trace surface** — projections, correlations, audit packs, telemetry summaries, review paperwork, and other visibility artifacts derived from the canonical log. These govern legibility. Trace artifacts MAY be incomplete during normal operation. Later completion of tracing, correlation, or paperwork is **observability debt** — eventual consistency of the trace surface — not mutation of the historical control surface.

The distinction matters for fault classification: a missing proxy-log or unarchived review YAML is trace debt (detectable, repayable). A backdated `event_time` or a control-event emitted without the work having occurred is a log-integrity violation (permanent, unrepayable by definition).

### 6. Gate-stream self-consistency

**Mandatory gates are defined by self-consistency within their gate stream**, not by whether every gate must be traversed.

A gate stream is a bounded sequence of causally related events that together express a workflow transition (traversal, review, install, proxy decision). You may choose not to enter a gate. Once inside one, the events you emit must be internally consistent: the exit event must be causally preceded by the entry event, using valid IDs of the correct category.

Mandatory gates are those whose gate-stream inconsistency corrupts downstream reasoning — specifically:

| Gate stream | Self-consistency requirement |
|-------------|------------------------------|
| **Feature traversal** | `edge_started` → `iteration_completed` → `edge_converged` — exit requires entry; `edge_converged.feature` must resolve to a known feature vector in `features/active/` or `features/completed/` |
| **Review** | `feature_proposal` → `review_approved` — approval requires a prior proposal with matching `proposal_id` in the same stream |
| **Human-proxy** | `review_approved{actor: human-proxy}` — the referenced `proxy_log` file must exist in `reviews/proxy-log/` before the event is emitted |
| **Install** | `genesis_installed` — `version` must match what was actually written to disk |

Not every administrative process step is a mandatory gate. The test is: does gate-stream inconsistency here propagate errors downstream? If no downstream gate depends on this stream's consistency, it is advisory — a trace artifact that may lag.

### 7. Saga invariant (compensation)

The saga invariant is a spec-level correctness requirement for all multi-edge transitions:

```
Invariant (Saga Consistency):
  For any IterationCompleted(edge: A→B, instance: I) in the stream,
  if IterationFailed(edge: B→C, instance: I) is subsequently appended,
  then CompensationCompleted(edge: A→B, instance: I) MUST appear in the stream
  before any further IterationStarted(edge: A→B, instance: I).
```

Compensation is expressed as compensating events appended to the stream — not as state mutation or rollback. Implementations define the compensating event sequence for each edge type.

### 8. Required event taxonomy

The following event types are required by the spec. All carry universal fields `{instance_id, actor, causation_id, correlation_id}` plus their type-specific payload.

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

# CONSENSUS functor (required when CONSENSUS is active on an edge)
proposal_published    { asset_id, asset_version, roster_size, quorum, min_duration, review_closes_at }
comment_received      { asset_id, participant, gating: bool, disposition: null }
vote_cast             { asset_id, asset_version, participant, verdict, conditions: [] }
asset_version_changed { asset_id, prior_version, new_version, materiality: material|non_material }
consensus_reached     { asset_id, asset_version, approve_ratio, participation_ratio, gating_comments_dispositioned }
consensus_failed      { asset_id, failure_reason, available_paths: [] }
recovery_path_selected { asset_id, path: re_open|narrow_scope|abandon }

# Named Composition / Intent Vector
composition_dispatched  { intent_id, macro, version, bindings, vector_id }
intent_vector_converged { vector_id, produced_asset_ref, edge }
intent_vector_blocked   { vector_id, reason, disposition: null }
```

**Universal fields** (every event):

| Field | Type | Meaning |
|-------|------|---------|
| `instance_id` | string | Workflow instance — scopes projection and multi-tenancy |
| `actor` | string | Subject that caused the event — human, agent, or system |
| `causation_id` | UUID | `runId` of the immediate parent event |
| `correlation_id` | UUID | `runId` of the root event of the entire causal chain |

For root events (no triggering parent), `causation_id = correlation_id = this event's own runId`. Implementations MUST propagate both IDs through the execution context. Lightweight implementations MAY use `"local"` as `correlation_id` for spike/minimal profiles.

All events MUST conform to the OpenLineage schema (ADR-S-011).

### 9. Projection as the conformance contract

An implementation is conformant if:

1. It emits the required event taxonomy with required fields
2. It satisfies the three projection invariants (determinism, completeness, isolation)
3. It satisfies the saga invariant
4. Events are append-only — no event is modified or deleted after emission
5. `event_time` is append-assigned — no caller-supplied historical timestamps

Two implementations are spec-equivalent if they produce the same asset projections from the same event streams. A laptop implementation using `events.jsonl` and a cloud implementation using DynamoDB streams are equally conformant if they satisfy the five conditions above.

---

## Consequences

**Positive:**
- Durability is structural — any implementation that persists events survives process failure by replay
- Push context is native — `ContextArrived` events integrate async inputs without special-casing
- Compensation is formal — the saga invariant is verifiable by event stream replay
- Any event store technology is a valid substrate
- Downstream projections (audit trails, lineage, monitoring, consensus aggregation) are free read-side views
- Gate-stream consistency is an F_D check — deterministic, no LLM required
- Trace debt is distinguishable from control-surface violations — correct fault classification without bureaucratic overhead

**Negative / Trade-offs:**
- `Asset<Tn> = project(EventStream)` is harder to explain than "asset is a document"
- Projection performance is implementation-specific (lazy replay vs materialised views)
- `actor` is required on every event — lightweight implementations must supply at minimum `"local-user"`
- Saga invariant conformance tests require event replay infrastructure
- Causal ID propagation requires implementation discipline — not automatic
- Working tree synchronisation: implementations materialising assets as local files must keep the working tree consistent with the event stream

---

## Alternatives Considered

**Leave the model state-centric** — each implementation independently solves durability, push context, and compensation. Rejected — implementations diverge, conformance becomes untestable.

**Add compensation as a new primitive `compensate()`** — rejected. Compensation is a constrained event sequence, not a new primitive.

**Event sourcing for homeostasis only** — rejected. Creates a hybrid model; push context and compensation gaps remain.

**Require OpenLineage as the event store** — rejected. ADR-S-011 establishes local-first. The event store is a design decision.

**Amendment chain instead of merged ADR** — rejected. Amendment chains impose a context window tax on agentic builders, who must load parent and child, reconcile them, and detect which supersedes which. A single complete document is strictly better for agentic reasoning.

---

## References

- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — event sourcing for spec evolution; this ADR generalises to the full formal model
- [ADR-S-011](ADR-S-011-openlineage-unified-metadata-standard.md) — OpenLineage schema; event taxonomy defined here MUST conform
- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — homeostasis pipeline events are a subset of the taxonomy here
- [ADR-S-025](ADR-S-025-CONSENSUS-functor.md) — CONSENSUS event sources
- [ADR-S-026](ADR-S-026-named-compositions-and-intent-vectors.md) — Named Composition event sources
- [ADR-S-027](ADR-S-027-spec-consolidation-authority-boundaries.md) — Resolutions 1 and 3 (projection scope, event registrations)
- [ADR-S-037](ADR-S-037-projection-authority-and-convergence-evidence.md) — enforcement at workspace boundary; retroactive-evidence language should be read in light of §5 (control vs trace surface)
- `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3, §4, §5
