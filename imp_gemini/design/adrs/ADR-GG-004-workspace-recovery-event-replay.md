# ADR-GG-004: Workspace Recovery via Event Replay

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-TOOL-008 (Context Snapshot), REQ-INTENT-004 (Spec Reproducibility), **REQ-TOOL-NEW-001 (Restore)**

---

## Context

The AI SDLC Asset Graph Model relies on **Event Sourcing** (`events.jsonl`) as the immutable source of truth. All other workspace artifacts (feature vector files, `STATUS.md`, `ACTIVE_TASKS.md`) are derived projections.

The Claude Code implementation provides `/aisdlc-checkpoint` for snapshots, but lacks a formal "recovery" or "restore" command. This creates a gap in the "Spec Reproducibility" requirement—if a derived view is corrupted or deleted, there is no tool to reconstruct it.

Gemini CLI has the ability to run sophisticated Python scripts as tools, which can manipulate the local filesystem and state.

### Options Considered

1.  **Manual Git-based Recovery**: Rely on standard Git operations (`checkout`, `reset`) for project recovery.
2.  **Snapshot-only Restore**: Implement a tool that only restores files from the most recent `.ai-workspace/snapshots/` file.
3.  **Hybrid Event Replay (Reconstruction)**: Implement a tool that can both restore from snapshots AND reconstruct derived state by replaying the entire `events.jsonl` log.

---

## Decision

**We will implement a native `aisdlc_restore` Tool that uses Event Replay to reconstruct the workspace's derived state.**

Workflow:
1.  **Read Log**: The Tool reads the append-only `.ai-workspace/events/events.jsonl`.
2.  **Clear Projections**: If `reconstruct=true` is requested, the Tool clears the derived directories (`.ai-workspace/features/active`, `.ai-workspace/tasks/active`, `STATUS.md`).
3.  **Replay Events**: The Tool iterates through every JSON event in the log, sequentially updating the in-memory state of each feature vector and task.
4.  **Emit Assets**: The final state is written back to the workspace as fresh files.

---

## Rationale

### Why This Approach (vs Snapshot Only)

1.  **Full Traceability**: Snapshot-only recovery can lose fine-grained iteration data if a checkpoint wasn't created recently. Event Replay ensures *every* converged iteration is recovered.
2.  **Self-Healing**: It allows the methodology to "heal" from accidental deletions of the `.ai-workspace` sub-directories without needing Git-level intervention.
3.  **Spec Reproducibility**: It proves that the "Source of Truth" is indeed the event log, fulfilling REQ-INTENT-004 by demonstrating that the project state is deterministic and reconstructible from its inputs.
4.  **Auditing**: Replay provides a mechanism for "Time Travel" debugging—allowing a developer to reconstruct the project as it existed at any specific event ID or timestamp.

---

## Consequences

### Positive

-   **Robustness**: The project is highly resilient to local state corruption.
-   **Verification**: Replay acts as a continuous verification of the event schema's integrity.
-   **Transparency**: The relationship between the event log and the derived views is explicitly coded and maintainable.

### Negative

-   **Replay Time**: On very large projects with thousands of iterations, replaying the entire log could be slow (mitigated by starting from the most recent "Checkpoint" event).
-   **Implementation Complexity**: Requires a robust parser and state-machine for the 16+ event types.

### Mitigation

-   Implement **Snapshot Anchoring**: The `aisdlc_restore` tool will find the most recent `checkpoint_created` event and start replaying only from that point forward, using the snapshot as the base state.
-   The Tool will be implemented in Python for speed and easier JSON manipulation.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md) §2.2
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §7.5 (Event Sourcing)
