# ADR-GC-018: The Cloud Event Reactor — Stateless Homeostasis

**Status**: Accepted
**Date**: 2026-03-07
**Author**: Gemini
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-ITER-001, REQ-EVENT-001, REQ-SUPV-001
**Supersedes**: [ADR-GC-002: Cloud Workflows as Iterate Engine](ADR-GC-002-cloud-workflows-engine.md)

## Context

Previous designs (ADR-GC-002) proposed using Google Cloud Workflows as the primary orchestration engine for the SDLC graph. This assumed a "managed sequence" model where the state machine logic resided in a central workflow definition. 

Refinement of the formal system primitives (§III, §VII) and alignment with the `imp_claude` reference implementation have revealed that this managed model is redundant. If the Event Log is the single source of truth, then the **Event Log is the Orchestrator**.

## Decision

The methodology engine for `imp_gemini_cloud` is refactored from a "Managed Workflow" to a **Cloud Event Reactor**.

### 1. Fundamental Principle
**The Event Log is the Orchestrator**. The system state is a projection of the `events.jsonl` ledger (or Firestore equivalent). Transitions between edges and iterations within edges are not "managed" by a workflow engine; they are "reactions" to the current state of the ledger.

### 2. The Reactor Trigger Logic
The "metabolism" of the system is driven by a simple reactive pulse:

1. **Trigger**: Firestore `onWrite` (Triggered by any event append to the ledger).
2. **Observation**: A stateless **Cloud Run Job** (The Engine) is instantiated. It reads the full event log for the affected feature vector.
3. **Derivation**: The engine derives the current **Delta (V)** and **Hamiltonian (H)** from the log.
4. **Action**: 
    - If **V > 0**: The engine performs exactly **one stateless iteration pass** (`run_once`).
    - If **V = 0**: The engine checks the trajectory to identify the next edge. If one exists, it emits an `edge_started` event (which will re-fire the pulse).
    - If **all edges converged**: The engine emits `FEATURE_CONVERGED` and exits.

### 3. Separation of Signaling
To resolve the semantic ambiguity identified in previous reviews:
- **Metabolic Pulse**: Driven by any log append. Drives normal progression.
- **`intent_raised`**: Reserved exclusively for **Homeostasis/Escalation**. Triggered by out-of-band observers (e.g., security scanners, telemetry anomalies) when they detect a delta that the normal reactor cannot resolve.

## Consequences

### Positive
- **Serverless Simplicity**: Removes the need for monolithic Cloud Workflow definitions and persistent orchestrator state.
- **Resumability**: If a reactor pass fails (e.g., timeout, crash), the system is naturally stable. The "Intent" (non-zero delta) remains in the log, allowing a retry to be triggered by a human or a scheduled heartbeat.
- **OpenLineage Native**: The orchestration state is identical to the audit trail.

### Negative
- **Cold Start Latency**: Every iteration pass incurs a Cloud Run cold start (partially mitigated by min-instances if cost permits).
- **Infinite Loop Risk**: Requires a "Circuit Breaker" facet in the `iteration_started` event to prevent runaway recursion if delta fails to decrease.

## References
- [ADR-S-012: Event Stream as Formal Model Medium](../../specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md)
- [ADR-S-021: Project Instance Graph](../../specification/adrs/ADR-S-021-project-instance-graph.md)
- [ADR-GC-003: Firestore Event Sourcing](ADR-GC-003-firestore-event-sourcing.md)
