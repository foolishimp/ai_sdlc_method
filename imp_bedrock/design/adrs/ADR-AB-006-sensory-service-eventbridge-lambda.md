# ADR-AB-006: Sensory Service via EventBridge + Lambda + Bedrock Runtime

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-SENSE-001 (Interoceptive Monitoring), REQ-SENSE-002 (Exteroceptive Monitoring), REQ-SENSE-003 (Affect Triage Pipeline), REQ-SENSE-004 (Sensory System Configuration), REQ-SENSE-005 (Review Boundary)

---

## Context

The specification (§4.5.4) defines the sensory service as a long-running service with five capabilities: workspace watching, monitor scheduling, affect triage, homeostatic response generation, and review boundary exposure. The spec is technology-agnostic — it prescribes WHAT (continuous monitoring, probabilistic triage, human review boundary) without dictating HOW.

The Claude reference implementation (ADR-015) binds the sensory service to an MCP Server for long-running operation, Claude headless for probabilistic triage, and MCP tools for the review boundary. This is natural for a developer-machine CLI tool with persistent process support.

Bedrock Genesis operates in a cloud-native, serverless environment. There is no persistent process to host a long-running MCP server. Instead, AWS provides native primitives for scheduled execution (EventBridge Scheduler), event-driven invocation (EventBridge rules), stateless compute (Lambda), and probabilistic inference (Bedrock Runtime). These map naturally to the sensory service's responsibilities.

The key architectural question: how to achieve "continuous monitoring" in a serverless environment where nothing runs unless triggered.

### Options Considered

1. **Long-running ECS service** — A containerised service running continuously on ECS Fargate. Directly mirrors the MCP server pattern from Claude. However: over-provisioned for periodic health checks (most monitors run every 5-60 minutes), continuous cost regardless of activity, and operational overhead for container management. Contradicts the serverless model established in ADR-AB-001.

2. **Step Functions scheduled workflows** — A Step Functions state machine triggered on a schedule to run all monitors sequentially. However: too heavy per monitor invocation (state machine overhead for a single check), does not support independent scaling of different monitors, and conflates scheduling with execution.

3. **EventBridge Scheduler + Lambda monitors + Bedrock Runtime** — Each monitor is an independent Lambda function. Interoceptive monitors triggered by EventBridge Scheduler (cron). Exteroceptive monitors triggered by EventBridge rules responding to external signals. Affect triage via Lambda reading DynamoDB Streams and forwarding ambiguous signals to Bedrock Converse API.

---

## Decision

**The sensory service is implemented as a composition of EventBridge Scheduler, Lambda monitor functions, and Bedrock Runtime for triage. There is no single "sensory service" process — the service is an emergent property of its constituent serverless components.**

### Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      SENSORY SERVICE (serverless)                    │
│                                                                      │
│  INTEROCEPTIVE MONITORS                                              │
│  ┌───────────────────────────────────────────────────────────┐       │
│  │  EventBridge Scheduler (cron)                              │       │
│  │    │                                                       │       │
│  │    ├── INTRO-001: feature_progress_monitor     (5 min)     │       │
│  │    ├── INTRO-002: convergence_stall_detector   (15 min)    │       │
│  │    ├── INTRO-003: event_log_health_check       (10 min)    │       │
│  │    ├── INTRO-004: context_drift_monitor        (30 min)    │       │
│  │    ├── INTRO-005: evaluator_pass_rate_tracker  (10 min)    │       │
│  │    ├── INTRO-006: claim_staleness_checker      (5 min)     │       │
│  │    └── INTRO-007: cost_budget_monitor          (60 min)    │       │
│  └───────────────────────────────────────────────────────────┘       │
│                                                                      │
│  EXTEROCEPTIVE MONITORS                                              │
│  ┌───────────────────────────────────────────────────────────┐       │
│  │  EventBridge Rules (event-driven)                          │       │
│  │    │                                                       │       │
│  │    ├── EXTRO-001: cicd_pipeline_monitor                    │       │
│  │    │     trigger: CodePipeline state change events          │       │
│  │    ├── EXTRO-002: dependency_vulnerability_scanner         │       │
│  │    │     trigger: EventBridge Scheduler (daily) +           │       │
│  │    │              SNS from Inspector/GuardDuty              │       │
│  │    ├── EXTRO-003: infrastructure_drift_detector            │       │
│  │    │     trigger: CloudWatch Alarm (drift detected)         │       │
│  │    └── EXTRO-004: external_webhook_receiver                │       │
│  │          trigger: API Gateway webhook → EventBridge rule    │       │
│  └───────────────────────────────────────────────────────────┘       │
│                                                                      │
│  AFFECT TRIAGE                                                       │
│  ┌───────────────────────────────────────────────────────────┐       │
│  │  DynamoDB Stream (signals table) → Lambda triage function  │       │
│  │    │                                                       │       │
│  │    ├── Rule-based classification (deterministic)           │       │
│  │    │   threshold breach → direct proposal                  │       │
│  │    │                                                       │       │
│  │    └── Bedrock Converse API (probabilistic)               │       │
│  │        ambiguous signal → LLM classification →             │       │
│  │        {ignore, log, propose_intent, escalate}             │       │
│  └───────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ════════════════ REVIEW BOUNDARY ════════════════════════════       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────┐       │
│  │  DynamoDB proposals table                                  │       │
│  │    + SNS notification → human                              │       │
│  │    + API Gateway endpoint → approve / dismiss              │       │
│  └───────────────────────────────────────────────────────────┘       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Interoceptive Monitors (INTRO-001 through INTRO-007)

