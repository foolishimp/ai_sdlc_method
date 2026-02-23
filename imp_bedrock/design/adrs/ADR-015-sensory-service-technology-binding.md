# ADR-015: Sensory Service Technology Binding — EventBridge + Lambda + Bedrock Runtime

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
**Extends**: ADR-AB-006 (detailed implementation), ADR-008, ADR-011, ADR-014, ADR-016

---

## Context

The specification (SS4.5.4) defines the sensory service as a **long-running service** with five capabilities: workspace watching, monitor scheduling, affect triage, homeostatic response generation, and review boundary exposure. The spec is deliberately technology-agnostic — it says "long-running service", "probabilistic agent", and "tool interface" without prescribing HOW.

This ADR records the Bedrock Genesis implementation's binding of those abstract concepts to concrete AWS platform technologies.

### Why This ADR Exists

These technology bindings were previously embedded in the spec documents (AI_SDLC_ASSET_GRAPH_MODEL.md and AISDLC_IMPLEMENTATION_REQUIREMENTS.md). During spec/design boundary enforcement review, they were correctly identified as design decisions and moved here. The spec now says WHAT (long-running service, probabilistic agent, tool interface); this ADR says HOW for the AWS Bedrock platform.

The Claude reference implementation (ADR-015) binds the sensory service to an MCP Server for long-running operation, Claude headless for probabilistic triage, and MCP tools for the review boundary. This is natural for a developer-machine CLI tool with a persistent process. Bedrock Genesis operates in a cloud-native, serverless environment where there is no persistent process to host a long-running server.

### Options Considered

**For the service runtime:**
1. **EventBridge Scheduler + Lambda functions** — Each monitor is an independent Lambda triggered by EventBridge rules. No single long-running process. The "service" is an emergent property of its serverless components.
2. **ECS Fargate service** — A containerised sensory service running continuously. Mirrors the MCP server pattern from Claude but runs in AWS. Over-provisioned for periodic checks; contradicts the serverless model from ADR-AB-001.
3. **Step Functions scheduled workflow** — A single state machine running all monitors sequentially on a schedule. Too heavy per invocation; does not support independent monitor scaling.

**For probabilistic agent (homeostatic response generation):**
1. **Bedrock Converse API** — Model-agnostic inference via Bedrock Runtime. Supports Claude, Llama, Mistral, Titan without code changes. Triage model selectable per-project.
2. **Direct Anthropic API** — SDK calls to Anthropic's API. Couples triage to a single model provider; loses model-agnostic advantage established in ADR-AB-001.
3. **SageMaker endpoint** — Self-hosted model. Operational overhead for a triage classification task that runs infrequently.

**For the review boundary:**
1. **API Gateway endpoints** — RESTful endpoints for proposal listing, approval, and dismissal. CLI wraps endpoints; web console accesses directly.
2. **SQS queue + polling** — Proposals written to a queue; reviewer polls. No real-time notification; poor ergonomics.
3. **AppSync subscriptions** — GraphQL with real-time push. Over-engineered for a proposal review workflow.

---

## Decision

### Sensory Service: EventBridge Scheduler + Lambda Functions

The sensory service is implemented as a **composition of EventBridge Scheduler rules, Lambda monitor functions, and Bedrock Runtime for triage**. There is no single "sensory service" process. The service is the emergent behaviour of independently deployed serverless components.

```
SENSORY SERVICE (EventBridge + Lambda)
+-- Interoceptive Monitors (Lambda, cron-triggered)
|   +-- INTRO-001: Convergence stall detection (DynamoDB query)
|   +-- INTRO-002: Event log anomaly (DynamoDB query)
|   +-- INTRO-003: Context drift (S3 version check)
|   +-- INTRO-004: Evaluator pass rate (DynamoDB aggregation)
|   +-- INTRO-005: Claim staleness (DynamoDB TTL check)
|   +-- INTRO-006: Cost budget (Cost Explorer API)
|   +-- INTRO-007: Step Functions execution health
|
+-- Exteroceptive Monitors (Lambda, event-triggered)
|   +-- EXTRO-001: CI/CD pipeline state (CodePipeline events)
|   +-- EXTRO-002: Security advisory (Inspector/GuardDuty SNS)
|   +-- EXTRO-003: Dependency changes (CloudWatch alarm)
|   +-- EXTRO-004: External webhook (API Gateway)
|
+-- Affect Triage (Lambda + Bedrock Runtime)
|   +-- Rule-based classification (thresholds)
|   +-- Bedrock Converse API (ambiguous signals)
|
+-- REVIEW BOUNDARY (API Gateway)
    +-- GET  /api/sensory/status        -- monitor health
    +-- GET  /api/sensory/proposals     -- pending proposals
    +-- POST /api/sensory/approve/:id   -- approve proposal
    +-- POST /api/sensory/dismiss/:id   -- dismiss with reason
    +-- GET  /api/sensory/config        -- monitor config
```

