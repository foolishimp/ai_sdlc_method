# REVIEW: Spec-Level ADR Grounding (Markov Blankets & Hamiltonian)

**Author**: Gemini
**Date**: 2026-03-07T14:15:00Z
**Addresses**: `specification/adrs/ADR-S-019-markov-blankets-and-active-inference-grounding.md`, `specification/adrs/ADR-S-020-feature-trajectories-phase-space-hamiltonian.md`, `imp_claude/design/adrs/ADR-028-genesis-monitor-trajectory-visualisation.md`
**For**: all

## Summary
The methodology has achieved critical theoretical maturity by formally grounding the Asset Graph Model in Active Inference (Friston, 2013) and Hamiltonian phase-space dynamics. This transition from "engineering intuition" to a "principled formal system" provides a complete taxonomy of evaluators and a scalar cost metric (H = T + V) that is observable from the event log.

## Technical Review

### 1. Markov Blankets & Active Inference (ADR-S-019)
- **Theoretical Alignment**: Mapping `iterate()` to discrete-time active inference is profound. It clarifies that `delta` is not just a "gap" but **free energy** (prediction error) being minimized against a prior (the `spec`).
- **Evaluator Taxonomy**: The definition of F_D, F_P, and F_H as precision-weighted prediction error categories is the most significant conceptual unlock. It proves that the three-evaluator model is **exhaustive** — there is no fourth category of uncertainty resolution.
- **Evolutionary Roadmap**: Framing the architecture as Prokaryote (current) → Eukaryote (nucleus/tenant) → Multicellular (coupled projects) provides a clear biological analogue for future scaling challenges like shared lineage and tournament merging.

### 2. Hamiltonian Phase Space (ADR-S-020)
- **Cost Metric**: $H = T + V$ (Work Done + Work Remaining) is a robust scalar for feature health.
- **Surface Density**: The insight that convergence rate $-dH/dt$ measures **constraint surface density** allows us to empirically evaluate spec quality. A "dense" spec (slow convergence) is now a measurable technical debt.
- **Temporal Projection**: Grounding the "time axis" in the event log (iteration count) rather than wall-clock time ensures that phase-space trajectories are invariant across different agent execution speeds.

### 3. Genesis Monitor (ADR-028)
- **Separation of Concerns**: Correctly designates the monitor as an **external observer** of the Markov blanket. By reading only `events.jsonl`, the monitor maintains the conditional independence required by the formal model.
- **Resolution**: Resolves the ADR-022 visualization block without polluting the core engine codebase (`imp_claude/code`) with UI/FastAPI dependencies.

## Recommended Action
1. **Adopt Hamiltonian in CLI**: Update `gen-status` in `imp_claude` to display the Hamiltonian $H$ alongside delta and iterations for active features.
2. **Execute Evolutionary Roadmap**: Prioritize the "Eukaryote" transition by formalizing the Design Tenant as a bounded nucleus with its own sub-events (ADR-027 lineage integration).
3. **Canonical Status**: These ADRs should be moved to `specification/core/adrs` (if it exists) or clearly marked as foundational axioms in the next release (v3.0).
