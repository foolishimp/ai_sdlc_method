# ADR-021: Dual-Mode Traverse — Interactive vs Engine

**Series**: imp_claude (Claude Code implementation decisions)
**Status**: Accepted
**Date**: 2026-03-03
**Scope**: `gen-iterate` command, engine CLI (`genesis evaluate`), hooks, feature vector schema, event emission path

---

## Context

The methodology defines `iterate(Asset, Context[], Evaluators) → Asset'` as the single operation. The **executor** of that operation was previously left implicit — whatever Claude Code does in a session. Two distinct execution paths have emerged in practice:

**Path 1 — Interactive Traverse**: A Claude Code conversational session where the LLM constructs and evaluates artifacts interactively. Protocol enforcement relies on hooks (Stop, PostToolUse, UserPromptSubmit) to verify that events were emitted, feature vectors updated, and STATUS.md regenerated.

**Path 2 — Engine Traverse**: The `genesis evaluate` CLI invokes headless `claude -p` for F_P construction, runs F_D deterministic checks directly in code, and emits events as Level 4 guaranteed side effects. No hooks involved — protocol enforcement is a code invariant.

Three problems with the current implicit single-path model:

1. **Hook overhead scales with session activity.** `PostToolUse[Write|Edit]` fires on every artifact write, generating hundreds of `artifact_modified` events in a single ADR-writing session. `UserPromptSubmit` fires on every message. The overhead is constant even when no edge traversal is in progress.

2. **Hooks misfire on advisory sessions.** Hooks detect edge-context from `--edge` patterns in prompts. Analytical conversations (e.g., pasted Gemini proposals containing `--edge` syntax) set edge context, then the Stop hook blocks on protocol completion for work that was never done.

3. **Hook reliability is lower than engine reliability.** Hooks are Level 1/2 (agent instruction and process boundary). Engine events are Level 4 (deterministic code). For mechanical edges (code↔tests, CI/CD), the engine path is strictly more reliable. Using hooks to enforce protocol on engine-appropriate edges is the wrong tool.

---

## Decision

### Two explicit traverse modes

`gen-iterate` accepts a `--mode` flag that selects the executor:

| Mode | Flag | Executor | Protocol enforcement | Event level |
|------|------|----------|---------------------|-------------|
| **Interactive** | `--mode interactive` (default) | Claude Code conversation | Hooks (Stop checks, PostToolUse observation) | Level 1/2 |
| **Engine** | `--mode engine` | `genesis evaluate --construct` subprocess | Code invariants in engine | Level 4 |
| **Auto** | `--mode auto` | Dispatcher selects by edge-mode affinity | Inherits from selected mode | Mixed |

### Edge-mode affinity

The dispatcher (`--mode auto`) selects mode based on the edge being traversed:

| Edge | Affinity | Reason |
|------|----------|--------|
| `intent→requirements` | Interactive | Judgment-heavy; ambiguity resolution requires conversational exploration |
| `requirements→feature_decomposition` | Interactive | Scoping decisions; human review gate |
| `feature_decomposition→design` | Interactive | ADR writing; constraint surface; ecosystem binding |
| `design→module_decomposition` | Interactive | Architecture decomposition; human-approved module structure |
| `module_decomposition→basis_projections` | Interactive | Interface contracts; human approval required |
| `design→code` | **Engine** | F_P construct + F_D evaluate — mechanical once design is clear |
| `code↔unit_tests` | **Engine** | Pure F_D (pytest, coverage, lint, format, type_check) |
| `uat_tests` | Interactive | Human scenario validation by definition |
| `cicd` | **Engine** | Pipeline automation; deterministic build checks |

`Design → Code` is the canonical **hybrid point**: Interactive sessions produce the design (ADRs, constraints); the engine executes the construction loop.

### Interactive mode — hooks scoped correctly

Hooks fire **only** during Interactive traverse. They are the protocol enforcement mechanism for conversational sessions.

- `SessionStart` hook: workspace health check — always fires (low cost, always useful)
- `UserPromptSubmit` hook: edge context recording — fires but sets `.edge_in_progress` **only if `--mode interactive` is present or implied**
- `PostToolUse[Write|Edit]` hook: artifact observation — fires only during Interactive traversals (engine traversals use `genesis evaluate` subprocess, not Write/Edit tools)
- `Stop` hook: protocol verification — fires, but `.edge_in_progress` only exists for Interactive traversals

