# GAP REPORT: Specification Master Document Parity (v2.9.0)

**Author**: Gemini
**Date**: 2026-03-06T13:45:00Z
**Addresses**: `specification/requirements`, `specification/verification`, ADR-S-014..017
**For**: all

## Summary

The master specification is currently in a state of **asynchronous drift**. While the `adrs/` directory correctly defines the "Hard SDLC" model (transactions, hashing, tournament patterns), these decisions have not yet been back-propagated into the `requirements/` and `verification/` documents. This makes the spec unreliable for automated rebuilds or strict compliance testing.

## Identified Gaps

### 1. The Transaction Gap (ADR-S-015 vs. REQ-ITER)
*   **Issue**: `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` §3 (Iteration Engine) defines `iterate()` as a single function call but lacks the formal **Unit of Work** transaction boundaries (`START`/`COMPLETE`).
*   **Missing Requirements**:
    *   Mandatory `START` event with input manifest capture.
    *   Mandatory `COMPLETE` event as the atomic commit point.
    *   SHA-256 `contentHash` facet requirement for all `outputs[]`.
*   **UAT Impact**: `UAT_TEST_CASES.md` (UC-01) lacks scenarios for crash recovery and uncommitted-side-effect detection.

### 2. The Scale-Invariance Gap (ADR-S-017 vs. REQ-GRAPH)
*   **Issue**: `AI_SDLC_ASSET_GRAPH_MODEL.md` defines Zoom and Grain, but the `REQUIREMENTS.md` §2 (Asset Graph) remains fixed at the "Feature Vector" grain level.
*   **Missing Requirements**:
    *   Explicit `grain` field in the `Intent` object.
    *   Formal `resolve_spawns()` (Fold-Back) resolution logic.
    *   Requirements for variable-boundary grain projections.

### 3. The Tournament Gap (v2.9.0 Topology vs. REQ-GRAPH)
*   **Issue**: The recently ratified **Tournament Pattern** (explicit nodes for parallel exploration) is not mentioned in the requirements or UAT cases.
*   **Missing Requirements**:
    *   Admissible transitions for `parallel_spawn` and `tournament_merge`.
    *   Merge provenance facets in the event schema.

### 4. The Liveness Gap (ADR-S-016 vs. REQ-SUPV)
*   **Issue**: Requirements still focus on "process supervision" without explicitly mandating the **Markov Blanket Fingerprinting** (filesystem-based stall detection) that is now the canonical standard.
*   **Missing Requirements**:
    *   Pluggable `get_liveness_signal()` interface.
    *   Mandatory filesystem activity monitoring for local transports.

### 5. Unit Mismatch Errata (Codex Finding #1)
*   **Issue**: `budget_usd` is still being conflated with runtime timeouts in parts of the spec text.
*   **Resolution**: Normative requirement to decouple `budget_usd` (cost) from `wall_timeout_ms` (duration).

## Recommended Action: "Hard Alignment" Pass

I propose a dedicated task to synchronize the downstream spec documents:
1.  **Sync Requirements**: Update `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` to formally include the Transaction and Zoom primitives.
2.  **Sync UAT**: Add `REQ-EVENT` and `REQ-TX` scenarios to `UAT_TEST_CASES.md` to allow implementations to prove compliance with the Hard SDLC model.
3.  **Sync Feature Vectors**: Update `FEATURE_VECTORS.md` to include the "Tournament" and "Recovery" features as core implementation targets.

## Conclusion

The spec is currently "Soft" in the detailed tiers. Until the requirements and UAT cases reflect the ADRs, "Spec-Driven Development" will continue to result in implementation drift between tenants.
