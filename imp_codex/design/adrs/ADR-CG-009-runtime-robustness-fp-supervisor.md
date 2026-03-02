# ADR-CG-009: Runtime Robustness for Probabilistic Processing (F_P)

**Status**: Accepted  
**Date**: 2026-03-03  
**Requirements**: REQ-ROBUST-001, REQ-ROBUST-002, REQ-ROBUST-003, REQ-ROBUST-007, REQ-ROBUST-008

---

## Context

Probabilistic processing (F_P) performs construction or evaluation that may stall, hang, or crash. Without explicit isolation, supervision, and observability, a single hung invocation can block the engine, elide failure events, and leave sessions in ambiguous states.

The specification adds a set of runtime robustness requirements to make probabilistic execution resilient and observable.

## Decision

Adopt a supervisor pattern and isolation boundary for all F_P invocations:

1. Isolation boundary: execute each F_P call in a boundary that the caller can terminate cleanly on timeout/error. Nested invocations must not deadlock or share mutable state.
2. Supervisor: enforce wall‑clock timeout; detect stalls (no observable progress) within a configured window; retry transient failures up to a configured limit; on persistent failure, return structured error.
3. Failure events: guarantee emission of structured failure events to `events.jsonl` for all F_P failures. Include classification (timeout/error/stall), duration, retry count, feature, and edge.
4. Crash/session gap recovery: on engine startup, scan for `edge_started` without completion events; emit `iteration_abandoned` events describing gaps since last activity.

## Consequences

Positive:
- Prevents unbounded/hung F_P calls from blocking engine progress.
- Enables homeostasis: failures become observable signals for triage and intent generation.
- Improves auditability and recovery across sessions.

Trade-offs:
- Slightly higher runtime overhead from supervision and event emission.
- Requires configuration surface for timeouts/stall/retry thresholds.

## Implementation Notes

- Configuration surface: add supervisor settings (timeouts, stalls, retries) to `intentengine_config.yml` or a dedicated `runtime_robustness.yml`.
- Event schemas: document `failure_event`/`evaluator_detail` fields and add `iteration_abandoned` to the event catalogue in `agents/gen-iterate.md`.
- Startup hook: ensure `/gen-start` (or engine bootstrap) performs gap scan before state detection.

## References

- Spec §14 Runtime Robustness; FEATURE_VECTORS REQ‑F‑ROBUST‑001  
- ADR‑S‑008: Sensory‑Triage‑Intent pipeline (failure observability and triage)  
- IntentEngine (§4.6): observer→evaluator→typed_output composition

