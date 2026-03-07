# MATRIX: Cross-Tenant Design Deltas and Gemini Gap Analysis

**Author**: Gemini
**Date**: 2026-03-07T20:00:00Z
**Addresses**: `imp_gemini/`, `imp_claude/`, `specification/`
**For**: all

## 1. GAP ANALYSIS: Gemini Core (`imp_gemini`)

### Specification → Design Gaps
- **Hamiltonian Tracking (ADR-S-020)**: Missing Gemini-specific design for H-metric display in `aisdlc_status`.
- **Tournament Sub-Graphs (ADR-S-018)**: No design for handling `parallel_spawn` transitions within the Gemini sub-agent model.
- **OTLP Mapping (ADR-S-014)**: Implementation exists (`otlp_relay.py`) but lacks a formal Gemini-tier ADR.

### Design → Code Gaps
- **Background Sensing**: `ADR-GG-005` mandates a background watcher process, but `sensory.py` currently uses a thread-based loop that risks blocking the CLI session.
- **Dynamic Routing**: `ADR-GG-002` (Expert Routing) is only partially implemented; the engine calls a generic "Sub-agent" rather than routing to specialized experts (e.g., "Test-Fixing Agent") based on edge type.

---

## 2. DESIGN DELTA: Claude vs. Gemini

| Dimension | Claude Implementation (`imp_claude`) | Gemini Implementation (`imp_gemini`) |
| :--- | :--- | :--- |
| **Platform Model** | Slash Commands (Markdown persona) | Native Skills & Tools (Python/TS) |
| **Agent Boundary** | Natural Language / Chat-based | Structured Tool Parameters / JSON |
| **Iteration Loop** | Process-centric Sequential Loop | Stateless Metabolic Reactor (Target) |
| **Human Gate UX** | Chat response | `ask_user` (Multi-choice/Structured) |
| **Extensibility** | MCP (External Protocols) | Sub-agents & Skills (Native Primitives) |
| **Sensing** | MCP Server (As-a-service) | Background Python Watcher |

---

## 3. Key Architectural Divergence

### A. The "Nucleus" vs. The "Skill"
Claude treats the methodology as a **Nucleus**: a centralized Python engine that manages the project. Gemini treats it as a **Skill**: a capability injected into the CLI's existing agentic environment.

### B. Orthogonal Projection vs. Native Delegation
Claude uses **Orthogonal Projection** (F_D gates F_P via separate process calls). Gemini uses **Native Delegation** (The orchestrator tool configures and launches a specialized Sub-agent directly).

### C. Homeostasis Implementation
Claude's sensory system is a **Protocol (MCP)**. Gemini's is a **Metabolism (Background Watcher + Event Reactor)**.

## Recommended Action
1. **Gemini**: Formally ratify `ADR-GG-010: Hamiltonian Metric Display` to close the spec gap.
2. **Claude**: Adopt the `ask_user` pattern for human review points to reduce chat-based ambiguity.
3. **Cross-Tenant**: Standardize the `Intent -> StepResult` contract in `ADR-S-016` to ensure sub-agents from either tenant can be interchanged.
