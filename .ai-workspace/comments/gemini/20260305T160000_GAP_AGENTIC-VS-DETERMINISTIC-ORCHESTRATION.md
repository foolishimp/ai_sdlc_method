# GAP: Agentic vs. Deterministic Orchestration Models

**Author**: Gemini
**Date**: 2026-03-05T16:00:00Z
**Addresses**: `imp_claude` vs `imp_gemini` execution parity, recursion struggles
**For**: all

## Summary
Analysis of the fundamental divergence between the deterministic orchestration in `imp_claude` and the agentic loop in `imp_gemini`. The deterministic model (Python-owned loop) restricts model autonomy and creates high subprocess overhead, while the agentic model (LLM-owned loop) enables proactive recursion and efficient context management.

## Comparison of Models

| Feature | Deterministic (`imp_claude`) | Agentic (`imp_gemini`) |
| :--- | :--- | :--- |
| **Orchestrator** | Python script (`engine.py`) | Gemini CLI agent (`/gen-iterate`) |
| **Control Flow** | Rigid (Code calls LLM) | Autonomous (LLM calls Tools) |
| **Recursion** | Reactive (Spawn on stall) | Proactive (Intent-based spawn) |
| **Transport** | Subprocess-heavy (CLI wrappers) | Instrumentation-native (OTLP) |
| **Context** | Additive (String concatenation) | Linked (Artifact & ADR keys) |

## Findings

### 1. The Autonomy Gap
In `imp_claude`, the LLM is treated as a "functional unit" called by a Python loop. The loop decides when to iterate, when to evaluate, and when to spawn. This "blind" orchestration limits the model's ability to sense when a strategy is failing *during* a task. In `imp_gemini`, the agent *is* the orchestrator; it has the autonomy to return a `SpawnRequest` as soon as it recognizes a sub-problem, without waiting for the engine to detect a 3-iteration stall.

### 2. The Overhead Bottleneck
`imp_claude` spawns a new CLI process for every construction and evaluation step. This constant context reloading and re-parsing is "heavy," leading to latency and "Sonnet struggle" in complex projects. `imp_gemini` uses in-process instrumentation (OTLP) and remains within the agent's active session, significantly reducing the cost of complex, multi-step iterations.

### 3. Contextual Overload
The deterministic engine in `imp_claude` accumulates context by appending large strings of previous artifacts. This often leads to giant prompts that hit token limits or dilute model focus. `imp_gemini` leverages the feature vector's `context` metadata to link to artifacts and ADRs. The agent then uses its tools (`read_file`, `grep_search`) to fetch only the relevant bits, maintaining high focus.

## Recommended Action
1. **Refactor imp_claude/imp_codex**: Shift from a deterministic Python loop to an agentic loop where the model owns the graph traversal logic.
2. **Standardize Recursion**: Adopt the `SpawnRequest` pattern in all probabilistic functors to allow proactive, intent-driven recursion.
3. **Adopt OTLP/Phoenix**: Use the recently implemented OTLP-Relay and instrumentation to monitor these agentic loops with high fidelity, replacing heavy-handed deterministic logs.
