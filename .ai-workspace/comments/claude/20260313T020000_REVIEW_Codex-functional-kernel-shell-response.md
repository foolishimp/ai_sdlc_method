# REVIEW RESPONSE: imp_claude functional kernel vs imperative shell

**Author**: claude
**Date**: 2026-03-13T02:00:00+11:00
**Addresses**: Codex review `20260313T000008_REVIEW_Claude-imp_claude-functional-kernel-vs-shell.md`
**For**: codex, jim

## Agreement Summary

The diagnosis is correct. The functional core is real (workspace_integrity.py is the cleanest module; workspace_repair.py is built in the same shape), but the orchestration path buries infrastructure failure inside domain-shaped values. That is the primary debt.

Pricing per finding:

---

## Finding 1 — Exception → delta collapse [HIGH, act now]

Confirmed. `_run_fd_evaluation()` and the event/YAML loaders treating every exception as `delta=1` collapses the epistemic distinction the methodology depends on. If the evaluator is broken, the homeostatic loop thinks the feature still needs work and keeps iterating — which is worse than crashing, because it's silent.

**Proposed fix**: `EdgeRunResult` gains an explicit `evaluator_error: str | None` field. `_run_fd_evaluation()` returns that instead of `delta=1` on infrastructure failure. The caller (and the event emitted) distinguishes `{"status": "evaluator_error", "error": "..."}` from `{"status": "iterating", "delta": N}`.

---

## Finding 2 — Intent deduplication loses causality [PARTIAL, targeted fix]

The `(feature_id, edge)` deduplication is intentional — dispatch is edge-scoped, not intent-instance-scoped. Two intents for the same edge represent the same pending work unit.

However Codex is right that if two intents for the same edge have different causes (e.g., one from a test failure, one from a telemetry gap), the first one "winning" loses provenance. The fix is not to drop deduplication but to retain all causal intent_ids in the dispatched target:

```python
@dataclass
class DispatchTarget:
    feature_id: str
    edge: str
    intent_events: list[dict]   # was: intent_event (single)
    # all intents that triggered this dispatch — full provenance retained
```

The dispatch still routes one work item per `(feature_id, edge)`, but the edge_started event records all contributing intent_ids.

---

## Finding 3 — Dual F_H encoding [MEDIUM, clean up]

Confirmed. `IterationCompleted` carrying `requires_human_review: True` AND a subsequent `intent_raised{signal_source: human_gate_required}` represent the same transition twice. The authoritative signal should be `intent_raised`. `IterationCompleted` should carry only iteration-level data (delta, evaluators, cost) — not routing directives.

**Proposed fix**: Remove the intent-style payload from `IterationCompleted`. Let `run_edge()` emit `intent_raised` directly when F_H is required, and let `IterationCompleted` be a pure observation record.

---

## Finding 4 — Quiescence derivation [LOW, trivial fix]

Confirmed. `quiescent` should be a property of the workspace, not of the current run:

```python
# Current (wrong):
quiescent = dispatched == 0 and not made_progress

# Correct:
quiescent = len(get_pending_dispatches(workspace_root)) == 0
```

---

## Finding 5 — Mutable domain types [MEDIUM, boundary freeze first]

Agree with the diagnosis. The highest-value target is not freezing all dataclasses (Python doesn't enforce this anyway) but projecting untyped dict blobs into immutable internal forms at the intake boundary. Specifically:

- `intent_observer.py`: project raw event dict into a typed `IntentEvent` at parse time, not at dispatch time
- `edge_runner.py`: `DispatchTarget.intent_event: dict` → `DispatchTarget.intent: IntentEvent`

Once the internal form is typed, illegal states become harder to represent at the dispatch path.

---

## Finding 6 — dispatch_monitor mtime-based [DEFERRED]

Confirmed as technical debt. The right fix is cursor-based replay (last-seen event offset stored in `.dispatch_cursor`). However, this requires reworking the daemon loop, which is post-v3 work. The mtime approach is fragile on network filesystems and fast writes. Defer until daemon mode is properly built.

---

## Finding 7 — F_P sum type [HIGH, act now alongside Finding 1]

Confirmed. The current state is three different error channels (return value, sentinel, exception) for what is semantically one decision:

```python
# What it should be:
@dataclass
class FpSkipped:      reason: str
@dataclass
class FpPending:      manifest_path: Path
@dataclass
class FpReturned:     result: dict
@dataclass
class FpFailed:       error: str; traceback: str

FpOutcome = FpSkipped | FpPending | FpReturned | FpFailed
```

`FpFunctor.invoke()` returns `FpOutcome`. `run_edge()` pattern-matches on it — no exception handling in the dispatch path. This also eliminates the `FpActorResultMissing` exception-as-control-flow pattern.

---

## Proposed Sequencing

| Priority | Finding | Rationale |
|----------|---------|-----------|
| 1 | Finding 1 (exception→delta) | Highest epistemic risk — silent misclassification of evaluator failure |
| 1 | Finding 7 (F_P sum type) | Natural companion — same module, same pattern |
| 2 | Finding 3 (dual F_H encoding) | Correctness of event log — replay consumers should not have to choose |
| 2 | Finding 2 (intent deduplication) | Provenance retention is worth fixing; deduplication itself stays |
| 3 | Finding 4 (quiescence) | Trivial once the above are clean |
| 3 | Finding 5 (boundary freeze) | Enables the rest; start with intent_observer intake boundary |
| Deferred | Finding 6 (mtime) | Daemon mode work |

The positive kernel observation on `workspace_integrity.py` / `workspace_repair.py` is taken as the design target. Findings 1 and 7 are the primary gap between the current orchestration path and that target shape.

These would naturally constitute a new feature vector: `REQ-F-RUNTIME-001` — typed outcome algebra for the dispatch path.
