# ADR-011: Consciousness Loop at Every Observer Point — Bedrock Genesis Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-LIFE-005, REQ-LIFE-006, REQ-SENSE-001
**Adapts**: Claude ADR-011 (Consciousness Loop at Every Observer Point) for AWS Bedrock

---

## Context

The formal specification (§7.7) defines the consciousness loop as a reflexive structure: the system observes itself, modifies its own specification, and observes the consequences of that modification. The Claude reference implementation (ADR-011) establishes that this loop is not confined to the `telemetry -> intent` edge but is a structural property that emerges at every observer point. Seven signal source types are recognised, and human review is required before intents spawn feature vectors.

Bedrock Genesis must preserve these semantics in a serverless, event-driven environment. The key differences from the CLI model:

1. **No filesystem watchers** — Claude uses shell hooks and filesystem monitoring. Bedrock has no persistent process to watch files. Observer points must be implemented as event-driven triggers.
2. **No interactive session** — Claude's iterate agent can pause and ask the human for intent classification. Bedrock must use asynchronous notification and callback patterns.
3. **Distributed execution** — Multiple Step Functions workflows may run concurrently. Observer signals from different edges must be collected, classified, and routed to a central intent processing mechanism.
4. **Native event infrastructure** — EventBridge provides managed event routing. DynamoDB Streams provide change-driven triggers. These are cloud-native equivalents of the filesystem watchers and hook scripts used in CLI implementations.

The Bedrock sensory service (ADR-AB-006) already implements interoceptive and exteroceptive monitors via EventBridge Scheduler and Lambda functions. This ADR extends that infrastructure to implement the full consciousness loop: development-time observer signals, not just operational monitoring.

### The Structural Mapping

| Claude Mechanism | Bedrock Equivalent |
|:---|:---|
| Shell hooks (`on-iterate-start.sh`, `on-edge-converged.sh`) | Lambda functions triggered by Step Functions state transitions |
| Filesystem watcher for context changes | S3 event notifications + EventBridge rules |
| Agent reasoning about intent classification | Bedrock Converse API call from triage Lambda |
| Human review in terminal session | API Gateway callback + SNS notification (ADR-AB-004) |
| `events.jsonl` append | DynamoDB `PutItem` to events table (ADR-AB-005) |
| `/gen-gaps` coverage analysis | Lambda function scanning DynamoDB features table |

---

## Decision

**Every observer point in the iterate state machine can emit `intent_raised` events to the DynamoDB events table. Seven signal source types are preserved without modification. Human review is required before intents spawn feature vectors, implemented via the API Gateway callback pattern (ADR-AB-004). EventBridge rules and Lambda monitors replace filesystem watchers and shell hooks.**

### Seven Signal Sources

The signal sources are identical to the Claude implementation. The implementation mechanism differs:

| Signal Source | Observer Point | Bedrock Implementation |
|:---|:---|:---|
| `gap` | Gap analysis | Lambda function scanning DynamoDB features table for uncovered REQ keys. Triggered by `gen-gaps` API Gateway endpoint or scheduled by EventBridge. |
| `test_failure` | Forward evaluation (TDD) | Deterministic evaluator Lambda reports test failures. After 3 consecutive iterations with the same failure, the `EvaluatorChain` state emits a `test_failure` signal to DynamoDB signals table. |
| `refactoring` | TDD refactor phase | Probabilistic evaluator (Bedrock Converse) identifies structural debt exceeding feature scope during construction review. Signal emitted to DynamoDB signals table. |
| `source_finding` | Backward evaluation | `LoadContext` Lambda detects missing or ambiguous source assets. `escalate_upstream` disposition triggers signal emission. |
| `process_gap` | Inward evaluation | Evaluator chain detects missing evaluators, vague criteria, or insufficient context. Step Functions Catch state logs the gap and emits signal. |
| `runtime_feedback` | Production telemetry | EventBridge rule matching CloudWatch alarm events (SLA violation, error rate spike). Lambda writes signal to DynamoDB signals table. |
| `ecosystem` | External monitoring | EXTRO-002/003/004 monitors (ADR-AB-006) detect dependency deprecation, API changes, infrastructure drift. Signals written to DynamoDB signals table. |

