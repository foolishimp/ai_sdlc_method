# ADR-011: Consciousness Loop at Every Observer Point

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Methodology Author
**Requirements**: REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008
**Extends**: ADR-008 (Universal Iterate Agent)

---

## Context

The formal specification (§7.7) defines the consciousness loop as a reflexive structure: the system observes itself, modifies its own specification, and observes the consequences of that modification. The spec also defines `intent_raised` (§7.7.2) and `spec_modified` (§7.7.3) as first-class events, and protocol enforcement hooks (§7.8) as mandatory side effects.

However, the consciousness loop was implicitly scoped to the `telemetry→intent` edge — production monitoring feeding back to new development work. This left a gap: **during development**, every evaluator is already an observer, and the three-direction gap detection (backward/forward/inward) already detects deltas at every iteration. These development-time observations were being handled ad-hoc (escalate upstream, keep iterating) rather than formally entering the intent system.

The insight: the consciousness loop is not a single edge. It is a **structural property that emerges at every observer point**. The three evaluator types (human, agent, deterministic) running at every edge of the graph are observers. When they detect a delta that cannot be resolved within the current iteration scope, that delta is a signal that should become an intent.

### The Problem

Without formal intent capture from development-time observations:
1. **Test failures that reveal requirement gaps** are worked around with assumptions, not formally tracked
2. **Refactoring needs** decay into TODO comments instead of entering the graph as feature vectors
3. **Source finding escalations** are reported to the human but not event-logged for telemetry analysis
4. **Process gaps** (missing evaluators, vague criteria) are noted in iteration reports but not fed back as methodology improvement intents
5. **Gap analysis** (`/aisdlc-gaps`) finds coverage holes but doesn't generate actionable intents from them

### Options Considered

1. **Production-only consciousness loop** — keep `intent_raised` on the `telemetry→intent` edge only. Development-time observations stay ad-hoc.
2. **Development + production consciousness loop** — every observer point can emit `intent_raised`. Seven signal sources classified uniformly.
3. **Automatic intent generation** — observers emit intents without human review.

---

## Decision

**Every observer point in the iterate agent can emit `intent_raised` events. Seven signal source types are recognised. Human review is required before intents spawn feature vectors. The same mechanism operates during development and production.**

The signal sources are:

| Signal Source | Observer Point | When |
|---|---|---|
| `gap` | `/aisdlc-gaps` | Traceability validation finds uncovered REQ keys |
| `test_failure` | Forward evaluation (TDD) | Same check fails > 3 iterations, or test reveals upstream deficiency |
| `refactoring` | TDD refactor phase | Structural debt exceeds current feature scope |
| `source_finding` | Backward evaluation | Source asset ambiguous/missing, `escalate_upstream` disposition |
| `process_gap` | Inward evaluation | Evaluator missing, criterion vague, context missing |
| `runtime_feedback` | Production telemetry | SLA violation, error rate spike |
| `ecosystem` | External monitoring | Dependency deprecated, API changed, regulation updated |

Each `intent_raised` event carries:
- `prior_intents` — the causal chain enabling reflexive loop detection
- `signal_source` — classification for telemetry analysis
- `affected_req_keys` — which requirements are impacted
- `edge_context` — which edge was being traversed when the signal fired

---

## Rationale

### Why Every Observer (vs Production Only)

**1. The spec already says so** — §7.6 states: *"The methodology observes itself using the same evaluator pattern it uses for artifacts."* The two-level diagram (§7.6, lines 845–852) shows methodology observation as structurally identical to product observation. Restricting `intent_raised` to production contradicts this.

**2. Development IS homeostasis** — Gap analysis during development is the same pattern as telemetry monitoring in production: observe a delta between what should be (spec) and what is (reality), then respond. The delta detection mechanism (evaluators) is identical. Only the trigger context differs (iteration vs running system).

