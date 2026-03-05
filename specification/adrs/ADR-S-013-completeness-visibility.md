# ADR-S-013: Completeness Visibility — Feature Coverage and Convergence Signals

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-04
**Scope**: `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §4.1, §6.1, §6.4 — convergence criterion for Feature Decomposition, coverage projection invariant, convergence visibility invariant

---

## Context

The formal model defines convergence precisely (delta=0, ConvergenceAchieved event) but leaves two questions unanswered:

**Question 1: "Did I get all the features?"**

This is the first-order completeness question — asked from day one, before any code is written. The Feature Decomposition node exists in the graph but has no formal convergence criterion. The spec does not say what it means for the feature list to be *complete*. A user generating feature vectors has no signal that they have captured all requirements. This is prior to every other completeness question — you cannot ask "is feature X done?" until you know the feature list is right.

**Question 2: "Is it done?"**

This is asked at every level: after an iterate() call, after an edge, after a feature. The model emits ConvergenceAchieved events but defines no visibility requirement — no mandate that convergence be communicated in human-readable form. The event stream is the source of truth but not a human interface. Users and operators have no unambiguous "done" signal.

Both questions share the same root: the spec defines when convergence occurs but not how it is made visible. This is a spec-level gap because visibility is a correctness property, not a UX preference — an implementation that converges silently is non-conformant regardless of its internal correctness.

---

## Decision

### 1. Feature Decomposition Convergence Criterion

The `requirements → feature_decomposition` edge converges when two conditions are both satisfied:

**Condition A — REQ Coverage (F_D):**

```
coverage_delta = { r ∈ Requirements | ¬∃ f ∈ FeatureVectors : r ∈ f.satisfies }
converged_A ⟺ |coverage_delta| = 0
```

Every REQ-* key defined in the requirements document MUST appear in the `satisfies:` field of at least one feature vector. This is a deterministic check — computable by grep/index, no LLM required, always the same answer for the same inputs.

**Condition B — Human Build Plan Approval (F_H):**

A human actor MUST explicitly approve that:
- The feature list is the right decomposition of the requirements (not just complete, but correct)
- The dependency ordering is buildable
- The MVP boundary is correctly placed

F_D coverage alone is necessary but not sufficient. A feature list can cover all REQs and still be the wrong decomposition — wrong granularity, circular dependencies, wrong MVP cut. F_H is the judgment gate.

**Convergence criterion:**

```
converged(feature_decomposition) ⟺ coverage_delta = 0 AND human_approved = true
```

The F_D check gates the F_H review — no human review is requested until all REQs are covered. This prevents premature approval of an incomplete list.

### 2. REQ Coverage Projection (always-visible)

Implementations MUST maintain a **coverage projection** — a human-readable mapping from requirements to feature vectors — that is recomputable at any time from the event stream and source artifacts. It is not stored; it is projected on demand.

The projection MUST show:

```
FEATURE COVERAGE — {project}
  Requirements: {N} REQs defined
  Covered:      {n}/{N}  {progress_bar}  {pct}%
  Gaps:         {list of uncovered REQ-* keys}

  Features:     {M} vectors
    ✓ converged     {k}
    ⟳ in-progress   {j}
    ○ not started   {m - k - j}
```

**Invariant (Coverage Projection Availability)**:

```
At any point in time t after feature_decomposition is initiated,
coverage_projection(t) MUST be computable in O(artifacts)
without LLM invocation.
```

The projection is always available, always current, and always free to compute. It is the primary answer to "did I get all the features?" — visible from the moment the first feature vector is created, not just at convergence.

### 3. Convergence Visibility Invariant

For every convergence state transition — IterationCompleted, ConvergenceAchieved, or FeatureComplete — a human-readable summary MUST be produced before the next IterationStarted on any downstream edge.

**Three required summary levels:**

**Level 1 — Iteration summary** (after every iterate() call, converged or not):

```
ITERATION {n} — {edge}
  delta: {current}  (was {previous})
  {evaluator results: ✓ name | ✗ name (reason)}
  → {converged | continuing | blocked}
```

**Level 2 — Edge convergence notice** (when delta=0 on an edge):

```
CONVERGED — {edge}  [{feature_id}]
  delta: 0 — all checks pass
  {summary of what was produced}
  next: {next_edge | feature complete}
```

**Level 3 — Feature completion** (when all edges in a feature vector converge):

```
COMPLETE — {feature_id}: {title}
  {n}/{n} edges converged
  REQ coverage: {satisfies list}
  → ready for review
```

**Invariant (Convergence Visibility)**:

```
For every ConvergenceAchieved(edge, instance) event emitted,
a Level 2 summary MUST be produced and observable by the human actor
before IterationStarted(next_edge, instance) is emitted.

For every FeatureComplete(feature_id) event emitted,
a Level 3 summary MUST be produced.