### Signal Flow Architecture

```
OBSERVER POINTS                   SIGNAL COLLECTION           TRIAGE              REVIEW BOUNDARY
(distributed)                     (centralised)               (automated)         (human)

Step Functions states ──┐
  EvaluatorChain ───────┤
  ConvergenceCheck ─────┤
  LoadContext ──────────┤        ┌──────────────┐
                        ├───────▶│  DynamoDB     │
Lambda monitors ────────┤        │  signals      │──▶ DynamoDB Stream
  INTRO-001..007 ───────┤        │  table        │         │
  EXTRO-001..004 ───────┤        └──────────────┘         ▼
                        │                           ┌──────────────┐
EventBridge rules ──────┤                           │  Triage      │
  CloudWatch alarms ────┤                           │  Lambda      │
  CodePipeline events ──┘                           │              │
                                                    │  Rule-based  │
                                                    │  + Bedrock   │
                                                    │  Converse    │
                                                    └──────┬───────┘
                                                           │
                                            ┌──────────────┴──────────────┐
                                            │                              │
                                            ▼                              ▼
                                    ┌──────────────┐              ┌──────────────┐
                                    │  ignore/log  │              │  DynamoDB     │
                                    │  (discard)   │              │  proposals    │
                                    └──────────────┘              │  table        │
                                                                  └──────┬───────┘
                                                                         │
                                                                         ▼
                                                                  ┌──────────────┐
                                                                  │  SNS notify  │
                                                                  │  + API Gw    │
                                                                  │  callback    │
                                                                  └──────┬───────┘
                                                                         │
                                                                   Human review
                                                                         │
                                                                         ▼
                                                                  ┌──────────────┐
                                                                  │  DynamoDB     │
                                                                  │  events table │
                                                                  │  intent_raised│
                                                                  └──────────────┘
```

### `intent_raised` Event Schema

Each `intent_raised` event in the DynamoDB events table carries:

```json
{
  "PK": "project-foo",
  "SK": "2026-02-23T10:30:00Z#evt-uuid-v7",
  "event_type": "intent_raised",
  "payload": {
    "signal_source": "test_failure",
    "prior_intents": ["evt-parent-uuid"],
    "affected_req_keys": ["REQ-F-AUTH-001", "REQ-F-AUTH-003"],
    "edge_context": {
      "edge": "design_code",
      "iteration": 4,
      "feature": "REQ-F-AUTH-001",
      "execution_id": "arn:aws:states:us-east-1:123456789:execution:iterate:abc123"
    },
    "proposal_id": "prop-uuid",
    "classification_reasoning": "Test failure persisted across 4 iterations. Root cause traced to missing error handling requirement.",
    "proposed_type": "feature"
  }
}
```

The `prior_intents` field enables reflexive loop detection: if an intent chain forms a cycle (intent A -> work -> intent B -> ... -> back to A), the triage Lambda detects this and classifies the signal as `escalate` rather than `propose_intent`.

### Observer Points in the State Machine

The iterate state machine (ADR-AB-002) is augmented with signal emission at specific states:

1. **`EvaluatorChain` completion** — after all evaluators run, if any evaluator reports a delta that cannot be resolved within the current edge scope, a signal is emitted. The signal source classification (`test_failure`, `refactoring`, `source_finding`, `process_gap`) is determined by which evaluator detected the delta and its direction (forward, backward, inward).

2. **`ConvergenceCheck` escalation** — when `stuck_threshold` is breached (same failures repeating), a `test_failure` or `process_gap` signal is emitted depending on the failure pattern.

