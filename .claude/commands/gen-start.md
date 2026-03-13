# /gen-start — State-Driven Routing Entry Point

<!-- Implements: REQ-UX-001, REQ-UX-002, REQ-UX-004, REQ-UX-005, REQ-TOOL-003 -->
<!-- Implements: REQ-INTENT-001, REQ-INTENT-002 -->
<!-- Design: ADR-032 (skills as dispatch surfaces) -->

State machine controller. Detects project state, selects the next work unit,
runs the engine, handles F_P dispatch. The engine owns all logic and events.
This skill owns only the MCP handoff.

## Usage

```
/gen-start [--auto] [--human-proxy] [--feature REQ-F-*] [--edge "source→target"]
```

| Flag | Effect |
|------|--------|
| `--auto` | Loop through all pending targets until converged or blocked |
| `--human-proxy` | Evaluate F_H gates as proxy (requires `--auto`) |
| `--feature` | Override feature selection |
| `--edge` | Override edge selection |

## Execution

**Step 1 — Run the engine**

```bash
PYTHONPATH=.genesis python -m genesis start \
  [--auto] [--human-proxy] [--feature {F}] [--edge {E}]
```

Parse stdout as JSON.

**Step 2 — Route on exit code**

| Exit | Status | Action |
|------|--------|--------|
| 0 | converged / nothing_to_do | Done. Report to user. |
| 2 | fp_dispatched | MCP dispatch (Step 3) |
| 3 | fh_required | Surface gate to user. Wait for approval. |
| 1 | error | Report error. Stop. |

**Step 3 — MCP dispatch (exit code 2 only)**

```
manifest_path = output["fp_manifest_path"]
manifest = read(manifest_path)
```

Call `mcp__claude-code-runner__claude_code` with:
- `prompt`: manifest["prompt"]
- `workFolder`: workspace root

Actor writes result to `manifest["result_path"]`.

Go to Step 1.

## F_H Gate (exit code 3)

Surface the gate output to the user verbatim. Wait.
On approval: append `review_approved` event to events.jsonl, then Step 1.
On rejection: stop. Report to user.

## Human Proxy Mode

`--human-proxy` is only valid with `--auto`. Never activate from config or env.
At each F_H gate the engine signals `fh_required`. The skill evaluates the gate
criteria from the manifest, writes a proxy-log to
`.ai-workspace/reviews/proxy-log/`, emits
`review_approved{actor: "human-proxy"}`, then returns to Step 1.

Proxy decisions are provisional. `gen-status` surfaces them for morning review.