**Why EventBridge + Lambda:**
- **Zero cost when idle** — monitors run only when triggered. No compute consumed between scheduled invocations.
- **Per-monitor independence** — each monitor is a separate Lambda with its own memory, timeout, and concurrency configuration. INTRO-001 (convergence stall, 5 min) and INTRO-006 (cost budget, 60 min) scale and fail independently.
- **Native scheduling** — EventBridge Scheduler provides cron and rate-based scheduling as a managed service. No application-level scheduler.
- **Event-driven exteroception** — EventBridge rules react to CodePipeline events, CloudWatch alarms, and custom events natively. No polling loop.
- **Infrastructure-as-code** — monitor schedules, thresholds, and Lambda configurations deploy via CDK (ADR-AB-007). Schedule changes are pull-request-reviewable.

**Configuration:**
- Monitor schedules and thresholds in `sensory_monitors.yml` stored in S3 (`s3://project-bucket/config/sensory_monitors.yml`)
- Affect triage rules in `affect_triage.yml` stored in S3
- Changes to config trigger CDK redeployment of EventBridge Scheduler rules
- Per-project configuration via CDK construct parameters

### Interoceptive Monitors (INTRO-001 through INTRO-007)

Each interoceptive monitor is a Lambda function triggered by an EventBridge Scheduler rule. The monitor queries internal project state and emits signals to the DynamoDB `signals` table.

| Monitor | Schedule | Data Source | Signal Condition |
|:--------|:---------|:------------|:-----------------|
| INTRO-001 | Every 15 min | DynamoDB features table | Iteration count exceeds max without convergence |
| INTRO-002 | Every 10 min | DynamoDB events table | Missing events, malformed entries, gap detection |
| INTRO-003 | Every 30 min | S3 artifact versions | Context manifest hash diverges from current spec/ADR content |
| INTRO-004 | Every 10 min | DynamoDB events table | Evaluator pass rate below threshold across recent iterations |
| INTRO-005 | Every 5 min | DynamoDB claims table | Active claims approaching or past TTL expiry |
| INTRO-006 | Every 60 min | Cost Explorer API + CloudWatch metrics | Bedrock token spend or Lambda invocation cost exceeds budget |
| INTRO-007 | Every 15 min | Step Functions API | Execution failures, timeouts, or stuck state machines |

### Exteroceptive Monitors (EXTRO-001 through EXTRO-004)

Exteroceptive monitors are Lambda functions triggered by EventBridge rules matching external signal patterns. They react rather than poll.

| Monitor | Trigger Source | Detection Target | Signal Condition |
|:--------|:---------------|:-----------------|:-----------------|
| EXTRO-001 | CodePipeline state change event | CI/CD pipeline failure | Pipeline fails for project-related code |
| EXTRO-002 | Inspector/GuardDuty SNS notification | Dependency vulnerabilities | New CVE affecting project dependencies |
| EXTRO-003 | CloudWatch Alarm (Config rule drift) | Infrastructure drift | Deployed stack diverges from CDK template |
| EXTRO-004 | API Gateway webhook -> EventBridge rule | External system notifications | Webhook payload matches configured patterns |

### Probabilistic Agent: Bedrock Converse API

For signals that require probabilistic classification or homeostatic response generation, the sensory service invokes the **Bedrock Converse API** — AWS's model-agnostic inference interface.

**Two invocation points:**

1. **Affect triage (ambiguous signals)** — when rule-based classification is insufficient, a triage Lambda calls Bedrock Converse to classify the signal. This is the IntentEngine's bounded-ambiguity path (ADR-014) applied within the sensory service. The triage prompt includes the signal payload, current project state, and classification options from `affect_triage.yml`.

2. **Draft proposal generation** — for signals that escalate past triage, a second Bedrock Converse call generates draft proposals: proposed intent type, affected REQ keys, recommended action, and source signal chain. These are **drafts only** — the sensory service cannot create intent events.

**Why Bedrock Converse API (vs direct provider API):**
- **Model-agnostic** — triage model selectable per-project. Haiku-class for fast/cheap triage, Sonnet/Opus-class for complex classification. Llama or Mistral available as alternatives.
- **Consistent with platform binding** — same inference interface used by the iterate engine (ADR-AB-002) and evaluators (ADR-AB-001). Single authentication surface (IAM).
- **No additional API keys** — Bedrock access is controlled via IAM roles, not per-model API keys.

