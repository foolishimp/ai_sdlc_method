# ADR-019: Orthogonal Projection Reliability — Engine and LLM Agent as Cross-Validators

**Status**: Accepted
**Date**: 2026-02-24
**Deciders**: Methodology Author
**Requirements**: REQ-ITER-001, REQ-EVAL-001, REQ-EVAL-002, REQ-SUPV-003, REQ-TOOL-014
**Extends**: ADR-008 (Universal Iterate Agent), ADR-017 (Functor-Based Execution Model)

---

## Context

The spec defines one operation: `iterate(Asset, Context[], Evaluators) → Asset'`. Two implementations of this operation exist:

1. **E2E Agent (Strategy A)**: One LLM session constructs and evaluates. Context-coherent, can build artifacts, emits events via agent instruction (Level 1 — probabilistic, may be skipped).
2. **Deterministic Engine (Strategy B)**: Python loop evaluates via checklist dispatch. Cannot construct, but emits events via `fd_emit.emit_event()` (Level 4 — guaranteed if code runs).

The FUNCTOR_FRAMEWORK_DESIGN.md v2.1 (§13) framed these as competing strategies — Strategy A or B, with Strategy C (Hybrid) as a pipeline where the LLM constructs and the engine evaluates sequentially.

The problem with the pipeline framing: it still treats them as a single execution path. If the engine evaluates after the LLM constructs, you get better events but lose cross-validation. The LLM's evaluation and the engine's evaluation never compare notes.

### The Reliability Problem

Neither projection is reliable alone:

| Projection | Strength | Weakness |
|-----------|----------|----------|
| LLM agent | Can judge, can construct, context-coherent | Can hallucinate, can skip events, non-deterministic |
| Engine | Guaranteed events, deterministic delta, can't lie | Can't construct, can't judge beyond pass/fail, false convergence on SKIP |

Current event reliability hierarchy:

| Level | Mechanism | Reliability | Current coverage |
|-------|-----------|-------------|-----------------|
| 4 | Deterministic code (`fd_emit`) | Guaranteed | Engine path only |
| 3 | Observer/gap analysis (`/gen-gaps`) | Verification | On-demand |
| 2 | Hook (`hooks.json` post_tool_call) | Automatic, can fail | Limited |
| 1 | Agent instruction ("emit event" in .md) | Probabilistic | Most events today |

The vast majority of events in `events.jsonl` (344 events) are Level 1 — the E2E agent happened to follow the command spec. Different session, different prompt → events might not fire.

### The Insight

The LLM agent and the engine are not competing strategies. They are **interoperable projections of the same spec requirement** (REQ-ITER-001). Because they implement the same contract with orthogonal failure modes, running both against the same checklist and comparing results creates reliability that neither has alone.

This is not redundancy (running the same thing twice). It is **orthogonal verification** — two projections with independent failure modes cross-checking each other.

---

## Decision

**The engine and LLM agent are orthogonal projections of `iterate()` that cross-validate each other. Both run against the same evaluator checklist for the same edge. Disagreement between their deltas is a first-class signal that triggers escalation. Event emission flows through the engine's deterministic path (Level 4) regardless of which projection constructed the asset.**

### Cross-Validation Protocol

```
┌─────────────────────────────────────────────────────┐
│  iterate(asset, context, evaluators)                │
│                                                     │
│  1. LLM agent constructs candidate                  │
│  2. LLM agent evaluates (produces delta_P)          │
│  3. Engine evaluates same candidate (produces delta_D)│
│  4. Compare:                                        │
│     delta_P == delta_D  → consistent, trust result  │
│     delta_P != delta_D  → disagreement signal       │
│                           → η escalation            │
│  5. Engine emits Level 4 event (always fires)       │
│  6. Event includes both deltas for audit            │
└─────────────────────────────────────────────────────┘
```

### Disagreement as Signal

When `delta_P != delta_D`, the disagreement itself is informative:

| delta_P | delta_D | Meaning | Action |
|---------|---------|---------|--------|
| 0 | >0 | LLM hallucinated a pass | Trust engine. Feed failures back to LLM for fix. |
| >0 | 0 | LLM was too strict (or deterministic checks insufficient) | Log for calibration. Agent checks may catch real gaps that deterministic checks miss. |
| 3 | 5 | Partial overlap, different judgment on some checks | Both deltas recorded. Union of failures is the working set. |

