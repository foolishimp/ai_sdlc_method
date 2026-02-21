# ADR-GG-008: Two-Verb UX Architecture (Start/Status)

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-UX-001 (Simplicity), REQ-UX-002 (Progressive Disclosure), REQ-UX-003 (Situational Awareness), REQ-UX-004 (Auto-pilot), REQ-UX-005 (Self-healing)

---

## Context

The Asset Graph Model v2.6/v2.7 introduced significant complexity, expanding the methodology to 9+ commands. Dogfooding revealed that this created a high cognitive load for users who had to manually decide which command to run at each stage.

The Claude Code implementation (ADR-012) collapsed this complexity into two primary verbs: `/aisdlc-start` and `/aisdlc-status`. We need to adapt this "autopilot" UX for the Gemini Genesis implementation.

### Options Considered

1.  **Maintain Multi-Tool Model**: Keep all methodology operations as top-level Gemini tools (`aisdlc_init`, `aisdlc_iterate`, etc.).
2.  **Orchestrated Two-Verb Model**: Collapse the interface to `aisdlc_start` and `aisdlc_status`, hiding specialized operations behind a state-driven routing logic.
3.  **Chat-Native Flow**: Rely on natural language intent detection to trigger the appropriate methodology steps without explicit verbs.

---

## Decision

**We will adopt the "Two-Verb UX Architecture," implementing `aisdlc_start` as the state-machine controller and `aisdlc_status` as the primary situational awareness tool.**

Key changes:
-   **`aisdlc_status`**: Becomes the "Affect Phase" tool. It runs the State Detection Algorithm (§7.5) to determine if the project is `UNINITIALISED`, `NEEDS_INTENT`, `IN_PROGRESS`, `STUCK`, etc.
-   **`aisdlc_start`**: Becomes the "Reflex Phase" orchestrator. It uses the state detected by `status` to delegate to underlying logic (scaffolding, iteration, recovery).
-   **Encapsulation**: Previous tools (`init`, `iterate`, `spawn`, `review`) are relegated to "Internal Skills" that the orchestrator calls but are not typically invoked directly by the user.

---

## Rationale

### Why This Approach

1.  **Progressive Disclosure (REQ-UX-002)**: The user only sees what they need to do *next*. Tech stack constraints are deferred until the design edge, and recovery steps only appear when the system is stuck.
2.  **Reduced WIP (REQ-UX-004)**: The `start` routing algorithm prioritizes "Closest-to-Complete" features, naturally driving the project toward convergence rather than starting new work.
3.  **Situational Awareness (REQ-UX-003)**: `status` provides a consistent "You Are Here" visualization across all features, regardless of their individual lifecycle stage.
4.  **Self-Healing (REQ-UX-005)**: By running state detection on every `start`, the system can proactively offer recovery options (e.g., "Event log corrupted, want to truncate?") before the user even realizes there is a problem.

---

## Consequences

### Positive

-   **Zero Learning Curve**: New users only need to know one command: `start`.
-   **Agentic Efficiency**: The Gemini Agent can run in `--auto` mode more reliably when it only has to manage a single state-machine loop.
-   **Platform Parity**: Maintains high interoperability with the Claude binding while utilizing Gemini's native agentic strengths.

### Negative

-   **Reduced Granularity**: Power users might occasionally want to skip the routing logic and call `iterate` directly (mitigated by keeping internal tools available for manual override).
-   **Complexity Shift**: The logic for "What to do next" moves from the human's brain to the `aisdlc_start` tool's code.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md) §1.1
- [aisdlc-start.md](../../../claude-code/.claude-plugin/plugins/aisdlc-methodology/v2/commands/aisdlc-start.md)
- [aisdlc-status.md](../../../claude-code/.claude-plugin/plugins/aisdlc-methodology/v2/commands/aisdlc-status.md)