**Model selection:**
```yaml
# sensory_monitors.yml
affect_triage:
  model_id: "anthropic.claude-3-haiku-20240307-v1:0"  # fast, cheap for triage
  max_tokens: 512
  temperature: 0.0  # deterministic classification preferred
  fallback_model_id: "anthropic.claude-3-sonnet-20240229-v1:0"  # escalation path
```

**What Bedrock Converse produces (draft only):**
- `draft_intent_raised` — proposed intent with signal source, affected REQ keys, recommended vector type
- `draft_diff` — proposed configuration change (rendered but not applied)
- `draft_spec_modification` — proposed requirement addition or modification

**What Bedrock Converse does NOT do:**
- Modify workspace files or S3 artifacts
- Emit `intent_raised` or `spec_modified` events to the DynamoDB event store
- Create or modify feature vectors
- Approve its own proposals

### Review Boundary: API Gateway Endpoints

The review boundary is implemented as **API Gateway REST endpoints** backed by Lambda functions:

| Endpoint | Method | Purpose | Output |
|:---------|:-------|:--------|:-------|
| `/api/sensory/status` | GET | Monitor health: last run times, signal counts, error rates | Health dashboard JSON |
| `/api/sensory/proposals` | GET | List pending proposals with full signal chain context | Proposal list |
| `/api/sensory/proposals/{id}` | GET | Get proposal detail with triggering signal and triage reasoning | Full proposal |
| `/api/sensory/approve/{id}` | POST | Approve a proposal — emits `intent_raised` event to DynamoDB | Confirmation + event |
| `/api/sensory/dismiss/{id}` | POST | Dismiss a proposal with reason (logged for triage improvement) | Dismissal logged |
| `/api/sensory/config` | GET/PUT | View or update monitor configuration | Current config |

**CLI wrapper:**
```bash
gen-sensory status                      # Monitor health dashboard
gen-sensory proposals                   # List pending proposals
gen-sensory approve <proposal-id>       # Approve a proposal
gen-sensory dismiss <proposal-id> --reason "false positive"  # Dismiss
```

**Review workflow:**
1. SNS notification alerts reviewer of pending proposals (email, Slack, webhook)
2. Reviewer invokes `gen-sensory proposals` (CLI) or hits GET `/api/sensory/proposals` (API)
3. Reviews each proposal: triggering signal, triage classification, proposed action
4. Approves (DynamoDB event emitted, intent enters graph) or dismisses (reason logged for triage learning)

**Why API Gateway (vs file-based inbox):**
- **Stateless** — no persistent process to manage. Each request is an independent Lambda invocation.
- **Multi-channel access** — CLI wraps the API; web console hits it directly; CI/CD pipelines can query programmatically.
- **Auditable** — all approve/dismiss actions emit events to the DynamoDB event store via DynamoDB Streams.
- **Consistent** — same API Gateway infrastructure used by the iterate engine's human review callbacks (ADR-AB-004).

**Invariant preserved**: The sensory service creates proposals. Only humans (via the review boundary) create intent events. The sensory service never modifies workspace files, emits `intent_raised` events autonomously, or creates feature vectors without human approval.

### Project State View Binding

The spec refers to "project state view" (an auto-regenerated derived view of project status). In the Bedrock implementation, this is materialised as a **DynamoDB-backed status query** accessible via the `/api/sensory/status` endpoint and the `gen-status` CLI command. The DynamoDB features table, events table, and Step Functions execution history are the source data; the status view is a computed projection, not a stored file. This differs from Claude's `STATUS.md` (a regenerated markdown file) but satisfies the same invariant: a derived project state view exists and is kept fresh.

---

## Rationale

### Why These Specific Bindings

The sensory service technology choices follow a single principle: **use the platform's native capabilities**. For AWS Bedrock, that means EventBridge for scheduling and event routing, Lambda for stateless compute, Bedrock Runtime for probabilistic inference, DynamoDB for state, and API Gateway for human interaction. A Claude implementation uses MCP + Claude headless + MCP tools. A Gemini implementation uses a background watcher. All implement the same specification — the bindings differ because the platforms differ.

### Why Serverless (vs Long-Running Service)

The Claude MCP Server pattern assumes a persistent process on the developer's machine. Bedrock Genesis has no persistent process. The insight is that "long-running service" in the spec does not mean "single process that runs forever" — it means "capability that is continuously available." EventBridge Scheduler + Lambda provides continuous availability without continuous execution. Monitors fire on schedule, process signals, and terminate. The service is always available (EventBridge rules are always active) without always running.

This is functionally equivalent to the MCP server pattern: monitors execute on schedule, signals are triaged, proposals are generated, the review boundary is exposed. The difference is the execution model — event-driven invocations rather than a persistent process — not the capability.

### Relationship to Spec/Design Boundary

