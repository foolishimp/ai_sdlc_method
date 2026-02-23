# ADR-013: Multi-Agent Coordination — Immutability over Mutexes

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Claude (Lead Engineer), with review by Codex and Gemini
**Requirements**: REQ-COORD-001 (Agent Identity), REQ-COORD-002 (Feature Assignment via Events), REQ-COORD-003 (Work Isolation), REQ-COORD-004 (Markov-Aligned Parallelism), REQ-COORD-005 (Role-Based Evaluator Authority)
**Supersedes**: None (new capability)

---

## Context

As the AI SDLC transitions from a single-agent "pilot" to a multi-agent "fleet," we must ensure that concurrent agents do not corrupt project state or perform redundant work. Traditionally, this is solved via filesystem locks (mutexes) or distributed lock managers.

However, Project Genesis is built on **Event Sourcing** and **Spec Reproducibility**. Introducing stateful locks would compromise the ability to replay the project from its logs and would introduce platform-specific dependencies.

Two sibling implementations (Gemini Genesis and Codex Genesis) independently proposed multi-agent coordination mechanisms. This ADR synthesises the best of both.

### Options Considered

1. **Filesystem Mutexes (`.lock` files)**: Simple but prone to ghost locks on crash, not replayable, platform-specific.
2. **Central Coordination Service**: Requires persistent background process (violates CLI-first ethos).
3. **Optimistic Concurrency (Gemini proposal)**: Atomic O_APPEND to shared events.jsonl, detect conflicts after the fact. Risk: POSIX atomicity only guaranteed up to PIPE_BUF (~4KB).
4. **Lease Protocol with Lock Files (Codex proposal)**: Explicit `.lock` files with TTL and heartbeat. Contradicts immutability principle.
5. **Immutable Event-Sourced Claims with Inbox Staging (this ADR)**: Claims are events. A single-writer serialiser resolves conflicts. No locks. All state derivable from the event log.

---

## Decision

**We will implement coordination via immutable event-sourced claims with inbox staging and a single-writer serialiser. No lock files. All coordination state is derivable from the event log.**

### Canonical Event Flow

```
Agent A                    Agent B
   │                          │
   ▼                          ▼
┌──────────────┐       ┌──────────────┐
│ inbox/a-01/  │       │ inbox/b-01/  │
│ edge_claim   │       │ edge_claim   │
└──────┬───────┘       └──────┬───────┘
       └──────────┬───────────┘
                  │
         SERIALISER (single writer)
                  │
                  ▼
         events/events.jsonl
         ├── edge_started  (A granted)
         └── claim_rejected (B conflict)
```

### Claim Protocol

1. Agent emits `edge_claim` to its inbox: `{agent_id, agent_role, feature, edge}`
2. Serialiser reads inboxes in **ingestion order** (lexicographic `agent_id` order, then filesystem modification time within each inbox — no clock-skew dependency). Implementations MAY use monotonic sequence numbers on inbox entries for strict replay-stability across platforms.
3. If feature+edge is unclaimed → serialiser writes `edge_started` with `agent_id` to events.jsonl
4. If feature+edge is already claimed → serialiser writes `claim_rejected` with `reason` and holding agent
5. Agent reads events.jsonl (or its projection) to confirm assignment before iterating
6. On convergence → agent emits `edge_converged` → serialiser writes to log → claim released
7. On abandonment → agent emits `edge_released` → claim freed

### Single-Agent Mode (Backward Compatible)

The invariant is **"events.jsonl has exactly one writer."**

- In single-agent mode: the agent IS the sole writer. No inbox, no serialiser, no claim step. Agent emits `edge_started` directly. `agent_id` defaults to `"primary"`, `agent_role` defaults to `"full_stack"`.
- In multi-agent mode: the serialiser is the sole writer. Agents write only to their inbox.

Both modes satisfy the invariant. The event log format is identical — multi-agent fields are optional and additive.

### Inbox Semantics

The inbox (`events/inbox/<agent_id>/`) is a **non-authoritative write buffer**, not coordination state:

- It is analogous to a filesystem write cache
- If an inbox is deleted, only unprocessed events are lost — the event log retains all truth
- Inboxes are not replayed during recovery — only `events.jsonl` is
- The serialiser may run continuously (fswatch trigger) or on-demand

### Stale Claim Detection

No heartbeat files. The serialiser checks time since last event from each active agent. If no event within configurable timeout → `claim_expired` telemetry signal emitted to events.jsonl. Stale claims are not auto-released — human decides.

### Work Isolation and Promotion

Agents iterate in `agents/<agent_id>/drafts/`. Promotion to shared state requires:
- All evaluators for the edge pass
- Human review for: spec mutations, new ADRs, edges with `human_required: true`
- Serialiser updates feature vector and derived views on `edge_converged`

Agent state is ephemeral. On crash, only emitted events persist. Drafts and scratch are disposable.

### Role-Based Evaluator Authority

`agent_roles.yml` maps roles to convergence authority:

```yaml
roles:
  architect:
    converge_edges: [intent_requirements, requirements_design, design_code]
  tdd_engineer:
    converge_edges: [code_unit_tests, design_test_cases]
  full_stack:
    converge_edges: [all]  # single-agent backward compat
```

Convergence outside authority → `convergence_escalated` event → held for human approval.

### Markov-Aligned Parallelism

`/gen-start` in multi-agent mode uses the inner product (spec §6.7) to route agents:

- **Zero inner product** (no shared modules): freely assign to parallel agents
- **Non-zero inner product** (shared modules): warn, suggest sequential ordering
- Feature priority tiers (closest-to-complete first) apply per-agent, skipping already-claimed features

---

## Rationale

### Why Immutability (vs Mutexes)

1. **Platform agnostic**: No OS-specific lock semantics. Works on POSIX, Windows, containerised environments.
2. **Auditability**: The history of "who worked on what and when" is preserved in the immutable log forever. Mutexes leave no trace.
3. **Self-healing**: If an agent dies mid-iteration, there is no stale lock to clean up. Other agents see the lack of progress and the serialiser emits `claim_expired`.
4. **Time-travel support**: Event replay reconstructs project state at any point.
5. **Stateless recovery**: Replay events.jsonl → derive all assignments, feature states, and derived views.

### What We Took From Each Proposal

| From Gemini | From Codex | Original (Claude) |
|-------------|------------|-------------------|
| Agent registry concept | Inbox/serialiser pattern | Event-sourced claims (no locks) |
| Cross-agent signals via events | Promotion via review gate | Markov-aligned assignment |
| Agent-private drafts | Spec mutation requires human gate | Role-based evaluator authority |
| "Immutability over Mutexes" framing | Single serialiser for derived views | Inner product for parallelism |

---

## Consequences

### Positive

- **Zero deadlocks**: No locks means no deadlocks.
- **High concurrency**: Orthogonal features (zero inner product) run with zero coordination overhead.
- **Markov alignment**: Agents coordinate at the boundaries of converged assets, not through internal state.
- **Backward compatible**: Single-agent mode works unchanged.
- **Platform-portable**: Identical workspace and event format across Claude, Gemini, Codex.

### Negative

- **Merge resolution**: If two agents claim the same feature+edge simultaneously, one gets `claim_rejected` and must re-route (by design — not a bug).
- **Log density**: Coordination events (`edge_claim`, `claim_rejected`, `claim_expired`) increase events.jsonl volume.
- **Serialiser is a single point of serialisation**: All events funnel through it. Mitigation: serialiser is lightweight (JSON append), agents are never blocked — they continue working and the serialiser catches up.
- **Eventual consistency**: Agents see assignments only after serialiser runs. Mitigation: serialiser can run on every inbox write (fswatch).

---

## New Event Types

This ADR introduces 5 new event types to the canonical catalogue:

| Event Type | Where Written | Purpose |
|-----------|---------------|---------|
| `edge_claim` | Inbox only (not in events.jsonl) | Agent proposes to work on feature+edge |
| `claim_rejected` | events.jsonl (by serialiser) | Conflict: feature+edge already claimed |
| `edge_released` | events.jsonl (by serialiser) | Agent voluntarily abandons claim |
| `claim_expired` | events.jsonl (by serialiser) | Stale claim detected (telemetry signal) |
| `convergence_escalated` | events.jsonl (by serialiser) | Agent tried to converge outside role authority |

Note: `edge_claim` is **inbox-local** — it never appears in the canonical event log. The serialiser transforms it into `edge_started` (success) or `claim_rejected` (conflict). This distinction is important: the event log contains only resolved facts, not proposals.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §6.7 (Basis Projections), §7.5 (Event Sourcing), §7.7.6 (Markov Boundaries)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §12 (Multi-Agent Coordination)
- [GEMINI_GENESIS_DESIGN.md](../../../imp_gemini/design/GEMINI_GENESIS_DESIGN.md) — agent registry, cross-agent signals, "Immutability over Mutexes" framing
- [ADR-GG-006](../../../imp_gemini/design/adrs/ADR-GG-006-multi-tenant-workspace.md) — design-level multi-tenancy (complementary concern)
- Codex Genesis handoff draft — inbox/serialiser, review-gated promotion
