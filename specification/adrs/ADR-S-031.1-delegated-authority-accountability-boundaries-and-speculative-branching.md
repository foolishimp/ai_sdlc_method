# ADR-S-031.1: Delegated Authority, Accountability Boundaries, and Speculative Branching

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted — 2026-03-09
**Scope**: Specification-level — extends ADR-S-031 (Supervisor Pattern, Event Sourcing, and Choreographed Saga)
**Extends**: ADR-S-031
**Cross-references**: ADR-S-015 §Decision table, ADR-S-030.1 (immutable lineage)
**Revised**: 2026-03-09 — four findings from Codex review addressed (accountability boundary predicate, Decision 2 completeness, Decision 7 over-specification, CONSENSUS/compensation miscategorisation)

---

## Context

The vocabulary inherited from mutable workflow systems conflates three distinct operations under a single term — "rollback":

| Situation | What actually happens | What people say |
|-----------|----------------------|-----------------|
| Agent crashes mid-iteration | Return to the last committed state; no history is erased | "rollback" |
| CONSENSUS saga fails (quorum not reached) | Terminal failure resolution with typed recovery paths | "rollback" |
| Feature vector abandoned mid-trajectory | Head moves to prior anchor; abandoned branch retained in lineage | "rollback" |

These are not the same operation. They have different recovery models, different observability requirements, and different implications for what the accountability record looks like afterward.

**The motivating case**: payment dispatch. An autonomous relay is executing a payment saga under delegated authority:

1. Before payment dispatch: the relay has run sub-steps (validation, fee calculation, routing selection) but has not yet committed external effects. If anything fails here, recovery is simply returning to the last accountable state — no external effects have propagated.

2. At payment dispatch: the external API call crosses an irreversibility boundary. Once the payment is confirmed by the external system, the relay cannot undo it by replaying earlier events.

3. After payment confirmation: if subsequent steps fail (notification, ledger update), recovery is compensation — forward moves that describe the partial state and prescribe how to restore balance. "Rollback" is not available.

Three distinct situations; three distinct recovery models. The current vocabulary collapses all three, which produces implementations that over-apply or misapply recovery semantics.

This ADR is a child amendment to ADR-S-031. It does not introduce a new saga ownership domain — it extends the supervisory vocabulary for how F_H can cede bounded authority, where speculative branches are legal, and when recovery is re-anchoring versus compensation.

---

## Why This Belongs Under ADR-S-031

ADR-S-031 already owns: supervisor, observer, relay, saga, and compensating events. The new clarification is about how authority is delegated within that supervisory saga. The central question is supervisory: who may proceed autonomously, up to which boundary, and what kind of recovery is possible after that boundary?

This does not belong under:
- **ADR-S-029** (compiled dispatch intermediate) — dispatch compilation is not the issue; authority boundaries are.
- **ADR-S-030.1** (immutable lineage and vector typing) — lineage immutability is a constraint here, not the rule being added.
- **ADR-S-015** (unit-of-work transaction model) — transaction commit semantics are relevant at edge scope; the rule being added is larger than one edge-local unit of work.

---

## Definitions

Six terms, each normative. These replace "rollback" in any context where the operation is a saga-scope or external-commit recovery.

### `delegated authority`

Bounded operational authority ceded by F_H to a relay or saga, allowing autonomous progression within a mandate without requiring live F_H approval at each step.

**Relationship to `mandate`**: A mandate (issued via `emit(intent_raised)` per ADR-S-031 §Minimum Operators) is the mechanism by which authority is delegated. Issuing a mandate *is* granting delegated authority to the relay. They are not synonyms — a mandate is the instruction (the event); delegated authority is the permission envelope the mandate conveys. The mandate is the vehicle; delegated authority is the scope of what the relay may do while fulfilling it.

F_H retains accountability throughout. Delegated authority does not transfer accountability — it licenses execution within pre-agreed bounds while F_H remains the accountable principal.

### `accountability boundary`

The most recent event in the log that represents a state the human principal has positively ratified — explicitly or by non-objection — within the current causal scope, and which has not been causally superseded.

**Machine-checkable definition**: The most recent event of one of the following types, scoped to the current causation/correlation chain (same `run_id`, `review_id`, or feature+edge session key):

- `COMPLETE` (ADR-S-015) — committed edge traversal
- `edge_converged` — stable asset produced
- `consensus_reached` — governance saga ratified (valid boundary at review edges)

Such an event constitutes the accountability boundary unless it has been **causally superseded** by a later event that explicitly contests, reopens, or replaces it within the same causal scope. Causal supersession requires one of:

- An `intent_raised` event that references this specific event as contested (via `prior_event_ref` or equivalent causation field)
- A `consensus_requested` event that explicitly reopens a prior ratified state (e.g., `prior_review_id` field)
- A child-authoritative branch selection that designates a different branch as the new active head

A later `intent_raised` for unrelated new work in the same session does **not** supersede a prior accountability boundary. The predicate is causal, not temporal. New work coexisting with a ratified state does not retroactively un-ratify it.

Implementations find the accountability boundary by reading `events.jsonl` filtered to the current causal scope, walking in reverse, and returning the first event matching the above types that has not been causally superseded.

### `irreversibility boundary`

A point in a saga after which external effects have been committed to systems outside the event log's authority domain and cannot be undone by replaying, re-anchoring, or editing events.

**Scope — external effects only**: Irreversibility applies to external effects exclusively: payments, emails, API calls to systems outside the event log's authority, regulatory filings, user-visible notifications, and any action whose effects propagate beyond the accountability domain.

Internal effects — file writes, event log entries, feature vector updates, local state — are **not** irreversibility boundaries regardless of their size or importance, because they are all within the event log's authority and can be re-anchored. Writing a 50,000-line codebase is not an irreversibility boundary. Sending an email confirming deployment is.

This scope constraint must be explicit in all implementations. An implementation that treats writing a file as crossing an irreversibility boundary is over-applying this concept.

### `speculative branch`

A predictive branch explored under delegated authority before an irreversibility boundary has been crossed.

A speculative branch is legal whenever: (1) the relay holds delegated authority for the saga, and (2) no irreversibility boundary has been crossed. Before an irreversibility boundary, all effects are internal — they can be abandoned without external consequence. Speculative branching is how the system makes progress on multi-path problems without requiring F_H presence at each decision point.

### `abandoned branch`

A retained but non-authoritative branch that is no longer the active path.

An abandoned branch is operationally inactive — it is not being continued, and the system's active head has moved elsewhere. It is historically present — the event log retains it, the lineage is immutable, the branch can be inspected or resumed. Abandonment is a change in which branch is authoritative, not a deletion of the branch from history.

This is consistent with ADR-S-030.1: "branches are never deleted; the system changes which branch is authoritative."

### `compensation`

Forward recovery after an external or otherwise irreversible commitment has been made.

Compensation is not undoing. The payment was sent; compensation is recording that the payment was sent, describing the partial state, and prescribing what forward moves restore the system to a consistent state (refund request, ledger correction, notification). Compensation always moves forward — it never pretends a committed external effect did not happen.

Compensation applies only after an irreversibility boundary has been crossed. Before that boundary, recovery is re-anchoring (Decision 5), not compensation. A saga that fails before any external commitment does not require compensation — it requires re-anchoring or typed terminal failure resolution.

Compare: re-anchoring is possible before an irreversibility boundary; compensation is required only after.

---

## Normative Decisions

### Decision 1 — F_H delegates without ceding accountability

F_H may delegate bounded operational authority to a relay or saga without ceding accountability. F_H remains the accountable principal throughout. The relay is authorized to execute, not to be accountable.

Implementations must not treat mandate acceptance as accountability transfer.

### Decision 2 — Relays continue until a declared boundary condition

Autonomous relays operate within delegated authority until they encounter a declared boundary condition. The complete set of boundary condition classes is:

1. **Terminal completion** — the mandate is fulfilled; the relay has reached its declared done-done state. Terminal completion is itself a boundary condition; the relay stops because the work is finished, not because it hit a constraint.
2. **Irreversibility boundary** — an external commit is about to occur (as defined above). The relay must check whether it holds standing policy authority before proceeding.
3. **Policy-sensitive boundary declared in Context[]** — a class of actions flagged in the standing context as requiring live F_H approval. Context[] is the authoritative source; see Decision 7.
4. **Graph/edge/composition-declared live-approval boundary** — some approval gates are intrinsic to the workflow shape: an edge or dispatched composition declares that a specific step requires live F_H approval regardless of context policy. These boundaries are declared in the graph topology or composition spec, not in project policy.
5. **Implementation-local event trigger** — a tenant-specific event pattern that the relay's configuration registers as a pause/escalation trigger.

Implementations must ensure every relay has at least one applicable boundary condition from this set. A relay that proceeds indefinitely without encountering any of these conditions violates this decision.

**Example**: A payment relay operating under delegated authority continues autonomously through validation, routing selection, and fee calculation (no boundary conditions triggered). The irreversibility boundary condition fires at the external payment API call. The relay checks Context[] for standing policy authority covering this payment class and amount. If found: proceeds and records the policy reference. If not: pauses and emits `intent_raised` requesting live approval.

### Decision 3 — Speculative branching is allowed before an irreversibility boundary

Before an irreversibility boundary has been crossed, speculative branches are permitted. A relay with delegated authority may explore multiple paths, evaluate alternatives, and select a branch — all without external consequence.

Implementations must not treat speculative branching as an irreversibility event. Internal file writes, draft artifacts, and provisional event log entries are not irreversibility events.

### Decision 4 — Abandoned branches are retained in immutable lineage

Unselected or failed speculative branches are abandoned operationally but retained historically. The event log is immutable; abandoned branches remain in the lineage record.

Implementations must not delete events from abandoned branches. The system changes which branch is authoritative — it does not rewrite history.

### Decision 5 — Recovery before irreversible commitment is re-anchoring, not history rewrite

When a relay or saga fails before an irreversibility boundary has been crossed, recovery is **re-anchoring to the last accountability boundary**. The relay returns to the most recent event constituting the accountability boundary (as defined above), treats it as the operative ground state, and may proceed from there.

Re-anchoring is not history rewrite. The failed attempt remains in the event log. The system's active head moves back to the accountability boundary; the failed branch becomes an abandoned branch (retained, non-authoritative).

The term "rollback" must not be used for this operation in any Genesis implementation. Use **re-anchor**.

### Decision 6 — Recovery after irreversible commitment is compensation, never rollback

When external effects have been committed (an irreversibility boundary has been crossed), recovery is **compensation** — a forward move that describes the partial state and prescribes how to restore consistency. Compensation never pretends the committed external effect did not happen.

The term "rollback" must not be used for this operation. Use **compensate** or **compensation path**.

### Decision 7 — Non-compensable or policy-sensitive external boundaries require F_H approval or standing delegated policy authority

Actions that cross a non-compensable boundary or a policy-sensitive boundary require one of:

1. **Live F_H approval**: `intent_raised` event emitted, relay pauses, F_H issues `vote_cast` or equivalent approval event, relay resumes.
2. **Standing delegated policy authority**: F_H has pre-approved this class of action. Standing policy authority must satisfy three invariants:
   - It lives in Context[] — the relay's standing context at the time of execution, not a side channel
   - It is auditable — the policy source and version are identifiable from Context[]
   - The emitted event references the specific policy basis used, so the authorization is traceable in the event log

Tenant implementations bind this to a concrete mechanism: `project_constraints.yml` policy block, a signed policy event, an external policy service, or other. That binding is a tenant-level decision documented in the implementation's own ADRs. The spec invariants above (in Context[], auditable, referenced in emitted event) apply to all bindings.

---

## The Vocabulary Replacement

Across all Genesis implementations, the following replacements apply at saga scope:

| Situation | Prohibited term | Correct term |
|-----------|----------------|-------------|
| Agent crashes mid-iteration; returning to last committed state | "rollback" | **re-anchor** to the last accountability boundary |
| CONSENSUS saga fails; quorum not reached | "rollback" | **terminal failure resolution** — typed outcome, recovery paths available |
| External commitment made; subsequent steps fail | "rollback" | **compensation** — forward recovery after irreversibility boundary |
| Feature vector abandoned mid-trajectory | "rollback" | **branch abandonment** — lineage retained, head moves |

"Rollback" remains acceptable vocabulary within ADR-S-015's edge-local transaction scope (`FAIL` / `ABORT` events at a single `iterate()` invocation). That is the intended scope of the term. At saga scope — multi-step, multi-relay workflows — the terms above apply.

**Note on CONSENSUS**: `consensus_failed` is a typed terminal failure resolution event, not a compensation event. It occurs before any irreversibility boundary in the normal governance saga. The recovery paths available after `consensus_failed` (re_open, narrow_scope, abandon — per ADR-S-025) are forward moves in a governance saga, not compensation for an external commit. Compensation applies only where an irreversibility boundary has been crossed. See ADR-S-025 for the full CONSENSUS recovery model.

---

## Cross-Reference: ADR-S-015

ADR-S-015 §Decision table currently reads:

```
| Rollback | FAIL or ABORT | Execution failed; prior state is authoritative |
```

That row remains correct for edge-local scope. The following note is added after the decision table:

> At saga scope, the term "rollback" is not used. Recovery before an irreversibility boundary is **re-anchoring** to the last accountability boundary. Recovery after an external commitment is **compensation**. Saga terminal failures (such as `consensus_failed`) are typed terminal failure resolutions, not rollbacks. Abandoned speculative branches are retained in immutable lineage — the event log is never rewritten. See ADR-S-031.1.

---

## Cross-Reference: ADR-S-030.1

ADR-S-030.1 establishes that branches are never deleted from immutable lineage. This ADR is additive and consistent with that decision. "Abandoned branch" is defined here as the operational state of a branch that ADR-S-030.1 guarantees is historically retained.

---

## Payment Dispatch Example

The motivating example walked through using the new vocabulary.

**Context**: A payment relay operates under delegated authority issued by F_H via `intent_raised {mandate: process_payment, scope: {max_amount: 10000, currency: USD}}`.

**Before payment dispatch (speculative branch territory)**:
- Relay validates payment details — internal check, no external effects
- Relay queries two routing providers for best rate — read-only external calls (no commit)
- Relay selects Provider B — branch decision, two speculative branches existed, one is now abandoned (retained in log, non-authoritative)
- Relay calculates final fee — internal computation

At this point: everything is re-anchorable. If the relay crashes, recovery re-anchors to the last `COMPLETE` event for this edge within this causal scope. No compensation needed.

**At payment dispatch (irreversibility boundary)**:
- Relay checks Context[] for standing delegated policy authority: payment class `standard`, amount within pre-approved scope, policy reference recorded
- Relay calls external payment API — this crosses the irreversibility boundary
- External system confirms: `payment_id: PAY-20260309-001`
- Relay emits `COMPLETE` event with `payment_id` and policy reference in facet data

**After payment confirmation (compensation territory)**:
- Relay attempts ledger update — internal
- Ledger service returns 503 (unavailable)
- Relay cannot "undo" the payment. Re-anchoring is not available — the payment is committed externally.
- Relay emits `compensation_triggered {cause: ledger_unavailable, committed_effect: PAY-20260309-001, compensation_path: retry_ledger_then_manual_reconcile}`
- Compensation relay takes over: retries ledger, and if still failing, emits `intent_raised` for human manual reconciliation

The three phases use three distinct vocabulary sets. No "rollback" appears at any point.

---

## Relationship to Other ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-S-031 | Parent — this ADR extends the supervisory vocabulary defined there |
| ADR-S-015 | Cross-reference — adds note after §Decision table; does not modify the table |
| ADR-S-030.1 | Consistent — "abandoned branch" aligns with immutable lineage; no conflict |
| ADR-S-025 (CONSENSUS Functor) | `consensus_failed` is typed terminal failure resolution, not compensation — CONSENSUS sagas typically complete before any irreversibility boundary |
| ADR-S-012 (Event Stream as Formal Model) | Immutability of the event log is a prerequisite for re-anchoring and branch abandonment semantics |
