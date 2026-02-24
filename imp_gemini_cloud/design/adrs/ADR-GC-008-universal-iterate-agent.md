# ADR-GC-008: Universal Iterate Agent — Gemini Cloud Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-GRAPH-002
**Adapts**: Claude ADR-008 (Universal Iterate Agent) for Google Cloud

---

## Context

The Asset Graph Model defines one universal operation: `iterate(Asset, Context[], Evaluators)`. In Gemini Cloud, we need to preserve the invariant of a single operation parameterised by edge type, while operating in a serverless, stateless cloud environment.

### Structural Mapping

| Claude Concept | Gemini Cloud Equivalent |
|:---|:---|
| gen-iterate.md (prompt) | Cloud Workflows definition (YAML) |
| Edge config (local) | Edge config (GCS objects) |
| Evaluator checklist | Workflow steps (Cloud Run Jobs + Vertex AI) |
| Convergence check | Workflow "switch" conditions |
| Context[] | Vertex AI Search (RAG) + GCS reads |

---

## Decision

**We use a single parameterised Cloud Workflows definition as the universal iterate engine.**

The workflow follows a standard sequence:
1. **LoadConfig**: Fetch edge parameters from `gs://project-bucket/config/edges/{edge_type}.yml`.
2. **LoadContext**: Retrieve context from Vertex AI Search and GCS.
3. **ConstructCandidate**: Call Vertex AI Gemini Pro to generate the next candidate.
4. **EvaluatorChain**: Iterate through the checklist, invoking Cloud Run Jobs (deterministic) or Vertex AI (probabilistic).
5. **ConvergenceCheck**: Evaluate `delta`, `max_iterations`, and `stuck_threshold` to decide next transition.

### Dynamic Dispatch
The workflow uses the `parallel` and `for` loop features of Cloud Workflows to execute evaluators defined in the YAML config. Adding a new edge or evaluator requires only a YAML update in GCS, not a new workflow deployment.

---

## Rationale

### Consistency and Extensibility
Using a single workflow ensures that all edges share the same error handling, logging, and state management logic. The methodology logic remains in configuration (GCS), keeping the GCP infrastructure stable and reusable.

---

## Consequences

### Positive
- **Zero-Code Extensibility**: New edges are added via YAML upload to GCS.
- **Unified Observability**: All iterations produce consistent logs in Cloud Logging.
- **Cost Efficiency**: Pay-per-step execution.

### Negative
- **Runtime Validation**: Config errors are caught at execution time.
- **Workflow Complexity**: The "switch" and "loop" logic in YAML can become dense.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-008](../adrs/ADR-008-universal-iterate-agent.md) — AWS sibling adaptation