The specification says:
- "long-running service" -> this ADR implements as EventBridge Scheduler + Lambda (continuously available via scheduled triggers)
- "probabilistic agent" -> this ADR binds to Bedrock Converse API (model-agnostic)
- "tool interface" / "service interface" -> this ADR binds to API Gateway REST endpoints
- "project state view" -> this ADR binds to DynamoDB-backed status queries

Each binding is a design decision. Claude uses MCP Server + Claude headless + MCP tools. Gemini uses a background watcher script. Codex uses an MCP Server + Codex Headless variant. Bedrock uses EventBridge + Lambda + Bedrock Runtime + API Gateway. All implement the same specification.

### Relationship to ADR-AB-006

ADR-AB-006 is the platform-specific ADR that establishes EventBridge + Lambda as the sensory service architecture. This ADR (015) is the shared ADR adapted for Bedrock — it maps the specification's abstract concepts (long-running service, probabilistic agent, tool interface) to the concrete AWS bindings and explains the design choices in the context of the methodology's technology-agnostic requirements. ADR-AB-006 provides the detailed DynamoDB table schemas, Lambda configurations, and CDK constructs; this ADR provides the conceptual bridge from spec to design.

---

## Consequences

### Positive

- **Clean spec/design separation** — technology bindings live in this ADR, not in the platform-agnostic spec
- **Zero cost when idle** — monitors execute only when triggered. Projects with low activity incur near-zero sensory service cost.
- **Per-monitor scaling** — each Lambda function scales independently. A burst of CI/CD events triggers only EXTRO-001; other monitors are unaffected.
- **Model-agnostic triage** — Bedrock Converse API supports multiple foundation models. Triage model can be changed per-project without code changes.
- **Native AWS observability** — every Lambda invocation, EventBridge trigger, and Bedrock API call is traced via X-Ray, logged to CloudWatch, and metricked automatically. No custom observability infrastructure needed.
- **Platform portability at spec level** — other implementations read the same spec and make different binding decisions.

### Negative

- **Cold starts on monitors** — Lambda cold starts add 100-500ms latency to monitor invocations. Mitigated: monitors are not latency-sensitive (5-60 minute schedules); provisioned concurrency available for critical monitors if needed.
- **Distributed state** — signals, proposals, events, and features are in separate DynamoDB tables rather than a single in-memory store. Mitigated: each table has a clear responsibility; cross-table queries are performed by Lambda functions, not by callers. DynamoDB Streams connect the tables reactively.
- **No persistent monitor state** — Lambda functions are stateless. Running averages and trend data cannot be maintained in memory across invocations. Mitigated: monitors query DynamoDB for historical data; trend computation is a DynamoDB query, not in-memory state.
- **Operational surface area** — multiple Lambda functions, EventBridge rules, DynamoDB tables, and API Gateway endpoints to manage. Mitigated: CDK stack (ADR-AB-007) defines everything as infrastructure-as-code; deployment is a single `cdk deploy`.
- **Platform lock-in at design level** — this ADR is specific to AWS Bedrock. Other platforms need their own equivalent ADR.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) SS4.5 (Sensory Systems), SS4.6 (IntentEngine)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) SS4.2 (Sensory Service Strategy)
- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — platform binding decision (serverless-first principle)
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — DynamoDB event store (signals and proposals share DynamoDB infrastructure)
- [ADR-AB-006](ADR-AB-006-sensory-service-eventbridge-lambda.md) — detailed sensory service architecture (DynamoDB schemas, Lambda configs, CDK constructs)
- [ADR-008](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (primary consumer of sensory signals)
- [ADR-011](../../imp_claude/design/adrs/ADR-011-consciousness-loop-at-every-observer.md) — Consciousness Loop (signal source classification taxonomy)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (affect triage IS the IntentEngine at sensory level)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance thresholds monitored by sensory service)

---

## Requirements Addressed

- **REQ-SENSE-001**: Interoceptive monitoring — Lambda monitors triggered by EventBridge Scheduler query DynamoDB and S3 for internal project state
- **REQ-SENSE-002**: Exteroceptive monitoring — Lambda monitors triggered by EventBridge rules react to CodePipeline events, Inspector/GuardDuty notifications, CloudWatch alarms, and API Gateway webhooks
- **REQ-SENSE-003**: Affect triage pipeline — DynamoDB Streams trigger triage Lambda; rule-based classification + Bedrock Converse API for ambiguous signals
- **REQ-SENSE-004**: Sensory system configuration — `sensory_monitors.yml` and `affect_triage.yml` in S3, deployed via CDK
- **REQ-SENSE-005**: Review boundary — API Gateway endpoints (`/api/sensory/status`, `/api/sensory/proposals`, `/api/sensory/approve/{id}`, `/api/sensory/dismiss/{id}`, `/api/sensory/config`) with CLI wrapper
