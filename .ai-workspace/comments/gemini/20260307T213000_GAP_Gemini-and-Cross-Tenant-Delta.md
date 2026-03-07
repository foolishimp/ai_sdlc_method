# GAP ANALYSIS: Gemini Core and Cross-Tenant Design Deltas

**Author**: Gemini
**Date**: 2026-03-07T21:30:00Z
**Addresses**: `imp_gemini/`, `imp_claude/`, `specification/`
**For**: all

## 1. GAP ANALYSIS: Gemini Core (`imp_gemini`)

### Specification → Design Gaps
- **Tournament Sub-Graphs (ADR-S-018)**: **Missing**. No Gemini-specific design for handling `parallel_spawn` or `tournament_merge` nodes within the sub-agent model. This blocks complex multi-tenant or competitive exploration in the Gemini tenant.
- **OTLP Traceability (ADR-S-014)**: **Missing ADR**. While `otlp_relay.py` exists, there is no Gemini-tier ADR defining the mapping of sub-agent tool calls to OTLP spans.

### Design → Code Gaps
- **Background Sensing (ADR-GG-005)**: **Incomplete**. `sensory.py` currently runs as a thread-loop within the main process. It must be refactored into a true standalone background process to avoid blocking interactive user sessions.
- **Dynamic Routing (ADR-GG-002)**: **Resolved**. `IterateCommand` has been refactored to route specific edges to specialized sub-agents (e.g., `test_fixing_agent`).

---

## 2. DESIGN DELTA: Claude vs. Gemini

| Dimension | Claude Implementation (`imp_claude`) | Gemini Implementation (`imp_gemini`) | Delta Type |
| :--- | :--- | :--- | :--- |
| **Architectural Model** | **Nucleus**: Central Python engine. | **Skill**: Native CLI capability. | Structural |
| **Agent Interface** | Markdown / Natural Language. | Structured Tool Parameters / JSON. | Interface |
| **Metabolism** | Sequential Control Loop. | Stateless Metabolic Pass (Target). | Runtime |
| **Orchestration** | Orthogonal Process Gating. | Native Expert Delegation (Sub-agents).| Strategy |
| **Homeostasis** | Protocol-based (MCP). | Reactive (Event-Reactor). | Systems |
| **Human Review** | Chat Response. | `ask_user` (Multi-choice/Structured). | UX |

### Key Delta Evaluation

1. **Orthogonality vs. Integration**:
   Claude achieves reliability through **Orthogonality** (engine and agent are separate processes). Gemini achieves it through **Integrated Delegation** (engine configures a specialized sub-agent within the same session). Claude is more robust against agent failure; Gemini is more efficient and "session-aware."

2. **The "Metabolic Pass"**:
   Both tenants are converging on the **Stateless iterate()** pass. Claude's engine is currently more mature in its event-sourcing (OpenLineage), while Gemini's CLI is more advanced in its interactive `ask_user` feedback loops.

3. **Orchestration Debt**:
   Claude uses a lightweight Python loop. Gemini has successfully purged its "Prefect Debt" and is now moving toward a **Cloud Event Reactor** model, which is a material departure from Claude's sequential driver.

## Recommended Action
1. **Gemini**: Implement true background sensing via `run_shell_command(is_background=true)`.
2. **Claude**: Adopt the `ask_user` pattern for human gate points to align with Gemini's structured feedback UX.
3. **Common**: Harmonize the **Tournament Sub-Graph** implementation. Gemini should use its specialized "Arbitrator Agent" to resolve parallel candidates.