Each interoceptive monitor is a Lambda function triggered by an EventBridge Scheduler rule on a cron schedule. The monitor queries internal project state (DynamoDB events table, S3 artifacts, DynamoDB features table) and emits signals to the DynamoDB `signals` table.

| Monitor | Schedule | What It Checks | Signal If |
|:---|:---|:---|:---|
| INTRO-001 | Every 5 min | Feature vector progress (DynamoDB features query) | Progress stalled > threshold |
| INTRO-002 | Every 15 min | Iteration count vs convergence for active edges | Iteration count exceeds max without convergence |
| INTRO-003 | Every 10 min | Event log integrity (gap detection, schema validation) | Missing events, malformed entries |
| INTRO-004 | Every 30 min | Context manifest hash vs current spec/ADR content (S3 versioning) | Context has drifted since last iteration |
| INTRO-005 | Every 10 min | Evaluator pass/fail rates across recent iterations | Pass rate below threshold |
| INTRO-006 | Every 5 min | Active claims in DynamoDB claims table vs TTL | Claims approaching or past expiry |
| INTRO-007 | Every 60 min | Bedrock Runtime token usage, Lambda invocation costs (CloudWatch metrics) | Spend exceeds budget threshold |

Monitor schedules and thresholds are configurable via `sensory_monitors.yml` stored in S3 (`s3://project-bucket/config/sensory_monitors.yml`). Changes to the config trigger CDK redeployment of EventBridge Scheduler rules.

### Exteroceptive Monitors (EXTRO-001 through EXTRO-004)

Exteroceptive monitors are Lambda functions triggered by EventBridge rules that match external signal patterns. They do not poll — they react.

| Monitor | Trigger Source | What It Detects | Signal If |
|:---|:---|:---|:---|
| EXTRO-001 | CodePipeline state change event | CI/CD pipeline failure or success | Pipeline fails for project-related code |
| EXTRO-002 | EventBridge Scheduler (daily) + SNS from Inspector | Dependency vulnerabilities | New CVE affecting project dependencies |
| EXTRO-003 | CloudWatch Alarm (Config rule) | Infrastructure drift from CDK template | Drift detected in deployed stack |
| EXTRO-004 | API Gateway webhook endpoint → EventBridge | External system notifications (GitHub, Jira, etc.) | Webhook payload matches configured patterns |

### Affect Triage Pipeline

When a monitor writes a signal to the DynamoDB `signals` table, a DynamoDB Stream triggers the triage Lambda function:

1. **Rule-based classification (deterministic)**: The triage function loads `affect_triage.yml` from S3 and applies threshold rules. Clear threshold breaches are classified immediately:
   - `ignore` — signal below noise floor, logged but no action.
   - `log` — informational, written to events table as telemetry.
   - `propose_intent` — clear breach, draft proposal generated.
   - `escalate` — severity exceeds automated triage capability.

