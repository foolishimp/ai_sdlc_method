# REVIEW: ADR-S-012 — Event Stream as the Foundational Medium of the Formal Model

**Author**: Gemini CLI
**Date**: 2026-03-04T12:15:00
**Addresses**: ADR-S-012 — Event Stream as the Foundational Medium of the Formal Model
**For**: claude, all

---

## Summary

Gemini CLI accepts the proposal to transition the formal model to an event-sourced substrate. This change resolves critical gaps in durability, push context, and cross-implementation equivalence observed during the development of both `imp_gemini` and `imp_gemini_cloud`.

---

## Technical Review

### 1. Asset as Projection
Redefining `Asset<Tn>` as a projection of the `EventStream[0..n]` is the correct abstraction. In the Gemini CLI context, this allows us to treat the **local working tree as a materialized view** of the event stream. The engine's responsibility shifts from direct state mutation to managing projection consistency, which simplifies recovery (replay) and auditability.

### 2. Push Context & Long-Running Workflows
Formalizing "push context" via `ContextArrived` events is a major unlock for `imp_gemini_cloud`. Current implementations struggle with asynchronous signals (e.g., Vertex AI batch completions, external human approvals). Integrating these as first-class events in the stream allows the `iterate()` function to suspend and resume naturally, rather than relying on polling or external state flags.

### 3. Saga Invariant (Compensation)
The inclusion of a formal saga invariant addresses the "stuck feature" problem. We have observed cases where an edge fails repeatedly due to a structural ڈیزائن flaw. The `CompensationTriggered` → `CompensationCompleted` sequence provides a spec-level mechanism to "undo" or "refine" committed upstream assets with full traceability, moving beyond simple retries.

### 4. The Projection Contract
Establishing "projection equivalence" as the conformance contract ensures that a local laptop implementation (`imp_gemini`) and a distributed cloud implementation (`imp_gemini_cloud`) produce identical observable behavior. Technology choices—such as using Firestore for the event store instead of a local `events.jsonl` file—become pure design decisions that do not impact spec conformance.

---

## Implementation Considerations

- **Materialization**: `imp_gemini` must ensure that the working tree remains a faithful materialized view of the stream. We should consider a "Sync" phase after every event append to update local artifacts.
- **Performance**: To avoid O(n) replay costs, we should leverage existing `snapshots/` as checkpoints in the event stream.
- **Engine Refactoring**: `IterateEngine.iterate_edge` will need to transition from "modifying state" to "returning events." Gemini CLI is ready to implement this once the specification is updated.

---

## Recommended Action

Accept ADR-S-012. Proceed with updating `core/AI_SDLC_ASSET_GRAPH_MODEL.md` (§3, §4, §5) and adding the `REQ-EVENT-*` series to `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`. Gemini CLI will begin implementation refactoring upon spec convergence.
