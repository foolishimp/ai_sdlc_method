# ADR-011: The Gradient and Spec Review at Every Observer Point

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Methodology Author
**Requirements**: REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008, REQ-LIFE-009
**Extends**: ADR-008 (Universal Iterate Agent)

---

## Context

The formal specification (v2.7.0, §7.1) defines **The Gradient** (`delta(state, constraints) → work`) as the unified operation applied everywhere. The "consciousness loop" is reframed as this gradient operating at progressively larger scales.

Every evaluator is an observer of the gradient. The three-direction gap detection (backward/forward/inward) detects deltas at the iteration scale. Spec Review (`REQ-LIFE-009`) detects deltas at the workspace-spec scale.

The insight: The gradient is not a single edge. It is a **structural property that emerges at every observer point**. When any evaluator detects a non-zero gradient that cannot be resolved locally, that delta is a signal that should become an intent.

### The Problem

Without formal intent capture from all gradient observer points:
1. **Local iteration work** stays isolated, losing the causal chain to larger scale goals.
2. **Refactoring needs** (irreducible iteration deltas) are lost.
3. **Spec Review deltas** (workspace-spec misalignment) are handled ad-hoc.

### Options Considered

1. **Production-only feedback** — keep `intent_raised` on the production edge only.
2. **Unified Gradient Feedback (The Decision)** — every observer point can emit `intent_raised` based on gradient detection.
3. **Automatic intent generation** — observers emit intents without human review.

---

## Decision

**Every observer point in the iterate agent can emit `intent_raised` events when a non-zero gradient is detected. Seven signal source types are recognised. Spec Review is implemented as a stateless gradient check against the workspace.**

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
