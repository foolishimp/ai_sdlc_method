# REVIEW: OpenLineage Metadata Standard (ADR-S-011)

**Date**: 2026-03-01
**Author**: Gemini
**Subject**: Formalizing the Unified Metadata Contract

## Summary
The proposal to adopt OpenLineage (OL) as the primary metadata format for the AI SDLC is approved. This transition moves the methodology from a bespoke JSONL "log" to a standardized "lineage stream," enabling professional-grade observability and decoupling routing logic from data capture.

## Key Recommendations for ADR-S-011

### 1. Unified OL Envelope
All entries in `events.jsonl` must strictly follow the OpenLineage `RunEvent` schema.
- **Iterate Events**: Map cleanly to `START`, `COMPLETE`, `FAIL`.
- **Homeostasis Signals**: Use `OTHER` with a `job.type: "SENSORY_PROBE"`. This avoids "dataset bloat" while maintaining schema consistency.

### 2. Custom Facet Library (sdlc-facet-v1)
We must define a versioned facet library to house methodology-specific semantics:
- `sdlc:valence`: `{ regime: "reflex"|"affect"|"conscious", severity: int, urgency: int }`
- `sdlc:delta`: `{ value: int, converged: bool }`
- `sdlc:req_keys`: `list[string]` (The REQ keys this run touches)
- `sdlc:event_type`: The original semantic type (e.g., `intent_raised`) for `OTHER` events.

### 3. Causal Chaining via ParentRunFacet
This is the critical unlock for the "Historical Evolution" requirement.
- Signal (`OTHER`) → Triage (`OTHER`) → Intent (`OTHER`) → Proposal (`OTHER`) → Iteration (`START`).
- Each child run MUST include the `parent` run facet pointing to its predecessor in the chain.

### 4. Namespace Protocol
To prevent collisions in global lineage backends (e.g., Marquez):
- **Job Namespace**: `aisdlc://{project_name}`
- **Dataset Namespace**: `file://{project_root}`

### 5. Local-First Invariant
The spec must declare that the local `events.jsonl` file is the **Source of Truth**. Infrastructure backends are optional enhancements. The methodology must remain portable and "laptop-runnable."

## Implementation Note for Writers
Upon approval of ADR-S-011, a one-time migration of existing `events.jsonl` data to the new schema is required. Tools (`gemini cli`, `genisis_monitor`) must be updated to navigate the nested OL JSON structure.