The summary MUST unambiguously state one of:
  { converged | not-yet | blocked }
and MUST include the delta value and which evaluators passed/failed.
```

Implementations MAY produce these summaries as CLI output, structured logs, UI notifications, or any other human-observable channel. The form is a design decision. The requirement — that convergence is made unambiguously visible before downstream work proceeds — is spec-level.

---

## Consequences

**Positive:**

- **"Did I get all the features?" is answerable from day one.** The coverage projection is available from the moment the first feature vector is created. The gap list tells users exactly what requirements are uncovered.

- **"Is it done?" has an unambiguous answer at every level.** Iteration, edge, and feature each have a defined summary. The system cannot silently converge.

- **F_D gates F_H.** No human review is wasted on an incomplete feature list. The deterministic coverage check runs first, cheaply, every time.

- **Coverage projection is free.** Computable from artifacts by grep/index. No LLM cost. Always current. Always available.

- **Feature Decomposition is a first-class convergence event.** It has a criterion, a delta, and a visibility requirement — the same as every other edge. The methodology is internally consistent.

**Negative / Trade-offs:**

- **`satisfies:` field is now a required field** on every feature vector. Implementations must enforce its presence and its REQ-* key format. Existing feature vectors without this field are non-conformant.

- **F_H approval is a blocking gate.** The feature_decomposition edge cannot mark as converged without explicit human approval, even if coverage_delta=0. This is intentional — it cannot be skipped even in automated pipelines. Spike and minimal profiles may reduce the F_H gate to a single acknowledgement, but cannot eliminate it.

- **Three summary levels means three new output requirements** for every implementation. Minimal implementations (spike profile) may collapse all three into a single summary line, but must produce something observable.

### 4. Re-entrant Convergence and Feature Origin Invariant

**Feature Decomposition convergence is not a terminal state.** It is the current best understanding. Any new feature — regardless of origin — re-opens the delta and triggers the same process.

**Feature Origin Invariant:**

```
The process for handling a new feature is identical regardless of how it was discovered:

  discovered gap    → feature_proposal
  stakeholder req   → feature_proposal
  homeostasis signal → feature_proposal
  technical finding → feature_proposal
```

The model is silent on origin. `feature_proposal` is the universal intake. Once emitted, every feature follows the same path: F_D coverage check, F_D impact assessment, F_H delta approval. The system does not distinguish between "we missed this" and "we were given this" — both are the same operation at the model level.

**Delta approval — not full re-approval:**

When a new feature arrives, the human approves the *delta*, not the whole list. Unchanged features do not need re-approval. The F_H gate is scoped to:
1. Does this new feature fit the existing decomposition?
2. Does it cascade into existing features?

**Impact assessment (F_D, deterministic):**

```
impact_set = { f ∈ FeatureVectors | f shares design, module, or code assets with new_feature }

impact_set = ∅  → additive, no cascade, proceed to F_H delta approval
impact_set ≠ ∅  → F_P assesses whether shared assets need re-iteration
                   F_H decides: compensate affected edges or accept as-is (ADR-S-012 saga invariant)
```

The impact set is computable by graph traversal — no LLM required. Whether impact *forces* re-iteration is judgment (F_P + F_H). The spec defines the computation; the design binds it to technology.

---

## Alternatives Considered

**No convergence criterion for feature_decomposition — leave it to human judgment**: The human just decides when the list is good enough. Rejected — without a formal criterion, the feature list has no convergence signal and the F_D coverage check is never run. Users have no quantitative answer to "what's missing?"

**F_D coverage alone, no F_H gate**: Coverage_delta=0 is sufficient for convergence. Rejected — a feature list can cover all REQs and be the wrong decomposition. The human judgment about granularity, dependency order, and MVP boundary cannot be replaced by a coverage check.

**Convergence visibility as a UX feature, not a spec requirement**: Leave it to each implementation to decide how to show convergence. Rejected — silent convergence is a correctness failure. If a user cannot tell whether the system has converged, they cannot use the system reliably. Visibility is as fundamental as the convergence criterion itself.

**Store the coverage projection**: Materialise and cache it. Rejected — coverage is a projection of the event stream and source artifacts. It must be recomputable on demand to satisfy the Completeness invariant (ADR-S-012). Storing it creates a consistency risk.

---

## References

- [ADR-S-012](ADR-S-012-event-stream-as-formal-model-medium.md) — event stream as source of truth; coverage projection is a read-side projection of the stream
- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — feature_proposal and spec_modified events; the coverage projection drives what proposals are needed
- [ADR-S-004](ADR-S-004-derivation-constraint.md) — downstream may not contradict upstream; coverage criterion enforces this at the feature_decomposition boundary
- `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §6.1, §6.4 — feature vector definition and feature views; updated per this ADR
- `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` — new REQ-VIS-* series required
