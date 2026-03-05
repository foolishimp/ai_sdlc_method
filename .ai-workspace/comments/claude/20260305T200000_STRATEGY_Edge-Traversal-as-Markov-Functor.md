# STRATEGY: Edge Traversal as Autonomous Markov Functor

**Author**: Claude Code
**Date**: 2026-03-05T20:00:00Z
**Addresses**: ADR-017 (Functor Execution Model), ADR-023 (MCP Transport), pre-ADR-024 (Invocation Contract)
**For**: all

## Summary

Each edge traversal in the asset graph is a **Markov step**: a memoryless transition from one asset state to the next, parameterised by the edge type and executed by a functor (F_D, F_P, or F_H). The E2E runner is a concrete instantiation of this step. The invocation contract (ADR-024 candidate) is the interface that any functor — subprocess, MCP, API call, human action — must satisfy to participate in the graph. Transport and execution category are implementation details; the Markov step is the invariant.

---

## The Markov Property of Edge Traversal

The asset graph defines a state space. Each node is an asset type (intent, requirements, design, code, unit_tests, …). Each edge is a typed transition. A traversal of an edge is a function:

```
T(Asset_n, Context[], edge_type) → Asset_{n+1}
```

This is Markov: the output depends only on the **current state** (`Asset_n`, `Context[]`) — not on the history of how that state was reached. It does not matter whether `Asset_n` required 1 iteration or 7 to converge. The next transition sees only the current state.

This is why:
- The E2E runner scaffolds a complete initial state (`e2e_project_dir`) and runs ONE transition (`converged_project`). It doesn't need to know how prior states were built.
- The feature vector carries trajectory metadata (iteration counts, timestamps) as **audit data**, not as input to the next transition. The transition itself is stateless.
- Session-scoped fixtures are correct: one run, one Markov step, all validators inspect the output state.

---

## The Functor as Transition Function

ADR-017 defined three functor categories. In Markov terms, each is a different **computation engine** for the same transition function:

| Functor | Computation Engine | Markov Guarantee |
|---|---|---|
| **F_D** (Deterministic) | Code, subprocess, pytest | Same input → same output. Transition is a pure function. |
| **F_P** (Probabilistic) | LLM call (claude -p, MCP, API) | Same input → distribution over outputs. Convergence is probabilistic. |
| **F_H** (Human) | Human action (review, approval) | Same input → human judgment. Transition is bounded by the human's context window. |

The Markov step is the same regardless of functor. The natural transformation η (ADR-017) re-renders the step across categories when ambiguity changes — but the step's interface (inputs, outputs, convergence contract) is invariant.

**Critical implication**: the invocation contract (what the engine calls, what it expects back) must be defined at the level of the Markov step — not at the level of any particular functor implementation. `run_claude_headless()`, `call_claude_tool()`, and `run_pytest()` are all functors satisfying the same step contract.

---

## The Autonomous Vector

A feature vector is an **autonomous Markov chain**: a sequence of steps through the graph topology, each step independent, the vector carrying only the current state and trajectory audit data.

```
pending → [T(intent→requirements)] → requirements_converged
       → [T(requirements→design)]  → design_converged
       → [T(design→code)]          → code_converged
       → [T(code↔unit_tests)]      → unit_tests_converged
```

"Autonomous" means: each step can be executed independently, by any functor, at any time, without coordination with other vectors. Two feature vectors in the same project are independent Markov chains sharing a state space (the project filesystem). They don't need to know about each other.

This is the property that makes parallelism natural: independent vectors = independent chains = no synchronisation required. Spawn is the operation that creates a new autonomous chain from a step in an existing one.

---

## The Invocation Contract (pre-ADR-024)

The Markov framing makes the invocation contract precise. Any functor executing a step must satisfy:

```
invoke(intent: Intent, state: ProjectDir) → StepResult

Intent   = { edge: str, feature: str, constraints: dict, context: list[Asset] }
StepResult = {
    converged: bool,
    delta: float,          # 0.0 = converged, >0 = gap remaining
    artifacts: list[Path], # files written/modified
    events: list[OLEvent], # events emitted to events.jsonl
    cost_usd: float,
    duration_ms: int,
    audit: StepAudit,      # stall_killed, budget_capped, exit_code
}
```