The engine's delta is ground truth for deterministic checks (F_D). The agent's delta adds coverage for judgment calls (F_P). The **union** is more reliable than either alone.

### Event Emission Architecture

The engine owns event emission. All events flow through `fd_emit.emit_event()` regardless of which projection operated:

```
LLM agent constructs ──→ engine evaluates ──→ fd_emit (Level 4)
                              │
engine evaluates alone ──────→ fd_emit (Level 4)
                              │
LLM evaluates alone ──→ engine records ──→ fd_emit (Level 4)
```

This eliminates Level 1 event dependency. The agent never needs to "remember" to emit — the engine does it deterministically as a side effect of evaluation.

### Projection Interoperability

Both projections expose the same interface, enabling composition in either direction:

**Engine calls LLM** (existing):
```python
# fp_evaluate.py — engine dispatches to claude -p for agent checks
cr = fp_run_check(check, asset_content, context, model, timeout)
```

**LLM calls engine** (new capability needed):
```python
# Exposed as CLI entry point or MCP tool
from genisis.engine import iterate_edge, EngineConfig
record = iterate_edge(edge, edge_config, config, feature_id, asset)
# Returns: IterationRecord with delta, check results, events already emitted
```

The missing piece is small: a CLI entry point (`python -m genisis.engine evaluate --edge ... --asset ...`) or MCP tool that lets the LLM agent invoke `iterate_edge()` and read back the `IterationRecord`.

### How This Changes Strategy C

Strategy C in the design doc was framed as a pipeline: "LLM constructs, engine evaluates." The cross-validation model changes this:

**Old Strategy C (Pipeline)**:
```
LLM constructs → engine evaluates → done
```

**New Strategy C (Cross-Validation)**:
```
LLM constructs + evaluates  → delta_P
Engine evaluates same asset  → delta_D (Level 4 events guaranteed)
Compare deltas               → disagreement triggers η escalation
LLM reads engine's delta     → fixes what the engine found
Engine re-evaluates           → repeat until delta_D == 0
```

Both projections evaluate. The engine's deterministic checks catch what the LLM missed. The LLM's agent checks catch what deterministic tests can't assess. Convergence requires `delta_D == 0` (engine says pass) — this is the hard gate. The LLM's `delta_P` is advisory — it surfaces concerns that may need human judgment.

### Reliability Composition

The formal claim: for any check `c` in the evaluator checklist:

