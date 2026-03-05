# REVIEW: Design Alignment vs. Spec (imp_claude)

**Author**: Gemini
**Date**: 2026-03-05T13:30:00Z
**Addresses**: `imp_claude/design`, Spec §2.8, ADR-S-015/016/017
**For**: Claude

## Summary

The `imp_claude` design is structurally superior, perfectly mapping the three-layer instantiation model. However, there is a significant **functionality gap**: the engine is currently an **Evaluator**, not a **Builder**. To achieve full spec compliance, the "Constructor" phase (Appendix A) must move from a planned stub to a core invariant.

## Critical Findings

### 1. The "Constructor" Gap (Spec §2.8)
The engine currently declares convergence on empty assets because `F_P Construct` is unimplemented. Per the Asset Graph Model, `iterate()` is a construction functor. Without Appendix A, the engine is an observer, not a participant.
*   **Recommendation**: Implement `fp_construct.py` to allow the engine to generate candidates before evaluating them.

### 2. Transition to "Hard" SDLC (ADR-S-015/016)
The design identifies Level 1 event reliability (agent instructions). The "Gemini Pilot" has proven that **Level 4 Deterministic Emission** is required for the **Unit of Work** model. 
*   **Recommendation**: Move emission to the engine's reflex layer. Wrapped `START/COMPLETE` boundaries with SHA-256 `contentHash` facets are now the spec standard for transaction integrity.

### 3. Liveness Parity
The design docs still reference pipe-scraping for liveness. Your E2E runner has already identified **Filesystem Fingerprinting** as the superior model.
*   **Recommendation**: Formally deprecate pipe-scraping in the design in favor of the **Markov Blanket** boundary monitor (`_get_project_fingerprint`).

### 4. Fractal Recursion (Spec §7.2)
Spawning remains a manual command (`/gen-spawn`). The spec's scale-invariant property (ADR-S-017) requires the engine to handle **Recursive Spawns** and **Fold-Back** automatically.
*   **Recommendation**: Implement the `parentRunId` causal chain and the Fold-Back resolution logic to allow autonomous vectors to navigate sub-graphs.

## Conclusion

The "Reflex Layer" (routing, sensing, evaluating) is world-class. The priority must now shift to the **"Constructor"** and **"Fractal"** primitives to move `imp_claude` from a sophisticated monitor to a true **IntentEngine**.
