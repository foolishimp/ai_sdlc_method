# ADR-024: Recursive Actor Model — F_P as Constrained Intent Invocation

**Series**: imp_claude (Claude Code implementation)
**Status**: Accepted
**Date**: 2026-03-05
**Scope**: F_P functor implementation, engine dispatch, checklist schema
**Supersedes**: ADR-020 (F_P Construct + Batched Evaluate via `claude -p --json-schema`)
**Extends**: ADR-S-016 (invocation contract), ADR-S-017 (variable grain), ADR-023 (MCP transport)

---

## Context

ADR-020 defined F_P construction as `claude -p --json-schema` — a constrained subprocess call that asks Claude to return an artifact as a JSON string. This approach has three fundamental problems identified in practice:

1. **Wrong transport**: `claude -p` has no tool access. Real code work requires reading files, running tests, writing fixes. A JSON string response cannot represent filesystem changes.
2. **Unreliable**: `claude -p` subprocesses hang. Stall detection was broken in production (reset every poll cycle — processes ran for hours). Even with correct timeouts, the `-p` path is a persistent source of failure.
3. **Wrong model**: `fp_evaluate.py` spawns separate `claude -p` calls to evaluate artifacts. This is circular — the engine (called by a Claude session) spawns another Claude to evaluate. It duplicates judgment the calling agent already has.

The deeper problem: ADR-020 treated F_P as "make a constrained LLM call." The correct model — implicit in ADR-S-016 and ADR-S-017 but never stated as an implementation decision — is that **F_P is a recursive actor invocation**, not a subprocess call.

---

## Decision

### F_P is an actor, not a subprocess

When the engine needs F_P work (construction, judgment), it does not call `claude -p`. It invokes an **actor** — a full Claude Code session with tool access — passing a structured `Intent`. The actor:

1. Receives the `Intent` (edge, feature, failures from F_D, constraints, budget_usd)
2. Runs `iterate()` autonomously — the same model, at a finer grain (ADR-S-017)
3. Uses its full tool access to read files, modify code, run tests, verify output
4. Self-evaluates against the edge criteria
5. Returns `StepResult` (via fold-back to the engine)

The engine's role after actor invocation: **run F_D checks only**. The engine does not evaluate the actor's judgment — it verifies the actor's output against deterministic criteria. F_D is the hard gate.

### The invocation flow

```
CLI session (user)
  └─ /gen-iterate (skill)
       └─ engine (F_D supervisor)
            ├─ F_D: proc.run_bounded(pytest, ruff, mypy, ...)
            │        → CheckResult[]
            │        → delta > 0: build Intent from failures
            └─ F_P: MCP → actor
                     actor = Claude Code session (full tool access)
                     actor receives Intent{
                       edge:        "code↔unit_tests",
                       feature:     "REQ-F-ENGINE-001",
                       grain:       "iteration",
                       failures:    ["tests_pass: 3 tests fail...", ...],
                       constraints: {language: python, ...},
                       budget_usd:  2.0,   # cost cap → --max-budget-usd (NOT a timeout)
                       max_depth:   3,     # recursion depth limit (separate from cost)
                       run_id:      uuid
                     }
                     actor runs iterate() at grain="iteration"
                     actor self-evaluates, writes files, verifies
                     actor returns → fold-back
            F_D re-evaluates filesystem state
            delta == 0 → converged
            delta > 0  → loop (up to max_iterations)
```

### The engine checklist has no agent checks

`type: "agent"` entries in edge_params checklists are **invalid at the engine level**. Agent judgment belongs to the actor, not the engine. The engine's checklist is F_D only:

```yaml
checklist:
  - name: tests_pass
    type: deterministic          # ✅ engine runs this
    command: pytest ...
  - name: coverage_threshold
    type: deterministic          # ✅ engine runs this
    command: pytest --cov ...
  - name: code_quality           # ❌ WRONG — remove from engine checklist
    type: agent
    criterion: "code follows patterns..."
```

Agent criteria belong in the `Intent.context` passed to the actor. The actor self-evaluates against them. The engine cannot and should not replicate that judgment.

### MCP is the only F_P transport — no subprocess fallback

Per ADR-023, MCP is the primary transport. This ADR strengthens that decision:

**There is no `claude -p` fallback for F_P.**

If MCP is unavailable (no active Claude session), F_P returns `outcome: SKIP`. The engine continues with F_D results only. A `delta` computed from F_D checks alone is still a valid delta — it just reflects only deterministic failures.

Detection: `CLAUDE_CODE_SSE_PORT` env var present → MCP available → invoke actor.
No env var → MCP unavailable → skip F_P, return F_D delta only.

This is not a degraded mode. Running F_D only is the engine's primary use case (evaluation, CI, cross-validation per ADR-019). F_P actor invocation is the construction use case, available only inside an active session.

### The recursive structure

The actor model is recursive by construction (ADR-S-017 §deepest invariant):

- The actor receives `Intent{grain="iteration"}`
- The actor runs `iterate()` — the same four primitives at finer grain
- The actor may spawn sub-actors (zoom in) if its problem has sub-structure
- Each sub-actor receives a further-constrained `Intent`
- Recursion terminates via two independent bounds: `budget_usd` (cost cap — not a timeout) and `max_depth` (structural spawn depth limit). These are separate: cost and structure are orthogonal constraints.