**3. Dogfood integrity** — The methodology claims it is a living system (§7.7.6). If its own development-time observations don't enter the intent system, the living system property is aspirational rather than structural. We are building a tool (genesis-monitor) that observes this exact event stream. It must see ALL signals, not just production ones.

**4. Refactoring capture** — Without formal intent capture, refactoring needs decay into TODO comments. TODO comments are invisible to the graph, don't get REQ keys, don't get tests, and don't close the loop. An `intent_raised` event makes them visible, trackable, and convergence-testable.

### Why Human Review (vs Automatic)

**1. Signal vs noise** — Not every delta warrants a new feature vector. A test failing once is normal TDD. A test failing 5 times on the same check across iterations is a signal. The human distinguishes signal from noise.

**2. Priority allocation** — Intents compete for resources. The human decides which development-time signals to act on vs acknowledge.

**3. Circuit breaker** — Without human gating, the consciousness loop could enter infinite regression: observer detects gap → generates intent → intent triggers work → work generates new gaps → more intents. Human review is the circuit breaker.

### Why Seven Sources (vs Fewer)

**1. Telemetry value** — Classification enables analysis: "40% of our intents come from test failures, 30% from gap analysis, 20% from refactoring." This is methodology self-observation data.

**2. Different response patterns** — A `test_failure` signal typically spawns iteration on the current edge. A `gap` signal spawns a new feature vector. A `process_gap` signal feeds back to the graph package (methodology improvement). Different sources need different response patterns.

**3. Exhaustive** — The seven sources map exactly to the three evaluation directions (forward → test_failure; backward → source_finding; inward → process_gap), plus the aggregate analysis (gap), the construction observation (refactoring), and the two production signals (runtime_feedback, ecosystem). No delta type is unclassified.

---

## Consequences

### Positive

- **Complete lineage**: Every signal that generates work is event-logged with causal chain
- **Reflexive traceability**: `prior_intents` enables detection of feedback loops (intent A → work → intent B → ... → back to A)
- **Development-time homeostasis**: Gap analysis, test failures, and refactoring become first-class signals, not ad-hoc observations
- **Methodology self-improvement**: Process gaps (`EVALUATOR_MISSING`, `EVALUATOR_VAGUE`) enter the intent system, making methodology improvement trackable
- **Dogfood completeness**: genesis-monitor sees ALL signals in `events.jsonl`, not just production telemetry

### Negative

- **Event volume**: Development-time signals generate more `intent_raised` events. Mitigated by human gating (most signals are acknowledged, not acted on).
- **Human fatigue**: More signals means more review decisions. Mitigated by clustering (group related gaps into one intent) and threshold-based triggering (test failure only after > 3 iterations).
- **Complexity**: Seven signal sources is more to understand. Mitigated by the mapping being exhaustive and non-overlapping — each delta has exactly one correct classification.

### Implementation Notes

- The iterate agent (`aisdlc-iterate.md`) already has three-direction gap detection. The change adds `intent_raised` emission when deltas warrant it.
- The feedback loop edge config (`feedback_loop.yml`) already had 2 sources. The change adds 5 development-time sources with intent templates.
- `/aisdlc-gaps` already finds coverage holes. The change adds `intent_raised` emission per gap cluster.
- The TDD edge config (`tdd.yml`) already has refactor guidance. The change adds intent generation for structural debt and stuck deltas.
- Protocol enforcement hooks (REQ-LIFE-008) are new — they ensure `iterate()` can't skip event emission silently.

---

## Requirements Addressed

- **REQ-LIFE-005**: Intent events as first-class objects — `intent_raised` with full causal chain
- **REQ-LIFE-006**: Signal source classification — 7 types covering all observer points
- **REQ-LIFE-007**: Spec change events — `spec_modified` with traceability
- **REQ-LIFE-008**: Protocol enforcement hooks — mandatory side effects after every iteration

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.6 (IntentEngine), §7.7 (Consciousness Loop)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (extended by this ADR)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (signal sources are affect-phase observers; ambiguity classification determines escalation)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (continuous background signal generation feeds the consciousness loop)
