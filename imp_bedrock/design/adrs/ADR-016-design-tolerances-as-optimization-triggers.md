# ADR-016: Design Tolerances as Optimization Triggers

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-SUPV-002
**Extends**: ADR-AB-006 (Sensory Service), ADR-015 (Sensory Service Technology Binding)

---

## Context

ADR-014 and ADR-015 capture technology bindings — the decisions that map spec abstractions to AWS Bedrock mechanisms (EventBridge + Lambda, Bedrock Converse API, API Gateway, DynamoDB). These bindings are recorded as choices but not yet as **monitored constraints with tolerances**.

The insight: every technology binding implies tolerances. Every tolerance is a threshold the sensory system can monitor. Every breach is an optimization intent waiting to be raised.

### The Gap

Current design documents say WHAT was chosen but not:
- What performance, cost, or quality tolerances the choice implies
- What monitoring signals detect tolerance breaches
- What happens when a better option emerges or a tolerance is exceeded

Without explicit tolerances, design decisions are static. With them, the design layer becomes a homeostatic surface — it evaluates itself and generates intents when its own constraints shift.

### AWS-Specific Monitoring Infrastructure

Bedrock Genesis has a natural advantage for tolerance monitoring: AWS provides **CloudWatch Metrics** as a unified metrics substrate. Every service — Lambda, Step Functions, DynamoDB, Bedrock Runtime, API Gateway — emits metrics automatically. CloudWatch Alarms can trigger EventBridge rules when thresholds are breached. This means tolerance monitoring is not an additional system to build — it is a configuration layer on top of existing AWS observability infrastructure.

---

## Decision

**Design documents (ADRs, design docs) should capture technology-specific tolerances alongside binding decisions. These tolerances are monitored via CloudWatch Metrics and Alarms, EventBridge rules route breach events to the sensory service (ADR-015), and breaches generate optimization intents via the IntentEngine (ADR-014).**

### Tolerance Structure

Each technology binding can declare tolerances as CloudWatch Alarm configurations:

```yaml
# design_tolerances.yml (stored in S3, deployed via CDK)
tolerances:
  bedrock_converse:
    binding: ADR-AB-001
    monitors:
      - metric: bedrock/InvocationLatency
        namespace: AWS/Bedrock
        threshold: 30s
        direction: below
        alarm_name: iterate-latency-breach
        signal: INTRO-004
      - metric: custom/IterationCostUSD
        namespace: AiSdlc/CostTracking
        threshold: 0.05
        direction: below
        alarm_name: iteration-cost-breach
        signal: INTRO-006

  step_functions:
    binding: ADR-AB-002
    monitors:
      - metric: ExecutionTime
        namespace: AWS/States
        threshold: 300000  # 5 minutes in ms
        direction: below
        alarm_name: iterate-execution-time-breach
        signal: INTRO-007
      - metric: ExecutionsFailed
        namespace: AWS/States
        threshold: 1
        direction: below  # healthy when below 1
        alarm_name: iterate-failure-breach
        signal: INTRO-007

  lambda_evaluators:
    binding: ADR-AB-002
    monitors:
      - metric: Duration
        namespace: AWS/Lambda
        threshold: 10000  # 10 seconds in ms
        direction: below
        alarm_name: evaluator-duration-breach
        signal: INTRO-004
      - metric: Throttles
        namespace: AWS/Lambda
        threshold: 0
        direction: equal
        alarm_name: evaluator-throttle-breach
        signal: INTRO-004

  dynamodb:
    binding: ADR-AB-005
    monitors:
      - metric: ThrottledRequests
        namespace: AWS/DynamoDB
        threshold: 10  # per 5-minute period
        direction: below
        alarm_name: dynamodb-throttle-breach
        signal: INTRO-002
      - metric: SystemErrors
        namespace: AWS/DynamoDB
        threshold: 0
        direction: equal
        alarm_name: dynamodb-error-breach
        signal: INTRO-002

  knowledge_base:
    binding: ADR-AB-003
    monitors:
      - metric: custom/RetrievalLatencyMs
        namespace: AiSdlc/Context
        threshold: 2000  # 2 seconds
        direction: below
        alarm_name: retrieval-latency-breach
        signal: INTRO-003
```

### Breach -> Intent Pipeline

When a CloudWatch Alarm fires, the standard IntentEngine pipeline engages:

```
CloudWatch Metric crosses threshold
    -> CloudWatch Alarm transitions to ALARM state
    -> EventBridge rule matches alarm state change
    -> Lambda sensory triage function invoked
    -> Affect triage classifies severity:
        Zero (reflex):     Log degradation, auto-tune threshold
        Bounded (affect):  Generate optimization intent -- "reduce iteration latency"
        Persistent (escalate): Propose technology rebinding -- "switch to Express Workflow"
    -> Optimization intent enters graph as new feature vector
```

The key insight: **a persistent escalation at the tolerance level means the binding decision itself should be revisited**. The ADR that made the choice becomes the target of a new design iteration. The methodology does not just maintain the system — it evolves the design.

### Examples of Tolerance-Driven Optimization

| Binding | Tolerance | Breach Signal | Generated Intent |
|:--------|:----------|:--------------|:-----------------|
| Bedrock Converse (ADR-AB-001) | Cost < $0.05/iteration | Token pricing spike | "Evaluate smaller model for this edge" |
| Step Functions (ADR-AB-002) | Iterate latency < 30s | Cold start + complex edge | "Pre-warm Lambda, use Express workflow" |
| Lambda evaluators (ADR-AB-002) | Duration < 10s | Large test suite | "Parallelise test execution" |
| Knowledge Base (ADR-AB-003) | Retrieval latency < 2s | Large corpus | "Tune chunk size, add metadata filtering" |
| DynamoDB (ADR-AB-005) | Throttle rate < 1% | Hot partition | "Enable adaptive capacity, review key design" |
| EventBridge monitors (ADR-AB-006) | Lambda error rate < 1% | Monitor function bug | "Fix monitor, add integration test" |
| API Gateway (ADR-AB-004) | Review response < 24h | Reviewer backlog | "Add notification escalation, reduce review scope" |
| CDK deployment (ADR-AB-007) | Deploy time < 10 min | Stack growth | "Split stacks, use nested stacks or CDK pipelines" |

### Relationship to Graph Discovery (SS4.6.8)

Design tolerances connect directly to graph discovery. When the IntentEngine's escalation signal suggests the graph is too coarse (SS4.6.8), the new edges it generates have their own tolerances. If those edges consistently breach tolerances (too slow, too expensive, too complex), the graph discovery process receives negative feedback — the topology should be simplified, not grown.

This creates a **bidirectional pressure**:
- **Escalation pressure** (SS4.6.8): persistent ambiguity -> graph needs more edges
- **Tolerance pressure** (this ADR): tolerance breaches -> graph needs fewer/simpler edges

The equilibrium between these pressures is the optimal graph topology for the current ecosystem.

### CloudWatch Dashboard Integration

Tolerance metrics are surfaced in a CloudWatch Dashboard deployed by CDK:

```
+--------------------------------------------------------------+
|  AI SDLC TOLERANCE DASHBOARD                                  |
|                                                               |
|  Bedrock Costs     Step Functions     Lambda Evaluators       |
|  [GRAPH]           [GRAPH]            [GRAPH]                 |
|  $0.03/iter        22s avg            6.2s avg                |
|  Threshold: $0.05  Threshold: 30s     Threshold: 10s          |
|  Status: OK        Status: OK         Status: OK              |
|                                                               |
|  DynamoDB           Knowledge Base     Alarms Active: 0       |
|  [GRAPH]            [GRAPH]            Proposals Pending: 0   |
|  0 throttles/5m     1.4s retrieval                            |
|  Threshold: 10      Threshold: 2s                             |
|  Status: OK         Status: OK                                |
+--------------------------------------------------------------+
```

The dashboard provides at-a-glance tolerance health. Developers and operators share the same view. The `gen-status --health` CLI command queries the same CloudWatch metrics.

---

## Rationale

### Why Tolerances Belong in Design, Not Spec

Tolerances are inherently technology-specific:
- "Bedrock Converse cost < $0.05/iteration" is meaningless for a Claude Code implementation using Claude headless
- "Step Functions latency < 30s" is meaningless for a CLI tool where iterate runs in a single process
- "DynamoDB throttle rate < 1%" is meaningless for a file-based event store

The spec says "the sensory system monitors" and "the IntentEngine evaluates ambiguity." Design tolerances fill in the WHAT with HOW MUCH — and HOW MUCH is always ecosystem-dependent.

