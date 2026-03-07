# REQ-F-EVOL-001: Spec Evolution Pipeline — Implementation Requirements

<!-- Implements: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005 -->

**Feature**: REQ-F-EVOL-001
**Edge**: intent→requirements (iteration 1)
**Traces To**: INT-AISDLC-001
**Date**: 2026-03-07
**Phase**: 1 (REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-004) + 2 (REQ-EVOL-003, REQ-EVOL-005)
**Dependencies**: REQ-F-LIFE-001.|code⟩, REQ-F-ENGINE-001.|code⟩, REQ-F-TOOL-001.|code⟩

---

## Overview

The Spec Evolution Pipeline is the mechanism by which the AI SDLC methodology evolves its own specification. It is the closure of the homeostasis loop:

```
Running System → Telemetry → Observer (REQ-F-SENSE-001)
                                    ↓ intent_raised signal
                           Homeostasis Pipeline (REQ-F-LIFE-001)
                                    ↓ feature_proposal event
                           Spec Evolution Pipeline (REQ-F-EVOL-001)  ← this feature
                                    ↓ human approve
                           specification/ updated + workspace inflated
```

The pipeline has two separation-of-concerns boundaries:
1. **REQ-F-LIFE-001** emits signals (`intent_raised`, gap events) — the *sensing* tier
2. **REQ-F-EVOL-001** consumes those signals, stages proposals, gates human review, and promotes to spec — the *evolution* tier

The spec is the **source of truth for what the system should be**. Any change to the spec is an observable event with a causal chain. No silent mutations.

**Scope boundary**: This feature covers the evolution pipeline only. The sensing pipeline (how signals are detected) is REQ-F-LIFE-001 and REQ-F-SENSE-001.

---

## Terminology

| Term | Definition |
|------|-----------|
| **feature_proposal** | An event in the event log proposing that a new feature vector be added to the spec. Not a file — event-log-only until promoted. |
| **Draft Features Queue** | The computed set of `feature_proposal` events not yet promoted or rejected. Computed from event log. |
| **promote** | The act of moving a draft proposal from the event log into `specification/features/`, emitting `spec_modified`, and inflating the workspace trajectory. |
| **inflate** | Adding a new workspace feature vector file (`.ai-workspace/features/active/{id}.yml`) with all edges in pending state, derived from the standard profile. |
| **spec_modified** | An event emitted on any `specification/` change, recording the file, hashes, and causal chain. |
| **JOIN** | The display operation that merges `specification/features/` (spec layer) with `.ai-workspace/features/active/` (trajectory layer) to produce the complete feature view. |
| **PENDING** | Feature defined in spec but not yet in workspace (no trajectory started). |
| **ORPHAN** | Feature in workspace but not in spec (definition missing from canonical source). |
| **ACTIVE** | Feature present in both spec and workspace. |
| **causal chain** | The trail of event IDs linking: `intent_raised` → `feature_proposal` → `spec_modified`. Required for full auditability. |

---

## Functional Requirements

### REQ-EVOL-001: Workspace Vectors Are Trajectory-Only

**Priority**: High | **Phase**: 1 | **Type**: Functional

Workspace feature vector files (`.ai-workspace/features/active/*.yml`) shall contain trajectory state and reference fields only.

**Acceptance Criteria**:
1. Workspace YAML schema must NOT include `satisfies`, `success_criteria`, or dependency graph fields
2. Workspace YAML schema MUST include: `feature` (ID reference), `title` (display only), `vector_type`, `profile`, `status`, `trajectory`, `functor`, `time_box`, `parent_id`, `children`
3. Schema enforcement runs in `workspace_state.py` — violations raise `WorkspaceSchemaViolation` with the offending field name
4. Health check (`gen-status --health`) reports all workspace files that contain definition fields
5. The `spec_workspace_join.py` module enforces this boundary at read time — definition fields are read from spec, trajectory fields from workspace

**Traces To**: INT-AISDLC-001 (traceability, separation of concerns) | ADR-S-009

---

### REQ-EVOL-002: Feature Display Tools Must JOIN Spec and Workspace

**Priority**: High | **Phase**: 1 | **Type**: Functional

Any tool that displays feature vectors shall JOIN the spec definition layer with the workspace trajectory layer.

**Acceptance Criteria**:
1. `gen-status` and `gen-trace` compute three sets: ACTIVE (both), PENDING (spec only), ORPHAN (workspace only)
2. PENDING features must display: feature ID, title, satisfies list, phase — sourced from `specification/features/FEATURE_VECTORS.md`
3. ORPHAN features must be displayed as health warnings in `gen-status --health`, not silently omitted
4. JOIN failure (spec unreadable or missing) must surface as a named warning: `JOIN_FAILURE: spec layer unreadable` — never a silent empty list
5. Project progress display must show: `N/M features active` where M = total spec features count, N = active workspace count
6. `gen-status` default view must show all three categories (ACTIVE, PENDING, ORPHAN) even if some are empty

**Traces To**: INT-AISDLC-001 (developer observability) | ADR-S-009

---

### REQ-EVOL-003: `feature_proposal` Event Type

**Priority**: High | **Phase**: 2 | **Type**: Functional

The `feature_proposal` event type must be supported in the canonical event schema. It is emitted by the homeostasis pipeline when gap analysis produces a candidate new feature.

**Acceptance Criteria**:
1. Event schema (all fields mandatory unless noted):
   - `event_type: "feature_proposal"`
   - `proposal_id`: `PROP-{SEQ}` format, stable and unique
   - `proposed_feature_id`: the REQ-F-* key for the proposed feature
   - `proposed_title`: short human-readable title
   - `proposed_description`: 1-3 sentence description
   - `proposed_satisfies`: list of REQ-* keys the feature would cover
   - `trigger_intent_id`: INT-* causal link (may be null if origin is external signal)
   - `trigger_signal_id`: originating signal event ID
   - `source_stage`: which homeostasis stage emitted (e.g., "conscious_review")
   - `rationale`: free-text explanation of why this feature is warranted
   - `status: "draft"`
2. Event is emitted by the Conscious Review stage (ADR-S-008 Stage 3) only — not by reflex or affect stages
3. The event MUST NOT write to any file outside the event log at emission time
4. `proposal_id` is the join key for all subsequent `spec_modified` and `feature_proposal_rejected` events referencing this proposal
5. `ol_event.py` must include `feature_proposal` in its supported event taxonomy (REQ-EVENT-003)

**Traces To**: INT-AISDLC-001 (homeostasis, self-improvement) | ADR-S-010 | ADR-S-008

---

### REQ-EVOL-004: `spec_modified` Event Type with Causal Chain

**Priority**: High | **Phase**: 1 | **Type**: Functional

A `spec_modified` event must be emitted to the event log whenever `specification/` is modified.

**Acceptance Criteria**:
1. Event schema (all fields mandatory unless noted):
   - `event_type: "spec_modified"`
   - `file`: path relative to repo root (e.g., `specification/features/FEATURE_VECTORS.md`)
   - `what_changed`: human-readable summary (1-2 sentences)
   - `previous_hash`: `sha256:{hex}` of file content before change (null if new file)
   - `new_hash`: `sha256:{hex}` of file content after change
   - `trigger_event_id`: `PROP-{SEQ}` | `INT-{SEQ}` | `"manual"`
   - `trigger_type`: `"feature_proposal"` | `"intent_raised"` | `"manual"`
2. Event is emitted for ALL spec modifications: feature additions, requirement amendments, ADR updates, any file under `specification/`
3. `trigger_event_id: "manual"` with `trigger_type: "manual"` is used for direct author edits not driven by the pipeline
4. Implementations MUST support emission via `gen-spec-review` command; SHOULD support via git post-commit hook for manual edits
5. Content hash verification: `sha256(current_file_content) == most_recent_spec_modified.new_hash` confirms spec is in sync with event log
6. `ol_event.py` must include `spec_modified` in its supported event taxonomy

**Traces To**: INT-AISDLC-001 (audit trail, compliance) | ADR-S-010 | REQ-SUPV-003

---

### REQ-EVOL-005: Draft Features Queue in Observability

**Priority**: Medium | **Phase**: 2 | **Type**: Functional

The Draft Features Queue — unresolved `feature_proposal` events — must be surfaced in status and observability commands.

**Acceptance Criteria**:
1. `gen-status` computes the Draft Features Queue as: `feature_proposal` events where no subsequent `spec_modified` event references `trigger_event_id == proposal_id` AND no `feature_proposal_rejected` event references the same `proposal_id`
2. Queue entries display: proposal ID, proposed feature ID, title, triggering intent, rationale summary, age (days since emission)
3. Promotion (`gen-review approve {proposal_id}` or equivalent):
   - Appends the proposed feature to `specification/features/FEATURE_VECTORS.md`
   - Emits `spec_modified` with `trigger_event_id = proposal_id`
   - Creates `.ai-workspace/features/active/{proposed_feature_id}.yml` with all standard profile edges in `{status: pending}` state (inflate operation)
