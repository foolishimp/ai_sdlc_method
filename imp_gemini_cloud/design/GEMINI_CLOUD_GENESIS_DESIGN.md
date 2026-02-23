# AI SDLC — Gemini Cloud Genesis Implementation Design (v1.0)

**Version**: 1.0.0
**Date**: 2026-02-23
**Derived From**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.8.0)
**Reference Implementation**: [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md)
**Platform**: Google Cloud Platform (Vertex AI + Cloud Native)

---

## Design Intent

This document defines the |design> asset for a Google Cloud-specific Genesis binding. It is a sibling implementation to Claude (CLI), Gemini (CLI), and Bedrock (AWS Cloud) bindings.

Primary objective: preserve methodology semantics and feature coverage while mapping execution to cloud-native GCP primitives (Vertex AI, Cloud Workflows, Cloud Run, Firestore, Eventarc, Cloud Storage, Terraform).

**Unique Value**: This implementation leverages **Vertex AI's** integrated model garden and **Cloud Workflows** for orchestration, providing a serverless, event-driven implementation of the Asset Graph Model.

Core objectives:

1. **Reference parity**: Maintain feature-level compatibility with Claude v2.8 design.
2. **GCP-native binding**: Map iterate/evaluator/context/tooling to GCP managed services.
3. **Hybrid workspace**: Support both local `.ai-workspace/` and cloud-backed state.
4. **Spec-first control**: Disambiguation via intent/spec/design layers.

---

## 1. Architecture Overview

### 1.1 Three Layers (GCP Mapping)

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer / CI/CD)                    │
│     gcloud CLI / API Gateway / Console / CI/CD webhook             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                           │
│   API Gateway + Cloud Functions + Cloud Workflows                  │
│   (init / start / iterate / review / status / restore / trace)     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ENGINE LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Asset Graph Engine                        │   │
│  │  - graph_topology.yml + edge params (GCS / local)           │   │
│  │  - universal iterate as Cloud Workflows definition           │   │
│  │  - evaluator execution (Cloud Run / Vertex AI / Functions)   │   │
│  │  - event emission + derived projections                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  GCP primitives used:                                               │
│  - Vertex AI (Gemini Pro) — LLM construction + evaluation          │
│  - Cloud Workflows — iterate workflow, edge orchestration           │
│  - Cloud Run Jobs — deterministic evaluators (pytest containers)    │
│  - Cloud Functions — routing, event processing, light logic         │
│  - Firestore — event store, feature vector state, claim tracking    │
│  - Eventarc — sensory service scheduling, signal routing            │
│  - Cloud Storage (GCS) — config store, artifact storage             │
│  - API Gateway — human review callbacks, CLI entry point            │
│  - Pub/Sub — notification delivery for human review                 │
│  - Vertex AI Search — RAG context for spec/ADR retrieval            │
│  - Terraform — infrastructure-as-code deployment                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKSPACE LAYER                            │
│  LOCAL: .ai-workspace/                                              │
│  ├── specification/     Shared tech-agnostic specification (REQ)    │
│  ├── events/            Local event cache (sync from Firestore)     │
│  ├── features/          Local feature vector cache                  │
│  ├── gcp/               Design-specific tenant                      │
│  │   ├── standards/     GCP-specific conventions                    │
│  │   ├── adrs/          GCP design decisions                        │
│  │   ├── data_models/   GCP runtime schemas                         │
│  │   ├── context_manifest.yml                                       │
│  │   └── project_constraints.yml                                    │
│  ├── tasks/             Active/completed tasks                      │
│  └── snapshots/         Immutable checkpoints                        │
│                                                                     │
│  CLOUD: GCS bucket + Firestore collections                          │
│  ├── gs://project-bucket/config/    Graph topology + edge params    │
│  ├── gs://project-bucket/artifacts/ Generated assets per edge       │
│  ├── firestore://events            Canonical event store            │
│  ├── firestore://features          Feature vector state             │
│  └── firestore://claims            Multi-agent coordination         │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Binding Map

| Concept | Claude Reference | Gemini Cloud Genesis |
| :--- | :--- | :--- |
| Iterate engine | `gen-iterate.md` agent | Cloud Workflows state machine; Vertex AI Gemini for construction |
| Commands | `/gen-*` slash commands | API Gateway endpoints + gcloud wrapper; Cloud Functions route to Workflows |
| Context | `.ai-workspace/context/*` | Vertex AI Search (RAG) + GCS config reads |
| Deterministic evaluators | Tests/linters | Cloud Run Jobs (containerised pytest/lint) |
| Human review | `/gen-review` command | API Gateway callback + Pub/Sub + Workflow callback |
| Event log | `events.jsonl` | Firestore `events` collection |
| Multi-agent coordination | Inbox + serialiser | Firestore transactions/conditional writes |

### 1.3 Universal Iterate Orchestration (Cloud Workflows)

The iterate operation is a **Cloud Workflows** definition:

```text
┌──────────────────────────────────────────────────────────────────┐
│                 ITERATE WORKFLOW (per edge)                      │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐  │
│  │ Load Config  │───▶│ Load Context│───▶│ Construct Candidate  │  │
│  │ (GCS/local)  │    │ (Vertex/GCS)│    │ (Vertex AI Gemini)   │  │
│  └─────────────┘    └─────────────┘    └──────────┬───────────┘  │
│                                                    │              │
│                                                    ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │ Emit Events  │◀──│ Convergence  │◀──│ Evaluator Chain      │  │
│  │ (Firestore)  │   │ Check        │   │ RunJob(F_D)→         │  │
│  └──────┬───────┘   └──────┬───────┘   │ Vertex(F_P)→         │  │
│         │                  │            │ PubSub(F_H)          │  │
│         ▼                  ▼            └──────────────────────┘  │
│  ┌──────────────┐   ┌──────────────┐                             │
│  │ Update State │   │ Converged?   │──Yes──▶ Promote + Exit      │
│  │ (Firestore)  │   │              │                             │
│  └──────────────┘   └──────┬───────┘                             │
│                        No  │                                      │
│                            ▼                                      │
│                     Loop / Escalate                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Design

### 2.1 Asset Graph Engine (REQ-F-ENGINE-001)

- Topology: `gs://project-bucket/config/graph_topology.yml`
- Edge Params: `gs://project-bucket/config/edges/*.yml`
- Model: Vertex AI Gemini Pro (via `https://us-central1-aiplatform.googleapis.com`)

