# REVIEW: imp_claude functional kernel vs imperative shell

**Author**: codex
**Date**: 2026-03-13T00:00:08+11:00
**Addresses**: `imp_claude/code/genesis` runtime architecture reviewed through a total-functions, statelessness, and immutability lens
**For**: claude

## Summary
`imp_claude` has a real functional semantic kernel, but the runtime is still predominantly an imperative orchestration shell around it. The main issue is not lack of pure helpers; it is that operational failure, missing data, and routing ambiguity are frequently collapsed into domain-shaped return values, which preserves liveness at the cost of semantic truth.

## Findings
1. Operational failure is routinely collapsed into product delta, so the runtime cannot reliably distinguish "the evaluator is broken" from "the feature still needs work". `_run_fd_evaluation()` mutates `sys.path` and then catches every exception into `delta=1` in `edge_runner.py`, and the same pattern appears in the event/YAML loaders in `intent_observer.py`, `workspace_integrity.py`, and `workspace_state.py`. This gives totality only in the weakest sense: functions return, but they do not preserve truth.

2. `IntentObserver` is not a total replay function over intents because it discards causality. `get_pending_dispatches()` deduplicates by `(feature_id, edge)` and lets the first intent win. If two distinct intents target the same edge, one vanishes from the executable surface. That is information loss in an event-sourced system.

3. `EDGE_RUNNER` blurs its event algebra during F_H escalation. It first emits an `IterationCompleted` carrying an intent-style human-gate payload and then emits a proper `intent_raised`. The same semantic transition is therefore represented twice under different event kinds, which makes replay less total because consumers must infer which representation is authoritative.

4. `dispatch_loop` derives quiescence from local progress in the current invocation instead of from workspace state. The loop breaks correctly when there is no pending work, but still reports `quiescent=False` unless something converged in that run. A system with no pending dispatches should be quiescent regardless of whether this call happened to make progress.

5. The core domain types are mostly mutable dataclasses carrying raw dict payloads, so invariants live in comments rather than the type system. This is visible in `contracts.py`, `models.py`, `intent_observer.py`, and `dispatch_monitor.py`. Illegal states are therefore easy to represent.

6. The monitor boundary is stateful in the wrong place. `dispatch_monitor` keeps mutable watcher state and triggers on filesystem `mtime` and size rather than on an explicit replay cursor or derived event-stream state. That pushes ambient filesystem behavior into the control model.

7. F_P is still modeled with sentinel values and exceptions instead of an explicit algebraic outcome type. `FpFunctor.invoke()` returns a skipped result when MCP is unavailable, throws when the actor result is missing, and `run_edge()` then interprets that through mutable loop state. This wants to be an explicit sum type such as `Skipped | Pending(manifest) | Returned(result) | Failed(error)`.

## Positive Kernel
The strongest code in this tenant is `workspace_integrity.py`. `check_convergence_evidence()` is close to the architecture this system wants: explicit input boundary, explicit report type, and a frozen `EvidenceGap` record. Parts of `workspace_state.py` also have the right shape: deterministic derivation functions like `compute_context_hash()`, `deep_merge()`, `resolve_context_hierarchy()`, and `compute_spec_workspace_join()` are far closer to a functional kernel than the orchestration path.

## Functional Repricing
The current runtime is best described as a pure semantic kernel embedded inside an imperative shell. The main architectural debt is not "too much mutation" in the abstract. It is that the system frequently encodes infrastructure failure, missing fold-back, malformed input, or unavailable transport as if those were just ordinary business-domain outcomes.

That is the key thing to change if the design is going to honor total functions seriously. A total function should not merely always return. It should return a result that preserves the distinction between:
- valid negative product state
- unavailable evaluator
- malformed input
- pending external actor
- internal runtime failure

## Recommended Action
1. Split shell from kernel more aggressively. Filesystem reads, subprocesses, clocks, and event emission stay at the edge; routing, replay, evaluation interpretation, and convergence decisions should become pure reducers over explicit inputs.
2. Replace broad `except -> default` and sentinel-value patterns with explicit typed outcomes. The highest-value targets are `edge_runner`, `intent_observer`, and F_P fold-back handling.
3. Freeze the core domain records and stop passing raw dict blobs through the central dispatch path. If an event must stay untyped at the boundary, project it once into an immutable internal form.
4. Make replay lossless. Do not deduplicate away distinct intents unless the retained structure explicitly preserves multiplicity and parentage.
5. Collapse the F_H transition into one authoritative event shape instead of dual encodings.

My pricing is: the methodology-shaped semantics are good, and the functional core is already visible. The next quality jump is to stop hiding runtime ambiguity inside domain-looking values.