4. Rejection (`gen-review reject {proposal_id} --reason "{reason}"`): emits `feature_proposal_rejected` event with `proposal_id` and `reason` fields; removes entry from queue view
5. An empty Draft Features Queue is an observable positive signal — displayed as "No pending proposals" not as empty/absent

**Traces To**: INT-AISDLC-001 (homeostasis closure) | ADR-S-009 | ADR-S-010

---

## Non-Functional Requirements

### REQ-EVOL-NFR-001: Event Log Integrity

**Priority**: High | **Phase**: 1 | **Type**: Non-Functional

All Spec Evolution Pipeline operations must be atomic with respect to the event log.

**Acceptance Criteria**:
1. `spec_modified` event is emitted before (or in the same transaction as) any file write to `specification/`; never after
2. If `specification/` write fails, `spec_modified` event must NOT be emitted
3. Draft Features Queue computation is idempotent — replaying from the same event log always yields the same queue

**Traces To**: INT-AISDLC-001 | REQ-EVENT-001 (append-only stream)

---

### REQ-EVOL-NFR-002: Spec Hash Verification

**Priority**: Medium | **Phase**: 1 | **Type**: Non-Functional

The system must be able to verify that `specification/` files are consistent with the event log.

**Acceptance Criteria**:
1. `gen-status --health` computes: for each `spec_modified` event referencing a file, verify `sha256(current file) == event.new_hash`
2. Hash mismatches are surfaced as `SPEC_DRIFT` health warnings with the affected file and divergence summary
3. The verification is non-destructive — it reports; it does not modify

**Traces To**: INT-AISDLC-001 | REQ-SUPV-002 (Constraint Tolerances — spec is within bounds)

---

## Data Requirements

### REQ-EVOL-DATA-001: Workspace Vector Schema

**Priority**: High | **Phase**: 1 | **Type**: Data Quality

The workspace feature vector YAML schema must be formally defined and enforced.

**Acceptance Criteria**:
1. Allowed fields in `.ai-workspace/features/active/*.yml`:
   ```yaml
   feature:      # string — REQ-F-* key (required)
   title:        # string — display title (required, sourced from spec but cached here)
   vector_type:  # enum: feature | discovery | spike | poc | hotfix (required)
   profile:      # string — profile name (required)
   status:       # enum: pending | iterating | converged | blocked (required)
   priority:     # enum: critical | high | medium | low (optional)
   created:      # ISO 8601 (required)
   updated:      # ISO 8601 (required)
   parent_id:    # REQ-F-* key (optional)
   children:     # list of REQ-F-* keys (optional)
   trajectory:   # map of edge → {status, iteration, started_at, converged_at, ...} (required)
   functor:      # map of encoding overrides and escalation history (optional)
   time_box:     # {enabled, duration, started, expires} (optional)
   constraints:  # {acceptance_criteria, additional_checks, threshold_overrides} (optional)
   ```
2. Forbidden fields (cause `WorkspaceSchemaViolation`): `satisfies`, `success_criteria`, `dependencies`, `what_converges`, any field that duplicates spec definition content
3. Schema version is recorded in each file as `schema_version: "1.0"` to support future migrations

**Traces To**: INT-AISDLC-001 | REQ-EVOL-001

---

## Business Rules

### REQ-EVOL-BR-001: Spec Is Authoritative

**Priority**: Critical | **Phase**: 1 | **Type**: Business Rule

`specification/` is the authoritative definition of what the system must do. Workspace files are derived trajectory state. This boundary must never be crossed.

**Acceptance Criteria**:
1. No tool or command may write feature definitions (satisfies lists, success criteria) to workspace files
2. No tool or command may read requirements from workspace files — requirements are always read from `specification/`
3. If the spec and workspace conflict (e.g., feature in workspace but removed from spec), the spec wins — workspace entry is flagged ORPHAN

**Traces To**: INT-AISDLC-001 | ADR-S-002 (`.ai-workspace/` is not specification)

---

### REQ-EVOL-BR-002: Human Gate on Spec Promotion

**Priority**: Critical | **Phase**: 2 | **Type**: Business Rule

No `feature_proposal` may be promoted to the spec without explicit human approval. The pipeline may generate proposals autonomously; it may never promote them autonomously.

**Acceptance Criteria**:
1. The promotion command requires an explicit human invocation — no automatic promotion
2. Human approval is recorded as an `F_H` evaluator event in the event log before `spec_modified` is emitted
3. The pipeline may accumulate proposals in the draft queue indefinitely — there is no TTL forcing automatic promotion or rejection

**Traces To**: INT-AISDLC-001 | REQ-EVAL-003 (Human Accountability) | REQ-SENSE-005 (Review Boundary)

---

## Success Criteria

| Criterion | Measure | Linked REQ |
|-----------|---------|-----------|
| Workspace files contain no spec-definition fields | 0 schema violations in health check | REQ-EVOL-001 |
| `gen-status` shows complete feature scope | M = total spec features displayed (not just active) | REQ-EVOL-002 |
| All spec modifications recorded | `sha256(spec_file) == spec_modified.new_hash` for all tracked files | REQ-EVOL-004 |
| Draft queue computable from events alone | Replay from events.jsonl → same queue as live | REQ-EVOL-003, REQ-EVOL-005 |
| No autonomous spec promotion | All `spec_modified` events have `trigger_type` traceable to human action | REQ-EVOL-BR-002 |

---

## Assumptions and Dependencies

**Assumptions**:
- REQ-F-LIFE-001 is converged at code edge before EVOL-001 implementation begins (it emits the `intent_raised` signals consumed here)
- REQ-F-ENGINE-001 event log infrastructure (append-only JSONL) is available
- REQ-F-TOOL-001 gen-status and gen-review commands exist and are extendable
- The `specification/features/FEATURE_VECTORS.md` format is stable enough to parse programmatically (FEATURE_VECTORS.md is markdown with structured section headers)

**Dependencies**:
- `workspace_state.py` — schema enforcement (REQ-EVOL-001)
- `feature_view.py` / `spec_workspace_join.py` — JOIN display (REQ-EVOL-002)
- `ol_event.py` — event taxonomy for `feature_proposal` and `spec_modified` (REQ-EVOL-003, REQ-EVOL-004)
- `gen-status.md` command — Draft Features Queue display (REQ-EVOL-005)
- `gen-review.md` command — proposal approval/rejection (REQ-EVOL-005)

**Explicit Out of Scope**:
- Automated generation of `feature_proposal` events (that is REQ-F-LIFE-001 and REQ-F-SENSE-001)
- Multi-tenant proposal coordination (that is REQ-F-COORD-001)
- Version history or branching of the spec (event log provides lineage; no git branching strategy in scope)

---

## Domain Model

```mermaid
graph TD
    IL[events.jsonl\nappend-only] -->|feature_proposal events| DQ[Draft Features Queue\ncomputed projection]
    IL -->|spec_modified events| SH[Spec Hash Registry\ncomputed projection]

    DQ -->|human: gen-review approve| PROM[Promote]
    DQ -->|human: gen-review reject| REJ[feature_proposal_rejected\nevent]

    PROM -->|appends to| SPEC[specification/features/\nFEATURE_VECTORS.md]
    PROM -->|emits| SM[spec_modified event\ncausal chain preserved]
    PROM -->|inflates| WS[.ai-workspace/features/active/\n{id}.yml trajectory-only]

    SM -->|appended to| IL
    REJ -->|appended to| IL

    SPEC -->|JOIN| JOIN[Feature Display\nACTIVE / PENDING / ORPHAN]
    WS -->|JOIN| JOIN
```

---

## Phase Implementation Plan

### Phase 1 (implements REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-004)

These three are inter-dependent — workspace schema enforcement, JOIN display, and spec event recording form a closed triangle:

1. **workspace_state.py**: Add `WorkspaceSchemaViolation` — validate YAML on read; enforce forbidden fields
2. **spec_workspace_join.py**: Implement JOIN query; surface PENDING and ORPHAN in gen-status
3. **ol_event.py**: Add `spec_modified` to taxonomy; implement emit function with hash fields
4. **gen-spec-review command** (exists): Wire to emit `spec_modified` on every invocation that modifies spec
5. **gen-status --health**: Add spec hash verification against event log

### Phase 2 (implements REQ-EVOL-003, REQ-EVOL-005 — depends on REQ-F-LIFE-001 convergence)

1. **ol_event.py**: Add `feature_proposal` to taxonomy
2. **workspace_state.py**: Add `compute_draft_queue()` — query event log for unresolved proposals
3. **gen-status**: Add Draft Features Queue section to default view
4. **gen-review command**: Add `approve {proposal_id}` and `reject {proposal_id}` subcommands
5. **inflate operation**: Create workspace trajectory file from standard profile skeleton on approval
