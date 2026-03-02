# ADR-S-010: Event-Sourced Spec Evolution

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-03
**Scope**: Homeostasis → spec pipeline — `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §4.5, §7.3, `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` §15

---

## Context

ADR-S-008 declares **Draft-Only Autonomy** as an implementation invariant: "Homeostatic responses (fixing the gap) are generated as draft proposals only. No autonomous modification of production assets without human approval." This is correct but incomplete. It establishes the rule but not the mechanism.

Three gaps remain:

1. **The draft has nowhere to live.** The homeostasis pipeline (ADR-S-008, Stage 3) is specified to "spawn a new feature vector" in response to an intent. But where does the draft feature live before the human approves it? If it is placed in `specification/features/`, that violates the draft-only rule. If it is placed in `.ai-workspace/features/`, that conflates the spec definition layer with the operational trajectory layer (ADR-S-009). The draft must live in neither — it must be in the event log only until approved.

2. **The spec has no observable history.** `specification/` is modified over time — new features are added, requirements are amended, ADRs are appended. These changes happen as file edits. The event log records implementation progress but not spec evolution. This means there is no causal chain linking a runtime observation (a signal from sensing) to the resulting spec change. The homeostasis loop is not closed: it can sense, triage, and generate intent, but the final step — "did the spec actually change, and why?" — is invisible.

3. **The promotion path is undefined.** When a human decides to approve a homeostasis-generated draft feature, what happens? There is no formal operation, no event emitted, and no link back to the triggering signal. The "Conscious Review" stage of the pipeline (ADR-S-008, Stage 3) terminates at `intent_raised` — but the spec is not modified by intent; it is modified by human decision following intent.

---

## Decision

### Two new event types in the canonical schema

#### `feature_proposal`

Emitted by the homeostasis pipeline (Stage 3 of ADR-S-008 Conscious Review) when gap analysis produces a candidate new feature or spec modification.

**Schema:**

```json
{
  "event_type": "feature_proposal",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "proposal_id": "PROP-{SEQ}",
    "proposed_feature_id": "REQ-F-{DOMAIN}-{SEQ}",
    "proposed_title": "{title}",
    "proposed_description": "{what this feature does}",
    "proposed_satisfies": ["REQ-*", "..."],
    "trigger_intent_id": "INT-{SEQ}",
    "trigger_signal_id": "{event ID of the originating signal}",
    "source_stage": "{homeostasis stage: interoceptive | exteroceptive | gap_analysis}",
    "rationale": "{why this feature is needed, derived from delta analysis}",
    "status": "draft"
  }
}
```

**Invariants:**
- This event exists in the event log **only**. It does NOT write to `specification/` or `.ai-workspace/features/`.
- The `proposed_feature_id` is provisional until promotion.
- Each `feature_proposal` has a `trigger_intent_id` — the causal link back to the `intent_raised` event that generated it.
- Status is always `draft` on emission.

#### `spec_modified`

Emitted whenever `specification/` is written — whether through the promotion path or through manual author edit.

**Schema:**

```json
{
  "event_type": "spec_modified",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "file": "{path relative to repo root}",
    "what_changed": "{human-readable summary: e.g., 'Added REQ-F-AUTH-003 to FEATURE_VECTORS.md'}",
    "previous_hash": "sha256:{hash of file content before change}",
    "new_hash": "sha256:{hash of file content after change}",
    "trigger_event_id": "{PROP-SEQ | INT-SEQ | 'manual'}",
    "trigger_type": "feature_proposal | intent_raised | manual"
  }
}
```

**Invariants:**
- Every write to `specification/` — including to `FEATURE_VECTORS.md`, `AISDLC_IMPLEMENTATION_REQUIREMENTS.md`, any ADR file — must have a corresponding `spec_modified` event.
- `previous_hash` and `new_hash` are content hashes of the specific file that changed. They enable verification: replay the event log and recompute hashes to confirm the spec evolved as recorded.
- `trigger_event_id: "manual"` is used when no causal homeostasis event exists (author made the change directly).
- Multiple files changed in one operation emit multiple `spec_modified` events (one per file), linked by the same `trigger_event_id`.

### The Draft Features Queue

The **Draft Features Queue** is the observable state of the promotion pipeline: the set of `feature_proposal` events that have not yet been followed by a `spec_modified` event referencing them.

```
Draft Features Queue = {
    event e : e.event_type == "feature_proposal"
    AND NOT EXISTS event m :
        m.event_type == "spec_modified"
        AND m.data.trigger_event_id == e.data.proposal_id
    AND NOT EXISTS event r :
        r.event_type == "feature_proposal_rejected"
        AND r.data.proposal_id == e.data.proposal_id
}
```

This queue is computable from the event log alone — it requires no additional state. `gen-status` must surface it (REQ-EVOL-005). It is the human review gate for homeostasis-generated features.

### The Promotion Operation (F_H)

Promotion is a human-gated (F_H) operation. Implementations provide a command (`gen-review approve {proposal_id}` or equivalent) that:

1. Reads the `feature_proposal` event from the event log by `proposal_id`.
2. Appends the feature definition to `specification/features/FEATURE_VECTORS.md` (or creates a new file in `specification/features/` for large features).
3. Emits `spec_modified` with `trigger_event_id = proposal_id`, `trigger_type = "feature_proposal"`.
4. Calls the inflate operation (ADR-S-009) to create `.ai-workspace/features/active/{feature_id}.yml`.
5. Reports to the user: new feature ID, spec file path, workspace vector path, spec content hash.

Promotion is atomic in intent: if the spec write fails, no `spec_modified` event is emitted. If the inflate fails, the `spec_modified` event was already emitted (spec is already modified). In this case, the orphaned workspace vector must be created on next `gen-spawn`.

### The Rejection Operation (F_H)

Rejection is equally human-gated. Implementations provide a rejection command that emits:

```json
{
  "event_type": "feature_proposal_rejected",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "proposal_id": "PROP-{SEQ}",
    "reason": "{why the proposal was rejected}",
    "rejected_by": "human"
  }
}
```

The rejected proposal is removed from the Draft Features Queue. No spec modification occurs.

### Manual spec edits

When a methodology author modifies `specification/` directly — without going through the homeostasis pipeline — the `spec_modified` event SHOULD be emitted by a post-commit hook (git hook or equivalent). The `trigger_type` is `"manual"` and `trigger_event_id` is `"manual"`.

Implementations that do not have hook infrastructure SHOULD emit the event via a manual command (`gen-spec-record` or equivalent) invoked by the author after editing. This is advisory — the spec can be modified without it — but without `spec_modified` events, spec changes are invisible to the homeostatic loop.

### Causal chain

The full provenance of a spec change is readable from the event log:

```
interoceptive_signal / exteroceptive_signal
    → intent_raised           (ADR-S-008 Stage 3)
    → feature_proposal        (this ADR — Stage 3 output)
    → [human reviews Draft Features Queue]
    → spec_modified           (this ADR — promotion)
    → spawn_created           (ADR-S-009 inflate)
    → iteration_completed*   (ADR-S-008 — iterate loop begins)
