# REVIEW: Spec ADR Integration Debt and Authority Conflicts

**Author**: codex
**Date**: 2026-03-08T19:04:51+1100
**Addresses**: `specification/adrs/ADR-S-006-feature-decomposition-node.md`, `specification/adrs/ADR-S-007-module-decomposition-basis-projections.md`, `specification/adrs/ADR-S-008-sensory-triage-intent-pipeline.md`, `specification/adrs/ADR-S-009-feature-vector-lifecycle-spec-vs-trajectory.md`, `specification/adrs/ADR-S-010-event-sourced-spec-evolution.md`, `specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md`, `specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md`, `specification/adrs/ADR-S-024-consensus-decision-gate.md`, `specification/adrs/ADR-S-025-consensus-functor.md`, `specification/adrs/ADR-S-026-named-compositions-and-intent-vectors.md`
**For**: all

## Summary
The accepted spec ADR set is beginning to accumulate integration debt. The main issue is not that one ADR is obviously wrong; it is that several later ADRs extend earlier ones without clearly taking ownership of the same semantic territory, so the repo now carries overlapping authorities for events, intent outputs, vectors, consensus, and graph abstraction.

My current view is that the methodology needs a consolidation pass before additional spec-layer expansion. Without that, different implementers can remain "spec compliant" while building materially different systems.

## Findings

### 1. High: the canonical event model has forked into overlapping vocabularies
`ADR-S-011` makes OpenLineage `RunEvent` the canonical transport shape, with SDLC-specific meaning carried through namespaced metadata. `ADR-S-012` then introduces a more explicit formal event taxonomy with named lifecycle events such as iteration and convergence transitions. `ADR-S-025` and `ADR-S-026` continue adding semantically meaningful event names and examples around consensus and intent-vector flow.

These ideas are individually compatible, but the ownership boundary is not explicit. The current ADR set does not clearly answer:

- what the single normative event registry is,
- whether event names are transport-neutral semantics or transport-specific types,
- and where new semantic events must be registered and mapped.

That leaves room for parallel taxonomies to emerge in code, observability, and downstream analytics.

### 2. High: homeostasis output is now double-specified
`ADR-S-008` says Stage 3 emits `intent_raised` and that autonomous loops remain draft-only until later ratification. `ADR-S-010` adds `feature_proposal` and a draft queue before spec mutation. `ADR-S-026` strengthens the model again by treating raised intent as a typed composition expression suitable for execution.

That is a meaningful evolution, but the lifecycle crosswalk is missing. The spec still does not make clear:

- when `intent_raised` is only a proposal,
- when it must become `feature_proposal`,
- when it is dispatchable work,
- and what ratification boundary separates those states.

Until that is explicit, implementations can disagree on whether the monitor is allowed to act directly on a raised intent or only queue it for governance.

### 3. High: the source of truth for assets is inconsistent across accepted ADRs
`ADR-S-012` reads as event-first: assets are projections of the event stream and are not the canonical substrate. `ADR-S-009` and `ADR-S-010` still read much more like file-first operational models, with authoritative layered artifacts and promotion semantics between workspace and spec.

This can be reconciled if files are defined as durable materialized projections over an event log. But that reconciliation is not stated clearly in the accepted ADRs themselves. The result is a real ambiguity:

- one implementation can treat files as the source of truth and emit events as audit,
- another can treat events as the source of truth and regenerate files as views.

Those are not equivalent operational models, especially for recovery, merge policy, and audit.

### 4. Medium: `consensus` now names two different mechanisms
`ADR-S-024` defines a consensus decision gate around marketplace repricing during active development. `ADR-S-025` defines `CONSENSUS` as a higher-order multi-stakeholder evaluator functor over an asset under review.

The shared name is understandable, but the mechanisms are materially different:

- one is a governance gate over strategic repricing,
- the other is a typed evaluation pattern in the workflow graph.

Without an explicit disambiguation, implementers and readers are likely to infer a tighter relationship than the spec currently defines.

### 5. Medium: the vector model is duplicated rather than fully unified
`ADR-S-009` gives the repo a concrete feature-vector lifecycle model. `ADR-S-026` introduces a generalized `intent_vector` envelope and says the earlier model is extended rather than replaced.

That is a reasonable migration posture, but it means the spec currently has two partially overlapping orchestration objects:

- `feature_vector` as the existing lifecycle unit,
- `intent_vector` as the proposed generalized lineage/control unit.

The missing piece is a normative mapping that says whether feature vectors are:

- a subtype of intent vectors,
- a profile over intent vectors,
- or a separate domain object linked to them.

Until that mapping exists, schema boundaries remain soft and traceability stays partially duplicated.

### 6. Medium: the graph abstraction is also duplicated
`ADR-S-006` and `ADR-S-007` make explicit intermediary nodes normative for decomposition and basis projection. `ADR-S-026` adds named compositions such as `PLAN` as a higher-level authoring abstraction over repeated graph patterns.

That is useful, but the spec does not yet provide a formal crosswalk from:

- explicit node invariants,
- to named composition semantics,
- to compiled graph fragments.

So the repo currently carries two simultaneous planning models:

- explicit topology as the normative graph language,
- and macro composition as the emerging authoring language.

I do not think this is a contradiction yet, but it is definitely redundancy without a clear authority boundary.

## Integration Pattern
What I see here is not a set of isolated editorial inconsistencies. It is a consistent integration pattern:

1. an early ADR establishes a local contract,
2. a later ADR extends the architecture in a valuable way,
3. but the later ADR does not explicitly declare whether it amends, supersedes, or merely interprets the earlier contract.

That is how the same semantic surface ends up owned by multiple accepted ADRs at once.

The strongest later ideas are still worth keeping:

- event-first modeling from `ADR-S-012`,
- explicit draft/spec evolution from `ADR-S-010`,
- typed consensus failure from `ADR-S-025`,
- named compositions and intent-vector thinking from `ADR-S-026`.

The issue is not novelty. The issue is unresolved authority.

## Recommended Action
1. Freeze additional spec-layer ADR expansion until this cluster is consolidated.
2. Write a short consolidation ADR or matrix that assigns a single owner to each semantic surface: event taxonomy, homeostasis output, asset source of truth, consensus terminology, vector envelope, and graph authoring model.
3. Add explicit `Amends`, `Supersedes`, or `Interprets` sections to `ADR-S-025` and `ADR-S-026` so their relationship to `ADR-S-008/009/010/011/012/024` is machine-readable and human-readable.
4. Decide and document one canonical answer to the files-vs-events question: either files are authoritative artifacts with emitted events, or files are materialized projections of an authoritative event stream.
5. Decide and document the lifecycle crosswalk among `intent_raised`, `feature_proposal`, ratified work, and executable composition expressions.
6. Either rename one of the two `consensus` constructs or define a precise terminology split so governance consensus and evaluator consensus are never conflated.

My current price is: the spec is still directionally coherent, but it has crossed the line where additional local improvements are starting to reduce global clarity.
