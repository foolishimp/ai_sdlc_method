# ADR-001: Bootstrap Architecture

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-F-BOOT-001, REQ-F-BOOT-002

---

## Context
We need a robust mechanism to manage the "Two-Verb UX" (Start and Status) for Gemini CLI. The methodology has moved from a toolbox approach to an orchestrated, state-driven approach.

## Decision
We will implement a **Centralized State Manager** that is shared between `aisdlc_start` and `aisdlc_status`.

### Alternatives Considered
1.  **Distributed State Detection**: Each tool calculates state independently. (Rejected: Inconsistent routing risk).
2.  **Persistent State File**: Store the current state in a `.state.yml` file. (Rejected: Violates "State is derived from events" principle §7.5).

## Rationale
Using a centralized but transient State Manager ensures that both verbs always agree on "Where we are" and "What to do next" while remaining fully compliant with the event-sourcing source of truth.

## Consequences
- **Positive**: High consistency, simplified testing of state transitions.
- **Negative**: Slight overhead in parsing `events.jsonl` on every invocation (mitigated by line-streaming).
