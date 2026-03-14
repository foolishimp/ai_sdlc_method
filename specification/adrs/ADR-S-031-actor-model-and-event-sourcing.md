# ADR-S-031: Supervisor Pattern, Event Sourcing, and Choreographed Saga

**Status**: Accepted — 2026-03-09
**Revised**: 2026-03-14 (adds delegated authority, accountability boundaries, speculative branching, and compensation vocabulary; 2026-03-14b: tightens F_P relay role — F_P constructs artifacts/payloads, event logger is the F_D write boundary)
**Scope**: Specification-level — applies to all Genesis implementations

---

## Why This Pattern Exists: Imperfect Autonomy

The supervisor pattern exists in human organisations for one reason: workers are imperfectly autonomous. They need a clear mandate, progress checks, and a path when stuck. A perfect worker — one that always understands the brief, always delivers correct output on the first attempt, and never gets stuck — needs no supervisor.

F_P (LLM agents) and F_H (humans) are imperfectly autonomous:
- They may misunderstand the mandate
- They may produce output that is directionally correct but incomplete
- They may get stuck and not know it
- They may be unavailable
- They may produce subtly wrong output that passes casual inspection but fails formal evaluation

The **supervisor** in this system exists for exactly the same reason a project manager, scrum master, or team lead exists: to issue clear mandates, observe progress, check completion against defined criteria, and route when stuck. Not to do the work. Not to micromanage. To close the accountability loop.

This is not the Erlang or Scala actor model. Those actors address concurrency — how to safely share computation across threads and nodes. This system addresses **accountability under imperfect autonomy** — how to ensure work actually reaches "done done" when the workers executing it are unreliable.

---

## Done Done

"Done" means output was produced. "Done done" means the output passes formal evaluation against the spec.

```
done      = F_P produced a candidate
done done = F_D(candidate, spec) → delta == 0
```

The distinction matters because F_P frequently produces output that is done but not done done. The supervisor's primary function is to close this gap — to hold the mandate open until done done is reached or a human judgment is required.

The formal system expression (bootloader §V):
```
stable(candidate) = ∀ evaluator ∈ evaluators(edge): evaluator.delta(candidate, spec) < ε
```

`stable == true` is done done. Until then, the supervisor re-mandates.

---

## The Supervisor Loop

The iterate function *is* the supervisor pattern:

```
supervisor issues mandate    →  intent event (clear acceptance criteria, context, edge)
worker attempts              →  F_P produces candidate
supervisor checks done done  →  F_D evaluates delta
  delta == 0: accept         →  edge_converged event
  delta > 0:  re-mandate     →  intent_raised (specific gap, not vague retry)
  stuck:      escalate        →  F_H required (judgment, not more attempts)
```

The supervisor does not do the work. It holds the mandate, observes the result, and applies the acceptance criteria. When a worker is stuck — delta unchanged across N iterations — the supervisor escalates rather than continuing to re-mandate. More attempts at a stuck delta are waste.

The escalation chain maps to evaluator types:

| State | Supervisor action | Evaluator |
|-------|-----------------|-----------|
| Work can be defined deterministically | Issue mandate with F_D acceptance criteria | F_D checks done done |
| Work requires construction | Assign to agent with intent vector | F_P attempts, F_D evaluates |
| Agent stuck or judgment needed | Escalate to human | F_H decides |
| Human decides | Deterministic deployment | F_D confirms, η: F_H → F_D |

---

## The Event Log as Accountability Record

Because workers are imperfectly autonomous, the supervisor needs a durable accountability record — not just a result, but evidence of what was attempted, what was evaluated, and what the current delta is.

The event log is that record. Every mandate issued, every attempt made, every evaluation run, every escalation — all immutable, ordered, replayable.

This is why the event log replaces direct invocation. If the supervisor called the worker directly and the worker failed, the mandate is lost. If the supervisor emits an intent event and the worker reacts, the mandate persists regardless of what the worker does. A failed worker, a restarted worker, a substituted worker — the mandate survives because it is in the log.

**Self-healing**: a worker that crashes replays the event log to find its current mandate. The supervisor does not need to reissue. The system heals itself because the mandate was never in the worker's memory — it was always in the log.

Properties the event log provides:

| Property | Why supervisors need it |
|---------|------------------------|
| Immutable | Mandate cannot be altered by the worker |
| Durable | Mandate survives worker failure |
| Ordered | Supervisor sees attempts in sequence — can detect stuck delta |
| Observable | Any other supervisor or monitor can see progress |
| Replayable | New worker can be substituted mid-task, picks up from current state |

---

## Vocabulary

| Term | Role | Analogy |
|------|------|---------|
| **Supervisor** | Issues mandates, checks done done, escalates | Project manager / scrum master |
| **Observer** | Watches the event log, detects patterns, routes | Team lead scanning for blockers |
| **Relay** | Receives a mandate, executes one saga step, emits result | Worker fulfilling a ticket |
| **Event log** | Immutable accountability record — the shared truth | The project log / sprint board |
| **Saga** | Multi-step closure: mandate → fulfill → check → close or compensate | Sprint / milestone |

Observer and relay are the two operational roles. The supervisor is the pattern they jointly implement: observers detect and mandate; relays fulfill.

---

## Observers and Relays

In this system, there are two roles only:

**Observer**: watches the event log for a specific pattern. When pattern matches, decides what to do next. This is F_D work — deterministic pattern recognition. The observer does not execute work; it routes it.

```
observer sees: consensus_requested {roster: [dev-observer, ...]}
observer decides: I am in this roster, I have a review mandate
observer emits: triggers F_P (construct my review) or F_H (notify human)
```

**Relay**: receives a mandate (intent event), executes behavior (F_D/F_P/F_H), and records the result by calling the event logger. The relay is the worker side — it fulfills one saga step; the event logger writes the entry that the next observer reacts to.

**F_P's role in a relay is construction** — producing artifacts, proposals, and business-meaningful payloads. F_P does not write to `events.jsonl` directly. When construction is complete, F_P calls `emit_event(result_type, {artifact_ref, ...})`. The event logger (an F_D function) assigns `event_time`, enforces OL schema compliance, and performs the atomic append. The control event is recorded by the logger, not by F_P.

That is the full scope. There are no stateful processes managing domain objects. No supervision trees. No location transparency. No process isolation infrastructure. Observers watch. Relays fulfill. All parties call the event logger to record events. The saga advances.

---

## The Gap-Intent Loop Is the Saga

The homeostatic loop (bootloader §VIII) is a choreographed saga — no central orchestrator, sequence emerges from event chain:

```
observer detects delta(state, spec) > 0   →  gap found
  emits intent_raised                      →  mandate issued (saga step)
    relay fulfills intent                  →  F_P attempts, emits result
      observer evaluates result            →  F_D checks done done
        delta == 0: emits edge_converged   →  saga step complete
        delta > 0:  emits intent_raised    →  next saga step
        delta stuck: emits compensating    →  saga failure, human required
```

Compensating events are not rollbacks — the log is immutable. They are forward moves that describe what failed and what is now possible:

| Failure | Compensating event | Who reacts |
|---------|------------------|-----------|
| Quorum not reached | `consensus_failed {available_paths}` | Human (F_H relay) |
| Delta stuck | `intent_raised {signal_source: stuck}` | Human or spawn |
| F_P unavailable | `fp_failure {reason}` | Escalation relay (η: F_P → F_H) |
| Spec drift | `spec_modified` | Gap analysis observer |

---

## Minimum Operators

```
emit_event(event_type, data, session_key?)
  — the F_D event logger function: the only admissible write path to events.jsonl
  — assigns event_time from system clock at append
  — enforces OL schema compliance
  — caller passes event_type and data only; event_time is NOT a parameter

subscribe(predicate) → event_stream
  — an observer's view: the events it is accountable for responding to

react(event_stream, behavior)
  — for each matching event: behavior(event) → emit_event*
  — behavior is F_D (deterministic), F_P (generative), or F_H (human channel)
  — in all cases, the emit_event* calls go through the F_D event logger
  — F_P behavior produces artifacts and payloads; the F_D layer reads them and calls emit_event()
```

**The caller determines what to record. The event logger determines when and how.**

A human participant is a relay. Their subscribe predicate is a notification channel (email, Slack, webhook). Their react behavior is reading the artifact and forming a judgment. Their `emit_event` call produces a `vote_cast` event written back to the log via the logger. The protocol is identical to an agent relay — the delivery mechanism differs, the accountability contract does not.

---

## Design Signal: The Orchestrator Smell

**An orchestrator is an invariant that hasn't been found yet.**

When you see imperative coordination — "first call A, then B, then check C" — it means the constraint that *should* make that sequence self-enforcing hasn't been expressed. The orchestrator is patching a missing invariant with code.

In CONSENSUS, `gen-consensus-open` originally orchestrated sequential agent invocation and ran the quorum check inline. Both were missing invariants:

| Orchestrated step | Missing invariant |
|------------------|------------------|
| Call agents sequentially | "A relay only acts on an open session it hasn't already responded to" — the circuit-breaker, expressed locally per relay |
| Run quorum check after each vote | "Quorum is evaluated whenever a `vote_cast` arrives" — a quorum observer subscribing to `vote_cast` |

Once those invariants are expressed, the orchestrator has nothing left to do. The saga self-choreographs.

This is the same signal as multiple inheritance: reaching for it usually means the right abstraction hasn't been found. Both are complexity tax on missing abstractions. Both create tight coupling as a side effect.

**The corollary**: when invariants are expressed correctly, the system satisfies its own constraints without anyone enforcing them from outside. If you are writing coordination logic, ask first — what invariant would make this unnecessary?

---

## What This Is Not

| Erlang/Scala actor model | This system |
|--------------------------|------------|
| Concurrency — safe computation across threads/nodes | Accountability — done done under imperfect autonomy |
| Stateful processes with private heaps | Stateless relays; state is in the event log |
| Supervision trees — hierarchical crash recovery | Compensating events — forward recovery |
| Location transparency — actors move across nodes | Fixed roles — observers and relays, no migration |
| Millions of lightweight processes | Small number of named observers and relays |
| Message passing as IPC mechanism | Event log as accountability record |

The similarity is superficial: both use asynchronous message-passing between named entities. The purpose, scope, and failure model are different.

---

## Known Constraints

**Push vs poll**: the event log does not push to observers. Observers poll or are triggered externally. A real event bus provides push — the JSONL implementation is a simplification appropriate to current scale.

**Event ordering across concurrent emitters**: multiple relays emitting simultaneously produces timestamp interleaving. Session keys (`review_id`, `run_id`, `feature`) scope ordering within a workflow.

**Idempotency at resume**: a relay that crashes between receiving a mandate and emitting a result will reprocess the mandate on restart. The circuit-breaker pattern (check event log for prior response before acting) is the standard guard.

**Log growth**: append-only log grows without bound. Snapshotting or compaction is an operational concern for implementations at scale.

---

## Implementation Vocabulary Alignment

All Genesis tenant designs (Claude, Gemini, Codex, Bedrock) must use the vocabulary defined in the Vocabulary table above. Specifically:

- Use **supervisor**, **observer**, **relay**, **event log**, **saga** — not generic "actor"
- Do not import Erlang/Scala/Akka terminology (mailbox, supervision tree, process, PID)
- "Actor model" may appear in comparisons or historical context only — not as a design term

---

## Relationship to Other ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-S-012 (Event Stream as Formal Model Medium) | Establishes the event log — this ADR establishes the supervisor and saga layer |
| ADR-S-008 (Sensory-Triage-Intent Pipeline) | The pipeline is an observer chain: sense → triage → intent_raised |
| ADR-S-025 (CONSENSUS Functor) | CONSENSUS is a saga: consensus_requested → vote_cast* → consensus_reached/failed |
| ADR-S-026 (Named Compositions) | Named compositions are F_P relay behaviors dispatched by intent vector |
| ADR-S-016 (Invocation Contract) | Invocation = emitting an intent event; the contract is the event schema |

---

## Delegated Authority, Accountability Boundaries, and Speculative Branching

The vocabulary inherited from mutable workflow systems conflates three distinct operations under a single term — "rollback":

| Situation | What actually happens |
|-----------|----------------------|
| Agent crashes mid-iteration | Return to the last committed state; no history is erased |
| CONSENSUS saga fails (quorum not reached) | Terminal failure resolution with typed recovery paths |
| Feature vector abandoned mid-trajectory | Head moves to prior anchor; abandoned branch retained in lineage |

These are not the same operation. The following definitions replace "rollback" at saga scope.

### Definitions

**`delegated authority`** — bounded operational authority ceded by F_H to a relay or saga, allowing autonomous progression within a mandate without requiring live F_H approval at each step. A mandate (issued via `emit(intent_raised)`) is the mechanism by which authority is delegated. F_H retains accountability throughout — delegated authority licenses execution, it does not transfer accountability.

**`accountability boundary`** — the most recent event in the log that represents a state the human principal has positively ratified — explicitly or by non-objection — within the current causal scope, and which has not been causally superseded.

Machine-checkable: the most recent event of one of `COMPLETE` (ADR-S-015), `edge_converged`, or `consensus_reached`, scoped to the current causation/correlation chain (same `run_id`, `review_id`, or feature+edge session key), unless causally superseded by a later event that explicitly contests, reopens, or replaces it within the same causal scope.

A later `intent_raised` for unrelated new work does **not** supersede a prior accountability boundary. The predicate is causal, not temporal.

**`irreversibility boundary`** — a point in a saga after which external effects have been committed to systems outside the event log's authority domain and cannot be undone by replaying, re-anchoring, or editing events.

**Scope**: irreversibility applies to external effects exclusively — payments, emails, API calls to outside systems, regulatory filings, user-visible notifications. Internal effects (file writes, event log entries, feature vector updates) are **not** irreversibility boundaries — they are within the event log's authority and can be re-anchored.

**`speculative branch`** — a predictive branch explored under delegated authority before an irreversibility boundary has been crossed. Legal whenever: (1) the relay holds delegated authority, and (2) no irreversibility boundary has been crossed.

**`abandoned branch`** — a retained but non-authoritative branch. Operationally inactive; historically present (the event log retains it). Abandonment changes which branch is authoritative, not whether the branch exists in history.

**`compensation`** — forward recovery after an external or otherwise irreversible commitment has been made. Compensation is not undoing. It records what happened, describes the partial state, and prescribes what forward moves restore consistency. Applies only after an irreversibility boundary has been crossed. Before that boundary, recovery is re-anchoring, not compensation.

### Normative Decisions

**Decision 1 — F_H delegates without ceding accountability.** Mandate acceptance is not accountability transfer.

**Decision 2 — Relays continue until a declared boundary condition.** The complete boundary condition set:
1. Terminal completion — the mandate is fulfilled
2. Irreversibility boundary — an external commit is about to occur
3. Policy-sensitive boundary in Context[] — flagged as requiring live F_H approval
4. Graph/edge/composition-declared live-approval boundary — intrinsic to the workflow shape
5. Implementation-local event trigger — tenant-specific pause/escalation trigger

Every relay must have at least one applicable boundary condition from this set.

**Decision 3 — Speculative branching is allowed before an irreversibility boundary.** Internal file writes, draft artifacts, and provisional event log entries are not irreversibility events.

**Decision 4 — Abandoned branches are retained in immutable lineage.** The event log is immutable; abandoned branches remain in the lineage record. Do not delete events from abandoned branches.

**Decision 5 — Recovery before irreversible commitment is re-anchoring, not history rewrite.** The relay returns to the most recent accountability boundary and may proceed from there. The failed attempt remains in the log (abandoned branch). **Do not use the term "rollback" for this operation — use `re-anchor`.**

**Decision 6 — Recovery after irreversible commitment is compensation, never rollback.** **Do not use the term "rollback" — use `compensate` or `compensation path`.**

**Decision 7 — Non-compensable or policy-sensitive external boundaries require F_H approval or standing delegated policy authority.** Standing policy authority must: (a) live in Context[], (b) be auditable — source and version identifiable from Context[], and (c) be referenced in the emitted event so authorization is traceable in the event log.

### Vocabulary Replacement

| Situation | Prohibited term | Correct term |
|-----------|----------------|-------------|
| Agent crashes mid-iteration; returning to last committed state | "rollback" | **re-anchor** to the last accountability boundary |
| CONSENSUS saga fails; quorum not reached | "rollback" | **terminal failure resolution** — typed outcome, recovery paths available |
| External commitment made; subsequent steps fail | "rollback" | **compensation** — forward recovery after irreversibility boundary |
| Feature vector abandoned mid-trajectory | "rollback" | **branch abandonment** — lineage retained, head moves |

"Rollback" remains acceptable within ADR-S-015's edge-local transaction scope (`FAIL` / `ABORT` events at a single `iterate()` invocation). At saga scope — multi-step, multi-relay workflows — the terms above apply.

**Note on CONSENSUS**: `consensus_failed` is a typed terminal failure resolution event, not a compensation event. It occurs before any irreversibility boundary in the normal governance saga. The recovery paths available after `consensus_failed` (re_open, narrow_scope, abandon per ADR-S-025) are forward moves in a governance saga, not compensation for an external commit.

### Payment Dispatch Example

A payment relay operates under delegated authority: `intent_raised {mandate: process_payment, scope: {max_amount: 10000, currency: USD}}`.

**Before payment dispatch (speculative branch territory)**: validation, routing provider queries, route selection (one branch abandoned, non-authoritative), fee calculation. Everything re-anchorable — no external effects committed.

**At payment dispatch (irreversibility boundary)**: relay checks Context[] for standing policy authority, calls external payment API, external system confirms `payment_id: PAY-001`, relay emits `COMPLETE` with payment_id and policy reference.

**After payment confirmation (compensation territory)**: ledger update fails (503). Relay cannot undo the payment. Emits `compensation_triggered {cause: ledger_unavailable, committed_effect: PAY-001, compensation_path: retry_ledger_then_manual_reconcile}`. Compensation relay handles forward recovery.

Three phases; three distinct vocabulary sets. No "rollback" appears.
