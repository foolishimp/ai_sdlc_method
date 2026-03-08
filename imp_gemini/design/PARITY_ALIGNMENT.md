# STRATEGY: imp_gemini Parity and Spec Alignment (v2026.03.08)

**Author**: Gemini
**Date**: 2026-03-08
**Addresses**: Parity with imp_claude and alignment with ADR-S-018..026

## Summary
This document tracks the alignment of `imp_gemini` with the latest global specifications (ADR-S series) and the `imp_claude` reference implementation. It identifies superseded local ADRs and specifies the translation of shared functors (`CONSENSUS`, `PLAN`) into Gemini-native structures.

## Parity Matrix

| Shared Spec | Status in imp_gemini | Local Equivalent / Action |
|-------------|----------------------|---------------------------|
| ADR-S-018 (Tournament) | Missing | Add to design/adrs/ |
| ADR-S-019 (Markov) | Partial | Refined in ADR-GG-007 |
| ADR-S-020 (Hamiltonian) | Partial | ADR-GG-010 exists; needs spec link |
| ADR-S-021 (Project Graph) | Missing | Add to design/adrs/ |
| ADR-S-022 (Lineage) | Missing | Add to design/adrs/ |
| ADR-S-023 (Workspace) | Partial | ADR-GG-006 exists; needs unification |
| ADR-S-024 (Consensus Gate) | Missing | Add to design/adrs/ |
| ADR-S-025 (Consensus Functor) | Missing | **CRITICAL** - Implement |
| ADR-S-026 (Intent Vectors) | Missing | **CRITICAL** - Implement |

## Redundant / Superseded Local ADRs

- `ADR-007 (feature-vector-schema)`: Superseded by `ADR-S-026` (Unified Intent Vectors).
- `ADR-009 (graph-topology)`: Superseded by `ADR-S-021` and `PLAN` functor formalisation.
- `ADR-017 (functor-based-model)`: Needs update to match 9-functor provisional library.

## Implementation Steps
1. Translate ADR-S-024, 025, 026 into Gemini context.
2. Update `ENGINE_DESIGN.md` to support compositional intent vectors.
3. Refactor `EVALUATOR_FRAMEWORK_DESIGN.md` to include multi-stakeholder $F_H$ (CONSENSUS).
