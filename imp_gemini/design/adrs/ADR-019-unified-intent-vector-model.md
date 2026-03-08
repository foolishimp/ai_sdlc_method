# ADR-019: UNIFIED — Intent Vector Model Implementation in imp_gemini

**Series**: Implementation (imp_gemini)
**Status**: Proposed
**Date**: 2026-03-08
**Refers to**: ADR-S-026

--- 

## Context

As specified in ADR-S-026, the various vector types (product, design, feature, discovery) are ontological categories that collapse into a single construct: the **Intent Vector**.

## Decision

### Intent Vector as Composition Expression

In `imp_gemini`, we will refactor the internal `VectorModel` (previously ADR-007) to use the Unified Intent Vector Model:

1.  **Resolution Level**: The vector carries a `resolution_level` parameter (intent, requirements, design, code, deployment, telemetry).
2.  **Composition Expression**: Every intent vector in Gemini carries a `composition_expression` as its DNA (e.g., `PLAN`, `POC`, `SCHEMA_DISCOVERY`). This replaces the hard-coded feature vector schema.
3.  **The Causal Chain**: Lineage is now complete. Every Gemini vector has a `parent_vector` ID and a `source` (abiogenesis, gap, or parent).

## Operational Implementation

- **Vector Storage**: Updated JSON schema for `vectors/*.json` in the `.ai-workspace/` partition to include `composition_expression` and `resolution_level`.
- **Gap-to-Intent Mapping**: The Gemini `ObserverService` (`imp_gemini/code/src/gemini_cli/observer.py`) will now map gap types to specific named compositions (e.g., `missing_schema 	o SCHEMA_DISCOVERY`).
- **Gemini CLI Command**: `gemini -v` (vector) will display the complete causal ancestry of an intent vector, projecting it from the abiogenesis.

## Consequences

- **Positive**: Complete causal traceability. The methodology is now structurally recursive and self-modifying through gap-to-intent generation.
- **Negative**: Requires a one-time migration of existing `vectors/*.json` artifacts to the new unified schema.