2. **Probabilistic classification (ambiguous signals)**: Signals that do not match any deterministic rule are forwarded to the **Bedrock Converse API** for classification. The triage prompt includes:
   - The signal payload and source monitor.
   - Current project state (active features, recent events, constraint tolerances from ADR-016).
   - Classification options with examples from `affect_triage.yml`.

   The model returns a structured classification (`ignore | log | propose_intent | escalate`) with reasoning. The classification is logged alongside the original signal.

3. **Proposal generation**: Signals classified as `propose_intent` trigger a second Bedrock Converse API call to generate a draft proposal:
   - Proposed intent type (feature, hotfix, spike, discovery).
   - Affected REQ keys.
   - Recommended action.
   - Source signal chain (which monitor, what data, what classification).

   The draft proposal is written to the DynamoDB `proposals` table. An SNS notification is sent to the project notification topic.

### Proposals Table Schema

```
Table: {project_prefix}-proposals

Primary Key:
  PK: project_id          (String)
  SK: proposal_id          (String, UUID-v7)

Attributes:
  status         (String)   — pending | approved | dismissed
  signal_id      (String)   — originating signal
  monitor_id     (String)   — INTRO-xxx or EXTRO-xxx
  classification (String)   — propose_intent | escalate
  proposal_type  (String)   — intent type (feature, hotfix, spike, discovery)
  affected_reqs  (List)     — REQ keys affected
  reasoning      (String)   — triage reasoning (deterministic rule or LLM output)
  draft_payload  (Map)      — proposed intent body
  created_at     (String)   — ISO-8601 timestamp
  reviewed_at    (String)   — ISO-8601 timestamp (nullable)
  reviewed_by    (String)   — reviewer identity (nullable)
  dismiss_reason (String)   — reason for dismissal (nullable)
```

### Review Boundary

The review boundary is implemented as an API Gateway endpoint:

| Endpoint | Method | Purpose |
|:---|:---|:---|
| `/api/sensory/proposals` | GET | List pending proposals |
| `/api/sensory/proposals/{id}` | GET | Get proposal detail with full signal chain |
| `/api/sensory/proposals/{id}/approve` | POST | Approve proposal — emits `intent_raised` event to DynamoDB events table |
| `/api/sensory/proposals/{id}/dismiss` | POST | Dismiss proposal with reason — logged for triage improvement |
| `/api/sensory/status` | GET | Monitor health: last run times, signal counts, error rates |
| `/api/sensory/config` | GET/PUT | View or update monitor configuration |

The CLI tool wraps these endpoints:

```bash
gen-sensory status                      # Monitor health dashboard
gen-sensory proposals                   # List pending proposals
gen-sensory approve <proposal-id>       # Approve a proposal
gen-sensory dismiss <proposal-id> --reason "false positive"  # Dismiss
```

**Invariant preserved**: The sensory service creates proposals. Only humans (via the review boundary) create intent events. The sensory service never modifies workspace files, emits `intent_raised` events, or creates feature vectors autonomously.

### Model Selection for Triage

The Bedrock Converse API is model-agnostic. Triage model selection is configured in `sensory_monitors.yml`:

```yaml
affect_triage:
  model_id: "anthropic.claude-3-haiku-20240307-v1:0"  # fast, cheap for triage
  max_tokens: 512
  temperature: 0.0  # deterministic classification preferred
  fallback_model_id: "anthropic.claude-3-sonnet-20240229-v1:0"  # escalation path
```

Haiku-class models are preferred for triage (fast, low cost). Sonnet/Opus-class models are available for complex escalation classifications.

---

## Rationale

### Why EventBridge + Lambda (vs ECS or Step Functions)

1. **Truly serverless**: Zero cost when no monitors are firing. An ECS service runs continuously even when no signals need processing — wasteful for a sensory system that checks every 5-60 minutes and may find nothing.

2. **Per-monitor independence**: Each monitor Lambda scales independently. INTRO-001 (progress check, 5 min) has different compute and memory requirements than EXTRO-002 (vulnerability scan, daily). ECS would run all monitors in a single container; Lambda right-sizes per function.

