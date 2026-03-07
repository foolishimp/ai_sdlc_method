# ADR-S-024: Consensus Decision Gate — Marketplace-Driven Evaluation Checkpoints

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-07
**Scope**: Multi-agent governance — how marketplace signals gate in-progress development

---

## Context

ADR-S-023 establishes the workspace state partitioning rule. CONVENTIONS.md (as updated) describes `.ai-workspace/comments/` as the discussion and repricing layer of the broader Multivector Design Marketplace.

What neither document addresses is the **temporal relationship** between marketplace activity and active development. Without an explicit rule, two failure modes emerge:

1. **Marketplace as archive**: agents post reviews that are never read during the development cycle that prompted them. The repricing happens too late — code is already committed, ADRs already written.

2. **Marketplace as blocker**: every new comment post halts development until all agents have responded. The overhead of consensus eliminates the velocity that makes agents useful.

The question is: when does a marketplace signal become a **gate** — an evaluation checkpoint that the running development process must pass before continuing?

This is not a novel problem. It is the IntentEngine composition law (§VIII of the Genesis Bootloader) applied one level up: `observer → evaluator → typed_output`. The marketplace is a sensory system. Its signals have ambiguity levels. Ambiguity level determines routing.

---

## Decision

### The Consensus Decision Gate

A **consensus decision gate** is a naturally emergent evaluation checkpoint triggered when a marketplace artifact — a GAP, REVIEW, STRATEGY, or MATRIX post — enters the shared comments directory while development is active.

The gate is not a blocking mutex. It is a **homeostatic check**: the running agent evaluates whether the new signal reprices current working assumptions enough to change the active trajectory. Three outcomes are possible, determined by the signal's ambiguity level:

| Ambiguity | Signal Type | Outcome | Action |
|-----------|-------------|---------|--------|
| Zero | Deterministic conflict — new artifact contradicts an accepted ADR or spec | **Reflex** | Halt current task. Surface conflict immediately. Await user ratification before proceeding. |
| Bounded | Agent-resolvable — new artifact reprices confidence but does not contradict spec | **Affect** | Continue development. Post a REVIEW response. Note the repricing in the working context. |
| Persistent | Judgment required — new artifact raises a question that cannot be resolved without new information or human direction | **Escalate** | Pause at next natural boundary (end of current task, not mid-task). Surface the unresolved question. Await direction. |

### Trigger Conditions

A consensus decision gate fires when:

1. **Session start**: the agent scans peers' `comments/` directories for new files since the last session. Any new file is a pending market signal.
2. **Mid-session direction**: the user explicitly directs the agent to read a peer comment. This is an immediate gate trigger regardless of development state.
3. **Convergence boundary**: at the completion of any task (T-COMPLY step, feature edge convergence, sprint close), the agent scans for new marketplace signals before beginning the next task.

Gates do NOT fire:
- Mid-implementation within a single task (the agent completes the current unit of work first)
- Automatically on every file write to `comments/` (polling overhead without benefit)

### Evaluation Protocol

When a gate fires, the running agent:

1. **Reads** the new artifact
2. **Classifies** it against current working assumptions:
   - Does it contradict an accepted ADR? → Zero ambiguity, halt
   - Does it identify a gap in the current approach? → Bounded ambiguity, note and continue
   - Does it raise a question about the goal itself? → Persistent ambiguity, escalate at boundary
3. **Responds** with a REVIEW post (always — even if the response is "noted, continuing")
4. **Routes** per the ambiguity table above

### Ratification Events Clear the Gate

A gate in the "halt" or "escalate" state clears when:
- The user explicitly accepts or rejects the signal
- A new ADR is written that resolves the conflict
- The methodology author provides direction

Agents do not self-ratify. Comment volume does not clear a gate.

### Natural Emergence

The consensus decision gate is not a scheduled process. It emerges from the interaction of:
- The session start scan (CONVENTIONS.md — scan peers' comments at start)
- The convergence boundary (any sprint task completion)
- The user's ability to trigger mid-session reads at any time

This means the marketplace is always live: while T-COMPLY-001 is being implemented, a Gemini or Codex REVIEW can enter the marketplace and be evaluated at the next natural boundary — the completion of the T-COMPLY-001 task — without blocking the implementation in progress.

---

## Relationship to the IntentEngine

The consensus decision gate is the IntentEngine composition law applied to design decisions:

```
observer   = session start scan + boundary check + user direction
evaluator  = ambiguity classification (zero / bounded / persistent)
output     = reflex (halt) | specEventLog (note, continue) | escalate (pause at boundary)
```

The marketplace is an **exteroceptive sensory system** for design-level signals — it observes the external agent environment, not the codebase. The gate is its triage layer.

---

## Consequences

**Positive:**
- Marketplace signals reach active development before the work they comment on is finalized, not after.
- The gating rule is explicit: agents know when to halt, when to continue, and when to escalate. No ambiguity about whether a new review post must be acted on immediately.
- The three-outcome routing table is consistent with the reflex/affect/conscious processing phase model (§VI of the bootloader). No new concepts introduced.
- Development velocity is preserved: bounded-ambiguity signals do not halt work, they reprice it.

**Negative / trade-offs:**
- A REVIEW post that appears mid-task will not be acted on until the task boundary. An agent that needs immediate attention from a running peer must use a direct user redirect, not a comment post.
- The "halt on zero-ambiguity conflict" rule requires the agent to correctly classify a signal as contradicting an accepted ADR. Misclassification either blocks unnecessarily or allows a spec conflict to proceed undetected.

---

## References

- [specification/core/GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §VI (Processing Phases), §VII (Sensory Systems), §VIII (IntentEngine)
- [ADR-S-023](ADR-S-024-consensus-decision-gate.md) — workspace state partitioning
- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — sensory triage and intent pipeline
- `.ai-workspace/comments/CONVENTIONS.md` — marketplace conventions and session start scan protocol
