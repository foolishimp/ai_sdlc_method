# ADR-GG-001: Gemini CLI as Target Platform

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003
**Supersedes**: ADR-001 (Claude Code as MVP Platform) — for Gemini Genesis implementation

---

## Context

The AI SDLC Asset Graph Model is designed to be platform-agnostic, but requires a concrete "binding" to a developer-facing tool to be operational. The reference implementation uses Claude Code (ADR-001). We need to define the binding for the **Gemini CLI** environment.

Gemini CLI provides a different set of primitives than Claude Code:
- **Sub-agents**: Specialized experts for specific tasks.
- **Tools**: Executable functions with structured parameters.
- **Skills**: Encapsulated prompt logic and tool definitions.
- **Memory**: Global and workspace-specific persistent state.
- **Interactive Tools**: `ask_user` for multi-choice or free-text input.

### Options Considered

1.  **Direct Port of Claude Commands**: Implement `/gen-*` style commands as shell scripts.
2.  **Gemini-Native Tooling**: Implement operations as Gemini Tools and Sub-agents.
3.  **Hybrid Approach**: Use shell scripts for low-level file ops, but Gemini-native tools for high-level methodology transitions.

---

## Decision

**We will implement Gemini Genesis as a native Gemini CLI Skill, mapping methodology operations to Tools and complex construction tasks to specialized Sub-agents.**

Key mappings:
-   **Slash Commands** → **Gemini Tools** (`aisdlc_iterate`, `aisdlc_status`).
-   **Iterate Agent** → **Gemini Sub-agent** (`aisdlc_investigator` or custom role).
-   **Context Store** → **Skill Prompt + File System**.
-   **User Review** → **`ask_user` Tool**.

---

## Rationale

### Why Gemini CLI (vs Claude Code)

1.  **Native Agentic Orchestration**: Gemini's Sub-agent architecture is a better fit for the "Universal Iterate Agent" concept. It allows the methodology to delegate specific edges (e.g., `code↔unit_tests`) to agents with relevant expertise (e.g., a "Test-Fixing Agent").
2.  **Structured Interaction**: The `ask_user` tool provides a vastly superior UX for refinement loops compared to the chat-based interaction in Claude. It enables multi-select, yes/no, and placeholder hints.
3.  **Autonomous Backgrounding**: Gemini's ability to run shell commands in the background (`is_background=true`) simplifies the implementation of the Sensory Service without needing a separate MCP infrastructure.
4.  **Global Memory**: Gemini can store high-level user preferences across projects using `save_memory`, which aligns with the "Context Hierarchy" (REQ-CTX-002).

---

## Consequences

### Positive

-   **Deep Integration**: The methodology feels like a native feature of the IDE/CLI rather than a bolted-on plugin.
-   **Improved Reliability**: Structured tool parameters reduce the "hallucination" risk compared to natural language slash commands.
-   **Self-Healing**: Native access to shell and git allows for more robust recovery operations.

### Negative

-   **Implementation Divergence**: The Gemini-specific code (Python/TS for tools) will differ from the Claude implementation (Markdown/JSON).
-   **Learning Curve**: Users familiar with Claude slash commands will need to adapt to natural language or tool-based interaction in Gemini.

### Mitigation

-   Maintain the **same workspace structure** (.ai-workspace) and file formats (YAML/JSONL) to ensure project portability between platforms.
-   Provide a `cli_help` extension for Gemini to explain the AI SDLC tools.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md)
- [AISDLC_V2_DESIGN.md](../../claude_aisdlc/AISDLC_V2_DESIGN.md)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md)
