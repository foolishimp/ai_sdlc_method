# Side-by-Side Comparison: imp_claude vs. gemini_cli

**Date**: February 25, 2026
**Author**: Claude Code (imp_claude reference implementation)
**Subject**: Honest Architectural Audit — Two Implementations of the Asset Graph Model v2.8

---

## 1. Executive Summary

Both implementations prove the Asset Graph Model is implementable. They took fundamentally different paths to the same specification and arrived at complementary strengths and weaknesses. Neither is strictly superior — the Gemini report's claim of "theoretically superior" is overstated, and so would be any claim that Claude's "industrial" strength makes it the better design.

The truth is more interesting: **they made different trade-offs at a shared decision point**, and the right answer depends on what you're optimising for.

---

## 2. What the Gemini Report Gets Right

Before disagreeing with anything, credit where due:

1. **Dict Blindness is real**. Gemini's `evaluate() → Dict` return type means typos in field names (`"delat"` vs `"delta"`) are silent bugs. Claude's `CheckResult(outcome=CheckOutcome.PASS)` catches this at construction time.

2. **Natural transformation logging matters**. Claude's explicit `η_D→P` escalation logging makes the functor encoding audible. Gemini's implicit ordering obscures which level produced the result.

3. **The naming fix (code/ → gemini_cli/) was necessary**. Python's `import code` shadows stdlib — both implementations correctly identified this.

---

## 3. Where the Gemini Report Overstates

### 3.1 "Theoretically Superior" — The Recursion Claim

Gemini claims to be "the first to prove the Recursive LLM concept in code." Let's look at what's actually implemented:

```python
# f_probabilistic.py (46 lines)
if context.get("iteration_count", 0) > 3:
    return {
        "spawn": SpawnRequest("Why is delta not decreasing?", "discovery")
    }
```

This is a **hardcoded heuristic**: if iteration count > 3, emit a spawn signal. It doesn't:
- Actually create a child feature vector
- Run iterate() recursively on the child
- Fold back the child's result into the parent
- Track spawn dependency resolution

The CLI handler creates a `feature_spawned` event, but no code path picks it up and runs it. The parent is "blocked" but nothing unblocks it. This is **spawn detection, not recursion**. Claude's design document marks recursion as `[FUTURE]` because it IS future — Gemini's implementation is in the same state, just labelled differently.

**Claude's position**: We don't claim to have recursive spawning because we don't. Neither does Gemini. Both have the spawn signal; neither has the recursive execution.

### 3.2 "Generic Programming" — The Functor Protocol

Gemini's `Functor` protocol (3 classes implementing `evaluate(candidate, context) → Dict`) is cleaner in interface but weaker in substance:

| Property | Gemini | Claude |
|----------|--------|--------|
| Interface | `evaluate() → Dict` | `run_check(check) → CheckResult` |
| Type safety | Dict (key errors at runtime) | Dataclass + Enum (errors at construction) |
| Granularity | 1 call per functor level | 1 call per check per level |
| Checklist | Not implemented | Full: resolve $vars → dispatch → aggregate |
| $Variable resolution | Not implemented | `config_loader.py`: 115 lines of constraint binding |
| Per-check metadata | None | `ResolvedCheck.functional_unit`, `required`, `command`, `criterion` |

Gemini has a protocol. Claude has an implementation. A protocol without content is an interface waiting for a body.

### 3.3 "Event Sourcing" — Projections

Both implementations use `events.jsonl` as append-only log. The difference:

- **Gemini**: `EventStore.emit()` + `Projector.get_feature_status()` — clean API, 81 lines total. But the projector only does iteration counting and basic status aggregation.
- **Claude**: `fd_emit.emit_event()` — 52 lines, `fcntl` file-locked for safe concurrent writes. Delta computed deterministically from `CheckResult` outcomes, not from LLM output. Events carry the full check-by-check detail.

The Gemini report claims "better state-machine decoupling." That's true — Gemini's `Projector` is cleaner than Claude's embedded emission. But Claude's events carry more information per event because every check result is individually typed and traceable.

---

## 4. What Claude Actually Has That Gemini Doesn't

### 4.1 Constraint Surface as Variable Binding

The specification says Context[] is a constraint surface. Claude implements this literally:

```yaml
# edge_params/tdd.yml
checklist:
  - name: tests_pass
    command: "$tools.test_runner.command"
    pass_criterion: "exit code 0"
    required: true
  - name: coverage_minimum
    command: "$tools.test_runner.command --cov"
    pass_criterion: "coverage >= $coverage.threshold%"
    required: "$coverage.required"
```

```yaml
# project_constraints.yml
tools:
  test_runner:
    command: "python -m pytest imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
coverage:
  threshold: 70
  required: true
```

`config_loader.py` resolves `$tools.test_runner.command` → the actual pytest command. Checks with unresolved variables are SKIPped, not failed. This is the spec's constraint surface made operational — the same edge config works for any project by binding different constraints.

Gemini has `project_constraints.yml` but doesn't resolve `$variables` in edge configs. The checklist is not parameterised.

### 4.2 Per-Check Dispatch and Typed Results

Claude dispatches each check individually:

```python
# Simplified from engine.py + fd_evaluate.py
for check in resolved_checklist:
    if check.check_type == "deterministic":
        result = fd_run_check(check, cwd=workspace, timeout=120)
    elif check.check_type == "agent":
        result = fp_run_check(check, asset, model="sonnet", timeout=120)
    elif check.check_type == "human":
        result = CheckResult(outcome=SKIP, message="human checks skipped in engine mode")
    results.append(result)

delta = sum(1 for r in results if r.required and r.outcome in (FAIL, ERROR))
```

Each `CheckResult` carries: outcome (enum), exit_code, stdout, stderr, message, and the original `ResolvedCheck` metadata. This enables:
- **Pattern detection**: "check X failed 4 consecutive iterations" (REQ-SUPV-003)
- **Root cause analysis**: stdout/stderr from the failing subprocess
- **Selective retry**: re-run only failing checks

Gemini runs one evaluation per functor level. If F_D fails, you know "deterministic failed" but not which check, why, or what the subprocess output was.

### 4.3 Engine CLI That Converges on Itself

```bash
PYTHONPATH=imp_claude/code python -m genesis evaluate \
    --edge "code↔unit_tests" \
    --feature "REQ-F-ENGINE-001" \
    --asset imp_claude/code/genesis/engine.py \
    --deterministic-only --fd-timeout 120
```

This runs against the methodology's own codebase and produces **delta=0**: tests pass, coverage ≥70%, lint clean, format clean, type check clean. The engine dogfoods itself. Gemini's CLI runs but doesn't have a comparable self-convergence demonstration.

### 4.4 Interoceptive Monitors

`fd_sense.py` (246 lines) implements 5 monitors:

| Monitor | What it senses | Threshold |
|---------|---------------|-----------|
| `event_freshness` | Time since last event | 60 min |
| `feature_stall` | Delta unchanged N iterations | 3 |
| `event_log_integrity` | JSON parse errors | 0 |
| `req_tag_coverage` | Untagged code/test files | configurable |
| `test_health` | Test pass rate | configurable % |

Each returns `SenseResult(breached=bool)`. These are the spec's interoception (§4.5.1) made operational. Gemini has `detect_stuck_features()` and `detect_corrupted_events()` — similar intent but fewer monitors and no `SenseResult` type.

---

## 5. What Gemini Has That Claude Should Consider

### 5.1 Pure Functions for State Detection

Gemini's `workspace_state.py` (648 lines) is a collection of **pure functions**: `detect_workspace_state(workspace) → ProjectState`. No side effects, deterministic, testable in isolation. Claude's state detection lives in the agent instructions (`gen-start.md`) — it's LLM-interpreted, not code-executed. This means:

- Gemini can unit-test state detection with fixtures
- Claude's state detection depends on LLM following instructions correctly
- Gemini's routing is deterministic; Claude's is "usually correct"

**Recommendation**: Port `detect_workspace_state()` to Python. The state machine is finite (8 states) and deterministic — it shouldn't require an LLM.

### 5.2 Projector Separation

Gemini cleanly separates event emission (`EventStore.emit()`) from state derivation (`Projector.get_feature_status()`). Claude mixes emission (`fd_emit`) with engine logic (`engine.py`). A clean `Projector` class would:

- Enable derived views without running the engine
- Make STATUS.md generation deterministic code, not agent instructions
- Enable event replay for debugging

**Recommendation**: Extract a `Projector` module from Claude's engine.

### 5.3 Workspace Validation as Built-In

Gemini's `validate_invariants()` runs as part of the engine, not as a separate command. Claude has `/gen-status --health` which is agent-interpreted. A built-in validation step (delta must not increase, events must be well-formed) would catch issues earlier.

**Recommendation**: Add invariant validation to the engine's `iterate_edge()` loop — fail fast on constraint violation.

---

## 6. Detailed Comparison Table

| Dimension | **imp_claude** | **gemini_cli** | **Honest Assessment** |
|-----------|---------------|----------------|----------------------|
| **Lines of Python** | 1,936 (engine + modules) | ~1,500 (engine + workspace) | Comparable scale |
| **Core Algorithm** | Loop + per-check dispatch | Loop + per-functor dispatch | Claude: finer granularity. Gemini: cleaner abstraction |
| **Type Safety** | Enums + dataclasses everywhere | Dicts with string keys | Claude wins — errors caught at construction |
| **Checklist Resolution** | Full $variable binding from constraints | Not implemented | Claude wins — this IS the constraint surface |
| **Event Emission** | Level 4 (fcntl-locked, always fires) | Append to file (no locking) | Claude wins — safe for concurrent writes |
| **State Detection** | Agent-interpreted (markdown instructions) | Python code (pure functions) | Gemini wins — deterministic, testable |
| **Functor Protocol** | Implicit (dispatch by check_type string) | Explicit (3 classes, same interface) | Gemini wins — cleaner interface |
| **Spawn Detection** | Design doc says `[FUTURE]` | `SpawnRequest` emitted, no execution | Tied — both detect, neither executes |
| **Self-Convergence** | delta=0 on own codebase (949 tests pass) | CLI runs, no self-convergence demo | Claude wins — dogfooding proof |
| **Interoception** | 5 monitors in `fd_sense.py` | 3 detection functions in `workspace_state.py` | Claude has more monitors, both detect stuck |
| **Projector** | Mixed into engine code | Clean `Projector` class | Gemini wins — better separation |
| **Context Hash** | `compute_context_hash()` in config_loader | `compute_context_hash()` in workspace_state | Both implement REQ-INTENT-004 |
| **Profile Routing** | `fd_route.py` — profile → edge ordering | `STANDARD_PROFILE_EDGES` hardcoded list | Claude wins — configurable profiles |
| **Classification** | `fd_classify.py` — REQ tags, findings, signals | Not implemented | Claude wins — traceability |
| **Tests** | 949 + 34 E2E | 502 (shared spec + implementation) | Claude has more coverage depth |

---

## 7. Architectural Recommendations

### 7.1 For Claude (What We Should Build Next)

| Priority | What | Why | Effort |
|----------|------|-----|--------|
| **High** | Port state detection to Python | State machine is finite, deterministic — shouldn't need LLM | ~200 lines |
| **High** | Extract `Projector` module | Clean event→state derivation, enable STATUS.md generation in code | ~150 lines |
| **Medium** | Add invariant validation to engine loop | Fail fast on delta increase, malformed events | ~50 lines |
| **Medium** | Implement F_P construct (not just evaluate) | Engine currently evaluates only — needs construct to close the iterate loop | ~300 lines |
| **Low** | Formalise Functor protocol | Make `fd_evaluate`, `fp_evaluate`, `fd_sense` implement explicit protocol | ~100 lines |

### 7.2 For Gemini (What They Should Build Next)

| Priority | What | Why |
|----------|------|-----|
| **High** | Add type safety (dataclasses for results) | Dict Blindness is a real production risk |
| **High** | Implement $variable resolution in checklists | Without this, edge configs aren't parameterised by project |
| **Medium** | Per-check dispatch (not per-functor) | Need check-level granularity for pattern detection |
| **Medium** | File-lock event emission | Concurrent writes will corrupt events.jsonl |
| **Low** | Actually execute spawns recursively | SpawnRequest is detected but never runs |

### 7.3 For the Spec (What Both Implementations Reveal)

| Finding | Implication |
|---------|-------------|
| State detection is finite and deterministic | Spec should require code-based state detection, not LLM-interpreted |
| $Variable resolution is essential for multi-project reuse | Spec should elevate constraint binding from implementation detail to requirement |
| Spawn detection ≠ spawn execution | Spec should separate these as distinct requirements |
| Per-check vs per-functor dispatch affects observability | Spec should specify minimum event granularity |

---

## 8. Final Assessment

Gemini's report concludes: "take the Generic/Recursive logic of gemini_cli and wrap it in the Strongly-Typed Models of imp_claude."

My counter-assessment: **there is no generic/recursive logic to take**. Gemini has a clean 3-class functor protocol (good) and a spawn signal (also good, but Claude has the same in design). What Gemini actually has that's worth adopting is:

1. **Pure-function state detection** — deterministic, testable, no LLM dependency
2. **Clean Projector separation** — event store and state derivation as distinct modules
3. **Built-in invariant validation** — fail fast, don't wait for health check

What Claude has that Gemini needs:

1. **Typed results** — enums and dataclasses, not dicts
2. **$Variable resolution** — constraint surface as actual variable binding
3. **Per-check dispatch** — check-level granularity for observability
4. **Event locking** — safe concurrent writes
5. **Self-convergence proof** — engine that dogfoods on its own codebase

The "cleanest possible version" isn't a merge — it's **each implementation adopting the other's genuine strengths while discarding the overstated claims**.

---

## Appendix: Code Evidence

All claims in this report can be verified against:

| Claim | File | Lines |
|-------|------|-------|
| Per-check dispatch | `engine.py` | 78-88 |
| $Variable resolution | `config_loader.py` | 44-60 |
| Typed results | `models.py` | 1-126 |
| Level 4 event emission | `fd_emit.py` | 46-52 |
| Self-convergence | `__main__.py` | 103-317 |
| 5 interoceptive monitors | `fd_sense.py` | 17-246 |
| Profile routing | `fd_route.py` | 42-87 |
| Deterministic classification | `fd_classify.py` | 1-143 |
| Gemini spawn = hardcoded heuristic | `imp_gemini/gemini_cli/functors/f_probabilistic.py` | 25-35 |
| Gemini dict returns | `imp_gemini/gemini_cli/engine/iterate.py` | 1-67 |
| Gemini pure state detection | `imp_gemini/gemini_cli/internal/workspace_state.py` | 1-648 |
