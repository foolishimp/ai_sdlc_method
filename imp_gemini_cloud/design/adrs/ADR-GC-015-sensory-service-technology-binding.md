# ADR-GC-015: Sensory Service Technology Binding — Gemini Cloud Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003
**Extends**: ADR-GC-014 (IntentEngine Binding)

---

## Context

The Sensory Service provides interoceptive (internal health) and exteroceptive (external ecosystem) monitoring. In Gemini Cloud, we need a serverless, event-driven mechanism to detect signals and feed them into the IntentEngine triage pipeline.

---

## Decision

**We use Eventarc and Cloud Functions to implement the Sensory Service.**

### Implementation Components

1. **Monitors (Cloud Functions)**: Small, stateless functions that run on schedule (Cloud Scheduler) or in response to events (Eventarc).
2. **Signal Router (Eventarc)**: Captures events from Cloud Build, Cloud Storage, and Cloud Logging (e.g., build failures, dependency updates).
3. **Affect Triage (Vertex AI)**: A dedicated Cloud Function that takes signals from Firestore Streams and calls Vertex AI Gemini to classify ambiguity and severity.
4. **Review Boundary (Pub/Sub)**: Escalated signals are pushed to a Pub/Sub topic, which triggers notifications for human review.

### Signal Mapping

| Signal Source | GCP Trigger |
|:---|:---|
| Build Health (INTRO-005) | Eventarc (Cloud Build events) |
| Dependency Freshness (EXTRO-001) | Cloud Scheduler (weekly) |
| Event Freshness (INTRO-001) | Cloud Scheduler (daily) |

---

## Rationale

### Event-Driven Homeostasis
Using Eventarc allows the system to react instantly to failures (like a failed CI build) without polling. This aligns with the "Homeostasis" requirement (REQ-LIFE-003) by closing the loop between construction results and new intent generation.

---

## Consequences

### Positive
- **Reactive Sensing**: Signals are processed the moment they occur.
- **Decoupled Monitors**: Each monitor is an independent Cloud Function.

### Negative
- **Event Volume**: High-frequency signals could trigger excessive Cloud Function invocations (mitigated by rate-limiting in triage).

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-006](../adrs/ADR-AB-006-sensory-service-eventbridge-lambda.md) — AWS equivalent
