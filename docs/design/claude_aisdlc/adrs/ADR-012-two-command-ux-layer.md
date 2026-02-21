# ADR-012: Two-Command UX Layer

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: foolishimp
**Implements**: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005

---

## Context

The AI SDLC methodology exposes 9 slash commands (`/aisdlc-init`, `/aisdlc-iterate`, `/aisdlc-spawn`, `/aisdlc-status`, `/aisdlc-checkpoint`, `/aisdlc-review`, `/aisdlc-trace`, `/aisdlc-gaps`, `/aisdlc-release`). To use these effectively, the user must know:

1. Which command to invoke
2. The edge syntax (`--edge "requirements→design"`)
3. Feature vector naming conventions (`--feature "REQ-F-AUTH-001"`)
4. The graph topology (which edges exist, which are valid next)
5. Profile semantics (when to use spike vs standard vs hotfix)

Dogfooding (CDME test04) confirmed this is the primary adoption barrier. New users ask two questions: "Where am I?" and "What do I do next?" — they should not need to learn 9 commands to get answers.

## Decision

Add `/aisdlc-start` as a **state-machine controller** that detects project state and delegates to existing commands. Enhance `/aisdlc-status` with **project-wide observability**, "you are here" indicators, and health checks.

The two verbs are:

| Command | Question it answers | Role |
|---------|-------------------|------|
| `/aisdlc-status` | "Where am I?" | Observability — project-wide state, per-feature trajectory, signals, health |
| `/aisdlc-start` | "Go." | Routing — detect state, select feature, determine edge, delegate to iterate/init/spawn/review |

Existing 9 commands remain as **power-user escape hatch**. Start delegates to them; it does not replace them.

## Rationale

The iterate agent and edge configs are the **computational machinery**. Start is the **routing layer**. Status is the **observability layer**. Separation preserves the universal iterate model (one agent, parameterised by edge config) while hiding the parameterisation from the user.

This is consistent with the spec principle that the 4 primitives are universal — the UX layer is parameterisation (how the user interacts), not a new primitive.

**State-driven routing** (REQ-UX-001) ensures the entry point computes what to do from workspace state (filesystem + event log), consistent with the event sourcing model (§7.5 — state derived, not stored).

**Progressive disclosure** (REQ-UX-002) defers configuration until the edge where it is consumed — constraint dimensions at `requirements→design`, not at init. This matches the spec's incremental Layer 3 binding (§2.8).

**Project-wide observability** (REQ-UX-003) adds cross-feature rollup, "you are here" indicators, signal surfacing, and health checks to Status — making it the single observability command.

## Alternatives Considered

### Alternative 1: Replace all 9 commands with Start/Status
- **Rejected**: Breaks power users who need direct edge control (e.g., re-running a specific edge, manual spawn with custom profile). The escape hatch is essential for debugging and non-standard workflows.

### Alternative 2: Auto-wizard with no escape hatch
- **Rejected**: Too opaque. When Start makes a wrong routing decision, the user needs to be able to override it explicitly. Transparency in routing reasoning is a requirement (REQ-UX-004: "selection reasoning displayed to user").

### Alternative 3: Keep all 9 commands as primary UX
- **Rejected**: Current state. Proven adoption barrier. Users must learn graph topology before they can start working.

### Alternative 4: Merge Start into Status (single command)
- **Rejected**: Violates separation of concerns. Status is read-only (observability); Start modifies state (routing + delegation). Combining them would make `--dry-run` semantics confusing and break the principle that observation is separate from action.

## Consequences

### Positive
- New users need only two verbs: Status ("Where am I?") and Start ("Go.")
- Existing power-user workflows are preserved
- State detection is computed (event sourcing), not stored
- Progressive init reduces friction for first-time setup

### Negative
- One additional command to maintain (10 total)
- State machine logic must stay in sync with graph topology
- Auto-mode loop needs careful human gate placement to avoid runaway iteration

### Neutral
- The iterate agent is unchanged — Start delegates to it, does not modify it
- Event emission delegates to underlying commands — no new event types needed

## References

- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §11 — REQ-UX-001 through REQ-UX-005
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §7.5 (Event Sourcing), §7.6 (Self-Observation)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (preserved by this ADR)
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (Start reads topology)
