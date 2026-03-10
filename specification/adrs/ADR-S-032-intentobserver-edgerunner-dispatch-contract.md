# ADR-S-032: IntentObserver and EDGE_RUNNER — Autonomous Dispatch Contract

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-11
**Scope**: Homeostatic loop closure — autonomous dispatch from `intent_raised` to edge traversal
**Revises**: ADR-S-008 §Implementation Invariants (Draft-Only Autonomy)
**Depends on**: ADR-S-008 (Sensory-Triage-Intent Pipeline), ADR-S-012 (Event Stream),
  ADR-S-025 (CONSENSUS Functor), ADR-S-029 (Dispatch Contract)

**Review record**:
- Proposed: Claude Code `20260311T020000` via marketplace STRATEGY posts
- Codex review: `20260311T040646` — agreed, confirmed parity gap and Codex-specific
  schema binding (`affected_req_keys` → `affected_features` mapping)
- Ratified: 2026-03-11 (cross-tenant consensus, two independent implementations)

---

## Context

ADR-S-008 formalised the Sensory-Triage-Intent pipeline and named three stages:
Sensing → Affect Triage → Intent Generation. Stage 3 emits `intent_raised`
events. ADR-S-008 then imposed a hard constraint (Invariant 2):

> "Draft-Only Autonomy: Homeostatic responses are generated as draft proposals
> only. No autonomous modification of production assets without human approval."

This invariant was correct at the time — it prevented an unproven loop from
making autonomous changes. It is now the architectural source of Finding 1 in
data_mapper.test11: the homeostatic loop can detect delta but cannot act on it.
The `intent_raised` event is emitted and sits in the event log with no engine
component reading it and dispatching work.

Cross-tenant evaluation (Claude + Codex, March 2026) confirmed:
- Both implementations have the same gap — `intent_raised` is emitted, no
  autonomous consumer exists
- Both implementations have CONSENSUS as a correct F_H package, not the missing
  component
- The missing component is the **IntentObserver** — an engine-backed reader of
  the intent stream that dispatches **EDGE_RUNNER** in response to detected deltas

---

## Decision

### 1. IntentObserver — Named Executable Component

IntentObserver is a named component in the formal system. It is the Stage 4
addition to the ADR-S-008 pipeline:

```
Stage 1: Continuous Sensing      → interoceptive_signal / exteroceptive_signal
Stage 2: Affect Triage           → reflex.log or escalation
Stage 3: Intent Generation       → intent_raised
Stage 4: Intent Dispatch         → IntentObserver → EDGE_RUNNER        ← THIS ADR
```

**IntentObserver contract**:

```
input:  events.jsonl (intent_raised stream)
output: EDGE_RUNNER dispatch
guard:  deduplication via edge_started (intent already handled)
```

**Dispatch algorithm**:

```
on intent_raised event e:
  scope = e.data.affected_features
  if scope is empty or ["all"]:
    mode = BOOTSTRAP                     # full gap analysis — traverse all features
  else:
    mode = HOMEOSTASIS                   # constrained — traverse named features only

  for each feature_id in resolve(scope):
    if edge_started exists for (e.intent_id, feature_id):
      skip                               # already dispatched — deduplication guard
    load feature_vector(feature_id).trajectory
    first_edge = first non-converged edge in topological order
    emit edge_started(intent_id=e.intent_id, feature=feature_id, edge=first_edge)
    dispatch EDGE_RUNNER(first_edge, feature_id, context[intent_stream ∩ feature_id])
```

The `edge_started` event is the idempotency marker. On session resume,
IntentObserver re-scans for `intent_raised` events with no matching
`edge_started` — those are unhandled and re-dispatched. Events with a matching
`edge_started` are skipped.

### 2. EDGE_RUNNER — Execution Contract

EDGE_RUNNER is the executor that traverses a single edge for a single feature.
It is not a new primitive — it is the composition of existing components:

```
EDGE_RUNNER(edge, feature, context) =
  F_D: evaluate(asset, edge_params, context)       # deterministic gate
  if F_D.delta == 0: converge → edge_converged
  F_P: dispatch(fp_intent_manifest)                # fold-back protocol (ADR-023/024)
  re-evaluate F_D against fold-back result
  if F_D.delta == 0: converge → edge_converged
  if budget_exhausted or max_iterations: F_H gate
  F_H: singular or CONSENSUS per edge policy       # human or multi-party
  → convergence | escalation | stuck
```

CONSENSUS (ADR-S-025) is the F_H evaluator configuration for edges requiring
multi-party accountability. It is invoked by EDGE_RUNNER at the F_H gate when
the edge policy specifies `F_H.mode: CONSENSUS`. CONSENSUS is not an
orchestration layer — it is what F_H looks like on those edges.

### 3. Gap Analysis as Scoped F_D Traversal

Gap analysis is not a separate phase before traversal. It is the F_D evaluation
at the first non-converged edge inside EDGE_RUNNER, with `Context[]` scoped by
the intent vector.

**The scope parameter is the only variable**:

| Operation | `Context[scope]` | Entry point |
|-----------|-----------------|-------------|
| Full gap analysis | all features, all spec | Bootstrap — no prior feature vectors |
| Intent-scoped repair | `intent_raised.affected_features` | Homeostasis — feature vectors exist |

`/gen-gaps` is the human-invocable form of the IntentObserver bootstrap path.
`/gen-gaps --feature REQ-F-X` is the human-invocable form of intent-scoped
traversal. Both emit `intent_raised` events that IntentObserver would pick up
and dispatch autonomously in an engine-backed system.

**Invariant**: gap analysis and edge traversal are the same operation under
different `Context[scope]`. Implementations MUST NOT treat gap analysis as a
separate execution path.

### 4. Canonical Intent Payload Field: `affected_features`

The canonical field for dispatch routing in `intent_raised` is `affected_features`.

| Field | Role | Required |
|-------|------|----------|
| `affected_features` | IntentObserver dispatch key — which feature vectors to traverse | Yes |
| `affected_req_keys` | F_D evaluation hint — which specific REQ keys have gaps | Optional |

**Rationale**: EDGE_RUNNER's atomic dispatch unit is a feature vector, not a
REQ key. `affected_features` maps directly to the dispatch unit with no
indirection. `affected_req_keys` is subordinate — a feature vector contains REQ
keys; if you have the feature, you can enumerate its keys.

**Tenant binding note**: Implementations using `affected_req_keys` as the
primary field (e.g., `imp_codex`) MUST map to `affected_features` at the
IntentObserver boundary. The mapping rule: group `affected_req_keys` by their
owning feature vector. The dispatch unit is the feature, not the individual
key.

**Canonical `intent_raised` payload**:

```json
{
  "event_type": "intent_raised",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "intent_id": "INT-{SEQ}",
    "trigger": "{what detected the delta}",
    "delta": "{specific gap description}",
    "signal_source": "{gap|postmortem|sensory|test_failure|refactoring}",
    "vector_type": "feature|hotfix|spike|discovery",
    "severity": "high|medium|low",
    "affected_features": ["{feature_id}", "..."],
    "affected_req_keys": ["{REQ-*}", "..."]
  }
}
```

`affected_features` is required. `affected_req_keys` is optional context.

### 5. Revision to ADR-S-008 Invariant 2 (Draft-Only Autonomy)

ADR-S-008 Invariant 2 is replaced by the following:

**Prior text**:
> "Draft-Only Autonomy: Homeostatic responses are generated as draft proposals
> only. No autonomous modification of production assets without human approval."

**Revised text**:
> "Graduated Autonomy: F_D and F_P phases of EDGE_RUNNER execute autonomously
> in response to `intent_raised` events. F_H gates (singular or CONSENSUS)
> remain human-controlled — no asset transitions through an F_H gate without
> explicit human or accountable-participant action. The autonomy boundary is
> the F_H gate, not the intent signal."

**What changes**: IntentObserver may dispatch EDGE_RUNNER without human
instruction. EDGE_RUNNER may run F_D and F_P phases autonomously. F_H gates
are unchanged — they require human action.

