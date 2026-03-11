# Claude Genesis Getting Started

This guide is for `imp_claude` only.

It covers:
- installing the Genesis plugin into any target project
- creating a new project workspace
- using Claude Code as the primary operator
- running the deterministic engine from the shell
- proving the full homeostatic loop without continuous human prompting

It does not cover Codex or Gemini bindings.

## Current Shape

`imp_claude` currently has:
- a one-command installer: `python gen-setup.py <target>` (deploys bootloader + engine + commands)
- 19 slash commands: `/gen-start`, `/gen-iterate`, `/gen-gaps`, `/gen-status`, and more
- a deterministic engine CLI: `python -m genesis evaluate | run-edge | construct`
- F_D (deterministic) + F_P (actor dispatch via MCP) + F_H (human gate / CONSENSUS) evaluator triad
- `dispatch_monitor.py` — watches `events.jsonl`, fires `run_dispatch_loop()` on append
- `/gen-start --auto` — homeostatic loop: dispatch pending intents → iterate → repeat
- live e2e proof for Claude convergence (4 standard-profile edges)

`imp_claude` does not yet have:
- a background autonomous `dispatch_monitor` daemon (the watcher exists; daemon mode is post-v3.0)
- installer telemetry (`req=` tags in `gen-setup.py` — deferred to Phase 2 homeostasis)

## Recommended UX

The default user experience should be:
- you tell Claude what outcome you want
- Claude invokes the slash commands for you
- you only drop to engine CLI commands when scripting, debugging, or running CI

So for normal use, prefer prompts like:
- `initialise this project for Genesis`
- `/gen-start`
- `/gen-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-001"`
- `/gen-gaps`
- `/gen-status`

Treat `python -m genesis evaluate ...` as the explicit automation surface, not the primary human UX.

## 1. Install the Plugin into a Target Project

From the repo root, run the installer against any target project directory:

```bash
cd /Users/jim/src/apps/ai_sdlc_method
python imp_claude/code/installers/gen-setup.py /path/to/target-project
```

The installer:
- writes the Genesis Bootloader into `CLAUDE.md`
- creates `.ai-workspace/` with context, features, events, graph, profiles, tasks
- copies the Python engine (32 modules) into `.genesis/genesis/`
- copies all 19 edge_params YAML configs into `.genesis/genesis/config/edge_params/`
- emits a `project_initialized` event into `.ai-workspace/events/events.jsonl`

Verify the install:

```bash
cd /path/to/target-project
PYTHONPATH=.genesis python -m genesis --help
```

Optional smoke test from the repo root:

```bash
python -m pytest imp_claude/tests/ -m "not e2e and not mcp" -q
```

## 2. Normal Interactive Flow

For normal usage, open Claude Code in the target project and let it drive.

### Project bootstrap

Tell Claude:

```text
Initialise this project for Genesis.
```

Or invoke directly:

```text
/gen-init
```

### State-driven routing

Tell Claude:

```text
/gen-start
```

Claude detects the current project state (UNINITIALISED → IN_PROGRESS → ALL_CONVERGED),
selects the highest-priority unconverged feature and edge, and delegates to `/gen-iterate`.

### Single-edge iteration

Tell Claude:

```text
/gen-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-001"
```

Claude runs the F_D gate (deterministic engine), dispatches an F_P actor if needed
(MCP round-trip via `mcp__claude-code-runner__claude_code`), and surfaces any F_H
gate (human approval or CONSENSUS review).

### Autonomous loop

Tell Claude:

```text
/gen-start --auto
```

Claude loops: check for unhandled intents → dispatch → iterate → re-detect state → repeat.
Pauses at F_H gates (human approval required), stuck deltas, or spawn decisions.

### Traceability and gaps

```text
/gen-gaps
/gen-status
/gen-trace
```

`/gen-gaps` runs all three traceability layers: REQ tag coverage (L1), test gap analysis (L2),
and telemetry gap analysis (L3).

### Consensus review

Tell Claude:

```text
/gen-consensus-open --artifact specification/adrs/ADR-001.md --roster human:alice,agent:dev-observer
```

Then:

```text
/gen-comment --review-id REVIEW-ADR-001-1 --participant alice --content "Please make the rollback path explicit."
```

Then:

```text
/gen-dispose --review-id REVIEW-ADR-001-1 --comment-id COMMENT-001 --disposition resolved --rationale "Rollback section added."
```

Then:

```text
/gen-vote --review-id REVIEW-ADR-001-1 --participant alice --verdict approve
/gen-vote --review-id REVIEW-ADR-001-1 --participant dev-observer --verdict approve
```

That is the preferred UX. Claude manages the review flow; you provide judgment at F_H gates.

## 3. Scripted Flow From the Command Line

Use this section when:
- scripting
- building CI checks
- debugging the engine directly
- proving the exact event/artifact sequence outside the Claude Code UX

### Step 1: Drive the first edge (deterministic)

```bash
cd /path/to/target-project
PYTHONPATH=.genesis python -m genesis evaluate \
  --edge "intent→requirements" \
  --feature "REQ-F-DEMO-001" \
  --asset specification/INTENT.md \
  --deterministic-only
```

The engine reads the edge_params config, evaluates the asset against the checklist,
emits Level 4 OL events into `.ai-workspace/events/events.jsonl`, and exits with
the delta as the return code (0 = converged).

### Step 2: Run a full edge loop until convergence

```bash
PYTHONPATH=.genesis python -m genesis run-edge \
  --edge "code↔unit_tests" \
  --feature "REQ-F-DEMO-001" \
  --asset src/demo.py \
  --max-iterations 5
```