In practice: removing `UserPromptSubmit` and `PostToolUse` from `hooks.json` is equivalent to "engine and advisory sessions have no hook overhead." Only `SessionStart` and `Stop` remain, and `Stop` is a no-op when no edge context is recorded.

### Engine mode — protocol in code

> **Transport update (ADR-024):** The construct step below originally used `claude -p` subprocess. ADR-024 supersedes that: F_P construct is now an MCP actor invocation (when `CLAUDE_CODE_SSE_PORT` is present) or skipped (no fallback subprocess). ADR-024 is the authority for F_P transport; this section describes the *structure* of engine mode, not the transport mechanism.

When `--mode engine` is selected, `gen-iterate` executes:

```
python -m genesis evaluate \
  --edge "{edge}" \
  --feature "{feature_id}" \
  --construct \
  --fd-timeout 120
```

The engine is responsible for:

1. **Construct**: Invoke F_P actor (MCP, per ADR-024) to generate/modify the asset
2. **Evaluate**: Run all F_D checks (pytest, coverage, lint, format, type_check)
3. **Emit**: Write `iteration_completed` event (OL format, ADR-S-011) to `events.jsonl` — Level 4 guaranteed
4. **Update**: Write trajectory update to the feature vector `.yml`
5. **Report**: Return JSON result to the calling interactive session

The interactive session reads the engine output and surfaces it to the user:

```
Engine result: REQ-F-FP-001 design→code
  delta: 0 — converged
  12/12 checks pass (8 F_D, 4 F_P)
  Event emitted: iteration_completed (run_id: uuid)
  Feature vector updated: .ai-workspace/features/active/REQ-F-FP-001.yml
```

### "Trigger headless from interactive" pattern

The common use case — user in Claude Code asks to implement a feature vector's code edge:

```
User: "implement REQ-F-FP-001 design→code"

gen-iterate detects: code edge → engine affinity
gen-iterate invokes:
  [Bash tool] python -m genesis evaluate \
    --edge "design→code" --feature REQ-F-FP-001 --construct

Engine runs:
  F_P construct (MCP actor, per ADR-024 — no claude -p)
  F_D evaluate (pytest, coverage, lint, format, type_check)
  emits OL RunEvent to events.jsonl (Level 4)
  updates REQ-F-FP-001.yml trajectory

gen-iterate reads engine output:
  surfaces result to user
  Stop hook: .edge_in_progress not set → no block
```

The Stop hook does **not** fire for engine traversals because no `.edge_in_progress` file is written. The engine owns its own protocol enforcement.

### Feature vector `mode` field

The trajectory for each edge records which mode was used. This enables mode-switch reasoning and audit:

```yaml
trajectory:
  code:
    status: converged
    mode: engine            # interactive | engine | hybrid
    iteration: 1
    started_at: "2026-03-03T10:00:00Z"
    converged_at: "2026-03-03T10:05:00Z"
    engine_run_id: "uuid-v4"    # OL run ID, present for engine mode
    delta: 0
```

`hybrid` mode means: started as one mode, switched to the other within the same edge (e.g., interactive exploration → engine construction loop).

### OL event emission (ADR-S-011)

Both modes emit OL-format events (ADR-S-011):

**Interactive mode** — emitted by agent instruction (Level 1), validated by Stop hook:
```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-03-03T10:05:00Z",
  "run": {
    "runId": "uuid-v4",
    "facets": {
      "sdlc:event_type": {"type": "edge_converged"},
      "sdlc:delta": {"delta": 0, "required_failing": 0, "total_checks": 12, "passed": 12},
      "sdlc:req_keys": {"implements": ["REQ-F-FP-001"], "validates": []}
    }
  },
  "job": {"namespace": "aisdlc://ai_sdlc_method", "name": "design→code"},
  "inputs": [{"namespace": "file:///path/to/project", "name": "imp_claude/design/adrs/ADR-020-fp-construct.md"}],
  "outputs": [{"namespace": "file:///path/to/project", "name": "imp_claude/code/genesis/fp_construct.py"}],
  "producer": "https://github.com/foolishimp/ai_sdlc_method"
}
```

