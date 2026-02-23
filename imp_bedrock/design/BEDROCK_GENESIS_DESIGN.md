# AI SDLC — Bedrock Genesis Implementation Design (v1.0)

**Version**: 1.0.0
**Date**: 2026-02-23
**Derived From**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.8.0)
**Reference Implementation**: [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md)
**Platform**: AWS Bedrock (cloud-native, API-driven runtime)

---

## Design Intent

This document defines the |design> asset for an AWS Bedrock-specific Genesis binding. It is a sibling implementation to Claude, Gemini, and Codex bindings, with explicit feature alignment to Claude as the reference baseline.

Primary objective: preserve methodology semantics and feature coverage while mapping execution to cloud-native AWS primitives (Bedrock Runtime, Step Functions, Lambda, DynamoDB, EventBridge, S3, CDK).

**What makes Bedrock unique**: This is the first **cloud-native, API-driven** implementation. The three existing implementations (Claude, Gemini, Codex) are developer-machine-first CLI tools. Bedrock Genesis operates as a **serverless, pay-per-invocation** system with infrastructure-as-code deployment, stateless API calls, and cloud-native orchestration.

Core objectives:

1. **Reference parity**: Maintain feature-level compatibility with Claude v2.8 design (all 11 feature vectors).
2. **Cloud-native binding**: Map iterate/evaluator/context/tooling to AWS managed services without changing the Asset Graph model.
3. **Hybrid workspace**: Support both local developer experience (`.ai-workspace/`) and cloud-backed state for team/CI/CD scenarios.
4. **Spec-first control**: Keep disambiguation at intent/spec/design layers; use runtime observability as secondary unblock and validation controls.

---

## 1. Architecture Overview

### 1.1 Three Layers (Bedrock Mapping)

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer / CI/CD)                    │
│     CLI tool / API Gateway / Console / CI/CD webhook               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                           │
│   API Gateway + Lambda router + Step Functions state machines      │
│   (init / start / iterate / review / status / restore / trace)     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ENGINE LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Asset Graph Engine                        │   │
│  │  - graph_topology.yml + edge params (S3 / local)            │   │
│  │  - universal iterate as Step Functions workflow              │   │
│  │  - evaluator execution (Lambda / Bedrock / API Gateway)     │   │
│  │  - event emission + derived projections                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  AWS primitives used:                                               │
│  - Bedrock Runtime (Converse API) — LLM construction + evaluation  │
│  - Step Functions — iterate workflow, edge orchestration            │
│  - Lambda — deterministic evaluators, routing, event processing    │
│  - DynamoDB — event store, feature vector state, claim tracking    │
│  - EventBridge — sensory service scheduling, signal routing        │
│  - S3 — config store, artifact storage, workspace sync             │
│  - API Gateway — human review callbacks, CLI/CI entry point        │
│  - SNS — notification delivery for human review requests           │
│  - Bedrock Knowledge Bases — RAG context for spec/ADR retrieval    │
│  - CDK — infrastructure-as-code deployment                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKSPACE LAYER                            │
│  LOCAL: .ai-workspace/                                              │
│  ├── specification/     Shared tech-agnostic specification (REQ)    │
│  ├── events/            Local event cache (sync from DynamoDB)      │
│  ├── features/          Local feature vector cache                  │
│  ├── bedrock/           Design-specific tenant                      │
│  │   ├── standards/     Bedrock-specific conventions                │
│  │   ├── adrs/          Bedrock design decisions                    │
│  │   ├── data_models/   Bedrock runtime schemas                     │
│  │   ├── context_manifest.yml                                       │
│  │   └── project_constraints.yml                                    │
│  ├── tasks/             Active/completed tasks (derived views)      │
│  └── snapshots/         Immutable checkpoints                        │
│                                                                     │
│  CLOUD: S3 bucket + DynamoDB tables                                 │
│  ├── s3://project-bucket/config/    Graph topology + edge params    │
│  ├── s3://project-bucket/artifacts/ Generated assets per edge       │
│  ├── dynamodb://events             Canonical event store            │
│  ├── dynamodb://features           Feature vector state             │
│  └── dynamodb://claims             Multi-agent coordination         │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Claude-to-Bedrock Binding Map

