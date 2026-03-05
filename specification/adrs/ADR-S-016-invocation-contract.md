# ADR-S-016: Invocation Contract — invoke(Intent, State) → StepResult

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-05
**Scope**: All implementations — functor interface, transport selection, StepResult schema
**Extends**: ADR-S-015 (transaction model), ADR-017-imp_claude (functor execution model)

---

## Context

ADR-017 (imp_claude) defined three functor categories: F_D (deterministic), F_P (probabilistic), F_H (human). It specified *what* each category does but not *how* the engine calls them. Each implementation has evolved its own calling convention:

- `imp_claude`: `run_claude_isolated(cmd, timeout)` → subprocess stdout
- `imp_gemini`: `IterateEngine.run(feature, edge)` → Prefect workflow result
- `imp_claude` E2E runner: `run_claude_headless(project_dir, prompt)` → `ClaudeRunResult`

These are all implementations of the same underlying concept — delivering an intent to a functor and receiving the output state — but they have incompatible interfaces. Cross-implementation observability (ADR-S-014 OTLP) and the event log (ADR-S-011) need a common vocabulary for what was invoked and what it produced.

This ADR specifies the minimal interface that every functor invocation must satisfy, regardless of implementation.

---

## Decision

### The invocation contract

Every functor invocation takes an `Intent` and a `State` and returns a `StepResult`:

```
invoke(intent: Intent, state: State) → StepResult
```

**Intent** is the parameterised operation — what to do, on what, against what constraints:

```
Intent:
  edge:         str          # e.g. "design→code"
  feature:      str          # e.g. "REQ-F-CONV-001"
  grain:        str          # "iteration" | "edge" | "feature" (ADR-S-017)
  constraints:  dict         # from project_constraints.yml
  context:      list[Asset]  # spec, prior artifacts, context sources
  budget_usd:   float        # maximum cost for this invocation
  run_id:       UUID         # OL runId for transaction linkage (ADR-S-015)
```

Intent is the first primitive of the Asset Graph Model applied to a specific invocation. It is not a new concept — it is the scoped form of the project-level Intent node.

**State** is the current asset filesystem — the working copy of the project at the point of invocation. For local implementations this is a directory path. For cloud implementations it may be a content-addressed snapshot reference.

**StepResult** is the outcome:

```
StepResult:
  run_id:       UUID                   # matches intent.run_id
  converged:    bool                   # delta == 0
  delta:        float                  # 0.0 = converged, >0 = gap remaining
  artifacts:    list[VersionedArtifact]
  spawns:       list[SpawnRecord]
  cost_usd:     float
  duration_ms:  int
  audit:        StepAudit

VersionedArtifact:
  path:          str
  content_hash:  str     # sha256 — written to COMPLETE event outputs[]
  previous_hash: str     # sha256 of input — written to COMPLETE event outputs[]

SpawnRecord:
  child_run_id:  UUID
  feature:       str
  edge:          str
  reason:        str

StepAudit:
  functor_type:  str     # "F_D" | "F_P" | "F_H"
  transport:     str     # "subprocess" | "mcp" | "api" | "human"
  stall_killed:  bool
  budget_capped: bool
  exit_code:     int | None
```

### The functor registry

Each implementation maintains a registry that maps (edge, grain, environment) to a concrete functor implementation:

```
registry(edge, grain, env) → Functor

Functor satisfies: invoke(Intent, State) → StepResult
```

The engine calls `invoke()` without knowing the transport. The registry resolves the appropriate implementation based on:
- **Edge affinity**: ADR-021 dual-mode affinity table (design→code → engine; intent→requirements → interactive)
- **Grain**: finer grain may prefer F_D; coarser grain may require F_P or F_H
- **Environment**: interactive Claude session → MCP transport available; CI → subprocess only

### Liveness monitoring is part of the contract

Any F_P or F_H functor that runs longer than `intent.budget_usd` or crosses a stall threshold MUST be terminated and return a `StepResult` with `converged=False`, `audit.budget_capped=True` or `audit.stall_killed=True`. The engine treats this as an unconverged step and re-iterates or escalates.

Liveness is monitored via **filesystem activity** (files written to artifact directories), not via transport-layer byte counting. This is the semantic proxy established by the E2E runner: a functor producing artifacts is alive; a functor that has stopped writing is stalled.

### What the contract does NOT specify

- The internal mechanism of any functor (subprocess, MCP tool call, LLM API, human form)
- The prompt format or agent instructions delivered to F_P functors
- The specific checks run by F_D functors
- The UI or notification mechanism for F_H functors

These are implementation details. The contract specifies only the interface boundary.

---

## Consequences

**Positive:**
- All implementations share a common vocabulary for invocation — cross-implementation observability is unambiguous.
- Transport changes (subprocess → MCP per ADR-023) are internal to the functor registry; the engine and event schema are unaffected.
- `StepResult.artifacts` with content hashes directly populates the COMPLETE event's `outputs[]` (ADR-S-015) — no translation layer needed.
- `StepResult.spawns` directly encodes the recursion tree for fold-back resolution.
- New functor types (e.g., cloud-native execution, agent-to-agent MCP) plug into the registry without engine changes.

**Negative / Trade-offs:**
- Implementations must adapt existing calling conventions to produce `StepResult`. `imp_claude`'s `ClaudeRunResult` and `imp_gemini`'s Prefect workflow result are both partial implementations that need wrapping.
- `Intent.run_id` must be generated before invocation (for the START event), which constrains dispatch order slightly.

---

## Current implementation status

| Field | imp_claude | imp_gemini |
|---|---|---|
| `Intent` struct | Implicit (prompt string + edge config) | Implicit (feature + edge params) |
| `StepResult` | `ClaudeRunResult` (partial) | Prefect result (partial) |
| `artifacts` with hashes | ❌ not yet | ✅ implemented 2026-03-05 |
| `spawns` | ❌ not yet | Partial |
| `StepAudit` | Partial (`stall_killed`, `timed_out`) | Partial |
| Functor registry | Implicit (fp_subprocess.py) | Implicit (IterateEngine) |

Neither implementation is fully compliant today. This ADR defines the target; implementations converge toward it.

---

## References

- [ADR-S-015](ADR-S-015-unit-of-work-transaction-model.md) — transaction model; `StepResult.artifacts` populates COMPLETE event outputs
- [ADR-S-017](ADR-S-017-variable-grain-zoom-morphism.md) — grain as a first-class parameter in Intent; spawn = zoom in; fold-back = zoom out
- [ADR-S-011](ADR-S-011-openlineage-unified-metadata-standard.md) — OL event schema consumed by StepResult
- [ADR-023](../../imp_claude/design/adrs/ADR-023-mcp-as-primary-agent-transport.md) — MCP transport; one implementation of F_P functor satisfying this contract
- [ADR-021](../../imp_claude/design/adrs/ADR-021-dual-mode-traverse.md) — edge affinity table used by the functor registry
