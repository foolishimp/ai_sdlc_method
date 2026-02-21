# ADR-GG-007: Sensory Review Boundary and Homeostatic Proposals

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SENSE-003 (Affect Triage), REQ-SENSE-005 (Review Boundary), REQ-LIFE-003 (Feedback Loop Closure)

---

## Context

The Asset Graph Model v2.6 introduces a formal **Review Boundary** (§4.5.4) between autonomous sensing and human-approved changes. The Sensory Service detects deviations, triages them (Affect Phase), and generates **Draft Proposals** (intents, diffs, spec modifications). These proposals *must not* modify the workspace until a human approves them.

In Gemini CLI, we need a native way to manage this boundary that is more structured than a simple "yes/no" chat prompt.

### Options Considered

1.  **Direct Intent Injection**: Have the sensor directly emit `intent_raised` events (Rejected: Violates Human Accountability REQ-EVAL-003).
2.  **Proposal Queue Tool**: A tool (`aisdlc_proposals`) that lists pending sensory observations and uses `ask_user` for approval.
3.  **Automatic Branching**: Each proposal creates a temporary git branch (Rejected: Too much overhead for minor sensory signals).

---

## Decision

**We will implement the Review Boundary as a dedicated `aisdlc_proposals` Tool that manages the lifecycle of homeostatic draft proposals.**

Workflow:
1.  **Drafting**: The background Sensory Service (§ADR-GG-005) writes `draft_proposal` events to `events.jsonl`.
2.  **Notification**: When the user starts a session, Gemini checks for new `draft_proposal` events.
3.  **Review**: The user invokes `aisdlc_proposals()`.
4.  **Structured Selection**: The tool uses `ask_user(type="choice")` to present each proposal with its trigger (e.g., "CVE found in requests") and proposed action (e.g., "Bump version to 2.32.0").
5.  **Execution**: Upon approval, the tool:
    -   Emits the `intent_raised` event.
    -   Applies any proposed file diffs or spec modifications.
    -   Updates the proposal status to `approved` in the event log.

---

## Rationale

### Why This Approach

1.  **Safety**: It ensures the "Autonomic Nervous System" (sensors) remains subordinate to the "Conscious Phase" (human).
2.  **Structured Triage**: By using `ask_user`, we can provide the human with clear context (signal source, severity, impact) for each proposal.
3.  **Traceability**: Every approved proposal carries the ID of the triggering sensory signal, closing the loop from Production → Sensor → Human → Spec.
4.  **Multi-tenancy Integration**: Proposals are scoped to the active design tenant, as different designs might have different sensory monitors or thresholds.

---

## Consequences

### Positive

-   **High-Signal Homeostasis**: The system proactively suggests fixes for drift/vulnerabilities, but the human remains the final arbiter.
-   **Reduced Cognitive Load**: Developers don't have to manually check for CVEs or staleness; they simply review the system's own "self-diagnosis."

### Negative

-   **Proposal Accumulation**: If the user ignores the proposals, the queue could grow large (mitigated by a "Dismiss All" option).

### Mitigation

-   The `aisdlc_status` tool will include a "Homeostasis" section showing the count of pending proposals.
-   The Sensory Service will include "Supersede" logic: if a newer signal makes an older proposal obsolete, the older one is marked as `superseded`.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md) §2.3
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5.4 (Sensory Service Architecture)