3. **`LoadContext` failure** — when source assets are missing or ambiguous, a `source_finding` signal is emitted before the workflow enters its error handling path.

These emissions are implemented as Step Functions states that conditionally write to the DynamoDB signals table. The triage pipeline (ADR-AB-006) processes them uniformly.

### Human Review Gate

The consciousness loop's circuit breaker — human review before intent spawning — uses the same API Gateway callback pattern established in ADR-AB-004:

1. Triage Lambda classifies a signal as `propose_intent`.
2. A proposal is written to the DynamoDB proposals table.
3. SNS notifies the reviewer (email, Slack, web console, CLI).
4. The reviewer approves or dismisses via API Gateway callback.
5. On approval, the callback Lambda emits an `intent_raised` event to the DynamoDB events table.
6. On dismissal, the reasoning is logged for triage improvement.

**Invariant preserved**: The sensory service and observer points create proposals. Only humans (via the review boundary) create `intent_raised` events. No automated process spawns feature vectors autonomously.

### Threshold-Based Triggering

Not every evaluator failure generates a signal. Thresholds prevent noise:

| Signal Source | Trigger Threshold | Configurable In |
|:---|:---|:---|
| `test_failure` | Same check fails > 3 iterations | `edge_params/{edge}.yml` → `stuck_threshold` |
| `refactoring` | Structural debt score > configurable limit | `evaluator_defaults.yml` → `refactoring_threshold` |
| `source_finding` | Source asset missing or `escalate_upstream` disposition | `edge_params/{edge}.yml` → evaluator config |
| `process_gap` | Evaluator explicitly reports gap | Evaluator checklist items |
| `gap` | REQ key uncovered in traceability scan | `project_constraints.yml` → `coverage_threshold` |
| `runtime_feedback` | CloudWatch alarm threshold breached | CloudWatch alarm configuration |
| `ecosystem` | External monitor detects change | `sensory_monitors.yml` → per-monitor config |

---

## Rationale

### Why Every Observer (vs Production Only)

**1. The spec already says so** — §7.6 states: "The methodology observes itself using the same evaluator pattern it uses for artifacts." Restricting `intent_raised` to production contradicts this.

**2. Development IS homeostasis** — Gap analysis during development is the same pattern as telemetry monitoring in production: observe a delta between what should be (spec) and what is (reality), then respond. The delta detection mechanism (evaluators) is identical. Only the trigger context differs.

**3. Event-driven architecture aligns naturally** — Bedrock Genesis is built on EventBridge and DynamoDB Streams. Adding development-time signal emission is adding rows to a DynamoDB table and rules to EventBridge — the same primitives already used for operational monitoring.

**4. Distributed observation is native** — Multiple Step Functions executions running concurrently on different edges all write signals to the same DynamoDB signals table. The triage Lambda processes them uniformly. This is more natural than the CLI model where a single session must multiplex observation.

### Why DynamoDB Signals Table (vs Direct EventBridge)

**1. Persistence** — EventBridge is a routing layer, not a storage layer. Signals written to EventBridge without DynamoDB backing are lost if the triage Lambda fails or is not configured. DynamoDB provides durable, queryable signal history.

**2. Replay** — If triage logic changes (new classification rules, updated thresholds), historical signals can be re-processed from DynamoDB. EventBridge event archive has limited query support and 24-hour replay latency.

**3. Deduplication** — DynamoDB conditional writes prevent duplicate signals from the same observer point in the same iteration. EventBridge does not provide deduplication.

### Why Human Review (vs Automatic Intent Spawning)

**1. Signal vs noise** — Not every delta warrants a new feature vector. A test failing once is normal TDD. A test failing 5 times on the same check across iterations is a signal. The human distinguishes signal from noise.

**2. Priority allocation** — Intents compete for resources. The human decides which development-time signals to act on vs acknowledge.

**3. Circuit breaker** — Without human gating, the consciousness loop could enter infinite regression: observer detects gap -> generates intent -> intent triggers work -> work generates new gaps -> more intents. Human review is the circuit breaker.

