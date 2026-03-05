# ADR-023: MCP as Primary Agent Invocation Transport

**Series**: imp_claude (Claude Code implementation decisions)
**Status**: Accepted
**Date**: 2026-03-05
**Scope**: `fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py`, engine CLI, E2E test runner
**Supersedes**: Transport assumption in ADR-021 §"Engine mode — protocol in code"
**Extends**: ADR-021 (Dual-Mode Traverse), ADR-019 (Orthogonal Projection Reliability)

---

## Context

### The lost decision

In February 2026, the E2E test suite was validated with two explicit invocation paths for calling Claude:

- **MCP tool path** — used when running from within an active Claude Code session: the calling Claude issues a `claude_code` tool call via `@steipete/claude-code-mcp`. No subprocess spawned; the MCP server manages the Claude instance lifecycle.
- **Subprocess path** — used from CI or headless contexts: `claude -p` with wall timeout and `--max-budget-usd` cap.

The commit `2cf2605` (2026-02-22) records: *"Runs via subprocess (CI) or MCP claude_code tool (interactive) — All 22 validators pass against MCP-driven convergence."* The SETUP.md from that commit documents both paths explicitly.

**What was lost:** Five days later (commit `b97e02e`, 2026-02-27), `fp_subprocess.py` was introduced with the note *"Patterns extracted from `imp_claude/tests/e2e/conftest.py` (proven in E2E runs)."* The session that wrote `fp_subprocess.py` had compacted context — it saw only the subprocess code in the conftest and formalised that as the sole transport. The MCP path, which existed in conversation and in the commit message but not in a committed code file or ADR, was silently dropped.

The entire `fp_subprocess.py` complexity — watchdog threads, stall detection, SIGTERM→SIGKILL escalation, environment sanitisation — exists because the subprocess transport is inherently fragile. Subsequent sessions then spent further cycles patching that fragility (Popen stall detection, heartbeat, wall-ceiling multipliers) without recognising that the root cause was the wrong transport choice.

This ADR exists to make the decision durable so context compaction cannot erase it again.

### Why subprocess is the wrong primary transport

`claude -p` as a subprocess has four structural problems:

1. **Cold start per call.** Every F_P invocation spawns a new process: load the Claude binary, initialise the runtime, authenticate, load MCP tool registrations, parse the prompt. This cost is paid on every check. For a 10-check edge, that is 10 cold starts.

2. **Output buffering is opaque.** As documented in the original conftest: *"claude -p buffers all output until completion, so stall detection based on output bytes doesn't work."* Every attempt to add liveness detection (watchdog threads, Popen byte-reading, stall timeouts) is fighting this property rather than working with it.

3. **No session continuity.** Each subprocess call has no memory of prior calls on the same edge. Context must be reconstructed from scratch: edge config loaded, spec injected, prior artifact injected — every time. In a 3-iteration convergence loop, the same context is loaded 3 times.

4. **Process management complexity leaks into application code.** `fp_subprocess.py` is 183 lines of process group management, environment sanitisation, and timeout escalation. None of this is methodology logic. It exists solely to compensate for using the wrong transport.

### Why MCP is the right primary transport for interactive mode

When the engine is invoked from within a Claude Code interactive session (ADR-021 interactive mode), the calling Claude has access to MCP tools. The `@steipete/claude-code-mcp` server is already declared in `.mcp.json` and installed via `package.json`.

The MCP invocation model:

```
Interactive Claude session (gen-iterate)
  │
  │  claude_code tool call (MCP protocol over stdio)
  ▼
claude-code-mcp server  ← persistent, already running
  │
  │  starts / reuses Claude instance
  ▼
Claude agent  ← executes F_P construct or evaluate
  │
  │  returns structured result via MCP tool response
  ▼
Interactive Claude session  ← receives result, updates feature vector
```

Properties:
- **No cold start.** The MCP server is persistent; the Claude instance is reused across calls within the same engine invocation.
- **No buffering problem.** MCP is a message-passing protocol over stdio, not raw stdout scraping. The response is a structured tool result delivered atomically.
- **No process management.** The calling Claude issues a tool call; the MCP server handles lifecycle. No watchdog threads, no SIGTERM, no environment sanitisation.
- **Structured output natively.** MCP tool responses are JSON by protocol. No `--json-schema` flag needed; no output parsing fragility.
- **Liveness is the MCP connection.** If the server goes silent, the tool call times out cleanly via MCP protocol semantics — not via byte-counting on a pipe.

---

## Decision

### Primary transport: MCP tool call (interactive mode)

When `gen-iterate` runs in interactive mode (ADR-021), F_P construct and F_P evaluate calls use the `claude_code` MCP tool provided by `@steipete/claude-code-mcp`:

```
Tool: claude_code
Input: {
  "prompt": "<full mandate: edge config + spec + asset + constraints>",
  "output_format": "json",
  "model": "claude-sonnet-4-6"
}
Output: { "result": "<structured JSON>", "cost_usd": 0.042, "duration_ms": 8300 }
```

The calling Claude receives the result as a tool response and proceeds. No subprocess is spawned by `gen-iterate` for F_P calls; the MCP server manages that.

### Fallback transport: subprocess (CI / headless mode)

When running from CI or any context without an active Claude Code session (no MCP server available), `fp_subprocess.py` is used as before. The fallback is detected by checking whether `CLAUDE_CODE_SSE_PORT` is set in the environment — this is the canonical indicator that an active Claude Code session exists (see ADR-024 §Transport selection for the definitive detection logic).