`run-edge` loops: F_D gate → if delta > 0, write F_P intent manifest → wait for fold-back →
F_D gate again → until converged or max iterations.

### Step 3: Construct + evaluate in one call

```bash
PYTHONPATH=.genesis python -m genesis construct \
  --edge "intent→requirements" \
  --feature "REQ-F-DEMO-001" \
  --asset specification/INTENT.md \
  --output artifacts/requirements.md
```

F_P builds the output asset, then F_D gates it. Both events are emitted.

### Step 4: Inspect results

```bash
cat .ai-workspace/events/events.jsonl | python -m json.tool | grep event_type
```

Expected event sequence for a converged standard-profile run:
- `project_initialized`
- `edge_started`
- `iteration_completed` (status: iterating)
- `iteration_completed` (status: converged)
- `edge_converged`

## 4. Run `start --auto` (homeostatic loop)

For autonomous progression through all edges:

Tell Claude:

```text
/gen-start --auto --feature "REQ-F-DEMO-001"
```

What happens on each loop iteration:
1. `dispatch_monitor` scans `events.jsonl` for unhandled `intent_raised` events
2. Any pending intents are dispatched via `run_dispatch_loop()`
3. Feature/edge selection: closest-to-complete, highest-priority
4. `/gen-iterate` runs the selected edge
5. State re-detected; loop continues or pauses at F_H gate

Notes:
- F_H gates pause auto-mode; human resolves via `/gen-review` or `/gen-consensus-open`
- After CONSENSUS quorum, `consensus_reached` event triggers dispatch_monitor on next loop
- Budget cap and wall timeout apply to each F_P actor call

## 5. Deterministic Engine Proof

Prove the engine works without a live Claude session:

```bash
# Full convergence e2e (requires Claude CLI — runs one /gen-start --auto session)
python -m pytest imp_claude/tests/e2e/test_e2e_convergence.py -q

# Archived convergence checks (validates a previously recorded run — no Claude CLI)
python -m pytest imp_claude/tests/e2e/test_e2e_archived_convergence.py -q

# Ecosystem / dispatch tests (all deterministic — no Claude CLI)
python -m pytest imp_claude/tests/e2e/test_e2e_ecosystem.py -q

# F_P actor dispatch e2e (requires active Claude Code session: CLAUDE_CODE_SSE_PORT set)
python -m pytest imp_claude/tests/e2e/test_e2e_fp_dispatch.py -m mcp -q
```

Lane 1 (no Claude CLI — runs in CI):

```bash
python -m pytest imp_claude/tests/ -m "not e2e and not mcp" -q
```

Lane 2 (live actor — requires Claude CLI):

```bash
python -m pytest imp_claude/tests/e2e/ -m "e2e or mcp" -q
```

## 6. What "Homeostatic Loop" Means Today

In `imp_claude`, the homeostatic loop is:

```
events.jsonl append
    → dispatch_monitor.check_and_dispatch()
        → intent_observer.get_pending_dispatches()
        → run_dispatch_loop() → run_edge() [F_D → F_P → F_H]
    → if F_H required: emit intent_raised{signal_source: human_gate_required}
    → auto-mode pauses; human resolves
    → CONSENSUS quorum → consensus_reached event
    → dispatch_monitor fires again on next /gen-start --auto iteration
```

The dispatch_monitor is a scan, not a daemon — it runs at the top of every `--auto` loop
iteration and also available as `from genesis.dispatch_monitor import check_and_dispatch`.

A daemon-mode watcher (`run_monitor()`) exists in `dispatch_monitor.py` but is not yet
wired to a background process. That is post-v3.0 work.

From a user-experience perspective:
- the user should run `/gen-start --auto` and let Claude manage dispatch
- Claude pauses at F_H gates and surfaces them as human decisions
- CONSENSUS quorum automatically resumes traversal on the next auto-loop pass

## 7. Genesis Monitor

The monitor observes all projects under a root watch directory:

```bash
cd projects/genesis_monitor/imp_fastapi
genesis-monitor --watch-dir /Users/jim/src/apps --port 8000
```

Open `http://localhost:8000` to see:
- all projects with `.ai-workspace/` — including archived e2e runs in `tests/e2e/runs/`
- feature trajectories, edge convergence, TELEM signals, Gantt charts
- live updates via SSE when any project's workspace changes

Archived e2e runs at `imp_claude/tests/e2e/runs/e2e_VERSION_TIMESTAMP_SEQ/` are
read-only snapshots — the monitor loads them at startup for post-analysis but does not
watch them for changes.

## 8. Related Files

- `imp_claude/code/installers/gen-setup.py` — installer (deploys Genesis to any project)
- `imp_claude/code/genesis/__main__.py` — engine CLI (`evaluate`, `run-edge`, `construct`)
- `imp_claude/code/genesis/engine.py` — `iterate_edge()`, `run_edge()` — the core loop
- `imp_claude/code/genesis/dispatch_monitor.py` — `check_and_dispatch()`, `run_monitor()`
- `imp_claude/code/genesis/intent_observer.py` — `get_pending_dispatches()`
- `imp_claude/code/genesis/edge_runner.py` — `run_edge()` — F_D → F_P → F_H gate
- `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md` — `/gen-start`
- `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md` — `/gen-iterate`
- `imp_claude/tests/e2e/test_e2e_convergence.py` — live Claude convergence proof
- `imp_claude/tests/e2e/test_e2e_ecosystem.py` — deterministic dispatch/intent tests
- `imp_claude/tests/e2e/test_e2e_fp_dispatch.py` — F_P MCP round-trip proof