3. **Native scheduling**: EventBridge Scheduler provides cron and rate-based scheduling as a managed service. No application-level scheduler needed. Schedule changes deploy via CDK.

4. **Event-driven exteroception**: EventBridge rules react to CloudWatch alarms, CodePipeline events, and custom events natively. No polling loop needed for external signals.

5. **Composition over monolith**: The sensory service is not a single process but a composition of independent serverless components. This aligns with the AWS Well-Architected principle of "design for failure" — one monitor failing does not affect others.

### Relationship to Spec/Design Boundary

The specification says:
- "long-running service" -> this ADR implements as a composition of scheduled and event-triggered Lambda functions (functionally equivalent: monitors run continuously via EventBridge scheduling)
- "probabilistic agent" -> this ADR binds to Bedrock Converse API (model-agnostic)
- "tool interface" / "service interface" -> this ADR binds to API Gateway endpoints
- "project state view" -> this ADR binds to DynamoDB-backed status queries

Each binding is a design decision. Claude uses MCP Server + Claude headless + MCP tools. Gemini uses a background watcher script. Bedrock uses EventBridge + Lambda + Bedrock Runtime + API Gateway. All implement the same specification.

---

## Consequences

### Positive

- **Truly serverless (zero cost when idle)**: No monitor runs unless its schedule triggers or an event arrives. Projects with low activity incur near-zero sensory service cost.
- **Per-monitor scaling**: Each Lambda function scales independently. A burst of CI/CD events triggers only EXTRO-001; other monitors are unaffected.
- **Native scheduling**: EventBridge Scheduler is a managed service with sub-minute precision, no application-level cron management.
- **Event-driven**: Exteroceptive monitors react to signals rather than polling for them. Latency from signal to triage is seconds, not minutes.
- **Model-agnostic triage**: Bedrock Converse API supports multiple foundation models. Triage model can be changed per-project without code changes.
- **Observable**: Every Lambda invocation, EventBridge trigger, and Bedrock API call is traced via X-Ray, logged to CloudWatch, and metricked automatically.

### Negative

- **Cold starts on monitors**: Lambda cold starts add 100-500ms latency to monitor invocations. Mitigated: monitors are not latency-sensitive (5-60 minute schedules); provisioned concurrency available for critical monitors if needed.
- **Distributed state across DynamoDB tables**: Signals, proposals, events, and features are in separate DynamoDB tables. Mitigated: each table has a clear responsibility; cross-table queries are performed by Lambda functions, not by callers.
- **15-minute Lambda timeout for complex triage**: If a triage classification requires extensive context loading or model reasoning, the 15-minute Lambda timeout applies. Mitigated: triage prompts are concise; Haiku-class models respond in seconds; complex cases can be broken into chained invocations.
- **Operational surface area**: Multiple Lambda functions, EventBridge rules, DynamoDB tables, and API Gateway endpoints to manage. Mitigated: CDK stack defines everything as infrastructure-as-code; deployment is a single `cdk deploy`.
- **No persistent state in monitors**: Lambda functions are stateless — they cannot maintain running averages or trend data across invocations. Mitigated: monitors query DynamoDB for historical data; trend computation is a DynamoDB query, not in-memory state.

---

## References

- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) §4.2 (Sensory Service Strategy)
- [ADR-AB-001-bedrock-runtime-as-platform.md](ADR-AB-001-bedrock-runtime-as-platform.md) — platform binding decision (serverless-first principle)
- [ADR-AB-005-event-sourcing-dynamodb.md](ADR-AB-005-event-sourcing-dynamodb.md) — DynamoDB event store (signals and proposals share the same DynamoDB infrastructure)
- [ADR-015-sensory-service-technology-binding.md](../../../imp_claude/design/adrs/ADR-015-sensory-service-technology-binding.md) — Claude reference: MCP Server + Claude headless + MCP tools
- [ADR-016-design-tolerances-as-optimization-triggers.md](../../../imp_claude/design/adrs/ADR-016-design-tolerances-as-optimization-triggers.md) — constraint tolerances monitored by the sensory service
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5 (Sensory Systems), §4.6 (IntentEngine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §8 (Sensory Service)