The subprocess path is not deprecated — it is the correct transport for headless/CI contexts where no interactive session exists. It is wrong only as the *primary* transport when a better one is available.

**Note (ADR-024 update):** ADR-024 strengthens this: for F_P actor invocations specifically, the fallback is not subprocess but **skip** (return `StepResult(skipped=True)`). The subprocess path for F_P (`claude -p`) is removed entirely. ADR-024 is the authority for F_P transport; ADR-023 remains the authority for *why* MCP is primary.

### F_D evaluate: no change

Deterministic checks (pytest, lint, type_check, coverage) run as direct subprocesses of the engine regardless of transport mode. These are not Claude calls; the subprocess transport is correct for them. `fd_evaluate.py` is unaffected by this ADR.

### Transport selection

```python
def _mcp_available() -> bool:
    """Canonical MCP availability check — shared by ADR-023 and ADR-024.

    CLAUDE_CODE_SSE_PORT is set by Claude Code when running inside an active session.
    This is the single detection point used by all transport selection logic.
    """
    return bool(os.environ.get("CLAUDE_CODE_SSE_PORT"))
```

---

## Implementation plan

### Phase 1: MCP invocation in fp_construct.py (replaces fp_subprocess.py for F_P)

Replace the `run_claude_isolated()` call in `fp_construct.py` with an MCP tool call when the MCP transport is available:

```python
# fp_construct.py — MCP path
def run_construct_mcp(prompt: str, model: str) -> ConstructResult:
    """Invoke F_P construct via MCP claude_code tool.

    Called from within an active Claude Code session.
    The calling Claude issues this as a tool use; result is delivered
    as a structured MCP tool response.
    """
    # This function body is executed by the calling Claude as a tool call.
    # In practice: the calling Claude's gen-iterate command issues:
    #   Tool: claude_code
    #   Input: { "prompt": prompt, "model": model }
    # and receives the result as a tool response.
    # fp_construct.py documents the contract; the actual invocation
    # is a tool call in the gen-iterate agent context.
    ...
```

### Phase 2: fp_subprocess.py scoped to CI fallback only

Rename or wrap `fp_subprocess.py` as `fp_subprocess_ci.py` (or gate behind `GENESIS_TRANSPORT=subprocess`). Remove the stall-detection and heartbeat complexity — the fallback only needs a simple wall-clock timeout since CI runs are bounded by the pipeline timeout.

### Phase 3: gen-iterate agent updated

Update `gen-iterate.md` to document the MCP invocation pattern for engine-affinity edges:

```markdown
## Engine-affinity edges (design→code, code↔unit_tests, cicd)

For engine-affinity edges, gen-iterate invokes the F_P construct via MCP:

Use the `claude_code` tool with the following mandate:
[mandate template]

Receive the JSON result and update the feature vector trajectory.
```

---

## Consequences

**Positive:**
- Eliminates the subprocess management complexity from the interactive path (`fp_subprocess.py` stall detection, watchdog threads, SIGTERM escalation).
- Cold start cost eliminated for multi-iteration convergence loops — same Claude instance across iterations.
- Liveness monitoring is the MCP connection, not byte-counting on a pipe. Gemini's critique of the pipe-scraper approach (2026-03-05 comment) is resolved at the transport layer, not patched at the application layer.
- `fp_subprocess.py` complexity is appropriate for its actual scope: CI fallback, not primary transport.

**Negative / Trade-offs:**
- MCP path requires `@steipete/claude-code-mcp` to be installed and running — additional setup step for new machines. (Already documented in SETUP.md; already declared in `package.json`.)
- Engine invocations from headless scripts still use subprocess. Two code paths must be maintained.
- Transport selection adds a startup check. Acceptable — the check is a lightweight MCP ping, not a heavy probe.

---

## Why this was lost — and how to prevent recurrence

The MCP path was validated in E2E testing (Feb 22) but existed only in conversation context and a commit message. No ADR was written. When context compacted (Feb 27), the next session saw only the subprocess code and formalised that.

**Prevention rule**: Any architectural decision that requires infrastructure (MCP server, environment variable, installed package) must have an ADR written the day it is validated. A decision that lives only in a commit message is not durable across context compaction.

This ADR is written five days late. The infrastructure (`.mcp.json`, `package.json`, `@steipete/claude-code-mcp`) was already correct. Only the decision record was missing.

---

## References

- [ADR-021](ADR-021-dual-mode-traverse.md) — dual-mode traverse; this ADR extends the transport layer of engine mode
- [ADR-019](ADR-019-orthogonal-projection-reliability.md) — orthogonal projection; MCP transport does not change cross-validation semantics
- [ADR-020](ADR-020-fp-construct-batched-evaluate.md) — F_P construct; MCP transport replaces subprocess in the construct path
- `imp_claude/tests/e2e/SETUP.md` — documents MCP setup; pre-existing, correct
- `.mcp.json` — MCP server declaration; pre-existing, correct
- `package.json` — `@steipete/claude-code-mcp` dependency; pre-existing, correct
- `imp_claude/code/genesis/fp_subprocess.py` — subprocess fallback; scoped to CI by this ADR
- Git commit `2cf2605` (2026-02-22) — "All 22 validators pass against MCP-driven convergence" — evidence that MCP path was validated
- Git commit `b97e02e` (2026-02-27) — `fp_subprocess.py` introduced; the point where MCP path was lost
- Gemini comment `20260305T170000_STRATEGY_OTLP-NATIVE-ACTORS.md` — correctly identified subprocess fragility; this ADR resolves the root cause rather than patching the symptom
