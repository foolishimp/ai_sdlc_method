# ADR-GC-014: IntentEngine Binding — Gemini Cloud Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-SUPV-001
**Extends**: ADR-GC-008 (Universal Iterate Agent)

---

## Context

The IntentEngine is a composition law: `IntentEngine(intent + affect) = observer -> evaluator -> typed_output`. In Gemini Cloud, we need to map this abstract pattern to GCP services and Cloud Workflows control flow.

---

## Decision

**The IntentEngine is realised through Cloud Workflows and Firestore events. No new service code is required.**

### Output Type Mapping

| Spec Output Type | GCP Realisation | Firestore Event |
|:---|:---|:---|
| reflex.log | Workflow continue / Firestore append | `iteration_completed`, `edge_converged` |
| specEventLog | Firestore document update | `affect_triage` (deferred) |
| escalate | Pub/Sub notification + Workflow pause | `intent_raised`, `convergence_escalated` |

### Ambiguity Classification Binding

The three ambiguity regimes map to GCP service boundaries:

| Regime | Evaluator Type | GCP Service |
|:---|:---|:---|
| **Zero** | Deterministic (F_D) | Cloud Run Jobs (isolated containers) |
| **Bounded** | Agent (F_P) | Vertex AI Gemini Pro |
| **Persistent** | Human (F_H) | API Gateway callback + Pub/Sub notification |

---

## Rationale

### Service Boundaries as Classification
Mapping ambiguity to service boundaries ensures cost-effective scaling. Cheap, deterministic checks (Cloud Run) handle the "reflex" phase, while expensive LLM (Vertex) or Human calls are reserved for higher ambiguity.

---

## Consequences

### Positive
- **Explicit Ambiguity Thresholds**: `max_iterations` and `stuck_threshold` in YAML clearly define escalation boundaries.
- **Native GCP Scaling**: Each regime scales according to its service (Run, Vertex, Pub/Sub).

### Negative
- **Distributed State**: Affect state spans Firestore and Workflow variables.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-014](../adrs/ADR-014-intentengine-binding.md) — AWS sibling adaptation
