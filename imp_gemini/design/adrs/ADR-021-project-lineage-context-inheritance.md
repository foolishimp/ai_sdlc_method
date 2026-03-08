# ADR-021: Project Lineage and Context Inheritance in imp_gemini

**Series**: Implementation (imp_gemini)
**Status**: Proposed
**Date**: 2026-03-08
**Refers to**: ADR-S-022

--- 

## Context

As specified in ADR-S-022, every intent vector requires a complete lineage back to its source (abiogenesis, gap, or parent) and must inherit its parent's context context (`Context[]`). 

## Decision

### Lineage as Context Threading

In `imp_gemini`, lineage is not just metadata; it is a mechanism for **Context Inheritance**.

1.  **Inheritance Chain**: Every child vector (spawned or gap-generated) automatically inherits the `Context[]` of its parent, including spec-level constraints and design ADRs.
2.  **Context Delta**: A child vector can only *add* to its inherited context, not remove from it (monotone context). This ensures that child iterations (e.g., a POC spike) remain bound by the parent's constraints.
3.  **Traceability**: The `traceability.py` parser in Gemini CLI will be updated to traverse the lineage chain to ensure REQ keys are preserved and correctly linked across vector boundaries.

## Operational Implementation

- **Context Loader**: The `gemini -l` (load) service will now recursively traverse the vector's lineage to assemble the full `Context[]` stack before iteration begins.
- **Traceability Matrix**: A unified matrix will show the complete causal ancestry for every requirement key, from the abiogenesis through all resolution levels.

## Consequences

- **Positive**: Prevents "context drift" in child vectors. Ensures that sub-projects remain aligned with the original project goals and constraints.
- **Negative**: Increased memory overhead for `Context[]` loading as the lineage chain grows deep.