| Concept | Claude Reference | Bedrock Genesis |
| :--- | :--- | :--- |
| Iterate engine | `gen-iterate.md` universal agent | Step Functions state machine per edge; Bedrock Converse API for construction |
| Commands | `/gen-*` slash commands | API Gateway endpoints + CLI wrapper; Lambda handlers route to Step Functions |
| Context | `.ai-workspace/context/*` | Bedrock Knowledge Bases (RAG) for large context; direct S3 reads for edge configs |
| Deterministic evaluators | Tests/linters/hooks | Lambda functions executing pytest/lint/schema in containerised environments |
| Human review | `/gen-review` command | API Gateway callback URL + SNS notification + Step Functions wait-for-callback |
| Event log | `.ai-workspace/events/events.jsonl` | DynamoDB events table (cloud); local `events.jsonl` via sync (hybrid) |
| Multi-agent coordination | Inbox staging + serialiser | DynamoDB conditional writes for claims; Step Functions for serialisation |

### 1.3 Universal Iterate Orchestration (Bedrock)

Bedrock Genesis keeps the invariant: **one iterate operation, parameterized per edge**.

The iterate operation is implemented as a **Step Functions state machine**:

```text
┌──────────────────────────────────────────────────────────────────┐
│                 ITERATE STATE MACHINE (per edge)                 │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐  │
│  │ Load Config  │───▶│ Load Context│───▶│ Construct Candidate  │  │
│  │ (S3/local)   │    │ (KB/S3)     │    │ (Bedrock Converse)   │  │
│  └─────────────┘    └─────────────┘    └──────────┬───────────┘  │
│                                                    │              │
│                                                    ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │ Emit Events  │◀──│ Convergence  │◀──│ Evaluator Chain      │  │
│  │ (DynamoDB)   │   │ Check        │   │ Lambda(F_D)→         │  │
│  └──────┬───────┘   └──────┬───────┘   │ Bedrock(F_P)→       │  │
│         │                  │            │ APIGw+SNS(F_H)      │  │
│         ▼                  ▼            └──────────────────────┘  │
│  ┌──────────────┐   ┌──────────────┐                             │
│  │ Update State │   │ Converged?   │──Yes──▶ Promote + Exit      │
│  │ (DynamoDB)   │   │              │                             │
│  └──────────────┘   └──────┬───────┘                             │
│                        No  │                                      │
│                            ▼                                      │
│                     Loop / Escalate                               │
└──────────────────────────────────────────────────────────────────┘
```

Iterate flow:

1. Resolve current edge + feature vector from DynamoDB/S3 (`graph_topology.yml`, `edges/*.yml`).
2. Load current asset and effective `Context[]` (Bedrock Knowledge Base for spec/ADR RAG, or direct S3 reads for config).
3. Construct candidate artifact via **Bedrock Converse API** (model-agnostic: Claude, Llama, Mistral, etc.).
4. Execute evaluator chain:
   - **F_D** (deterministic): Lambda functions running pytest/lint/schema in containers.
   - **F_P** (probabilistic): Bedrock InvokeModel for coherence/gap detection.
   - **F_H** (human): API Gateway callback URL + SNS notification + Step Functions `waitForTaskToken`.
5. Emit mandatory side effects to DynamoDB:
   - `iteration_completed` event,
   - feature vector state update,
   - process gaps and signal classification.
6. Promote asset or iterate again until convergence policy is satisfied.

---

## 2. Component Design

### 2.1 Asset Graph Engine (REQ-F-ENGINE-001)

<!-- Implements: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002 -->

Bedrock Genesis uses the same topology and edge parameterization files as Claude to preserve methodology behavior:

- `s3://project-bucket/config/graph_topology.yml` (or local `.ai-workspace/graph/graph_topology.yml`)
- `s3://project-bucket/config/evaluator_defaults.yml`
- `s3://project-bucket/config/edges/*.yml`
- `s3://project-bucket/config/profiles/*.yml`

No edge semantics are hard-coded into the Step Functions workflow. The state machine reads edge configuration dynamically and dispatches to appropriate evaluator Lambda functions.

**Model agnosticism**: Bedrock supports multiple foundation models (Claude, Llama, Mistral, Titan, etc.). The iterate engine uses the Converse API for model-agnostic invocation. Model selection is configured per-edge or per-project, not hard-coded.

### 2.2 Evaluator Framework (REQ-F-EVAL-001)

<!-- Implements: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003 -->

Evaluator types map to AWS service boundaries:

| Evaluator Type | AWS Service | Characteristics |
|:---|:---|:---|
| **Deterministic (F_D)** | Lambda (container image) | pytest, lint, schema checks, static analysis — runs in isolated container, pass/fail |
| **Probabilistic (F_P)** | Bedrock Runtime (Converse API) | Coherence review, gap detection, candidate generation — model-agnostic |
| **Human (F_H)** | API Gateway + SNS + Step Functions callback | Approval request via SNS, callback URL for decision, `waitForTaskToken` pattern |

Convergence remains edge-driven (`human_required`, `max_iterations`, thresholds). Step Functions enforces iteration limits and timeout policies natively.

### 2.3 Context Management and Reproducibility (REQ-F-CTX-001)

<!-- Implements: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004 -->

Two context strategies, selected per use case:

1. **Bedrock Knowledge Bases** (RAG): For large specification/ADR context. S3 data source → automatic chunking → vector store → retrieval at iterate time. Ideal for spec-level queries.
2. **Direct S3/local reads**: For edge configurations, feature vectors, and small deterministic context. Assembled directly into Converse API messages.

- `context_manifest.yml` hash is checked before iteration (stored in DynamoDB or local file).
- S3 object versioning provides content-addressable history.
- Tenant overlays resolved from `s3://project-bucket/config/bedrock/` or local `.ai-workspace/bedrock/`.

### 2.4 Feature Vector Traceability (REQ-F-TRACE-001)

<!-- Implements: REQ-INTENT-001, REQ-INTENT-002, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003 -->

Bedrock Genesis preserves REQ-key lineage:

- Feature vectors in DynamoDB `features` table (or local `.ai-workspace/features/active|completed/*.yml`)
- Structured intent docs under `s3://project-bucket/intents/INT-*.yml`
- Code/test tags:
  - `Implements: REQ-*`
  - `Validates: REQ-*`
- Trace projection generated from DynamoDB event stream + feature records

### 2.5 Edge Parameterisations (REQ-F-EDGE-001)

<!-- Implements: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004 -->

Claude and Bedrock share parameterized edge patterns:

- TDD co-evolution (`code <-> unit_tests`)
- BDD generation (`design -> test_cases/uat_tests`)
- ADR generation (`requirements -> design`)
- Code tagging and REQ-reference validation

Bedrock-specific change is execution surface only (Lambda + Bedrock Converse), not edge semantics. Lambda containers include language-specific test runners; Converse API handles construction across all edges.

### 2.6 Developer Tooling Surface (REQ-F-TOOL-001)

<!-- Implements: REQ-TOOL-001 through REQ-TOOL-010 -->

| Operation | Bedrock Genesis Entry | AWS Implementation | Purpose |
| :--- | :--- | :--- | :--- |
| Initialize workspace | `/gen-init` | Lambda + S3 + DynamoDB setup | Scaffold graph/context/features/events |
| Route next step | `/gen-start` | Lambda router → Step Functions | State-driven edge and feature selection |
| Iterate edge | `/gen-iterate --edge --feature` | Step Functions execution | Execute universal iterate |
| Review artifact | `/gen-review` | API Gateway + SNS callback | Human evaluator boundary |
| Spec-boundary review | `/gen-spec-review` | Lambda + Bedrock Converse | Gradient check for spec transitions |
| Escalation queue | `/gen-escalate` | DynamoDB query + Lambda | Process queued supervisory signals |
| Graph zoom | `/gen-zoom` | Lambda + DynamoDB query | Focused edge-level visibility |
| Status | `/gen-status [--feature] [--health]` | Lambda + DynamoDB query | Project and feature observability |
| Checkpoint | `/gen-checkpoint` | S3 snapshot + DynamoDB marker | Immutable snapshot |
| Trace | `/gen-trace --req` | DynamoDB query + projection | REQ trajectory reconstruction |
| Gaps | `/gen-gaps` | Lambda analysis | Coverage and process gap analysis |
| Release | `/gen-release` | Lambda + S3 manifest | REQ coverage release manifest |
| Spawn | `/gen-spawn` | Lambda + DynamoDB + Step Functions | Create feature/discovery/spike/hotfix vectors |

