# ADR-S-034: The Genesis Ecosystem — Cooperative Services, Co-Evolution, and Emergent Niches

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-11
**Scope**: Ecosystem layer — multiple Genesis-enabled systems interacting, co-evolving,
  discovering niches through mutual intent observation
**Depends on**: ADR-S-033 (Genesis-Enabled Systems), ADR-S-032 (IntentObserver + EDGE_RUNNER),
  GENESIS_BOOTLOADER.md §VI (The Gradient), §VIII (Homeostasis), §IX (IntentEngine)
**Foundation**: Constraint-Emergence Ontology

---

## Context

ADR-S-033 defines a Genesis-enabled system: one that runs the four primitives
at runtime, maintains its own event stream, and routes production delta back
into its build graph. This is the single cell — self-maintaining, homeostatic,
alive.

But software systems do not exist in isolation. A microservice has dependencies.
A dependency has its own spec, its own tolerances, its own runtime signals. When
one service's latency degrades, its consumers detect the delta in their own
telemetry. When a shared library releases a breaking change, every dependent
system faces a new gap.

In a system of Genesis-enabled services, these interactions are not accidents —
they are the mechanism by which the ecosystem discovers its own structure. Each
service runs its homeostatic loop independently. The topology of their
interactions is not designed top-down; it emerges from mutual constraint
satisfaction across overlapping delta surfaces.

This is the classical sense of ecosystem: no central coordinator, no global
planner, no master topology. Agents with local rules. Structure as emergence.
Niches as stable configurations within a constraint field.

---

## Decision

### The Ecosystem is Emergent, Not Orchestrated

Genesis does not orchestrate the ecosystem. It enables the cells that form it.
Each Genesis-enabled service:

- Runs its own `dispatch_monitor` over its own `events.jsonl`
- Defines its own constraint surface (spec, SLAs, tolerances)
- Emits its own `intent_raised` signals when delta > 0
- Routes its own work through its own `EDGE_RUNNER`

No service knows the global topology. No service plans the ecosystem. The
ecosystem is the sum of all running homeostatic loops, and it is always alive
because some delta is always > 0 somewhere.

### Niche Discovery Through Mutual Intent Observation

A **niche** in the classical ecological sense is a stable configuration — a
service that satisfies a constraint no other service satisfies, in a position
where its existence reduces delta for its neighbours.

In a Genesis ecosystem, niches are discovered, not designed:

1. Service A emits `intent_raised`: "need capability X — no current provider"
2. Service B observes A's intent stream (exteroception — ADR-S-008)
3. B computes: `delta(B.capabilities, A.needs) > 0` — B could fill this gap
4. B emits its own `intent_raised`: "opportunity to provide X"
5. B iterates toward providing X
6. A's delta → 0: need satisfied
7. B has found a niche

This is not planned integration. It is constraint satisfaction across interacting
loops. The niche exists because two constraint surfaces overlap in a way that
reduces total system delta.

### Co-Evolution Through Shared Constraint Surfaces

Services co-evolve when one service's convergence changes the constraint surface
of another:

```
Service A converges on interface contract v2
  → publishes spec_modified event to ecosystem stream
  → Service B reads: delta(B.dependency_on_A, A.new_contract) > 0
  → B emits intent_raised: "A interface changed — adaptation required"
  → B iterates → adapts → B converges on A.v2
  → Service C (depends on B) detects B's change
  → C emits intent_raised
  → ...
```

This is co-evolution: each convergence propagates as constraint change to
neighbours. The ecosystem is never fully at rest — it is always adjusting to
the most recent convergence event somewhere in the graph.

The gradient (`delta(state, constraints) → work`) operates at ecosystem scale
exactly as it operates at single-iteration scale. The constraint surface is
the union of all deployed specs. The delta is the distance between the current
collective state and that surface. Work is produced until delta → 0 — which,
in a living ecosystem, never fully arrives.

### The Ecosystem Event Stream

A Genesis ecosystem has two event stream layers:

**Local streams** (per service, per ADR-S-012):
- Each service's `events.jsonl` — its own build-time and runtime signals
- Isolated by `instance_id` (ADR-S-012 projection invariant)
- The service's `dispatch_monitor` watches only its own stream

**Ecosystem stream** (cross-service):
- A shared append-only stream for inter-service signals
- Event types: `capability_published`, `dependency_changed`, `niche_detected`,
  `interface_contract_modified`, `sla_breach_propagated`
- Services subscribe to ecosystem signals relevant to their constraint surface
- Exteroceptive monitors (ADR-S-008 Stage 1) are the intake mechanism

The ecosystem stream is not a message bus in the traditional sense — it is
not synchronous, not transactional, not guaranteed-delivery. It is an
**observation layer**: services emit what they have learned; other services
observe what is relevant to their constraints. The delivery guarantee is
eventual consistency toward lower total delta.

### The REQ Key as Ecosystem Identifier

The REQ key thread (ADR-S-003) extends into the ecosystem:

```
Service A:  REQ-F-AUTH-001 (authentication capability)
  publishes to ecosystem: capability="REQ-F-AUTH-001", contract=v2.3

Service B:  depends_on: REQ-F-AUTH-001@>=v2.0
  observes: REQ-F-AUTH-001 published at v2.3
  evaluates: delta(B.dependency, A.capability) = 0  ← satisfied

Service C:  depends_on: REQ-F-AUTH-001@>=v3.0
  observes: REQ-F-AUTH-001 published at v2.3
  evaluates: delta(C.dependency, A.capability) > 0  ← gap
  emits: intent_raised { trigger: "REQ-F-AUTH-001 at v2.3, need v3.0" }
```

REQ keys name capabilities across service boundaries. A service that publishes
`REQ-F-AUTH-001` is advertising a capability by its spec identifier. A service
that declares `depends_on: REQ-F-AUTH-001` is registering a constraint. The
ecosystem's delta is the set of unresolved `depends_on` constraints across all
services.

This is the same mechanism as feature dependencies within a single project
(FEATURE_VECTORS.md dependency DAG) — extended to the inter-service layer.

### Stability, Diversity, and Resilience

**Stability**: An ecosystem reaches a locally stable configuration when all
declared `depends_on` constraints are satisfied and no `intent_raised` events
are unhandled. This is never permanent — a new service joining, a contract
change, or an external signal (CVE, ecosystem dependency update) destabilises
it, triggering new co-evolution.

**Diversity**: Services that satisfy different constraint surfaces coexist
without conflict. A niche is occupied when a service's capability uniquely
satisfies a gap in the ecosystem. Multiple services can satisfy the same
constraint (redundancy / competition) — the ecosystem resolves this through
the CONSENSUS functor (ADR-S-025) when a choice must be made, or through
parallel coexistence when it need not be.

**Resilience**: Because each service runs its own homeostatic loop, a failure
in one service generates `intent_raised` signals in its dependents. Those
dependents route toward adaptation (find an alternative, degrade gracefully,
or escalate to F_H). The ecosystem does not have a single point of failure —
it has many local homeostatic loops that collectively absorb perturbations.

### Genesis as the Evolutionary Substrate

Genesis does not design the ecosystem. It is the **substrate** on which
ecosystem evolution happens:

- The formal system (4 primitives, 1 operation) is the evolutionary mechanism
- The constraint surface (spec + tolerances) is the selection pressure
- `intent_raised` is the variation signal
- `EDGE_RUNNER` convergence is the selection event
- The REQ key thread is the genetic material — the stable identifier that
  persists across generations of the service

A service that converges on a capability is not just "done" — it has found a
locally stable configuration within the current constraint field. When the
field changes (co-evolution, new entrants, external signals), it iterates again.
Fitness is not a fixed property; it is delta → 0 within a moving constraint
surface.

---

## Consequences

**Positive**:
- No ecosystem coordinator required. The topology emerges from constraint
  satisfaction. Adding a new service requires only that it publish its
  capabilities and declare its dependencies — the ecosystem self-organises.
- Resilience is structural. Each service's homeostatic loop absorbs its own
  perturbations. The ecosystem's resilience is the sum of its cells' resilience.
- Evolution is continuous. The ecosystem never finishes. It is always adjusting
  to the most recent convergence. This is a feature, not a bug — a finished
  ecosystem is a dead one.
- The same formal system operates at every scale: iteration, edge, feature,
  service, ecosystem. The gradient is scale-invariant.

**Negative / Trade-offs**:
- Ecosystem stream design is non-trivial. Defining which signals cross service
  boundaries, how they are scoped, and how exteroceptive monitors subscribe
  requires careful implementation. ADR-S-014 (OTLP/Phoenix) and ADR-S-011
  (OpenLineage) are the relevant binding points.
- Niche discovery is emergent, not plannable. Product teams accustomed to
  top-down architecture may find this disorienting. The answer is: define
  constraint surfaces clearly, declare dependencies formally, and let the
  ecosystem resolve the topology. Planning the topology in advance defeats
  the mechanism.
- Co-evolution propagation can cascade. A contract change in a widely-depended
  service triggers `intent_raised` signals across many dependents simultaneously.
  Budget controls (ADR-S-016) and time-boxing (PROJECTIONS_AND_INVARIANTS.md)
  bound the cascade.

---

## The Three-Sentence Genesis Value Proposition

**Genesis builds software.**
A Genesis-enabled system maintains itself against its specification at runtime.
A Genesis ecosystem of cooperative services co-evolves, discovering niches and
needs, sustaining itself without a coordinator — alive in the classical sense.

---

## References

- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §VI (The Gradient — scale invariance)
- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §VIII (Homeostasis — intent is computed)
- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §IX (IntentEngine — composition law)
- [ADR-S-033](ADR-S-033-genesis-enabled-systems.md) — the single Genesis-enabled service (the cell)
- [ADR-S-032](ADR-S-032-intentobserver-edgerunner-dispatch-contract.md) — dispatch_monitor (the cell's metabolism)
- [ADR-S-025](ADR-S-025-consensus-functor.md) — CONSENSUS (governance in the ecosystem)
- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — exteroceptive monitors (ecosystem signal intake)
- [ADR-S-003](ADR-S-003-req-key-format.md) — REQ key as ecosystem identifier
- Foundation: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology)
