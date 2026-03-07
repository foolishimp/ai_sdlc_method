# STRATEGY: Event-Driven Adhoc Assembly (Homeostatic Reactor)

**Author**: Gemini
**Date**: 2026-03-07T15:45:00Z
**Addresses**: `imp_gemini_cloud/`, `ADR-S-012` (Event Stream), `ADR-S-019` (Markov Blankets)
**For**: all

## Summary
Proposed shift from "Workflow Orchestration" to "Event-Driven Assembly." In this model, the methodology engine is a stateless reactor that triggers **Recursive Actors** in response to **Intent Events** (non-zero deltas). This aligns with the Homeostasis principle (§VI of the bootloader) and is the preferred architecture for `imp_gemini_cloud`.

## The Shift

| Feature | Workflow Model (Legacy) | Event-Driven Assembly (Target) |
| :--- | :--- | :--- |
| **State** | In-memory workflow status | The append-only Event Ledger |
| **Trigger** | Next step in a sequence | Computed Intent (Delta ≠ 0) |
| **Actor Role** | Task executor | Recursive "Ribosome" (Constructor) |
| **Recovery** | Workflow retry logic | Signal persistence (Intent remains until resolved) |

## Core Logic: The Assembly Loop

Instead of a sequential loop, the "Engine" becomes a set of reactive triggers:

1. **Observer**: Constantly monitors the state (Filesystem/Firestore) vs. the Spec.
2. **Evaluator**: If a gap is detected, it emits an `intent_raised` event (The Signal).
3. **Dispatcher**: A cloud-native trigger (e.g., Pub/Sub to Cloud Run) reacts to the `intent_raised` event by instantiating a **Recursive Actor**.
4. **Actor**: Receives the Intent, performs adhoc assembly/fixes, and emits a `COMPLETE` event.
5. **Homeostasis**: The `COMPLETE` event triggers a re-observation. If Delta = 0, the feature moves to the next edge in the fixed vector.

## Advantages for Cloud-Native (`imp_gemini_cloud`)
- **Serverless**: No persistent orchestrator nodes (Prefect/Engine) are required.
- **Atomic Billing**: You pay only for the compute time of the actor reacting to a specific event.
- **Traceability**: The entire "Adhoc Assembly" history is recorded as a causal chain of events in the ledger.

## Recommended Action
1. **Cloud Events**: Implement `intent_raised` as a first-class event type in `imp_gemini_cloud`.
2. **Stateless Dispatch**: Replace the linear loop in `CloudIterateEngine` with an event-handler pattern.
3. **Actor Isolation**: Ensure the `VertexFunctor` is invoked as a stateless transaction that returns its results to the event store.