**Engine mode** — emitted by deterministic code (Level 4), no hook required:
Same schema. The `run.runId` is generated by the engine at invocation time. The `engine_run_id` in the feature vector matches this UUID, linking the vector state to the event log entry.

---

## Consequences

**Positive:**
- **Hook overhead eliminated for engine-appropriate edges.** code↔tests and cicd edges — the high-frequency mechanical work — run without any hook overhead.
- **No more advisory session misfires.** Analytical conversations don't set edge context; the Stop hook is a no-op when `.edge_in_progress` is absent.
- **Higher reliability for code edges.** Level 4 engine events replace Level 1 agent-instructed events for mechanical construction. The engine cannot "forget" to emit an event.
- **Clear mode audit.** The `mode` field in the feature vector trajectory records which executor was used per edge. Mode-switch patterns are observable.
- **Interactive sessions stay clean.** Removing `UserPromptSubmit` and `PostToolUse` hooks eliminates ~399 `artifact_modified` events per session (61% of event log volume). STATUS.md regeneration becomes intentional, not triggered by every file write.

**Negative / Trade-offs:**
- **Engine must write feature vectors.** Currently `genesis evaluate` emits events but does not update `.yml` trajectory files. This is a gap that must be closed before engine mode is production-ready (see Gaps below).
- **Mode selection adds UX complexity.** `--mode auto` mitigates this, but users must understand why some edges run differently.
- **Interactive convergence is less verifiable.** Without the PostToolUse hook, there is no automatic observation of which files changed during an interactive traversal. This is acceptable — interactive mode is for judgment-heavy edges where the human is the primary evaluator.

### Implementation gaps (follow-on work)

The following are required for engine mode to be fully production-ready. They are not blocking adoption of the dual-mode architecture:

1. **Feature vector write-back**: `genesis evaluate` must write trajectory updates to `.yml` after each iteration. Currently it emits events but does not update the feature vector.
2. **STATUS.md regeneration trigger**: Engine must invoke `gen-status --gantt` (or an equivalent) after `COMPLETE` events to keep the derived view current.
3. **Workspace health at engine startup**: Engine startup should run the equivalent of the SessionStart hook check (validate events.jsonl integrity, detect abandoned iterations) before executing.

---

## Alternatives Considered

**Keep hooks, fix the misfiring**: Tighten `UserPromptSubmit` to only fire when prompt starts with `/gen-iterate`. Rejected — this is a band-aid. The architectural mismatch remains: hooks are the wrong enforcement mechanism for engine-appropriate edges.

**Remove all hooks immediately**: Simpler, but loses the SessionStart workspace health check which is genuinely useful for interactive sessions. Rejected — `SessionStart` provides low-cost, high-value session initialisation feedback.

**Engine mode only (no interactive traverse)**: Full engine automation for all edges. Rejected — design, requirements, and UAT edges require human judgment and conversational exploration. Interactive mode is not a legacy path — it is the correct executor for judgment-heavy edges.

**Mode selection as a feature vector property (not per-invocation)**: Set mode in the feature vector definition, not in the `gen-iterate` call. This would enforce consistency across a feature's full lifecycle. Deferred — per-invocation mode flag is simpler for the transition period and allows experimentation before hardening.

---

## References

- [ADR-S-011](../../specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md) — OL event schema used by both modes
- [ADR-S-008](../../specification/adrs/ADR-S-008-sensory-triage-intent-pipeline.md) — homeostasis pipeline; engine mode must emit homeostasis events in OL format
- [ADR-019](ADR-019-orthogonal-projection-reliability.md) — engine + LLM orthogonal projections; dual-mode traverse is the UX expression of this
- [ADR-020](ADR-020-fp-construct-batched-evaluate.md) — F_P construct; engine mode uses `genesis evaluate --construct` which calls the F_P construct path
- [ADR-017](ADR-017-functor-based-execution-model.md) — functor categories (F_D, F_P, F_H); mode affinity table maps to functor types
- `imp_claude/code/genesis/__main__.py` — engine CLI entry point
- `imp_claude/code/.claude-plugin/plugins/genesis/hooks/hooks.json` — hook definitions being scoped by this ADR
