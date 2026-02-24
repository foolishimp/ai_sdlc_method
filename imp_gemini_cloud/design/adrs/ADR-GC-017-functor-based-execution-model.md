# ADR-GC-017: Functor-Based Execution Model — Gemini Cloud Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-SUPV-001, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
**Extends**: ADR-GC-008 (Universal Iterate Agent), ADR-GC-014 (IntentEngine Binding)

---

## Context

The execution model needs a principled way to select between deterministic code, probabilistic agents, and human judgment for each functional unit (evaluate, construct, classify, route, propose, sense). We use the **Functor** model to render these units across three GCP-native categories.

### GCP Service Rendering

- **F_D** (Deterministic): Cloud Run Jobs or Cloud Functions (fast, cheap, unambiguous).
- **F_P** (Probabilistic): Vertex AI Gemini API (model-agnostic, metered, bounded ambiguity).
- **F_H** (Human): API Gateway + Pub/Sub + Cloud Workflows Callbacks (asynchronous, judgmental).

---

## Decision

**Each functional unit has three renderings (F_D, F_P, F_H) mapped to GCP services. Escalation occurs via natural transformations (eta) implemented as Workflow switches and callbacks.**

### The Rendering Table

| Functional Unit | F_D (Cloud Run/Functions) | F_P (Vertex AI Gemini) | F_H (API Gateway + Pub/Sub) |
|:---|:---|:---|:---|
| **Evaluate** | pytest, lint, schema (Run Job) | LLM gap analysis | Human approval callback |
| **Construct** | Template expansion | LLM candidate generation | Human artifact edit |
| **Classify** | Rule-based thresholds | LLM signal triage | Human manual triage |
| **Route** | Topological routing | LLM next-edge selection | Human task choice |
| **Propose** | Template-driven draft | LLM draft intent/diff | Human proposal authoring |
| **Sense** | Cloud Scheduler, Log metrics | LLM anomaly detection | Human observation |
| **Emit** | Firestore append (Always F_D) | -- | -- |
| **Decide** | -- | -- | Human review (Always F_H) |

### Natural Transformation (eta) Implementation

- **eta_D->P**: Cloud Workflows **switch** statement. If a Cloud Run Job returns a "non-zero ambiguity" signal, the workflow branches to a Vertex AI API call.
- **eta_P->H**: Cloud Workflows **callback** endpoint. If Vertex AI determines ambiguity is "persistent", the workflow generates a unique callback URL, publishes to Pub/Sub, and pauses until the human POSTs to the URL.

---

## Rationale

### Mapping Theory to Cloud Service Boundaries
GCP services provide clean boundaries for the functor categories. Cloud Run Jobs (F_D) offer isolated compute, Vertex AI (F_P) offers managed intelligence, and Workflows Callbacks (F_H) manage the asynchronous nature of human judgment.

---

## Consequences

### Positive
- **Cost-Transparency**: F_D is cheap, F_P is moderate, F_H is free compute.
- **Scale-to-Zero**: All selected GCP services are serverless and pay-per-use.
- **Unified Logic**: One workflow definition handles all rendering modes (Headless, Interactive, Autopilot).

### Negative
- **Startup Latency**: Cloud Run Job container cold starts.
- **Conceptual Density**: Developers must understand the functor mapping.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-017](../adrs/ADR-017-functor-based-execution-model.md) — AWS equivalent
