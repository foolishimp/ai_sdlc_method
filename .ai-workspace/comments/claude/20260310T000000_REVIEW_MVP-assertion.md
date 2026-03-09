# REVIEW: Genesis MVP Assertion — v3.0.0-beta.1

**Author**: Claude Sonnet 4.6 (imp_claude tenant)
**Date**: 2026-03-10T00:00:00Z
**Addresses**: MVP scope definition for v3.0.0-beta.1
**For**: all (independent evaluator)

## Summary

Genesis is an AI-augmented SDLC engine. Its MVP is defined as: a practitioner can
point Genesis at a project, run `/gen-iterate`, and Genesis autonomously drives that
project from intent to converged, tested code — without the practitioner writing code.
One capability remains incomplete. All others are done and evidenced.

## What Is Done

| Capability | Evidence |
|------------|----------|
| Spec + graph (10 nodes, 10 transitions) | `graph_topology.yml`, 86 REQ keys, ADR-S-001..031 |
| Installer (= CI/CD — deploys Genesis to any project) | `gen-setup.py`, REQ-TOOL-011/015 |
| Interactive iteration (`/gen-iterate` LLM path) | 13 commands, dogfooded across 339 commits |
| F_D deterministic evaluation | Engine `__main__.py`, OL events, runId causation, 1880 unit tests |
| Convergence signal (delta→0) | 25/25 features converged via this mechanism |
| Observability (= production telemetry — genesis_monitor) | Full stack: parsers → projections → HTMX UI, executor attribution |
| CONSENSUS functor (F_H human gate) | `consensus_engine.py`, 47 tests, architecture approved 2026-03-10 |
| Self-monitoring (methodology applied to itself) | `events.jsonl`, workspace_state monitors, affect triage |

## What Is Not Done

One capability:

**Engine Phase B — F_P actor dispatch via MCP round-trip**

When `/gen-iterate --mode engine` runs and F_D returns `delta > 0`, the engine is
specified (T-008, ADR-023/024) to build an actor mandate and invoke
`mcp__claude-code-runner__claude_code`. That actor modifies files directly. F_D then
re-evaluates. This loop is the autonomous construction path.

Currently the engine evaluates but does not construct. The fold-back contract (intent
manifest file) is implemented. The MCP invocation itself has never executed in a real run.

## What This Means

Without F_P dispatch, Genesis in engine mode is a linter, not a compiler. It can
tell you what's wrong but cannot fix it autonomously. The interactive path works —
it uses the LLM session directly — but requires a human-in-the-loop at every
iteration. That is not autonomous.

## Verification Criterion

```
pytest imp_claude/tests/e2e/ -q
→ 0 errors  (currently 59 — all from missing F_P dispatch)
→ TestE2EConvergence, TestE2EHomeostasis, TestE2EUATEdge all pass
```

Zero errors = MVP complete.

## Confidence

- What is done: **high** — 1967 passing tests, live archived run (`e2e_2.9.0_20260309T115730_0117`).
- The gap exists: **high** — 59 e2e errors are deterministic; all fail at the subprocess fixture (the MCP invocation stub).
- F_P dispatch is the *only* gap: **medium** — there may be integration issues that surface once F_P is wired. The fold-back protocol and actor contract have not been exercised under real load.

## Recommended Action

Implement Engine Phase B (F_P actor dispatch):
1. In `gen-iterate` skill, after F_D Phase A returns `delta > 0`, build actor mandate
2. Invoke `mcp__claude-code-runner__claude_code` with mandate + `max_budget_usd`
3. Actor modifies files directly (full tool access)
4. Re-run F_D Phase A on modified files
5. Loop up to 3 actor calls or until delta=0
6. Run `pytest imp_claude/tests/e2e/` — expect 0 errors
7. Tag v3.0.0-beta.1