- If `c` is deterministic (F_D): engine result is ground truth. LLM result is irrelevant.
- If `c` is agent (F_P): LLM result is primary. Engine result is SKIP (can't evaluate). But the engine still records the SKIP — making the gap visible.
- If both can evaluate `c`: disagreement is the signal. Neither is trusted over the other — disagreement triggers η_P→H (human resolves).

This means:
- **F_D checks get Level 4 reliability** — engine runs them, result is deterministic
- **F_P checks get Level 1 reliability** — LLM evaluates, but the engine records that the check was delegated (gap is visible, not silent)
- **Disagreement gets escalated** — not buried

The gap analysis observer (Level 3) then verifies the event stream: "did all expected checks fire? did any delta disagreements go unresolved?" This closes the reliability loop.

---

## Rationale

### Why Not Just Trust the Engine?

The engine can't construct. And for agent checks (F_P), the engine calls `claude -p` per check — 1 cold-start subprocess per check, no shared context, expensive. The LLM agent evaluates with full context in a single session. For judgment calls, the agent is better.

But "better" is not "reliable." The agent can hallucinate passes. The engine catches this by running the same deterministic checks independently.

### Why Not Just Trust the LLM?

The LLM's event emission is Level 1 — instruction-following. In 344 events, every one exists because the agent happened to comply with the command spec. A different model version, a long context, a complex construction — and events might not fire.

The engine's emission is Level 4 — `fd_emit.emit_event()` with `fcntl.flock`. If the code runs, the event fires. This is the reliability foundation.

### Why Cross-Validation (Not Redundancy)?

Redundancy runs the same implementation twice — the same bugs, the same blind spots. Cross-validation runs two implementations with orthogonal failure modes:

- The engine can't hallucinate (deterministic code)
- The LLM can't miss context (full session)
- The engine can't judge coherence (no language understanding)
- The LLM can't guarantee emission (instruction-following)

Their weaknesses don't overlap. This is the definition of orthogonal verification.

### Spec Grounding

This follows directly from the spec's projection model (PROJECTIONS_AND_INVARIANTS.md). The spec defines `iterate()` abstractly. Any implementation that preserves the 4 invariants is a valid projection. The engine and LLM agent are two such projections. The spec doesn't say "pick one" — it says the invariants must hold. Cross-validation is how you verify the invariants hold across projections.

---

## Consequences

### Positive

- **Deterministic event reliability**: All events flow through `fd_emit` (Level 4). No more depending on agent instruction for observability.
- **Hallucination detection**: Engine catches false passes from LLM. Disagreement is visible, not silent.
- **Calibration data**: Logging both `delta_P` and `delta_D` creates a dataset for calibrating agent check prompts. If the LLM consistently disagrees with deterministic checks, the prompts need tuning.
- **Incremental adoption**: Can start with engine-as-verifier on the existing E2E agent flow. No need to rewrite the agent.
- **Formal grounding**: Cross-validation follows from the projection model already in the spec. No new primitives.

### Negative

- **Doubled evaluation cost**: Running both projections means running evaluators twice. Mitigated: F_D checks are cheap (subprocess), F_P checks only run in the LLM session (engine SKIPs them). The overhead is the F_D checks that the engine runs — seconds, not dollars.
- **Complexity**: Two deltas to reason about instead of one. Mitigated: `delta_D` is the hard gate (must be 0 to converge). `delta_P` is advisory. Simple rule.
- **Engine entry point needed**: The LLM agent needs a way to invoke the engine. Requires a CLI command or MCP tool wrapper around `iterate_edge()`. Small implementation effort.

### Implementation Path

1. **Immediate**: Add CLI entry point for `iterate_edge()` — `python -m genisis.engine evaluate --edge <edge> --feature <id> --asset <path>`
2. **Short-term**: Modify `/gen-iterate` command spec to invoke engine after LLM evaluation, compare deltas, record both in event
3. **Medium-term**: Add disagreement detection to the engine — when `delta_P` is provided alongside `delta_D`, emit `delta_disagreement` event type
4. **Long-term**: Build the cross-validation into the engine loop itself — engine runs F_D checks, calls LLM for F_P checks, compares, escalates

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.1 (Evaluator Types), §4.3 (Three Processing Phases)
- [PROJECTIONS_AND_INVARIANTS.md](../../../specification/PROJECTIONS_AND_INVARIANTS.md) §2 (Projection Model — valid implementations preserve invariants)
- [FUNCTOR_FRAMEWORK_DESIGN.md](../FUNCTOR_FRAMEWORK_DESIGN.md) §13 (Execution Strategies), §4 (Data Model)
- [FRAMEWORK_COMPARISON_ANALYSIS.md](../FRAMEWORK_COMPARISON_ANALYSIS.md) §9 (Strategy comparison, cost models)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (the LLM projection)
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (shared checklist structure)
- [ADR-017](ADR-017-functor-based-execution-model.md) — Functor-Based Execution Model (F_D/F_P/F_H categories, escalation via η)
- [ADR-011](ADR-011-consciousness-loop-at-every-observer.md) — Consciousness Loop (disagreement as intent signal)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (calibration from cross-validation data)

---

## Requirements Addressed

- **REQ-ITER-001**: Universal iterate — both projections implement the same `iterate()` contract; cross-validation verifies contract compliance
- **REQ-EVAL-001**: Deterministic evaluator — engine provides Level 4 reliable F_D evaluation
- **REQ-EVAL-002**: Agent evaluator — LLM provides F_P evaluation; engine records SKIP (gap visible)
- **REQ-SUPV-003**: Failure observability — all events through `fd_emit` (Level 4); disagreement is a first-class observable signal
- **REQ-TOOL-014**: Observability integration contract — event schema extended with `delta_P`/`delta_D` fields for cross-validation audit