**What does not change**: No asset marked as converged through an F_H gate
without human or CONSENSUS approval. The audit trail (event log) records all
autonomous actions. Autonomous dispatch is bounded by the feature vector scope
in `affected_features` — IntentObserver does not dispatch beyond the named
features.

### 6. Brute-Force First

Implementations SHOULD implement brute-force traversal before optimised
localisation. Brute force: IntentObserver traverses the full profile edge chain
for all features in scope. Converged edges return immediately at F_D (delta = 0,
no F_P or F_H invoked). The feature vector trajectory is the memoisation layer.

Optimised localisation (enter at the specific delta node) is a performance
improvement and MAY be implemented once the brute-force loop is stable.
Premature localisation risks gap survival if the delta node is misidentified.

---

## Consequences

**Positive**:
- The homeostatic loop is closed. `delta → work` is autonomous through F_D and
  F_P phases. The 11-hour session gap in data_mapper.test11 is structurally
  eliminated.
- Finding 2 (event emission bypassed) becomes self-healing: IntentObserver
  detects missing events as delta, dispatches EDGE_RUNNER to re-traverse the
  affected edges formally, restoring the audit trail.
- Gap analysis and traversal unify into one operation. No separate "gap engine"
  required.
- CONSENSUS is correctly positioned — pure F_H package, invoked by EDGE_RUNNER
  at the F_H gate, not an orchestration layer.

**Negative / Trade-offs**:
- Autonomous F_P dispatch carries cost (LLM/compute per dispatch). Budget
  controls from ADR-S-016 (invocation contract `budget_usd`) apply.
- IntentObserver must correctly scope dispatch to `affected_features`. An
  intent with `affected_features: ["all"]` triggers full traversal — expensive
  at large feature counts. Implementations should apply the bootstrap/homeostasis
  distinction strictly.
- The F_P/F_H epoch boundary (when does F_P exhaustion trigger F_H?) must be
  defined per-edge in edge_params config. This is a configuration obligation,
  not an architectural question.

---

## Alternatives Considered

**Extend CONSENSUS as full orchestrator (Option A)**: Add F_D and F_P phases
to CONSENSUS as Phase -1 and Phase 0. Rejected — blurs CONSENSUS's correct
identity as a pure F_H package. Two independent tenant implementations
(Claude, Codex) confirmed Option B (separate EDGE_RUNNER) fits their
architectures better. Option A would require redesigning CONSENSUS for both.

**Dedicated `edge_dispatch_requested` event**: Add a new event type between
`intent_raised` and EDGE_RUNNER dispatch to record the routing decision.
Rejected — routing is a computation (deterministic from `affected_features` +
graph topology), not a state transition. Computations do not belong in the
event log (ADR-S-012). `edge_started` already serves as the dispatch marker and
deduplication guard.

**Keep Draft-Only Autonomy, add human approval step**: Require human to approve
each `intent_raised` before dispatch. Rejected — this is the current state and
the source of Finding 1. Human approval at intent level defeats homeostasis.
Human gates remain at F_H, not at intent dispatch.

---

## References

- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — pipeline this ADR extends (Stage 4)
- [ADR-S-012](ADR-S-012-event-stream-as-formal-model-medium.md) — event log as substrate
- [ADR-S-016](ADR-S-016-invocation-contract.md) — budget and invocation contract for F_P actors
- [ADR-S-025](ADR-S-025-consensus-functor.md) — CONSENSUS as F_H evaluator mode
- [ADR-S-029](ADR-S-029-the-dispatch-contract.md) — graph_fragment compiled intermediate
- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §VII — escalation chain η: F_D → F_P → F_H
- Marketplace: `.ai-workspace/comments/claude/20260311T000000_GAP_CONSENSUS-FP-dispatch-homeostatic-loop.md`
- Marketplace: `.ai-workspace/comments/claude/20260311T010000_STRATEGY_intentobserver-edgerunner-consensus-as-edge-type.md`
- Marketplace: `.ai-workspace/comments/claude/20260311T020000_STRATEGY_gap-analysis-is-fd-traversal-constrained-by-intent.md`
- Postmortem: `docs/analysis/20260310_POSTMORTEM_data_mapper_test11.md` (Finding 1, root cause)
