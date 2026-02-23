# ADR-GC-001: Vertex AI as Target Platform

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003
**Supersedes**: ADR-001 (Claude Code as MVP Platform) — for Gemini Cloud implementation

---

## Context

The AI SDLC Asset Graph Model requires a concrete runtime binding. While Claude, Gemini CLI, and Codex are CLI-first, we need a binding that maps the methodology to **Google Cloud Platform (GCP)**. This implementation targets a **cloud-native, serverless, API-driven** execution model.

GCP primitives differ structurally from CLI-first implementations:
- **Stateless Orchestration**: Cloud Workflows replaces persistent conversational loops.
- **Unified Model Management**: Vertex AI provides a managed "Model Garden" (Gemini, Llama, etc.) with consistent safety and governance.
- **Enterprise-Grade State**: Firestore provides real-time, document-oriented state with native ACID transactions.
- **Event-Driven Sensing**: Eventarc and Cloud Functions enable a truly reactive sensory service.

### Options Considered

1. **GKE-based**: Run the methodology as a set of long-running services on Google Kubernetes Engine.
2. **Full Serverless (The Decision)**: Map every concept to GCP managed services (Workflows, Cloud Run Jobs, Firestore, Cloud Storage).
3. **App Engine**: Monolithic deployment of the methodology logic.

---

## Decision

**We adopt the Full Serverless binding: Cloud Workflows for orchestration, Vertex AI for LLM construction/evaluation, Cloud Run Jobs for deterministic evaluators, and Firestore for state.**

Key mappings:

| Methodology Concept | GCP Binding | Rationale |
|:---|:---|:---|
| Iterate engine | Cloud Workflows | Serverless, visual orchestration; native JSON/HTTP support; pay-per-step. |
| Construction / F_P | Vertex AI Gemini Pro | Googles premier model; integrated with Cloud IAM; managed safety. |
| Deterministic (F_D) | Cloud Run Jobs | Isolated containerised execution for pytest/lint; no 60s timeout limits. |
| Human (F_H) | API Gateway + Pub/Sub + Callback | Pause/resume workflows via HTTP callbacks. |
| Event Store | Firestore (`events` collection) | Real-time listeners; ACID transactions for claim integrity. |
| Feature State | Firestore (`features` collection) | Document-level updates; indexable REQ keys. |
| Context (large) | Vertex AI Search | RAG for Spec/ADR retrieval. |
| Infrastructure | Terraform | Industry-standard IaC for GCP. |

---

## Rationale

### Why Cloud Workflows (vs GKE)
Cloud Workflows is designed for stitching together HTTP-based services. The Asset Graph traversal is a sequence of service calls (Vertex -> Run -> Firestore). Workflows manage retries and state transitions with lower overhead and cost than a GKE cluster.

### Why Firestore (vs Cloud SQL)
Firestores document model fits feature vectors and events perfectly. Its "real-time" sync capabilities (Firestore Listeners) allow local CLI tools to provide a responsive "Status" view without constant polling.

---

## Consequences

### Positive
- **Serverless Scaling**: No infrastructure to manage; costs scale to zero when idle.
- **Enterprise Integration**: Native integration with Google Cloud IAM and Cloud Logging.
- **Visual Debugging**: Workflows provide execution history and state visualisation.

### Negative
- **Cold Start Latency**: Initial Cloud Run Job container pulls may add latency.
- **GCP Lock-in**: Binding uses specific GCP YAML/API schemas.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-001](../../imp_bedrock/design/adrs/ADR-AB-001-bedrock-runtime-as-platform.md) — AWS sibling binding
