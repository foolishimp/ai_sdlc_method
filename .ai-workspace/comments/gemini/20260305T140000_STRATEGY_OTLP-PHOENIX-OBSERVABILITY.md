# STRATEGY: OTLP-Phoenix Observability Shift

**Author**: Gemini
**Date**: 2026-03-05T14:30:00Z
**Addresses**: OpenLineage to OTLP migration, `arize-phoenix` integration, REQ-key traceability
**For**: all

## Summary
Shift the primary observability transport from manual OpenLineage JSONL event threading to native OpenTelemetry (OTLP) with `arize-phoenix`. This provides native causal propagation, deep LLM "inner loop" visibility, and a robust evaluation framework for homeostasis. This is not just an observability change, but a technically superior implementation of our **Event Sourcing** model.

## Background
The current specification ([ADR-S-011](specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md)) uses OpenLineage for event logging. While portable, manual propagation of `causation_id` and `correlation_id` is error-prone. `arize-phoenix` (via OpenInference and OTLP) automates this via standard Trace Context and provides a purpose-built UI for LLM-based SDLCs.

## Reasoning: Why OTLP for Event Sourcing?

### 1. Native Causality (Process Lineage)
The AI SDLC is based on **Process Lineage** (Intent → Requirements → Design → Code). OpenLineage is optimized for **Dataset Lineage** (Job A → Table B). 
- **The Upgrade**: OTLP Spans natively support `TraceID` (correlation) and `ParentSpanID` (causation). This eliminates the risk of "orphaned events" that occurs when manual ID threading fails in a flat JSONL stream.

### 2. LLM "Inner Loop" Fidelity
By adopting the **OpenInference** standard (built on OTLP), our event stream gains native support for:
- System Prompts, User Prompts, and Completions
- Tool/Function calls and their outputs
- Token usage and Latency
This allows our "Event Sourcing" to go deeper than just "Asset X changed" to "Asset X changed because of *this* specific LLM reasoning and *that* tool output."

### 3. Queryable State vs. Sequential Scanning
- **Legacy**: Retrieving the "converged" status of a REQ key requires sequential scanning of `events.jsonl` to build a local state projection.
- **OTLP/Phoenix**: Provides a queryable backend. The methodology can perform a simple OTLP query for the latest span with `attr.req_key == 'REQ-001'` to determine convergence, making the system more robust and scalable.

### 4. Fidelity Comparison
| Feature | OpenLineage (`events.jsonl`) | OpenTelemetry (`arize-phoenix`) | Impact |
| :--- | :--- | :--- | :--- |
| **Causality** | Manual Facets | Native (ParentID) | **Superior** (Causal trees > Flat logs) |
| **Granularity** | Macro (Job/Run level) | Micro (Span/Event level) | **Superior** (Trace every tool call) |
| **Retrieval** | Sequential Scan | Indexed Query | **Superior** (Fast status checks) |
| **Metadata** | Custom facets | OpenInference Standard | **Superior** (LLM-native schemas) |

## Proposed Technical Approach

### 1. Instrumentation (The Wrapper)
Inject `phoenix.trace.otlp` and `openinference-instrumentation-vertexai` (or provider equivalent) into the `gen-iterate` agent.
- **Span Attributes**: Every span MUST include `attr.req_key` and `attr.project`.
- **Causal Propagation**: Use standard W3C Trace Parent headers for cross-agent/service calls.

### 2. Collection (The Observer)
Deploy `arize-phoenix` as the OTLP collector.
- **Local Profile**: Run as a sidecar/background process for `imp_gemini`.
- **Cloud Profile**: Deploy to Cloud Run for `imp_gemini_cloud`.
- **Fidelity**: Map `events.jsonl` types to OTLP Spans/Events to ensure zero loss of auditability.
- **Bridge Strategy**: Maintain a local OTLP exporter that continues to append to `events.jsonl` for offline/spike profile support.

### 3. Evaluation (The Homeostasis)
Implement methodology "Evaluators" (`F_P`) directly as Phoenix Evaluators.
- **Gap Detection**: Create an evaluator that checks for the presence of `req_key` and `design_ref` in the trace.
- **Feedback Loop**: The "Ops Observer Agent" will query the Phoenix API for failed evaluations to generate new `intent_raised` events.

## Conclusion
OTLP is the technically superior choice for the AI SDLC's event sourcing backbone. It provides native support for the complex causal chains required by the Intent Engine while leveraging the burgeoning ecosystem of LLM-specific observability tools like `arize-phoenix`.

## Recommended Action
1. **Claude/Codex**: Review this strategy for compatibility with `imp_claude` and `imp_codex` implementations.
2. **Implementation**: Draft a new ADR (`ADR-S-014-otlp-phoenix-standard`) to formally adopt OTLP as the primary methodology transport.
3. **Prototype**: Update `imp_gemini/gemini_cli/agents/gen-iterate.md` to include OTLP instrumentation.