This is the connection to the recursive LLM model: the actor is not a special construct. It is the model applied recursively. The engine does not know or care how deep the recursion goes — it waits for `StepResult` (fold-back) and re-evaluates with F_D.

The `budget_usd` in `Intent` is the zoom budget (ADR-S-017 §spawn depth limit as zoom budget). The actor cannot recurse past it. Combined with `max_iterations` at the engine level, the full invocation is bounded.

### What is deleted

| Component | Status | Reason |
|---|---|---|
| `fp_subprocess.py` | **Delete** | Sole purpose was managing `claude -p` — no longer used |
| `fp_evaluate.py` | **Delete** | Agent checks via `claude -p` per check — wrong model |
| `fp_construct.py` `run_construct()` | **Delete** | `claude -p --json-schema` construct — wrong model |
| `fp_construct.py` `run_construct_headless()` | **Delete** | subprocess `claude --print` — replaced by MCP actor |
| `fp_construct.py` `_call_claude()` | **Delete** | subprocess wrapper |
| `type: agent` checklist entries | **Remove** | Actor self-evaluates; engine cannot do F_P judgment |

### What replaces them

| New component | Purpose |
|---|---|
| `contracts.py` | `Intent`, `StepResult`, `VersionedArtifact`, `StepAudit`, `SpawnRecord` |
| `functor.py` | `Functor` protocol + registry: `(edge, grain, env) → Functor` |
| `fp_functor.py` | F_P implementation: detect MCP, invoke actor, return StepResult |
| `proc.run_bounded` | Stays — used by F_D only (pytest, ruff, mypy subprocess calls) |
| `fd_evaluate.run_check` | Stays — F_D check execution via `proc.run_bounded` |

---

## Implementation: fp_functor.py

```python
def invoke(intent: Intent, state: Path) -> StepResult:
    """F_P functor — invoke actor via MCP with constrained Intent.

    If MCP unavailable → return StepResult(converged=False, delta=-1, skipped=True).
    No subprocess fallback.
    """
    if not _mcp_available():
        return StepResult(
            run_id=intent.run_id,
            converged=False,
            delta=-1,
            skipped=True,
            audit=StepAudit(functor_type="F_P", transport="none", skipped=True),
        )

    prompt = _build_actor_prompt(intent)
    # MCP tool call → actor session in workspace
    result = mcp_invoke(prompt, workspace=state, budget_usd=intent.budget_usd)
    return _to_step_result(intent, result)

def _mcp_available() -> bool:
    return bool(os.environ.get("CLAUDE_CODE_SSE_PORT"))
```

---

## Consequences

**Positive:**
- `claude -p` is gone. All F_P reliability problems disappear at the source.
- Engine is purely F_D — deterministic, fast, testable without LLM calls.
- Actor has full tool access — can actually do code work, not just return strings.
- Recursion is structurally encoded — actor invocation IS spawn (ADR-S-017).
- `StepResult` from actor populates COMPLETE event directly (ADR-S-015).
- Engine checklist simplifies — F_D only, no agent check routing logic.
- `fp_subprocess.py`, `fp_evaluate.py`, bulk of `fp_construct.py` deleted.

**Negative / Trade-offs:**
- F_P only works inside an active Claude Code session. Standalone engine runs are F_D only.
- MCP actor invocation latency is higher than a `claude -p` call for simple judgments. Acceptable: the actor is doing real work, not just evaluating.
- Deleting `fp_evaluate.py` removes the existing agent check tests. New tests mock `fp_functor.py` instead.

---

## Current implementation status

| Component | Status |
|---|---|
| `contracts.py` (Intent, StepResult) | ❌ Not yet |
| `functor.py` (registry) | ❌ Not yet |
| `fp_functor.py` (MCP actor) | ❌ Not yet |
| `fp_subprocess.py` deleted | ❌ Still exists |
| `fp_evaluate.py` deleted | ❌ Still exists |
| `fp_construct.py` cleaned | ❌ Still has -p code |
| Engine checklist: agent checks removed | ❌ Still present in edge_params |

---

## References

- [ADR-S-016](../../../specification/adrs/ADR-S-016-invocation-contract.md) — `invoke(Intent, State) → StepResult`; functor registry
- [ADR-S-017](../../../specification/adrs/ADR-S-017-variable-grain-zoom-morphism.md) — spawn = zoom in; actor = finer grain invocation; budget_usd = zoom budget
- [ADR-S-015](../../../specification/adrs/ADR-S-015-unit-of-work-transaction-model.md) — StepResult populates COMPLETE event; parentRunId encodes recursion
- [ADR-023](ADR-023-mcp-as-primary-agent-transport.md) — MCP as primary F_P transport
- [ADR-019](ADR-019-orthogonal-projection-reliability.md) — engine (F_D) and agent (F_P) as orthogonal projections; F_D-only is valid
- [ADR-020](ADR-020-fp-construct-batched-evaluate.md) — superseded by this ADR
- Recursive LLM reference implementation: `/Users/jim/src/apps/recursive-llm/`
- Strategy comment: `.ai-workspace/comments/claude/20260305T200000_STRATEGY_Edge-Traversal-as-Markov-Functor.md`