Entry points:
- **CLI tool**: Thin Python/Node client wrapping API Gateway calls. Local developer experience.
- **API Gateway**: RESTful API for CI/CD integration, webhooks, and programmatic access.
- **Console**: Optional web UI for status dashboards and manual review.

---

## 3. Feature Alignment With Claude Reference

This section is the explicit parity contract.

| Feature Vector | Claude Reference Section | Bedrock Genesis Section | Alignment |
| :--- | :--- | :--- | :--- |
| REQ-F-ENGINE-001 | Claude §2.1 | Bedrock §2.1 | Aligned |
| REQ-F-EVAL-001 | Claude §2.2 | Bedrock §2.2 | Aligned |
| REQ-F-CTX-001 | Claude §2.3 | Bedrock §2.3 | Aligned |
| REQ-F-TRACE-001 | Claude §2.4 | Bedrock §2.4 | Aligned |
| REQ-F-EDGE-001 | Claude §2.5 | Bedrock §2.5 | Aligned |
| REQ-F-TOOL-001 | Claude §2.6 | Bedrock §2.6 | Aligned |
| REQ-F-LIFE-001 | Claude §3 | Bedrock §4 | Aligned |
| REQ-F-SENSE-001 | Claude §1.8 | Bedrock §4.2 | Aligned |
| REQ-F-UX-001 | Claude §1.9 | Bedrock §4.3 | Aligned |
| REQ-F-SUPV-001 | Claude §1.9, §2.6 | Bedrock §2.6, §4.3 | Aligned |
| REQ-F-COORD-001 | Claude §1.10 | Bedrock §4.4 + ADR-013 | Aligned |

**11/11 feature vectors aligned with Claude reference implementation.**

---

## 4. Lifecycle, Sensing, and UX

### 4.1 Lifecycle Closure

<!-- Implements: REQ-LIFE-001 through REQ-LIFE-012 -->

Phase model mirrors Claude with cloud-native advantages:

- **Phase 1**: Development-time consciousness loop. Step Functions iterate workflows, Bedrock Converse for construction, Lambda evaluators, DynamoDB event sourcing. Full `intent_raised` / `spec_modified` protocol.
- **Phase 2**: Production integration. EventBridge rules trigger iterate on CI/CD events (CodePipeline, CodeBuild). CloudWatch metrics feed sensory service. Runtime telemetry via X-Ray traces and CloudWatch Logs.

Cloud-native lifecycle advantage: CI/CD integration is a first-class EventBridge rule, not a bolted-on hook.

### 4.2 Sensory Service Strategy

<!-- Implements: REQ-SENSE-001 through REQ-SENSE-005 -->

Bedrock sensory service is **event-driven and serverless**:

1. **EventBridge Scheduler**: Periodic monitors (cron-based health checks, dependency scans, cost tracking).
2. **Lambda monitors**: Stateless functions triggered by EventBridge rules. Each monitor type is a separate Lambda.
3. **Bedrock Runtime for triage**: Ambiguous signals are classified via Converse API call (affect triage).
4. **DynamoDB proposals table**: Draft proposals stored for human review.
5. **SNS notifications**: Alert delivery when proposals require human attention.

Both modes emit the same event types into DynamoDB events table and preserve the same review boundary: sensors create proposals, humans approve intent creation.