### 2.2 Evaluator Framework (REQ-F-EVAL-001)

| Evaluator Type | GCP Service | Characteristics |
|:---|:---|:---|
| **Deterministic (F_D)** | Cloud Run Jobs | Pytest/lint in isolated containers. Pay-per-use, no timeout issues. |
| **Probabilistic (F_P)** | Vertex AI | Coherence checks via Gemini. |
| **Human (F_H)** | API Gateway + Pub/Sub | Approval via callback URL. Workflow pauses using callback mechanism. |

### 2.3 Context Management (REQ-F-CTX-001)

1. **Vertex AI Search**: RAG for Spec/ADRs.
2. **GCS**: Direct config reads.

### 2.4 Feature Vector Traceability (REQ-F-TRACE-001)

- Feature vectors stored in **Firestore** (`features` collection).
- Traceability projections built from Firestore event stream.

### 2.5 Edge Parameterisations (REQ-F-EDGE-001)

Standard edges (TDD, BDD, ADR) implemented via Cloud Workflows steps invoking Cloud Run Jobs (for test execution) and Vertex AI (for code generation).

### 2.6 Developer Tooling (REQ-F-TOOL-001)

**CLI**: A python wrapper around `requests` hitting the API Gateway.
**API**: REST endpoints for `start`, `status`, `iterate`.

---

## 3. Feature Alignment

Aligned with Claude v2.8 (11/11 feature vectors).

---

## 4. Lifecycle & Sensing

### 4.1 Lifecycle Closure

- **Phase 1**: Step Functions -> Cloud Workflows.
- **Phase 2**: Cloud Build -> Eventarc -> Sensory Service.

### 4.2 Sensory Service Strategy

**Serverless/Event-Driven**:
1. **Cloud Scheduler**: Cron jobs for monitors.
2. **Eventarc**: Routes signals (Cloud Build logs, Scheduler ticks) to...
3. **Cloud Functions**: The monitors (Interoceptive/Exteroceptive).
4. **Vertex AI**: Affect triage.
5. **Firestore**: Proposal storage.

### 4.3 UX Layer

- `/gen-start` -> `POST /api/start`
- `/gen-status` -> `GET /api/status`

### 4.4 Multi-Agent Coordination

**Firestore Transactions**:
- Claims: `transaction.get(claim_ref); if !exists: transaction.set(claim_ref)`
- Events: Append-only collection.

---

## 5. Cloud-Native Differentiation

### 5.1 Cost Model

- **Vertex AI**: Per-character/image.
- **Cloud Workflows**: Per-step execution (very cheap).
- **Cloud Run Jobs**: Per-second compute (no idle cost).
- **Firestore**: Read/write ops.

### 5.2 Observability

- **Cloud Trace**: Distributed tracing for Workflows -> Functions -> Vertex.
- **Cloud Logging**: Centralised logs.
- **Cloud Monitoring**: Metrics and Dashboards.

### 5.3 Security

- **IAM**: Service accounts for Workflows/Functions.
- **Secret Manager**: API keys (though Vertex uses IAM).
- **VPC Service Controls**: Network isolation.

---

## 6. Implementation Roadmap

- **Phase 1a**: Terraform module for core services (Workflows, Firestore, GCS, Artifact Registry).
- **Phase 1b**: Cloud Workflows iterate engine + Vertex AI integration.
- **Phase 2a**: Human review (Pub/Sub + callbacks).
- **Phase 2b**: Sensory service (Eventarc).

---

## 7. ADR Set

### Platform-Specific ADRs

- [ADR-GC-001-vertex-ai-platform.md](adrs/ADR-GC-001-vertex-ai-platform.md)
- [ADR-GC-002-cloud-workflows-engine.md](adrs/ADR-GC-002-cloud-workflows-engine.md)
- [ADR-GC-003-firestore-event-sourcing.md](adrs/ADR-GC-003-firestore-event-sourcing.md)
- [ADR-GC-004-cloud-run-evaluators.md](adrs/ADR-GC-004-cloud-run-evaluators.md)
- [ADR-GC-005-terraform-iac.md](adrs/ADR-GC-005-terraform-iac.md)

### Shared ADRs

- [ADR-008-universal-iterate-agent.md](adrs/ADR-008-universal-iterate-agent.md)
- ... (Standard set)

---

## References

- [BEDROCK_GENESIS_DESIGN.md](../../imp_bedrock/design/BEDROCK_GENESIS_DESIGN.md)
- [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md)

### Multi-tenant Observability

See [ADR-GC-006](adrs/ADR-GC-006-multi-tenant-observability.md) for the detailed design of the shared telemetry layer. This module provides:
1. **Isolation**: Firestore root collections keyed by tenant.
2. **Aggregability**: BigQuery sync for cross-project analysis.
3. **Consistency**: Enforced event schema across all tenants.

### OpenAPI Surface

See [openapi.yaml](api/openapi.yaml) and [ADR-GC-009](adrs/ADR-GC-009-openapi-interface.md) for the formal API contract. This allows browser-based Gemini to execute methodology verbs directly via tool-calling.
