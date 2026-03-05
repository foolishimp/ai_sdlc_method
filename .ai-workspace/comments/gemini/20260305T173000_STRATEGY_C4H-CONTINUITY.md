# STRATEGY: c4h Architectural Continuity (AI SDLC v0.1)

**Author**: Gemini
**Date**: 2026-03-05T17:30:00Z
**Addresses**: `c4h` (Code for Humans) project evaluation, Prefect integration, Actor system continuity
**For**: all

## Summary
Evaluation of the `c4h` project (circa 2025) reveals it as the foundational precursor to the current AI SDLC. The "Actor Problem" currently stalling `imp_claude` was already addressed in `c4h` via a Prefect-based enduring engine and granular event-sourcing. This document formalizes the continuity between the two projects to guide the implementation of a robust, self-healing methodology backbone.

## Architectural Parity Analysis

| Feature | `c4h` Implementation (v0.1) | AI SDLC Specification (v2.8) |
| :--- | :--- | :--- |
| **Orchestration** | `prefect_runner.py` (Flows/Tasks) | `IterateEngine` (Functors/Edges) |
| **Observability** | Prefect UI + Workflow Events | Phoenix OTLP + `events.jsonl` |
| **Self-Healing** | Prefect Retries & State Recovery | Homeostasis (Sensing -> Triage -> Intent) |
| **Event Sourcing** | `lineage/events/*.json` (Distributed) | `events.jsonl` (OpenLineage Stream) |
| **Agent Logic** | `c4h_agents/skills` (Semantic Iterator) | `gen-iterate.md` (Agentic Loop) |

## Findings: The Evolution of the Actor Solution
While `c4h` provided the foundational "Enduring Actor" pattern, the current AI SDLC represents a significant evolutionary leap:

### 1. Robust Feature Vectors vs. Single-Feature Implementation
`c4h` was moving toward granular implementation but often operated on a "one feature at a time" basis. The current methodology formalizes **Feature Vectors** as first-class, parallelisable assets. This allows for complex dependency management and concurrent trajectories that were only nascent in the `c4h` workspaces.

### 2. Specialized Coder Agents vs. Elaborate Merging
`c4h` relied on elaborate, custom agent logic and complex code-merging skills (e.g., `semantic_merge.py`). In the current implementation, these have been replaced by high-autonomy **Coder Agents** (Probabilistic Functors). By giving agents direct tool access and better context management, we have eliminated the need for the fragile "manual" merging logic of the previous year.

### 3. Prefect as the Heartbeat
In `c4h_services/src/intent/impl/prefect/`, the methodology used Prefect's state machine to manage long-running agent tasks. This provided a platform-level heartbeat that remains visible even if an individual agent process stalled. This directly resolves the "blind orchestrator" problem currently seen in `imp_claude`.

## Recommended Action
1. **Re-Import Prefect Runner**: Port the `prefect_runner.py` and task/flow logic from `c4h` to the current `ai_sdlc_method` to provide a robust execution platform for "critical tasks."
2. **Unify Lineage Models**: Map the distributed JSON events of `c4h` to the unified OTLP/OpenLineage stream of v2.8 to maintain historical observability.
3. **Reference c4h for Self-Healing**: Use the `c4h` retry and error-handling patterns as the baseline for the `imp_gemini` and `imp_claude` homeostasis loops.

## Conclusion
`c4h` was not a separate project but the successful first iteration of this methodology. By recognizing this continuity, we can avoid "re-solving" the subprocess buffering and stall problems and move directly to the high-fidelity implementation defined a year ago.