### Why CloudWatch Alarms (vs Custom Monitoring)

AWS services emit CloudWatch Metrics automatically. No instrumentation code needed for Lambda duration, Step Functions execution time, DynamoDB throttles, or Bedrock invocation latency. CloudWatch Alarms evaluate metrics and transition between OK, ALARM, and INSUFFICIENT_DATA states. Alarm state transitions emit EventBridge events. The sensory service's EventBridge rules already match events (ADR-015, ADR-AB-006). Adding tolerance monitoring is a configuration concern — define alarms in CDK, add EventBridge rules, and the existing triage pipeline handles the rest.

Custom monitoring would duplicate what CloudWatch provides natively, add operational overhead for metric collection and storage, and introduce a second alerting system alongside CloudWatch Alarms.

### Why Tolerances Generate Intents (Not Just Alerts)

An alert is a notification. An intent is a first-class object in the asset graph — it carries REQ keys, spawns feature vectors, converges through edges, and produces auditable artifacts. By generating intents (not alerts), tolerance breaches enter the same pipeline as every other development activity. They are traceable, reviewable, and subject to the same convergence criteria.

### Why This Is Homeostatic

The design evaluates its own fitness. When ecosystem conditions change (new API pricing, model deprecation, increased project scale), the tolerances detect drift and generate corrective intents. The system does not wait for a human to notice degradation — it senses, classifies, and proposes action. The human approves or dismisses (review boundary, ADR-015), preserving the "no autonomous modification" invariant.

---

## Consequences

### Positive

- **Living design** — ADRs evolve from static records to monitored constraints. A tolerance breach on ADR-AB-001 means ADR-AB-001 is due for re-evaluation.
- **Proactive optimization** — tolerance breaches surface before users notice degradation. CloudWatch Alarms detect trends that human operators would miss.
- **Principled technology evolution** — "replace Bedrock model X with model Y" is an intent with traceability, not a Friday afternoon decision.
- **Graph topology feedback** — tolerance pressure balances escalation pressure for optimal graph complexity.
- **Native integration** — CloudWatch Metrics, Alarms, and EventBridge are AWS-managed services. No custom monitoring infrastructure to build or operate.

### Negative

- **Tolerance specification burden** — every ADR should declare tolerances, adding authoring overhead. Mitigated: tolerances are optional; start with the most cost-sensitive and latency-sensitive bindings.
- **Alarm proliferation** — each tolerance needs a CloudWatch Alarm. Mitigated: CDK constructs generate alarms from `design_tolerances.yml`; a single YAML change adds a new alarm. CloudWatch supports up to 5,000 alarms per account.
- **Threshold tuning** — initial tolerance values will be wrong. Mitigated: the IntentEngine's own affect mechanism adjusts urgency based on breach frequency; consistently-breached tolerances auto-escalate. CloudWatch anomaly detection can replace static thresholds for metrics with variable baselines.
- **Cost of monitoring** — CloudWatch Alarms cost $0.10/alarm/month. A project with 20 tolerances costs $2/month for monitoring. Mitigated: negligible compared to Bedrock inference and Lambda compute costs.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) SS4.5 (Sensory Systems), SS4.6 (IntentEngine), SS4.6.8 (Graph Discovery)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) SS4.2 (Sensory Service Strategy)
- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as platform (tolerances on model cost and latency)
- [ADR-AB-002](ADR-AB-002-iterate-engine-step-functions.md) — Step Functions as iterate engine (tolerances on execution time and failure rate)
- [ADR-AB-003](ADR-AB-003-context-management-knowledge-bases.md) — Knowledge Bases for context (tolerances on retrieval latency)
- [ADR-AB-004](ADR-AB-004-human-review-api-gateway-callbacks.md) — API Gateway human review (tolerances on review response time)
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — DynamoDB event sourcing (tolerances on throttle rate and error rate)
- [ADR-AB-006](ADR-AB-006-sensory-service-eventbridge-lambda.md) — Sensory service architecture (monitors that observe tolerance metrics)
- [ADR-AB-007](ADR-AB-007-infrastructure-as-code-cdk.md) — CDK infrastructure (tolerances on deployment time)
- [ADR-AB-008](ADR-AB-008-local-cloud-hybrid-workspace.md) — Hybrid workspace (tolerances on sync latency)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory service technology binding (breach detection pipeline)
