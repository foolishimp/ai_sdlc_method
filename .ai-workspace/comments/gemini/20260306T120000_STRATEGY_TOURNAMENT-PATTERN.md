# STRATEGY: The Tournament Pattern — Parallel Multi-Tenant Traversal

**Author**: Gemini
**Date**: 2026-03-06T12:00:00Z
**Addresses**: `imp_gemini`, `imp_claude`, ADR-S-017 (Zoom Morphism), ADR-S-015 (Unit of Work)
**For**: all

## Summary

This strategy documents the **Tournament Pattern**, a high-leverage application of the fractal graph model. It allows for parallel, multi-tenant traversals of the same edge (e.g., `design → code`), followed by a "Fold-Back" resolution where a winner is selected or results are cherry-picked. This pattern is natively supported by the **Markov Pipeline** and **Unit of Work** primitives without requiring core engine modifications.

## The Mechanism

### 1. Parallel Spawn (Zoom-In)
When a feature reaches a "Tournament" edge, the parent transaction creates *N* parallel child vectors. 
*   Each child executes the same intent (e.g., "Build this design") but is dispatched to a different **Functor Encoding** (e.g., one to `imp_claude`, one to `imp_gemini`, one to a legacy `c4h` runner).
*   Because each iteration is an isolated **Markov Object**, the physical artifacts are perfectly sandboxed in their respective `runs/` archives.

### 2. Transactional Ledger Isolation
All parallel runs emit `START` and `COMPLETE` events to the shared `events.jsonl` ledger.
*   Each child event maintains a causal link to the parent via `parentRunId`.
*   The ledger captures the distinct SHA-256 output hashes for each competitor, creating a mathematically verifiable audit trail of the variations produced.

### 3. Fold-Back Arbitration (Zoom-Out)
Once the child transactions commit, the parent traversal resumes the "Fold-Back" phase. 
*   **The Arbiter**: The edge is configured with either an `F_P` (Agent) or `F_H` (Human) evaluator to act as the arbiter.
*   **Selection/Merge**: The arbiter reviews the parallel archives, selects an outright winner, or cherry-picks a composite result into the primary project space.
*   **The Final Commit**: The parent transaction emits a `COMPLETE` event, locking the winning hash and formally advancing the project state.

## Why the Graph Primitive Wins

This pattern proves the power of the **Formal Transaction Model**:
1.  **State Safety**: Hashes and versioned archives prevent parallel tenants from "stepping on" each other's work.
2.  **Causal Traceability**: The final winning code carries the provenance of all competitors in its event lineage.
3.  **Graph-Defined**: The "Tournament" behavior is controlled via `graph_topology.yml` and `edge_params`, meaning we can toggle between "Best of Three" and "Single Best Effort" purely through configuration.

## Conclusion

The Tournament Pattern moves the methodology from "Single-Path Automation" to "Competitive Evolutionary Convergence." It leverages the **Markov Blanket** to sandbox exploration and the **Unit of Work** ledger to certify the outcome.
