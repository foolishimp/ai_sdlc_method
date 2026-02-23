# ADR-015: Sensory Service Technology Binding — Gemini CLI Tools + Background Tasks

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
**Extends**: ADR-014 (IntentEngine Binding)

---

## Context

The specification (§4.5.4) defines the sensory service as a **long-running service** with five capabilities: workspace watching, monitor scheduling, affect triage, homeostatic response generation, and review boundary exposure.

This ADR records the Gemini CLI implementation's binding of those abstract concepts to concrete platform technologies.

---

## Decision

### Sensory Service: Integrated Background Tasks

The sensory service in Gemini CLI runs as a set of **integrated monitors** that can be invoked:
1. **On-demand** via `/gen-status` or `/gen-start`.
2. **Asynchronously** as background shell commands (`is_background: true`).
3. **Automatically** as protocol hooks (e.g., `on-iterate-start`).

**Realisation:**
- **Monitors:** Pure Python functions in `internal/workspace_state.py` or shell scripts in `hooks/`.
- **Affect Triage:** Rule-based matching in `internal/state_machine.py`.
- **Review Boundary:** Surfaced via `STATUS.md` and `ask_user` tool.

### Probabilistic Agent: Gemini Agent

For signals that require probabilistic classification or homeostatic response generation, the system invokes a **Gemini Agent** (the same model as the iterate agent).

**Invocation points:**
1. **Affect triage (ambiguous signals)** — when rule-based classification is insufficient.
2. **Draft proposal generation** — generating `draft_intent_raised` events.

### Review Boundary: Command Interface

The review boundary is implemented as interactions within the Gemini CLI session:

| Action | Gemini CLI realisation |
|----------|---------|
| View Status | `/gen-status` command, which reads `STATUS.md` |
| View Proposals | `/gen-status --proposals` or reading `events.jsonl` |
| Approve Proposal | User gives Directive to implement the proposed intent |
| Dismiss Proposal | User explicitly rejects the proposal in chat |

---

## Rationale

### Why This Binding

Gemini CLI is an interactive agent. Using its native tool calling and background execution capabilities is more efficient than building a separate long-running service for the MVP.

---

## Consequences

### Positive

- **Native integration** — uses standard Gemini CLI tools and hooks.
- **Low overhead** — no separate service to manage for small projects.
- **Observable** — all signals produce events in `events.jsonl`.

### Negative

- **Not truly "always-on"** — sensing primarily happens during active sessions or via background tasks started during a session.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5 (Sensory Systems)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding
