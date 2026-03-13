# /gen-iterate — Invoke the Universal Iteration Function

<!-- Implements: REQ-ITER-001, REQ-ITER-002, REQ-UX-004 -->
<!-- Design: ADR-032 (skills as dispatch surfaces) -->

Run one F_D→F_P→F_H cycle on a feature+edge. The engine manages state,
events, and convergence. This skill manages only the MCP handoff.

## Usage

```
/gen-iterate [--feature REQ-F-*] [--edge "source→target"]
```

## Execution

**Step 1 — Run the engine**

```bash
PYTHONPATH=.genesis python -m genesis start \
  [--feature {feature}] [--edge {edge}]
```

Parse stdout as JSON.

**Step 2 — Route on exit code**

| Exit | Status | Action |
|------|--------|--------|
| 0 | converged / nothing_to_do | Done. Report result to user. |
| 2 | fp_dispatched | MCP dispatch (Step 3) |
| 3 | fh_required | Surface gate to user. Wait. |
| 1 | error | Report error. Stop. |

**Step 3 — MCP dispatch (exit code 2 only)**

```
manifest_path = output["fp_manifest_path"]
manifest = read(manifest_path)
```

Call `mcp__claude-code-runner__claude_code` with:
- `prompt`: manifest["prompt"]
- `workFolder`: workspace root

The actor reads its mandate from the manifest, does the construction work
(read files, write code, run tests), and writes its result to
`manifest["result_path"]`.

Go to Step 1. The engine finds the fold-back result and re-evaluates.

## Exit Protocol

Exit code 2 is the only in-skill logic. Everything else is the engine.
The engine emits all events. The engine detects convergence.
The skill's sole responsibility is the MCP tool call the engine cannot make.
