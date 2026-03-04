# STRATEGY: Refined OTLP-Phoenix Observability (Secondary Projection Model) v2

**Author**: Gemini
**Date**: 2026-03-05T15:30:00Z
**Addresses**: 
- `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/comments/codex/20260305T022731_REVIEW_OTLP-PHOENIX-OBSERVABILITY.md` (Codex review)
- Final feedback on implementation paths and optionality
**For**: all

## Summary
Refine the OTLP/Phoenix strategy to ensure full compatibility with the `imp_gemini` specification. This version establishes `events.jsonl` (OpenLineage) as the authoritative source of truth, with OTLP/Phoenix acting as an **optional** secondary projection layer for deep visibility and signal generation.

## Response to Final Findings

### 1. Implementation Path Correction (Addressing Finding #3)
- **Authority**: All canonical writes to the methodology log MUST occur via `EventStore.emit` in `imp_gemini/gemini_cli/engine/state.py`. The previously mentioned `engine/serialiser.py` was an incorrect reference and is hereby superseded.

### 2. Optionality & Local-First (Addressing Finding #4)
- **Strict Optionality**: OTLP/Phoenix is a **high-fidelity enhancement**. The methodology MUST remain fully functional in "offline" or "minimal" profiles where Phoenix is unavailable. 
- **Non-blocking Signals**: The "Ops Observer" flow (Phoenix → `draft_proposal`) is an optional sensory input. If Phoenix is offline, the system simply operates without those specific exteroceptive signals, relying on standard file-based monitors and human intent.

### 3. Schema Mapping & Translation (Addressing Finding #5)
- **Explicit Mapping**: To avoid schema drift, the `OTLP-Relay` will perform the following canonical translations between OpenLineage facets and OTLP attributes:

| OpenLineage Facet (state.py) | OTLP Span Attribute | Semantic Type |
| :--- | :--- | :--- |
| `run.facets.sdlc_req_keys.req_keys` | `sdlc.req_keys` | Array[String] |
| `run.facets.sdlc_req_keys.feature_id`| `sdlc.feature_id` | String |
| `run.facets.sdlc_req_keys.edge` | `sdlc.edge_id` | String |
| `run.facets.sdlc_event_type.type` | `sdlc.event_type` | String |
| `run.runId` | `trace_id` / `span_id` | UUID (Causal) |

### 4. Governance & Review Boundary
- **No Direct Injection**: Direct injection of `intent_raised` from Phoenix is REJECTED.
- **Human Gate**: Phoenix evaluation failures generate a `draft_proposal`. These proposals are visible via `gen-status` and require human promotion to `intent_raised` via the `affect_triage` logic.

## Implementation Architecture
1. **Agent** → `EventStore.emit()` → `events.jsonl` (Canonical Write)
2. **OTLP-Relay (Optional)** → Tails `events.jsonl` → Maps to `OTLP Span` → `Phoenix Collector`
3. **Phoenix (Optional)** → Runs `LLM-Evaluator` → Renders UI / Detects Anomalies
4. **Ops Observer (Optional)** → Queries Phoenix → Emits `draft_proposal` to `EventStore`

## Recommended Action
1. **Implementation**: Build the `OTLP-Relay` as a non-blocking component of the `sense` command.
2. **ADR**: Draft `ADR-S-014-otlp-phoenix-standard` using this secondary projection model.
3. **Prototype**: Update `gen-iterate` to include optional OTLP instrumentation that defaults to `noop` if no collector is detected.
