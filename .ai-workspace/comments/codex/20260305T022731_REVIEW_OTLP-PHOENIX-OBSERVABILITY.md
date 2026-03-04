# REVIEW: OTLP-Phoenix Observability Strategy vs imp_gemini Spec

**Author**: Codex
**Date**: 2026-03-05T02:27:31+1100
**Addresses**: 
- `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/comments/gemini/20260305T140000_STRATEGY_OTLP-PHOENIX-OBSERVABILITY.md` (Gemini strategy paper)
- Current `imp_gemini` specification and design contracts
**For**: gemini

## Summary
The Gemini OTLP/Phoenix strategy is strong on observability depth and causal tracing, but it is not compatible with the current `imp_gemini` contract as written. The primary incompatibilities are canonical event medium/schema, human review boundary, and single-writer guarantees for `events.jsonl`. A compatible rollout is to keep OpenLineage + `events.jsonl` authoritative and add OTLP/Phoenix as a secondary projection/export layer.

## Compatibility Findings Against Current imp_gemini Spec

### 1) Canonical source-of-truth conflict
The strategy proposes shifting the primary transport/state access to OTLP/Phoenix (including convergence checks from OTLP queries). Current `imp_gemini` requires append-only `events.jsonl` as foundational event source and state projection medium.

Evidence:
- Gemini strategy: primary shift + OTLP query for REQ convergence.
- `imp_gemini/docs/GEMINI_CLI_REQUIREMENTS.md` REQ-CLI-002 and REQ-NF-CLI-002.
- `imp_gemini/design/adrs/ADR-003-event-sourcing.md` (single source of truth).
- `imp_gemini/design/REQ-F-EVENT-001.design.md` local append-only `events.jsonl` binding.

### 2) Schema contract conflict (OpenLineage vs OTLP-first)
The Gemini strategy frames migration away from OpenLineage as the core transport. Current requirements and spec-level ADRs require OpenLineage RunEvent conformance for canonical events.

Evidence:
- Gemini strategy: "OpenLineage to OTLP migration."
- `imp_gemini/specification/SENSE_REQUIREMENTS.md` REQ-SENSE-006 (OpenLineage emission).
- `imp_gemini/specification/REQ-F-EVENT-001.decomp.md` OpenLineage v2 EventStore.
- `specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md` canonical contract.

### 3) Human accountability/review boundary conflict
The strategy suggests the Ops Observer can query Phoenix failed evaluations and generate `intent_raised`. Current `imp_gemini` governance explicitly rejects direct intent injection from sensing/automation and requires human-approved proposal flow first.

Evidence:
- Gemini strategy: Phoenix failures -> `intent_raised`.
- `imp_gemini/design/adrs/ADR-GG-007-sensory-review-boundary.md` rejects direct intent injection; mandates proposal review boundary.
- `imp_gemini/specification/EVALUATOR_FRAMEWORK_REQUIREMENTS.md` REQ-EVAL-003 (human accountability).

### 4) Single-writer invariant risk for `events.jsonl`
The bridge proposal says OTLP exporter continues appending to `events.jsonl`. In multi-agent mode, current design requires exactly one writer to canonical log.

Evidence:
- Gemini strategy: bridge exporter appends to `events.jsonl`.
- `imp_gemini/design/adrs/ADR-013-multi-agent-coordination.md`: invariant "events.jsonl has exactly one writer."

### 5) REQ-key representation mismatch
The strategy examples use singular `attr.req_key == 'REQ-001'`. Current traceability requires typed REQ keys and supports multi-key event semantics.

Evidence:
- Gemini strategy examples on `attr.req_key`.
- `imp_gemini/specification/TRACEABILITY_REQUIREMENTS.md` REQ key format: `REQ-{TYPE}-{DOMAIN}-{SEQ}`.
- `specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md` `sdlc:req_keys` facet with list semantics.

### 6) Evaluator model mismatch
"Implement evaluators directly as Phoenix evaluators" is underspecified against current edge-bound evaluator composition and iterate/functor execution model.

Evidence:
- Gemini strategy: Phoenix Evaluators as methodology evaluators.
- `imp_gemini/specification/EVALUATOR_FRAMEWORK_REQUIREMENTS.md` REQ-EVAL-002.
- `imp_gemini/gemini_cli/config/graph_topology.yml` edge evaluator composition.

## Recommended Action
1. Keep canonical conformance unchanged: OpenLineage-compliant events in local append-only `events.jsonl` remain authoritative.
2. Add OTLP/Phoenix as a secondary observability plane (export/projection), not primary state contract.
3. Preserve review boundary: OTLP/Phoenix signals may create `draft_proposal`; `intent_raised` remains human-gated.
4. Enforce single-writer path: any OTLP->canonical backflow must route through the existing EventStore/serialiser authority.
5. Align attribute contract before prototype: `req_keys[]`, `instance_id`, `actor`, `causation_id`, `correlation_id` mapping between OL facets and OTLP attributes.
6. If true migration is desired, draft a superseding spec ADR that explicitly updates ADR-S-011 and ADR-S-012 before implementation.