The engine doesn't care which functor executed the step. It inspects `StepResult` and decides whether to converge, re-iterate, or spawn.

**The E2E runner already implements this contract** — informally:
- `intent` = the prompt string (`/gen-start --auto --feature "REQ-F-CONV-001"`)
- `state` = `project_dir` (the scaffolded filesystem)
- `StepResult` = `ClaudeRunResult` + `_count_converged_edges()` + the archived project dir

Formalising this into a typed interface is the ADR-024 work.

---

## Transport as Functor Implementation Detail

Under this framing, the subprocess vs MCP debate (ADR-023) is resolved cleanly: they are two implementations of F_P for the same Markov step.

```python
# Both satisfy the same invocation contract:

def run_via_subprocess(intent, state) -> StepResult:
    # claude -p, watchdog, budget cap, process group kill
    ...

def run_via_mcp(intent, state) -> StepResult:
    # claude_code tool call, MCP timeout, filesystem poll
    ...

def run_via_api(intent, state) -> StepResult:
    # anthropic.Anthropic().messages.create(stream=True)
    ...

def run_via_human(intent, state) -> StepResult:
    # prompt human, wait for approval, record decision
    ...
```

The engine calls `invoke(intent, state)`. The functor registry resolves to the appropriate implementation based on transport availability and edge affinity (ADR-021). The Markov step is identical in all cases.

---

## What This Changes About the Implementation

### The stall detection reframe

The E2E runner's filesystem fingerprint (`_project_fingerprint()`) is correct because it asks the right Markov question: **"is the transition still producing state changes?"** A transition that has stopped modifying artifacts has either converged or stalled. Stdout byte-counting asks whether the computation engine is active — a weaker, transport-specific proxy.

The filesystem fingerprint is transport-agnostic: it works for subprocess, MCP, and human functors alike. A human who stopped modifying files is also stalled.

### The budget cap reframe

`--max-budget-usd` is a **transition budget**: the maximum cost the engine is willing to pay for a single Markov step. It belongs in the invocation contract, not as a CLI flag specific to the subprocess transport. The MCP transport needs an equivalent budget constraint passed to the MCP server; the API transport needs a token budget. The value comes from `project_constraints.yml` or edge config.

### The archive reframe

The run archive is a **state snapshot**: a preserved record of `state_n` → `state_{n+1}` for a given step. This is directly analogous to the event log (which records step metadata) but at the artifact level (which records the full state). Both are necessary for replay, debugging, and cross-step analysis.

The genesis_monitor should be able to consume archived runs as historical state snapshots, not just current state derived from `events.jsonl`.

---

## Connection to the Spec

The spec defines `iterate(Asset, Context[], Evaluators) → Asset'`. In Markov terms:
- `Asset` = state_n
- `Context[]` = the intent context (spec, constraints, prior artifacts)
- `Evaluators` = the convergence test applied to state_{n+1}
- The functor is the computation engine that produces state_{n+1}

The spec does not prescribe the functor. The Markov step is the invariant. The functor is the implementation choice parameterised by edge type, execution environment, and ambiguity level. This is what ADR-017 formalised as the functor composition model — this comment is restating it in Markov language, which makes the autonomy and independence properties more explicit.

## Recommended Action

1. **ADR-024**: Formalise the invocation contract as typed interfaces (`Intent`, `StepResult`, `invoke()`). All functor implementations (subprocess, MCP, API, human) must satisfy this interface. The engine calls `invoke()` without knowing the transport.

2. **Update ADR-017**: Add a Markov framing section. The functor categories (F_D, F_P, F_H) are computation engines for Markov steps. The natural transformation η is the runtime mechanism for switching computation engines when ambiguity changes.

3. **Update feature vector schema**: Add `step_results: list[StepResult]` to the trajectory for each edge — not just status/iteration count, but the full step audit (cost, duration, stall_killed, budget_capped). This makes the Markov chain auditable at the step level.
