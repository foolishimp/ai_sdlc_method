# STRATEGY: E2E Runner as Canonical Agent Invocation Model

**Author**: Claude Code
**Date**: 2026-03-05T19:00:00Z
**Addresses**: `imp_claude/tests/e2e/conftest.py`, `fp_subprocess.py`, `fp_construct.py`, ADR-023
**For**: all

## Summary

The E2E test runner (`conftest.py`) is not a test fixture — it is a complete, proven implementation of `iterate(Asset, Context[], Evaluators) → Asset'` in Python. It gets the invocation model right in ways the engine's `fp_subprocess.py` does not. All F_P invocation paths should converge toward it. MCP transport (ADR-023) slots into this model cleanly by replacing only the invocation line, leaving the scaffolding, stall detection, and archival intact.

---

## The Model

The E2E runner implements the full iterate() cycle:

```
scaffold(project_dir)          → build Asset (spec, workspace, configs, feature vectors)
run_claude_headless(prompt)    → invoke agent with mandate
validate(project_dir)          → Evaluators inspect output (events, vectors, code, tests)
archive(project_dir)           → persist run for inspection and replay
```

The test suite sitting on top is just 22 different lenses on the validator output. The runner itself is the methodology made executable.

---

## What It Gets Right

### 1. Stall detection via filesystem activity — not stdout bytes

```python
def _project_fingerprint(directory):
    # checks src/, tests/, specification/, events/, features/, agents/
    # returns (latest_mtime, total_file_count)
```

This is semantically correct. "Is the agent working?" means "is it producing artifacts?" — not "is it emitting characters to stdout?" A Claude instance writing 500 lines of code silently for 4 minutes registers as alive. A hung process that stopped writing files registers as stalled. This proxy cannot be fooled by OS-level buffering, pytest dot output, or `PYTHONUNBUFFERED` conflicts.

`fp_subprocess.py` uses stdout byte-counting for its watchdog. Gemini correctly flagged this as fragile (2026-03-05T17:00 comment). The fix is already implemented in the E2E runner — it just hasn't been ported.

### 2. `--max-budget-usd` as the primary hard cap

```python
cmd = ["claude", "-p", "--max-budget-usd", "5.00", ...]
```

Claude enforces the budget internally. This is not the engine's responsibility to estimate or track. The budget cap is the primary safeguard; the watchdog is backup. `fp_construct.py` does not set `--max-budget-usd`. This is a gap: every F_P call has an uncapped cost envelope.

### 3. Process group kill, not process kill

```python
os.killpg(pgid, signal.SIGTERM)  # SIGKILL after 5s if still alive
```

`claude -p` spawns MCP servers and child processes. `proc.kill()` leaves orphans. Process group kill cleans the entire tree. `fp_subprocess.py` has this right; the E2E runner also has it right. Both correct here.

### 4. Session-scoped, once-per-run semantics

The mandate executes once. All validators inspect the same output. This is the correct model for "give the agent a mandate and evaluate the result" — not "call Claude 22 times for 22 checks." The session-scoped fixture enforces this structurally.

### 5. Run archive with manifest and symlink

Every run is preserved in `runs/e2e_<version>_<timestamp>_<seq>/` with:
- Full project directory (code, tests, workspace)
- `stdout.log` + `stderr.log` from the Claude session
- `run_manifest.json` (version, timestamp, pass/fail verdict)
- `test_results.json` (per-test outcomes)
- `e2e_latest` symlink for quick inspection

This is structural observability at the right level: not per-token telemetry, but per-run artifact preservation. Every run is reproducible and comparable.

---

## The Gap: Two Parallel Implementations, One Better

The E2E runner and `fp_subprocess.py` are parallel implementations of the same invocation idea. They are not reconciled:

| Feature | E2E runner (`conftest.py`) | `fp_subprocess.py` |
|---|---|---|
| Stall detection | Filesystem activity (semantic) | stdout bytes (fragile) |
| Budget cap | `--max-budget-usd` ✅ | ❌ not set |
| Process group kill | ✅ | ✅ |
| Run archive | ✅ versioned, with manifest | ❌ |
| Structured output | events.jsonl + feature vectors | `--json-schema` stdout |
| Proven in production | ✅ 22 validators pass | Partial |

The E2E runner is the better implementation. The engine should converge toward it.

---

## How MCP Fits

ADR-023 adopts MCP as the primary transport for interactive-mode F_P invocations. The E2E runner model accommodates this cleanly — only the invocation line changes:

```python
# Current transport (subprocess — CI / headless)
result = run_claude_headless(project_dir, prompt)

# MCP transport (interactive — from within Claude Code session)
result = call_claude_tool(prompt, cwd=project_dir)
# → issues claude_code tool call via @steipete/claude-code-mcp
# → no watchdog thread (MCP protocol has its own timeout semantics)
# → stall detection: poll filesystem fingerprint between MCP status checks
# → process group management: MCP server owns subprocess lifetime
```

The scaffolding, filesystem stall detection, archival, and validation logic are transport-agnostic and should be shared across both paths. The MCP path eliminates the watchdog thread, SIGTERM/SIGKILL escalation, and nesting-guard environment sanitisation. Everything else stays.

The mandate format is also transport-agnostic: `'/gen-start --auto --feature "REQ-F-CONV-001"'` is a valid prompt for both subprocess and MCP invocation.

---

## Proposed Next Steps

These are pre-ADR candidates, ordered by dependency:

**1. Port filesystem stall detection to `fp_subprocess.py`** (no ADR needed — straightforward improvement)
Replace the stdout byte-counting watchdog in `fp_subprocess.py` with the `_project_fingerprint()` approach from the E2E runner. Same logic, different call site.

**2. Add `--max-budget-usd` to all `fp_construct.py` calls** (no ADR needed — gap closure)
Every F_P invocation should declare its budget envelope. The E2E runner uses `$5.00`; the engine should use a configurable value from `project_constraints.yml` or edge config.

**3. Promote E2E runner as the reference implementation of the invocation contract** (candidate for ADR-024)
Formally document that `run_claude_headless()` and its parameters (wall_timeout, stall_timeout, max_budget_usd, process group kill, archive) define the invocation contract for all F_P calls, regardless of transport. MCP and subprocess are two implementations of this contract.

**4. Implement MCP transport path** (ADR-023 — already accepted)
Add `run_claude_via_mcp()` as a transport peer to `run_claude_headless()`. Same contract, different invocation mechanism. Transport selected by `select_transport()` at engine startup.

**5. Unify archive model across engine and E2E runner** (candidate for ADR-024)
Engine F_P runs should produce the same archive structure as E2E runs: versioned directory, manifest, stdout/stderr logs, `e2e_latest`-equivalent symlink. This gives the genesis_monitor dashboard visibility into engine runs, not just E2E test runs.

---

## Connection to the Broader Architecture

The E2E runner embodies the methodology's own evaluation model: give the agent a complete mandate, let it work autonomously, evaluate the output against the spec. The semantic tool era (c4h: `SemanticExtract`, `SemanticMerge`, explicit typed calls) is over — the agent is capable enough to work within its mandate without Python orchestrating individual operations. The runner's job is mandate delivery, liveness monitoring, and result preservation — not semantic scaffolding.

This is the model to standardise across all F_P invocations. The transport (subprocess vs MCP) is a detail. The mandate format, stall detection approach, budget governance, and archive contract are the invariants.
