# Engine Design Gap Analysis

**Date**: 2026-02-24
**Priority**: TOP — prerequisite for ADR-019 cross-validation
**Feature**: REQ-F-ENGINE-001

---

## What Exists

The engine is a working Python module at `imp_claude/code/genesis/`:

| Module | What it does | Status |
|--------|-------------|--------|
| `engine.py` | `run()` → `run_edge()` → `iterate_edge()` loop | Works, tested |
| `config_loader.py` | YAML loading, `$variable` resolution, `resolve_checklist()` | Works, 16 tests |
| `fd_evaluate.py` | Deterministic subprocess checks + `evaluate_checklist()` | Works, tested |
| `fp_evaluate.py` | Agent checks via `claude -p` (1 per check) | Works, tested |
| `fd_emit.py` | `emit_event()` with `fcntl.flock` — Level 4 | Works, tested |
| `fd_route.py` | `select_profile()`, `select_next_edge()`, `lookup_encoding()` | Works, tested |
| `fd_classify.py` | REQ tag + source finding + signal classification | Works, tested |
| `fd_sense.py` | 5 sense monitors (freshness, stall, integrity, coverage, health) | Works, tested |
| `dispatch.py` | `(FunctionalUnit, Category) → Callable` table (5 F_D entries) | Works, tested |
| `models.py` | All dataclasses, enums, CATEGORY_FIXED | Works, tested |

**948 tests pass.** The engine can evaluate any edge against any checklist and emit Level 4 events. This is real, not aspirational.

---

## What's Missing (4 Gaps)

### Gap 1: No CLI Entry Point

The engine has no `__main__.py`. The LLM agent cannot invoke it.

**What exists**: Python API — `iterate_edge(edge, edge_config, config, feature_id, asset_content)`

**What's needed**: A CLI that the LLM agent can call:

```bash
# Evaluate an asset against an edge's checklist
python -m genesis evaluate \
  --edge "code↔unit_tests" \
  --feature "REQ-F-AUTH-001" \
  --asset ./imp_claude/code/genesis/engine.py \
  --workspace . \
  --output json

# Returns: IterationRecord as JSON
{
  "edge": "code↔unit_tests",
  "iteration": 1,
  "evaluation": {
    "delta": 2,
    "converged": false,
    "checks": [...],
    "escalations": [...]
  },
  "event_emitted": true
}
```

**Scope**: ~50 lines. Parse args, build `EngineConfig` from workspace, call `iterate_edge()`, print JSON. The engine code is already factored for this — `EngineConfig` is a dataclass, `iterate_edge()` returns `IterationRecord`.

**Design decisions needed**:
- Does the CLI read `project_constraints.yml` from a default path or require `--constraints`?
- Does `--asset` take a file path (engine reads it) or stdin (pipe from LLM)?
- Does the CLI also accept `--context` for accumulated context from prior edges?
- JSON output schema: mirror `IterationRecord` dataclass directly, or a flattened format?

### Gap 2: No Cross-Validation Protocol

The engine and LLM agent evaluate independently but never compare results.

**What exists**:
- Engine produces `delta_D` via `iterate_edge()` → `evaluation.delta`
- LLM agent produces `delta_P` via in-session evaluation (reported in command output)
- Both use the same checklist YAML

**What's needed**: A protocol where:

1. LLM constructs an asset and self-evaluates → `delta_P`
2. LLM calls engine CLI to evaluate the same asset → `delta_D`
3. Disagreement (`delta_P != delta_D`) triggers escalation

**Design decisions needed**:
- Where does comparison happen — in the LLM session (agent reads engine output) or in the engine (engine accepts `delta_P` as input)?
- Does the event schema change? Currently `iteration_completed` has one `delta` field. Cross-validation needs `delta_D` and `delta_P`.
- What triggers η? Options:
  - `delta_P == 0 && delta_D > 0` → LLM hallucinated a pass → η_P→H (HIGH: engine overrules)
  - `delta_P > 0 && delta_D == 0` → LLM stricter than engine → log for calibration (LOW: advisory)
  - `delta_P != delta_D` on same checks → emit `delta_disagreement` event (MEDIUM: investigate)

**Recommended**: Comparison in the LLM session. The agent calls the engine, reads the JSON output, compares with its own evaluation. The agent reports both deltas. The engine's `delta_D == 0` is the convergence gate. Simple, no engine changes needed.

### Gap 3: No Context Accumulation

Each `iterate_edge()` call receives `asset_content` and `context` as strings. There's no mechanism to feed edge N's output into edge N+1.

**What exists**: `engine.run()` passes the same `asset_content` to every edge. Each `fp_evaluate.run_check()` gets `asset_content` and `context` but they're static across the traversal.

**What's needed**: After edge N converges, its output artifact becomes part of the context for edge N+1.

```python
# In run() — after edge converges:
context = context + f"\n\n--- Output from {edge} ---\n{edge_output}"
```

**Design decisions needed**:
- Where does the constructed artifact come from? The engine doesn't construct — the LLM does. So the LLM passes the artifact path/content when calling the engine for the next edge.
- Is context a growing string or a structured list of `(edge, artifact_path)` tuples?
- Should `EngineConfig` have a `context_dir` that accumulates artifacts per edge?

**Recommended**: Don't solve this in the engine. The LLM agent accumulates context naturally (it's in the same session). When calling the engine CLI for cross-validation, the LLM passes the current asset. Context accumulation is the LLM's job; the engine just evaluates what it's given.

### Gap 4: Deterministic Checks Require $variable Resolution

Most F_D checks in `tdd.yml` use `$variables`:

```yaml
command: "$tools.test_runner.command $tools.test_runner.args"
```

When the engine runs outside a project workspace (e.g., for cross-validation of the methodology itself), there's no `project_constraints.yml`. Unresolved `$variables` → check SKIP.

**What exists**: `resolve_checklist()` resolves from a constraints dict. Unresolved → SKIP with warning.

**What's needed**: For the dogfooding case (Genesis evaluating itself), a `project_constraints.yml` that maps:

```yaml
tools:
  test_runner:
    command: "python -m pytest"
    args: "imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
    pass_criterion: "exit code 0"
  coverage:
    command: "python -m pytest"
    args: "--cov=imp_claude/code/genesis --cov-report=term imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
    pass_criterion: "coverage percentage >= 0.70"
  linter:
    command: "ruff check"
    args: "imp_claude/code/genesis/"
    pass_criterion: "exit code 0"
  formatter:
    command: "ruff format"
    args: "--check imp_claude/code/genesis/"
    pass_criterion: "exit code 0"
```

**Design decision needed**: Should this live at `.ai-workspace/claude/context/project_constraints.yml` (the standard path) or be passed via `--constraints` CLI flag?

**Recommended**: Create the constraints file at the standard path. This makes the dogfooding case work AND validates that the constraint resolution pipeline works end-to-end.

---

## Implementation Order

```
Gap 4: project_constraints.yml    ← 10 min, unblocks deterministic checks
  │
Gap 1: __main__.py CLI            ← 30 min, unblocks LLM→engine invocation
  │
Gap 2: Cross-validation protocol  ← design only, wire into /gen-iterate command spec
  │
Gap 3: Context accumulation       ← not needed (LLM accumulates, engine evaluates)
```

**Gap 4 first** because without resolved `$variables`, the engine's F_D checks all SKIP — it has nothing to cross-validate against.

**Gap 1 second** because it's the minimal bridge between the LLM agent and the engine. 50 lines of Python.

**Gap 2 is design-level** — update the `/gen-iterate` command spec to say "after constructing, call `python -m genesis evaluate` and compare deltas." No engine code change.

**Gap 3 is not needed** — the LLM session IS the context accumulator. The engine is stateless per invocation. That's a feature, not a bug.

---

## Verification

After Gaps 1 + 4:

```bash
# Engine evaluates its own code against TDD checklist
PYTHONPATH=imp_claude/code python -m genesis evaluate \
  --edge "code↔unit_tests" \
  --feature "REQ-F-ENGINE-001" \
  --asset imp_claude/code/genesis/engine.py \
  --workspace .

# Expected: deterministic checks (pytest, lint, format) run and report pass/fail
# Agent checks SKIP (no --agent flag)
# Event emitted to events.jsonl (Level 4)
# JSON output with delta, check results
```

After Gap 2 (in `/gen-iterate`):

```
LLM constructs code → self-evaluates → delta_P = 0
LLM calls: python -m genesis evaluate ... → delta_D = 2
                                             (lint fail + coverage fail)
LLM reads: "Engine disagrees. 2 deterministic failures."
LLM fixes lint + coverage → re-calls engine → delta_D = 0
Both agree → converged
Event recorded with both deltas
```

---

## What This Enables

Once the engine works as a cross-validator:

1. **Event reliability moves to Level 4** — every `/gen-iterate` emits through `fd_emit`, not agent instruction
2. **Hallucination detection** — LLM can't claim "all tests pass" when pytest fails
3. **Calibration data** — logged `delta_P` vs `delta_D` reveals agent check quality over time
4. **Deterministic regression** — engine runs the same checks CI would, before the LLM commits
5. **Dogfooding** — Genesis validates itself through its own engine, not just through the LLM agent following command specs