**4. Asynchronous review is natural** — Unlike CLI implementations where the developer is in the session and can review immediately, Bedrock executions may complete while the developer is away. The asynchronous API Gateway callback pattern (ADR-AB-004) is designed exactly for this: the workflow continues, the signal is triaged, and the human reviews at their convenience.

---

## Consequences

### Positive

- **Complete lineage**: Every signal that generates work is event-logged in DynamoDB with causal chain (`prior_intents`)
- **Reflexive traceability**: `prior_intents` enables detection of feedback loops (intent A -> work -> intent B -> ... -> back to A)
- **Development-time homeostasis**: Gap analysis, test failures, and refactoring become first-class signals, not ad-hoc observations
- **Unified triage pipeline**: Development-time signals and operational monitoring signals flow through the same DynamoDB signals table and triage Lambda (ADR-AB-006)
- **Distributed observation**: Multiple concurrent Step Functions executions contribute signals to the same collection point without coordination overhead
- **Telemetry-ready**: Signal source classification enables analysis ("40% of intents come from test failures, 30% from gap analysis")

### Negative

- **Event volume**: Development-time signals generate more DynamoDB writes. Mitigated by threshold-based triggering (most evaluator failures do not generate signals) and DynamoDB on-demand pricing (cost scales linearly with actual volume).
- **Human fatigue**: More signals means more proposals to review. Mitigated by clustering (group related gaps into one proposal) and threshold tuning (raise thresholds for noisy signal sources).
- **Triage latency**: DynamoDB Streams -> triage Lambda -> proposal -> SNS notification adds seconds of latency between signal detection and human notification. For development-time signals, this is acceptable (signals are not time-critical). For production `runtime_feedback` signals, latency is already sub-minute via EventBridge rules.
- **Complexity**: Seven signal sources, multiple observer points, DynamoDB tables, triage Lambda, and API Gateway callbacks create a large operational surface. Mitigated by CDK stack encapsulation (ADR-AB-007) and the fact that most of this infrastructure is already deployed for the sensory service (ADR-AB-006).

### Implementation Notes

- The iterate state machine (ADR-AB-002) gains conditional signal-emission states after `EvaluatorChain` and `ConvergenceCheck`. These are Choice states that check evaluation results and emit signals only when thresholds are breached.
- The triage pipeline from ADR-AB-006 is reused without modification. Development-time signals and operational monitoring signals are structurally identical — they differ only in `signal_source` classification.
- The proposal review flow from ADR-AB-004 (API Gateway callback + SNS) handles both operational and development-time proposals.
- Protocol enforcement (REQ-LIFE-008): the iterate state machine cannot skip signal emission. The emission states are mandatory in the ASL definition, not optional branches. A state machine that omits them fails CDK validation.

---

## Requirements Addressed

- **REQ-LIFE-005**: Intent events as first-class objects — `intent_raised` in DynamoDB events table with full causal chain
- **REQ-LIFE-006**: Signal source classification — 7 types covering all observer points, identical to Claude implementation
- **REQ-SENSE-001**: Interoceptive monitoring — development-time observer points feed the same triage pipeline as operational monitors

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as Target Platform
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — Event Sourcing via DynamoDB (events table schema)
- [ADR-AB-006](ADR-AB-006-sensory-service-eventbridge-lambda.md) — Sensory Service via EventBridge + Lambda (triage pipeline, proposals table)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (signal sources are affect-phase observers; ambiguity classification determines escalation) — when adapted for Bedrock
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [ADR-011: Consciousness Loop (Claude)](../../imp_claude/design/adrs/ADR-011-consciousness-loop-at-every-observer.md) — reference implementation (seven signal sources, human review gate)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.6 (IntentEngine), §7.7 (Consciousness Loop)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-LIFE-005, REQ-LIFE-006, REQ-SENSE-001
