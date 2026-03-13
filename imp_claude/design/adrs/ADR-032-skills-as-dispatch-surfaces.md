# ADR-032: Skills Are Dispatch Surfaces, Not Execution Recipes

**Status**: Accepted
**Date**: 2026-03-14
**Scope**: imp_claude (Claude Code implementation)
**Implements**: REQ-UX-001, REQ-UX-004, REQ-ITER-001

---

## Context

Genesis skills (gen-start, gen-iterate, gen-gaps, etc.) are markdown files loaded into the LLM's context as slash commands. The LLM reads the skill text and acts on it.

Skills were written with detailed procedural instructions: read these files, rank by recency, walk the topology, determine the next edge, compute convergence, emit events. The intent was to describe what the engine should do so the LLM could invoke it correctly.

The outcome was the opposite. A skill that contains a complete recipe for doing the work will be executed by the LLM reading it — in-context, without invoking the engine. The engine is never called. No real events are emitted. No real F_D evaluation occurs. The LLM produces methodology theatre: plausible outputs with no durable side effects and no homeostatic loop.

**Observable symptom**: no events accumulate in `events.jsonl` across sessions, because the LLM is doing the work itself and the engine — the only thing that actually appends events — is never invoked.

---

## Decision

**Skills are dispatch surfaces. All logic lives in the engine.**

A skill must contain only:

1. **The engine invocation** — the exact shell command to run
2. **The MCP handoff** — what to do if `FpActorResultMissing` is raised
3. **Nothing else**

If a skill text can be "executed" by reading it — if an LLM can follow its instructions and produce correct outputs without calling the engine — the skill is wrong.

### Invariant

> A skill is conformant if and only if removing the engine invocation makes it inert — nothing useful can happen from the text alone.

This is the test. Apply it to every skill. If the skill still works without the Bash call, the logic belongs in the engine, not the skill.

### Correct skill structure

```markdown
# /gen-start

Run the genesis engine.

\`\`\`bash
PYTHONPATH=.genesis python -m genesis start [--auto] [--human-proxy] [--feature F] [--edge E]
\`\`\`

If the engine raises `FpActorResultMissing`:
1. Read `fp_intent_{run_id}.json` from the workspace
2. Call `mcp__claude-code-runner__claude_code` with the manifest as prompt
3. The actor writes `fp_result_{run_id}.json`
4. Re-invoke the engine (loop to step 1)

If the engine exits with convergence: done.
If the engine exits with F_H gate: surface the gate to the human. Wait.
```

That is the entire skill. ~15 lines. No algorithms. No file-reading instructions. No feature selection logic. No event schemas.

### What moves into the engine

Everything currently in skill text that describes logic:

| Currently in skill | Moves to |
|-------------------|----------|
| State detection algorithm | `python -m genesis start` (new subcommand) |
| Feature selection (rank by recency, priority) | `genesis/engine.py` or `genesis/intent_observer.py` |
| Edge determination (walk topology, skip converged) | `genesis/edge_runner.py` |
| Auto-loop (iterate → check → next edge → repeat) | `python -m genesis start --auto` |
| Human proxy evaluation | `python -m genesis start --human-proxy` |
| Event emission | `genesis/engine.py` (already there) |
| Gap detection algorithms | `python -m genesis gaps` (new subcommand) |
| Convergence detection | `genesis/engine.py` (already there) |

The LLM layer retains exactly one responsibility: **MCP dispatch** — calling `mcp__claude-code-runner__claude_code` when the engine signals that F_P construction is needed. This is the only thing the engine cannot do itself (ADR-023: no subprocess, no `claude -p`).

---

## Consequences

### Skills become stable

A 15-line skill does not need to be updated when methodology logic changes. Logic changes go into the engine and are tested there. Skills are updated only when the invocation interface changes.

### Events become real

The engine is the only thing that appends to `events.jsonl`. When the engine is always invoked, events always accumulate. The homeostatic loop closes. Sessions are resumable. Overnight runs produce durable state.

### F_D evaluation becomes real

Currently the LLM reads checklist items and self-reports pass/fail. When the engine is always invoked, F_D evaluation runs actual tests, actual schema checks, actual deterministic gates. The LLM cannot override F_D results — it can only respond to them.

### The engine becomes the methodology

The engine encodes the methodology. The skills are the UX surface. This separation is the same as the spec/design boundary: spec says WHAT (engine logic), design says HOW (skill dispatch). A skill that contains methodology logic conflates the two.

---

## Implementation Contract

Every skill must be rewritten to satisfy the dispatch-surface invariant before it can be considered conformant.

Checklist:
- [ ] Skill invokes the engine via Bash in its first substantive step
- [ ] Skill contains no feature-selection logic
- [ ] Skill contains no edge-determination logic
- [ ] Skill contains no event-emission instructions
- [ ] Skill contains no convergence-detection logic
- [ ] Skill contains no file-reading instructions beyond what is needed to parameterise the engine call
- [ ] Applying the inertness test: removing the Bash call makes the skill inert

The MCP handoff (FpActorResultMissing → dispatch actor → fold-back) is the one legitimate in-skill logic block, because it is the one thing the engine structurally cannot do.

---

## Related

- ADR-S-023: No subprocess / no `claude -p` — why MCP is the F_P transport
- ADR-S-032: IntentObserver + EdgeRunner dispatch contract — engine internals
- ADR-S-037: Projection authority — why engine-emitted events are the source of truth
- ADR-S-038: Natural language intent dispatch — NL routing to engine invocations
