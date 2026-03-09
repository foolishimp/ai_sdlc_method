# Codex Functor Framework - Design and Implementation Guide

**Version**: 1.0.0
**Date**: 2026-03-09
**Implements**: REQ-GRAPH-001, REQ-ITER-001, REQ-EVAL-002, REQ-F-EVENT-001
**Package**: `imp_codex/runtime/` + command/agent prompt surface

---

# Part I: Current State

## 1. Conceptual Overview [IMPLEMENTED baseline]

The Codex tenant still uses the same three evaluator categories:

| Category | Symbol | Codex rendering | Status |
|----------|--------|-----------------|--------|
| Deterministic | F_D | Python helpers, shell commands, replay/projection code | Implemented |
| Probabilistic | F_P | Interactive Codex reasoning plus heuristic runtime checks | Partial |
| Human | F_H | Explicit review decision recorded through `gen_review()` | Implemented |

Codex differs from Claude in transport, not in semantics. The methodology still reduces to graph, iterate, evaluators, and context. What changes is where those semantics execute.

---

## 2. Functional Unit Mapping

| Unit | Codex mapping | Status |
|------|---------------|--------|
| evaluate | `run_deterministic_checks()`, `run_agent_checks()` | Implemented / partial |
| construct | Interactive Codex session writes artifacts | Partial |
| classify | gap and traceability heuristics in runtime helpers | Implemented |
| route | `detect_state()`, `decide_start_action()`, `determine_next_edge()` | Implemented |
| propose | `intent_raised`, `gen_gaps()`, session-side proposal authoring | Partial |
| sense | health summary, stuck detection, monitor configs | Implemented baseline |
| emit | `append_run_event()` | Implemented |
| decide | `gen_review()` | Implemented |

Two invariants remain intact:
- event emission is deterministic,
- final human approval is explicit rather than implicit.

---

## 3. Package Structure [IMPLEMENTED]

| Module | Role |
|--------|------|
| `runtime/paths.py` | workspace layout and bootstrap |
| `runtime/events.py` | canonical RunEvent emission and normalization |
| `runtime/projections.py` | replay-derived state, routing, status, health |
| `runtime/evaluators.py` | deterministic and heuristic agent checks |
| `runtime/commands.py` | executable methodology commands |
| `runtime/traceability.py` | REQ scanning, manifest, gaps, trace, release reports |
| `runtime/__main__.py` | JSON CLI entry point |

This is the actual Codex functor surface. The markdown agent specs under `imp_codex/code/agents/` remain the prompt-layer contract, and the runtime remains the replayable deterministic substrate. The full engine is the logical composition of command surface, reusable skill behaviors, runtime helpers, and the Codex session.

---

## 4. F_D Processing [IMPLEMENTED]

Deterministic processing is where Codex is strongest today.

### 4.1 Deterministic Evaluate

`run_deterministic_checks()`:
- loads edge checklists,
- resolves `$foo.bar` templates from project constraints,
- executes commands in the project root,
- returns machine-readable check results.

### 4.2 Deterministic Emit

`append_run_event()`:
- emits canonical RunEvents,
- preserves semantic SDLC type in facets,
- keeps a normalized replay path through `load_events()`.

### 4.3 Deterministic Replay and Routing

`projections.py` provides:
- state detection,
- next action selection,
- next edge resolution,
- stuck feature detection,
- health summaries,
- markdown projections.

This is the clearest Codex implementation of the "event stream plus projections" model in the current tenant.

---

## 5. F_P Processing [PARTIAL]

The Codex tenant has two different F_P behaviors today:

1. **Interactive F_P** in the main session:
   the Codex conversation can reason, inspect files, and construct artifacts.
2. **Runtime heuristic F_P** in `run_agent_checks()`:
   local heuristics infer pass/fail against some agent-style criteria.

What is missing is a unified probabilistic contract that commands and reusable skill behaviors can invoke and the runtime can record as a bounded unit of work.

Current bridge state:
- the Codex session can construct candidate artifacts,
- `gen_iterate()` can now record candidate artifact refs and hashes,
- `intent_raised` events can now carry named composition selections and typed intent vectors,
- but the runtime still does not own the construct step itself.

That is why REQ-F-FP-001 remains design-tier only even though Codex already has strong probabilistic capabilities in-session.

---

## 6. F_H Processing [IMPLEMENTED]

Human review is explicit in the runtime:

- human-required edges are held in `pending_review`,
- `gen_review()` records `approved`, `rejected`, or `refined`,
- approval on zero delta can trigger convergence,
- all review decisions are emitted as events and projected back into feature state.

This is a clean Codex binding of the human evaluator without hidden state.

---

## 7. Event Model [IMPLEMENTED]

The runtime emits and reads OpenLineage-style RunEvents, then normalizes them for internal use.

Key properties:
- new events are written in one canonical structure,
- legacy rows are still readable,
- runtime logic works against normalized semantic fields,
- downstream monitors get a stable event contract.

This is a stronger event story than "append arbitrary JSON and hope projections cope."

---

## 8. Execution Strategies

### Strategy A: Prompt-Native Codex Session [IMPLEMENTED externally]

Strengths:
- richest construction context,
- easiest place for design reasoning,
- natural fit for ambiguous work.

Weakness:
- not the best durable source for replay and projection state.

### Strategy B: Executable Runtime [IMPLEMENTED baseline]

Strengths:
- replayable,
- testable,
- stable JSON outputs,
- bounded event and projection contract.

Weakness:
- no true construct step yet,
- runtime F_P is still only partial.

### Strategy C: Hybrid Codex Runtime [PLANNED]

Target split:
- commands trigger reusable skill behaviors,
- session constructs candidate artifacts through those behaviors,
- runtime validates and records them,
- human or consensus review closes the loop,
- typed intents and named compositions extend the same contract.

This is the strategy the Codex tenant should optimize for.

---

## 9. Spawn and Fold-Back [IMPLEMENTED baseline]

`gen_spawn()` and `gen_fold_back()` already give Codex a real child-vector bookkeeping layer:
- child feature creation,
- parent blockage,
- fold-back summaries,
- emitted lifecycle events.

This is enough for manual recursive work management even though automatic recursive execution is not implemented.

---

## 10. Test Architecture [IMPLEMENTED]

The tenant has three meaningful test layers:

| Layer | What it covers |
|------|-----------------|
| Spec compatibility tests | local compat mirror and design/spec consistency |
| UAT / integration tests | projections, commands, traceability, event flow |
| E2E harness | convergence-oriented end-to-end scenarios |

This is important because the Codex runtime design is now executable enough that parity work should be validated by tests, not only by document comparison.

---

## 11. What Is Not Implemented Yet

- true runtime construct path,
- real F_P relay contract,
- `CONSENSUS` functor,
- named composition execution beyond intent routing,
- stronger structural enforcement around REQ-TOOL-015 beyond the current warning path.

These are not small omissions, but they are now cleanly bounded. The runtime already covers enough of the deterministic substrate that the remaining work is additive rather than foundational.

---

# Part II: Direction

## 12. Recommended Next Step

Do not rewrite the runtime around a Claude-shaped subprocess model.

Instead:
1. keep replay, events, and projections in `imp_codex/runtime/`,
2. formalize the command/skill/session-to-runtime construct handoff,
3. add real F_P invocation semantics,
4. build `CONSENSUS` and fuller named-composition execution on top of that hybrid.

That is the Codex-native route to parity.
