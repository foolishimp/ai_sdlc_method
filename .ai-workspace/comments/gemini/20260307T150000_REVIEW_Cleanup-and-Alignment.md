# REVIEW: Cleanup and Alignment — Spec, Core, and Downstream

**Author**: Gemini
**Date**: 2026-03-07T15:00:00Z
**Addresses**: `specification/adrs/`, `imp_gemini/`, `imp_gemini_cloud/`, `.ai-workspace/`
**For**: all

## Summary
Completed a surgical cleanup to re-establish the **Spec/Design Separation** and ensure correct downstream alignment. Specification ADRs have been purged of implementation-specific references, and both the Core (`imp_gemini`) and Downstream (`imp_gemini_cloud`) engines have been updated to support the new Hamiltonian metric.

## Cleanup Actions

### 1. Specification Isolation
- **Orphanage Removal**: Purged `ADR-S-019` and `ADR-S-020` of all references to `ADR-022` and `ADR-027` (implementation-tier docs). All references now point to the newly promoted spec-level axioms `ADR-S-021` and `ADR-S-022`.
- **Abstract Observer**: Removed hard-coded filesystem paths to the `genesis_monitor` from the specification. The monitor is now correctly referred to by its functional role as an external observer.

### 2. Core Engine Alignment (`imp_gemini`)
- **Hamiltonian Support**: Updated `IterateEngine.iterate_edge()` in `imp_gemini/gemini_cli/engine/iterate.py` to emit the `iteration` count in the `iteration_completed` event. This enables the external observer to compute $H = T + V$ directly from the event stream without additional state.

### 3. Downstream Tenant Alignment (`imp_gemini_cloud`)
- **Downstream Parity**: Applied the same `iteration` event update to `CloudIterateEngine` in `imp_gemini_cloud/gemini_cloud/engine/iterate.py`.
- **Mandate Enforcement**: Verified that `imp_gemini_cloud` implementation is downstream of the core engine's logic while maintaining its GCP-native specializations (Firestore state, Vertex AI functors).

### 4. Shared System Area (`.ai-workspace`)
- **State Integrity**: Verified that the event stream remains the single source of truth for the **Instance Graph** (ADR-S-021). The `events.jsonl` ledger now carries all necessary data to reconstruct the Hamiltonian phase-space trajectory.

## Recommended Action
1. **Interactive Verification**: User to verify that `gen-status` or the monitor correctly reflects the iteration count in the event ledger.
2. **H-Metric Observation**: Observe the `-dH/dt` slope during the next active iteration to validate the "Unit-Efficient" ($dH/dt = 0$) diagnostic pattern.
