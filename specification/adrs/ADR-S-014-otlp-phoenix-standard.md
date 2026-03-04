# ADR-S-014: OTLP-Phoenix Observability Standard

## Status
Proposed

## Context
The AI SDLC methodology requires high-fidelity observability of the "Intent Engine" and its "Inner Loop" (LLM tool calls, prompts, and reasoning). 
[ADR-S-011](ADR-S-011-openlineage-unified-metadata-standard.md) established OpenLineage as the canonical event schema, stored in `events.jsonl`. However, OpenLineage is optimized for dataset lineage and macro-events, making it difficult to visualize the deep, causal trace trees of multi-agent LLM interactions.

`arize-phoenix` is a purpose-built LLM observability tool that uses OpenTelemetry (OTLP) and the OpenInference standard. To maintain compatibility with existing requirements while gaining deep visibility, we need a standard for projecting OpenLineage events into OTLP spans.

## Decision
We will adopt a **Secondary Projection Model** for observability:
1.  **Canonical Source**: `events.jsonl` (OpenLineage) remains the authoritative source of truth.
2.  **Transformation Layer**: An explicit **OTLP-Relay** will transform OpenLineage `RunEvents` into OTLP `Spans`.
3.  **Audit Parity**: Original OpenLineage identifiers (`runId`, `job`, `namespace`) will be preserved as span attributes.
4.  **Backend**: `arize-phoenix` will be the primary (optional) collector for these spans.

### Model Mapping Standard

| OpenLineage Concept | OTLP Mapping | Logic |
| :--- | :--- | :--- |
| `RunEvent (START)` | `Span Start` | Begins a trace or sub-span. |
| `RunEvent (COMPLETE)` | `Span End (OK)` | Closes the span successfully. |
| `RunEvent (FAIL)` | `Span End (Error)` | Closes the span with error status. |
| `run.runId` | `trace_id` | Preserves correlation across the stream. |
| `run.facets.sdlc_req_keys.req_keys` | `sdlc.req_keys` | Array of REQ keys for filtering. |
| `run.facets.sdlc_req_keys.feature_id`| `sdlc.feature_id` | Primary feature context. |
| `run.facets.sdlc_req_keys.edge` | `sdlc.edge_id` | The transition being observed. |
| `run.facets.sdlc_event_type.type` | `sdlc.event_type` | Mapping to methodology event types. |

### Cross-Regime Traceability (Mixed-Mode Spawning)
The Asset Graph serves as the interoperability layer between Deterministic (`F_D`) and Probabilistic (`F_P`) regimes. 
1. **Unified Causal IDs**: Both `F_D` (e.g., a CI/CD test runner) and `F_P` (e.g., an LLM agent) MUST emit events with a `causation_id` pointing to the triggering intent.
2. **Interoperable Spawning**: When a deterministic tool spawns an agentic task (or vice versa), the OTLP trace tree MUST reflect this as a parent-child relationship. 
3. **Regime Tagging**: Every span SHALL carry an `sdlc.regime` attribute (`deterministic`, `probabilistic`, or `human`) to allow Phoenix to filter and analyze the "Optimal Need" distribution across the SDLC.

### Causal Propagation
The `run.facets.parent_run_id` (if present) will be mapped to the OTLP `ParentSpanID`. This allows the asynchronous, file-based event stream to be reconstructed as a hierarchical trace tree in Phoenix, regardless of which regime produced the event.

## Consequences
- **Improved Visibility**: Developers can see the "Inner Loop" of agents directly in a UI.
- **Homeostasis Signals**: Phoenix Evaluators can detect drift/failures and emit `draft_proposal` signals back to the methodology.
- **Strict Optionality**: The system must not fail if the Phoenix collector is unreachable; the relay must use a `noop` or `try-except` pattern.
- **Resource Usage**: Running the OTLP-Relay adds a small amount of CPU/Memory overhead to the `sense` service.
