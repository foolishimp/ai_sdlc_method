# ADR-GC-002: Cloud Workflows as Iterate Engine

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-ITER-001, REQ-ITER-002
**Extends**: ADR-GC-001 (Vertex AI Platform)

---

## Context

The universal iterate function `iterate(Asset, Context[], Evaluators)` must be executed in a managed, scalable, and observable cloud environment. In CLI implementations, this is a linear loop in memory. In GCP, we need a serverless orchestration primitive that can handle HTTP callbacks (for human review) and long-running construction tasks.

### Options Considered

1. **Cloud Functions Chaining**: A series of functions calling each other. Hard to observe state and manage retries.
2. **Cloud Workflows (The Decision)**: A managed orchestration service using YAML/JSON. Native support for HTTP callbacks, retries, and parallel execution.
3. **Temporal on GKE**: Powerful but high operational overhead for a serverless design intent.

---

## Decision

**We use Cloud Workflows to implement the iterate engine and graph edge orchestration.**

The Cloud Workflows definition will:
1. **Resolve Edge Configuration**: Fetch YAML edge params from GCS.
2. **Load Context**: Invoke Vertex AI Search for RAG context.
3. **Invoke Constructor**: Call Vertex AI Gemini API for candidate generation.
4. **Run Evaluators**: Execute Cloud Run Jobs (F_D) and Vertex AI (F_P).
5. **Manage State**: Record events and feature updates in Firestore.
6. **Handle Human Review**: Pause execution using the "Callback" feature of Cloud Workflows, resuming only when an authorized HTTP POST is received via API Gateway.

---

## Rationale

### Native Serverless Integration
Cloud Workflows integrates natively with Cloud Run, Cloud Functions, and Vertex AI. It is pay-per-execution, aligning with the cloud-native design intent. Its ability to wait for callbacks (for days or weeks) makes it the ideal primitive for human-in-the-loop SDLC edges.

---

## Consequences

### Positive
- **Observability**: Execution history is preserved in the GCP Console.
- **Durability**: Workflow state is managed by GCP; resumes automatically after human review.
- **Cost**: Pay-per-step pricing is extremely efficient for SDLC workflows.

### Negative
- **DSL Learning Curve**: YAML-based workflow definitions require specific knowledge of Workflows syntax.
- **Payload Limits**: Individual workflow variables are limited in size (similar to AWS Step Functions).

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-002](../../imp_bedrock/design/adrs/ADR-AB-002-iterate-engine-step-functions.md) — AWS Step Functions equivalent