| Monitor Category | AWS Service | Trigger |
|:---|:---|:---|
| Interoceptive (INTRO-001..7) | Lambda | EventBridge Scheduler (cron) |
| Exteroceptive (EXTRO-001..4) | Lambda | EventBridge rule (CloudWatch alarm / external webhook) |
| Affect triage | Lambda + Bedrock Runtime | DynamoDB stream on new signals |
| Proposal review | API Gateway | Human callback |

### 4.3 Two-Command UX Layer

<!-- Implements: REQ-UX-001 through REQ-UX-005 -->

Bedrock Genesis preserves the UX pattern:

- **`/gen-start`** → `POST /api/start` → Lambda router → Step Functions: routing layer.
- **`/gen-status`** → `GET /api/status` → Lambda → DynamoDB query: observability layer.

Progressive disclosure is retained: newcomers use start/status (via CLI or API), power users invoke direct endpoints.

The CLI tool wraps API Gateway calls:
```bash
gen-start                          # Route next action
gen-status                         # Project overview
gen-status --feature REQ-F-AUTH    # Feature detail
gen-iterate --edge code_unit_tests # Direct edge iteration
gen-review --callback-id abc123    # Approve/reject pending review
```

### 4.4 Multi-Agent Coordination

<!-- Implements: REQ-COORD-001 through REQ-COORD-005 -->

DynamoDB provides native cloud coordination:

- **Claims table**: DynamoDB conditional writes replace inbox staging. `PutItem` with `attribute_not_exists(feature#edge)` condition provides atomic claim acquisition.
- **Events table**: Append-only DynamoDB table replaces `events.jsonl`. Stream processing via Lambda for derived projections.
- **Work isolation**: S3 prefix per agent: `s3://project-bucket/agents/<agent_id>/drafts/`.
- **Role-based authority**: `agent_roles.yml` in S3 config, enforced by Lambda evaluator.

Single-agent backward compatibility: Claims table has single entry with `agent_id = "primary"`.

---

## 5. Cloud-Native Differentiation

### 5.1 Cost Model

| Resource | Pricing Model | Optimisation Lever |
|:---|:---|:---|
| Bedrock Runtime | Per-token (input + output) | Model selection per edge; batch inference for bulk operations |
| Step Functions | Per state transition | Minimise states; use Express workflows for fast edges |
| Lambda | Per invocation + duration | Right-size memory; use container images for test runners |
| DynamoDB | Per read/write unit + storage | On-demand capacity; TTL for expired claims |
| S3 | Per request + storage | Intelligent tiering for artifacts; lifecycle policies |
| Knowledge Bases | Per query + vector storage | Cache frequent retrievals; tune chunk size |

### 5.2 Observability Stack

| Capability | AWS Service | What It Covers |
|:---|:---|:---|
| Execution traces | X-Ray | End-to-end iterate workflow visibility |
| Metrics | CloudWatch Metrics | Iteration count, convergence rate, evaluator pass rate |
| Logs | CloudWatch Logs | Lambda output, Step Functions history, Converse API logs |
| Dashboards | CloudWatch Dashboards | Project health, feature progress, cost tracking |
| Alerts | CloudWatch Alarms → EventBridge | Sensory monitor triggers |

### 5.3 Security Model

| Concern | AWS Mechanism |
|:---|:---|
| Authentication | IAM roles for services; Cognito for human users |
| Authorization | IAM policies scoped per project; resource-based policies on S3/DynamoDB |
| Encryption at rest | KMS managed keys for DynamoDB, S3, Bedrock |
| Encryption in transit | TLS everywhere (API Gateway, inter-service) |
| Audit | CloudTrail for all API calls |
| Network isolation | VPC for Lambda (optional); PrivateLink for Bedrock |

---

## 6. Implementation Baseline

### Completed Baseline

1. Design document aligned to v2.8 reference: 13 commands mapped to AWS services, observer agents, evaluator framework, and full config set.
2. Iterate protocol, event schema, and derived projections aligned with central spec and Claude reference semantics.
3. 8 platform-specific ADRs (AB-001 through AB-008) plus 10 shared ADRs adapted for Bedrock context.