```

Every `spec_modified` event is traceable back to the signal that triggered it. This closes the homeostasis loop: the specification's evolution is an observable, auditable artifact.

### Spec evolution audit

Because `spec_modified` events carry content hashes, the spec's evolution can be verified at any time:

```
For each spec_modified event (ordered by timestamp):
    assert hash(file at new_hash checkpoint) == event.data.new_hash
```

If the file's current hash matches the most recent `spec_modified.new_hash` for that file, the spec is consistent with the event log. If not, the spec was modified outside the event-sourced path.

---

## Consequences

**Positive:**
- **Closed homeostasis loop.** The pipeline from signal → intent → proposal → human approval → spec change is now formally complete and observable.
- **Auditable spec.** Every spec modification has an event log entry. The reason a feature exists can be traced back to the signal that first identified it.
- **Draft visibility.** The Draft Features Queue surfaces what homeostasis wants to add, without modifying the spec autonomously.
- **Immutable history.** `feature_proposal` events are immutable facts. Even if a proposal is rejected, the fact that the system identified the gap remains in the log.

**Negative / Trade-offs:**
- **Two audit trails for manual edits.** Git commits and `spec_modified` events are parallel. For manual edits, only git commits are guaranteed; `spec_modified` events are advisory. Implementations that hook both provide the best experience.
- **Promotion atomicity.** If the spec write succeeds but the inflate fails, the workspace and spec are temporarily inconsistent. Recovery: `gen-spawn {feature_id}` recreates the workspace vector.
- **Schema maintenance.** Two new event types (`feature_proposal`, `feature_proposal_rejected`) extend the canonical event catalogue. All consumers of the event log must handle unknown event types gracefully (already required by the event-sourcing model).

---

## Alternatives Considered

**Place draft features in `.ai-workspace/` as a staging area**: A `features/draft/*.yml` subdirectory holds proposals before promotion. Rejected — this conflates spec (what features exist) with workspace state (operational trajectories). The draft is a PROPOSAL, not a feature. It has not entered the methodology at all. Keeping it in the event log preserves the "nothing touches the spec without human approval" invariant.

**Git-only audit trail for spec changes**: Rely on git commit history to track spec evolution. Rejected — git commits are not causally linked to the signals that triggered the change. The homeostatic loop needs a traceable chain from signal to spec modification, which git history alone cannot provide. Git is complementary; `spec_modified` events thread through the event log alongside implementation events.

**Single `spec_proposal` event (no separation of `feature_proposal` and `spec_modified`)**: Combine proposal and approval into one event. Rejected — the proposal and the modification are different facts at different times: the proposal is the agent's recommendation; the modification is the human's decision. Collapsing them loses the temporal gap (the draft queue) and the human approval step.

**Autonomous spec modification for low-risk changes**: Allow the homeostasis pipeline to write to spec directly for simple changes (e.g., minor requirement clarifications) without human gate. Rejected — ADR-S-008 Invariant 2 ("Draft-Only Autonomy") is a hard invariant, not a heuristic. Any autonomous spec modification, however small, changes what the entire system is building. The human gate is the boundary between the agent's recommendation and the system's specification.

---

## References

- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — the upstream pipeline; this ADR completes Stage 3 (Intent Generation) by defining what the generated intent produces
- [ADR-S-009](ADR-S-009-feature-vector-lifecycle-spec-vs-trajectory.md) — the inflate operation triggered by promotion
- [ADR-S-002](ADR-S-002-multi-tenancy-model.md) — the one-writer rule; this ADR defines the controlled pathway for homeostasis-generated spec changes
- [ADR-S-004](ADR-S-004-derivation-constraint.md) — downstream may not contradict upstream; `feature_proposal` events are downstream of sensing; `spec_modified` events are downstream of promotion
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §15 — REQ-EVOL-003 (`feature_proposal`), REQ-EVOL-004 (`spec_modified`), REQ-EVOL-005 (Draft Features Queue)
