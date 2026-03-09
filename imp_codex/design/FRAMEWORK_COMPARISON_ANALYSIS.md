# Framework Comparison Analysis: Prompt-Native Codex vs Executable Runtime

**Date**: 2026-03-09
**Version**: 1.0.0
**Subject**: Which parts of Genesis should stay in the Codex session, and which should live in `imp_codex/runtime/`

---

## 1. The Two Frameworks

### 1.1 Prompt-Native Codex Session

One Codex conversation drives the methodology loop directly:
- reads project files,
- reasons over edge configs and profiles,
- constructs or edits artifacts,
- runs tools,
- asks for human input when needed,
- decides what to do next.

This is the closest Codex analogue to Claude's "single in-session orchestration" model. The key difference is that Codex already has tool-calling and patch application inside the main session, so it does not need a second CLI process to access deterministic tools.

### 1.2 Executable Codex Runtime

The Python runtime in `imp_codex/runtime/` handles the replayable part of the methodology:
- workspace bootstrap,
- event emission,
- state detection,
- evaluator execution,
- feature vector updates,
- projection rebuilding,
- review/spawn/fold-back bookkeeping,
- release and trace reports.

This is not just a stub. It already provides a machine-readable deterministic substrate that the prompt-native workflow can delegate to.

### 1.3 Missing Middle: Reusable Skill Behaviors

The Codex tenant also needs a stable reusable behavior layer between raw command
invocation and ad hoc in-session reasoning.

This is not a return to v1 stage-specific skills. It is:

- reusable construct/evaluate/review behavior,
- shared across commands and edges,
- small enough to compose,
- explicit enough to keep methodology semantics out of one-off prompts.

---

## 2. What Each Framework Actually Does

| Capability | Prompt-Native Codex Session | Reusable Skill Behaviors | Executable Runtime |
|-----------|------------------------------|---------------------------|--------------------|
| Read arbitrary workspace context | Yes | Context-specific | Indirectly through helpers |
| Construct artifacts | Yes | Yes | Not yet |
| Run deterministic checks | Yes, via tools | Can invoke | Yes, via `run_deterministic_checks()` |
| Run heuristic agent checks | Yes | Yes | Yes |
| Emit canonical RunEvents | Possible but ad hoc | No | Yes, standardized |
| Rebuild projections | Possible but manual | No | Yes |
| Record human review decision | Conversationally | Review prep only | Yes, `gen_review()` |
| Spawn/fold-back bookkeeping | Possible | No | Yes |
| Produce stable JSON outputs | No | No | Yes |
| Enforce replay-oriented state model | Weak | Medium | Strong |

---

## 3. Cost Model

### 3.1 Prompt-Native Session Cost

Advantages:
- richest construction context,
- zero impedance mismatch between reasoning and file edits,
- easiest place to perform disambiguation and exploratory design work.

Costs:
- harder to replay exactly,
- easier to drift into undocumented side effects,
- less suitable as the canonical source for status/report projections.

### 3.2 Executable Runtime Cost

Advantages:
- deterministic JSON outputs,
- stable event/projection contract,
- cheap to test and replay,
- clean surface for monitoring and downstream tooling.

Costs:
- cannot yet construct artifacts on its own,
- current agent evaluation is heuristic rather than a true F_P relay,
- phase-2 features are not implemented.

### 3.3 Why Codex Is Not Claude Here

Claude's comparison centered on nested `claude -p` subprocess patterns. That exact tradeoff does not port cleanly to Codex because the session already has first-class tool access. The real Codex split is not "LLM subprocess versus Python engine." It is:

- interactive construction and judgment in-session,
- replay, projection, and bounded workflow state in the runtime.

That is a better fit for Codex's tool-calling model.

---

## 4. Architectural Verdict

The best Codex architecture is a hybrid with a strict division of labor:

- **Session owns**: construction, design disambiguation, exploratory proposal generation, high-context probabilistic reasoning.
- **Reusable skill behaviors own**: stable construct/evaluate/review patterns that commands can reuse without collapsing back into many stage personas.
- **Runtime owns**: event emission, projection rebuilding, feature vector state, review persistence, traceability reports, release manifests, health summaries.

This implies the next parity move should not be "port Claude's subprocess F_P model verbatim." It should be:

1. define a command-to-skill and skill-to-runtime contract,
2. let the session produce candidate artifacts through reusable behaviors,
3. let the runtime validate, record, and project the outcome,
4. add phase-2 functors on top of that split.

---

## 5. What Needs to Change

### Immediate

- Keep using the runtime as the authority for emitted events and projections.
- Define the reusable skill-behavior layer explicitly instead of leaving construction and review logic in one-off prompts.
- Build on the new artifact-ref handoff in `gen_iterate()` rather than inventing a second construct boundary.

### Short-Term

- Replace heuristic-only agent checks with a real Codex-side F_P contract.
- Extend artifact handoff from metadata recording to evaluator-aware construct semantics.
- Extend workspace-root diagnostics into broader structural self-checks.

### Medium-Term

- Implement `CONSENSUS`.
- Implement named compositions and typed intent outputs.

---

## 6. Decision

The Codex tenant should treat the engine as a logical contract realized by:

- commands,
- reusable skill behaviors,
- runtime helpers,
- and the interactive Codex session.

That is the main translation from the Claude reference design:
- keep the same methodology semantics,
- do not copy the same transport choices,
- exploit Codex's native strengths instead of emulating Claude CLI internals.
