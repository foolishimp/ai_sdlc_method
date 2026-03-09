# CONSENSUS Observer Design - imp_codex

**Date**: 2026-03-09
**Status**: Design-tier package
**Feature**: REQ-F-CONSENSUS-001
**Design parents**: ADR-CG-010, ADR-S-025, ADR-S-029, ADR-S-030.1

---

## Purpose

This document defines the Codex-tenant package for building the first executable `CONSENSUS` supervisory saga. It is intentionally tenant-local: the shared spec provides the quorum semantics, while this document binds those semantics to Codex runtime events, projections, triggers, and delivery slices.

The objective is not "generic event-driven everything." The objective is one concrete observer loop that can be implemented and proven end-to-end:

`consensus_requested -> comments/votes -> quorum projection -> consensus outcome -> artifact writeback`

---

## Scope

This package covers:

- review-cycle event vocabulary,
- replay-derived state and quorum projection,
- observer trigger payloads,
- reviewer and instigator loop boundaries,
- idempotency and stale-trigger protection,
- monitor-facing projections.

This package does not yet cover:

- weighted voting,
- agent roster members as formal voters,
- generalized CI/CD or telemetry observers,
- a cross-tenant session protocol.

---

## Binding Decisions

### 1. No mutable review-state file

Codex will not create a separate session YAML for CONSENSUS review state. The event log is the canonical source of truth.

### 2. Review state is keyed by review cycle

`review_id` identifies the long-lived review thread.

`cycle_id` identifies the currently open voting window for a specific published asset version. A material change creates a new cycle.

### 3. Spec-level semantics stay intact

The tenant binding must preserve ADR-S-025 rules:

- gating comments are frozen by close time,
- late comments are non-gating unless a human re-opens,
- participation and quorum are deterministic,
- material change invalidates votes and starts a new cycle,
- failure outcomes remain typed (`consensus_failed`, not just "not converged").

### 4. Immutable lineage remains the repair model

If a CONSENSUS cycle results in a spec-changing repair or a gap-driven follow-up against a converged feature, the resulting work must use the tenant's accepted intent-vector envelope and child-lineage rules. The observer package does not reopen converged vectors in place.

### 5. No central review orchestrator

The tenant must follow ADR-S-031's "orchestrator smell" rule. `CONSENSUS` is a choreographed saga, not a central controller that imperatively sequences participants.

The implementation target is:

- observer watches `consensus_requested` and review-cycle events,
- reviewer relay responds if it has a mandate and has not already answered,
- quorum observer reacts to `vote_cast`,
- closeout relay acts only after terminal quorum projection.

If implementation code starts to look like "call A, then B, then check C," the missing invariant must be identified before more orchestration logic is added.

---

## Components

### Projection engine

Pure replay functions over `.ai-workspace/events/events.jsonl`.

Responsibilities:

- find the current cycle for a review,
- partition gating vs late comments,
- calculate valid votes for the active cycle,
- determine whether the cycle is open, deferred, passed, or failed.

### Consensus observer

The observer watches review events and emits normalized review mandates and rechecks. It does not decide quorum by itself. It only packages trigger context and requests replay.

### Reviewer relay

The reviewer relay is the agent-facing or human-facing fulfillment branch that:

- rehydrates review state,
- reads the current artifact and relevant thread state,
- emits `comment_received` and optionally `vote_cast`,
- exits without attempting final convergence.

### Closeout observer and relay

The closeout observer watches cycle events and asks the closeout relay to act only when deterministic quorum projection is terminal. The closeout relay is the only branch allowed to emit:

- `consensus_reached`
- `consensus_failed`
- the resulting artifact writeback event sequence

The closeout relay must rerun deterministic quorum projection before writing anything.

### Monitor projection

The monitor should consume the same replay logic to show:

- open reviews,
- current cycle ID,
- gating comments remaining,
- vote/participation state,
- terminal review outcomes.

---

## Event Vocabulary

### `consensus_requested`

Starts a review cycle.

Required payload fields:

- `review_id`
- `cycle_id`
- `asset_id`
- `asset_version`
- `artifact`
- `requested_by`
- `published_at`
- `review_closes_at`
- `min_duration`
- `participants`
- `quorum`

### `comment_received`

Records a participant comment.

Required payload fields:

- `review_id`
- `cycle_id`
- `comment_id`
- `participant`
- `timestamp`
- `asset_version`
- `content_ref`

Derived, not authoritative:

- `gating`

`gating` should be computed from `timestamp <= review_closes_at`, not trusted if written redundantly.

### `comment_dispositioned`

Records how a gating comment was handled.

Required payload fields:

- `review_id`
- `cycle_id`
- `comment_id`
- `disposition`
- `disposition_rationale`
- `material_change`
- `resulting_asset_version`

If `material_change = true`, the next required event is `review_reopened` with a new cycle ID.

### `vote_cast`

Records a participant vote for the current cycle.

Required payload fields:

- `review_id`
- `cycle_id`
- `participant`
- `timestamp`
- `asset_version`
- `verdict`
- `rationale`
- `conditions`

### `review_reopened`

Begins a new cycle after a material change or explicit human reopen.

Required payload fields:

- `review_id`
- `prior_cycle_id`
- `cycle_id`
- `reason`
- `asset_version`
- `reopened_by`
- `review_closes_at`
- `min_duration`

### `consensus_reached`

Terminal positive review outcome.

Required payload fields:

- `review_id`
- `cycle_id`
- `asset_id`
- `asset_version`
- `approve_votes`
- `reject_votes`
- `abstain_votes`
- `non_response_count`
- `approve_ratio`
- `participation_ratio`

### `consensus_failed`

Terminal negative review outcome.

Required payload fields:

- `review_id`
- `cycle_id`
- `asset_id`
- `asset_version`
- `failure_reason`
- `approve_votes`
- `reject_votes`
- `abstain_votes`
- `non_response_count`
- `approve_ratio`
- `participation_ratio`
- `available_paths`

---

## Projection Contract

The first implementation slice should expose these pure functions in runtime:

### `current_cycle(review_id)`

Returns the most recent open cycle for the review. If the last event is terminal (`consensus_reached` or `consensus_failed`) and there is no reopen, the cycle is closed.

### `session_state(review_id, cycle_id)`

Returns the ordered event set for that cycle only. This is the local equivalent of the "session" without storing session state separately.

### `gating_comments(review_id, cycle_id)`

Returns comments whose timestamps are at or before `review_closes_at` of the current cycle.

### `late_comments(review_id, cycle_id)`

Returns comments after close. These are contextual only unless a human re-opens.

### `disposition_state(review_id, cycle_id)`

Returns:

- total gating comments,
- dispositioned gating comments,
- undispositioned comment IDs.

### `vote_snapshot(review_id, cycle_id)`

Returns one effective vote per participant for the current cycle, preserving ADR-S-025 semantics:

- abstention is distinct from non-response,
- only current-cycle votes count,
- prior-cycle votes do not carry through a material reset.

### `quorum_state(review_id, cycle_id, now)`

Returns one of:

- `deferred` when the review window is still open or `min_duration` has not elapsed,
- `passed` when all deterministic criteria are met,
- `failed` when the window is closed and the criteria fail.

The projection output must include the same counters needed for `consensus_reached` and `consensus_failed`.

---

## Local Invariants

These invariants are the local replacements for imperative coordination:

1. A reviewer relay only acts on an open review cycle it has not already answered.
2. Quorum is recalculated whenever `vote_cast` or `comment_dispositioned` arrives for the current cycle.
3. Closeout only occurs from replay-derived terminal state, never from trigger context alone.
4. A reopened cycle invalidates prior-cycle votes by projection, not by destructive mutation.
5. The closeout relay must be idempotent for `(review_id, cycle_id, terminal_outcome)`.

---

## Observer Trigger Contract

The observer must normalize all invocations to:

```json
{
  "observer_id": "consensus_observer",
  "trigger_reason": "comment_received",
  "review_id": "REVIEW-ADR-S-029",
  "cycle_id": "CYCLE-001",
  "artifact": "specification/adrs/ADR-S-029-the-dispatch-contract.md",
  "source_run_id": "01H...",
  "source_event_type": "comment_received"
}
```

Allowed `trigger_reason` values for v1:

- `consensus_requested`
- `comment_received`
- `comment_dispositioned`
- `vote_cast`
- `review_window_elapsed`
- `review_reopened`
- `manual_recheck`

The trigger is advisory only. The invoked observer or relay must always rehydrate from events before acting.

---

## Idempotency and Safety

### Replay before write

Every loop must recompute current state before appending review events or writing artifacts.

### Duplicate suppression

For the same `(review_id, cycle_id, source_run_id, trigger_reason)` tuple, the observer must behave idempotently. If an equivalent terminal outcome already exists, it must exit without rewriting it.

### Stale-cycle rejection

If the trigger references a non-current `cycle_id`, the loop exits without mutation unless it is explicitly handling replay or audit.

### Asset-version check

Votes and dispositions must refer to the cycle's current asset version. If a material change has already advanced the cycle, late writes against the prior cycle are rejected.

### No direct terminal emit from reviewer relay

Reviewer relays may append `comment_received` and `vote_cast`. They must not emit `consensus_reached` or `consensus_failed`.

### No mutation on malformed trigger

Malformed or partial triggers are treated as no-ops with optional debug telemetry. They do not open fallback review state.

---

## Delivery Slices

### Slice 1: Pure projection package

Add replay functions and deterministic quorum math. No hooks, no file watchers, no agent automation.

Target runtime surfaces:

- `runtime/consensus.py`
- projection tests
- one fixture-driven review-cycle replay suite

### Slice 2: Event emitters and CLI entry points

Add explicit runtime commands for:

- request consensus
- record comment
- record disposition
- cast vote
- project review state

This makes the package testable without any live observer process.

### Slice 3: Observer trigger adapter

Add a normalized trigger path from comment/file/event deltas into the projection package. The adapter should be replaceable by hooks or external automation.

### Slice 4: End-to-end artifact writeback

Enable the closeout relay to write the next artifact only after replay confirms terminal outcome.

---

## Monitor Requirements

The monitor-facing view should include:

- `review_id`
- `cycle_id`
- `artifact`
- `asset_version`
- `state` (`open`, `deferred`, `passed`, `failed`)
- participation counts
- gating comment counts
- latest trigger reason
- terminal outcome if present

This is enough for observability without exposing every internal event row.

---

## Open Tenant Questions

1. Should `comment_dispositioned` be its own event or a specialized `review_updated` event family?
2. Should non-material asset-version changes be explicitly emitted, or only implied through disposition payloads?
3. Do we want an explicit `review_closed` optimization event for monitor latency, even though close is derivable?

These are tenant implementation questions, not blockers for Slice 1.