### Implementation Roadmap

- **Phase 1a**: CDK stack for core services (Step Functions, Lambda, DynamoDB, S3). CLI tool with init/start/status.
- **Phase 1b**: Iterate engine (Step Functions workflow + Bedrock Converse + Lambda evaluators). Knowledge Base setup.
- **Phase 2a**: Human review flow (API Gateway + SNS + callback). Multi-agent coordination (DynamoDB claims).
- **Phase 2b**: Sensory service (EventBridge + Lambda monitors). Production integration (CodePipeline triggers).

---

## 7. ADR Set (Bedrock Genesis)

### Platform-Specific ADRs

- [ADR-AB-001-bedrock-runtime-as-platform.md](adrs/ADR-AB-001-bedrock-runtime-as-platform.md) — platform binding decision
- [ADR-AB-002-iterate-engine-step-functions.md](adrs/ADR-AB-002-iterate-engine-step-functions.md) — Step Functions as iterate engine
- [ADR-AB-003-context-management-knowledge-bases.md](adrs/ADR-AB-003-context-management-knowledge-bases.md) — context via Knowledge Bases + S3
- [ADR-AB-004-human-review-api-gateway-callbacks.md](adrs/ADR-AB-004-human-review-api-gateway-callbacks.md) — human evaluator via API Gateway callbacks
- [ADR-AB-005-event-sourcing-dynamodb.md](adrs/ADR-AB-005-event-sourcing-dynamodb.md) — DynamoDB event sourcing
- [ADR-AB-006-sensory-service-eventbridge-lambda.md](adrs/ADR-AB-006-sensory-service-eventbridge-lambda.md) — serverless sensory service
- [ADR-AB-007-infrastructure-as-code-cdk.md](adrs/ADR-AB-007-infrastructure-as-code-cdk.md) — CDK deployment strategy
- [ADR-AB-008-local-cloud-hybrid-workspace.md](adrs/ADR-AB-008-local-cloud-hybrid-workspace.md) — hybrid local/cloud workspace

### Shared ADRs (Bedrock Adaptation)

- [ADR-008-universal-iterate-agent.md](adrs/ADR-008-universal-iterate-agent.md) — universal iterate via Step Functions
- [ADR-009-graph-topology-as-configuration.md](adrs/ADR-009-graph-topology-as-configuration.md) — YAML configs in S3
- [ADR-010-spec-reproducibility.md](adrs/ADR-010-spec-reproducibility.md) — content-addressable manifests (S3 versioning)
- [ADR-011-consciousness-loop-at-every-observer.md](adrs/ADR-011-consciousness-loop-at-every-observer.md) — signals at every observer
- [ADR-012-two-command-ux-layer.md](adrs/ADR-012-two-command-ux-layer.md) — CLI + API Gateway entry points
- [ADR-013-multi-agent-coordination.md](adrs/ADR-013-multi-agent-coordination.md) — DynamoDB conditional writes
- [ADR-014-intentengine-binding.md](adrs/ADR-014-intentengine-binding.md) — IntentEngine via Step Functions + edge configs
- [ADR-015-sensory-service-technology-binding.md](adrs/ADR-015-sensory-service-technology-binding.md) — EventBridge + Lambda + Bedrock
- [ADR-016-design-tolerances-as-optimization-triggers.md](adrs/ADR-016-design-tolerances-as-optimization-triggers.md) — CloudWatch-driven tolerances
- [ADR-017-functor-based-execution-model.md](adrs/ADR-017-functor-based-execution-model.md) — functor rendering via Lambda/Bedrock/API Gateway

---

## References

- [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md) — reference implementation
- [CODEX_GENESIS_DESIGN.md](../../imp_codex/design/CODEX_GENESIS_DESIGN.md) — sibling design
- [GEMINI_GENESIS_DESIGN.md](../../imp_gemini/design/GEMINI_GENESIS_DESIGN.md) — sibling design
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — canonical model
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — requirements baseline
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) — feature vectors
