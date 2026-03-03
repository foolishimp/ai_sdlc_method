# Design-Tier Requirements — imp_claude

**Version**: 1.0.0
**Date**: 2026-03-04
**Tier**: Design (Claude-specific — technology-bound)
**Spec parent**: `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`

---

## Purpose

This document anchors Claude-specific design requirements that refine the platform-agnostic spec. These keys appear in `imp_claude/` code and tests with `# Implements:` and `# Validates:` tags but cannot live in the shared spec because they reference Claude CLI details (`claude -p`, specific dataclass names, CLI flags).

**Traceability tier rule**:
- `REQ-*` keys in `specification/requirements/` → spec-level (tech-agnostic, applies to all implementations)
- `REQ-F-FPC-*`, `REQ-NFR-FPC-*`, `REQ-BR-FPC-*`, `REQ-DATA-FPC-*` → design-level (Claude-specific, this file)

The gap tool (`/gen-gaps` layer 1) shall treat this file as a valid requirements anchor for design-tier keys in `imp_claude/`.

---

## §1 F_P Construct & Batched Evaluate (FPC series)

**Spec parent**: REQ-ITER-001 (Universal Iteration), REQ-ITER-003 (Functor Encoding), REQ-EVAL-002 (Evaluator Composition)
**Design ADR**: ADR-020 (F_P Construct & Batched Evaluate)
**Feature**: REQ-F-FP-001 (F_P Construct & Batched Evaluate)

These requirements define the Claude-specific implementation of the F_P construct phase — how the engine generates artifacts by invoking `claude -p` once per edge, batching evaluation into the same call, and threading context across edges.

### REQ-F-FPC-001: Single LLM Call Per Edge (Construct)

**Spec parent**: REQ-ITER-001 (Universal Iteration Function — the engine must be able to construct, not just evaluate)

`fp_construct.run_construct()` shall invoke `claude -p` exactly once per edge traversal. It shall not make multiple separate calls for construction (contrast with the legacy `fp_evaluate.py` which makes one call per check).

**Acceptance**:
- One subprocess spawned per `run_construct()` call
- The prompt encodes the full edge context (asset, criteria, constraints)
- The response contains both the constructed artifact and batched evaluations

**Traces To**: ADR-020 §fp_construct module

---

### REQ-F-FPC-002: Batched Evaluate in Construct Response

**Spec parent**: REQ-EVAL-002 (Evaluator Composition Per Edge — all evaluators for an edge run as a unit)

The construct prompt shall include all agent-type evaluator criteria for the edge. The LLM response shall return an `evaluations` array — one entry per agent check — in addition to the constructed artifact. This eliminates per-check cold-start sessions.

**Acceptance**:
- Prompt includes the full agent checklist from `edge_params/*.yml`
- Response schema: `{"artifact": str, "evaluations": [{"check": str, "result": "pass|fail", "notes": str}]}`
- `parse_response()` maps evaluations to `CheckResult` objects
- One LLM call replaces N per-check `fp_evaluate.py` calls

**Traces To**: ADR-020 §Batched Evaluate, REQ-EVAL-002

---

### REQ-F-FPC-003: Context Threading Between Edges

**Spec parent**: REQ-ITER-001 (Universal Iteration — context[] accumulates across the graph traversal)

`engine.run()` shall accumulate constructed artifacts between `run_edge()` calls. Each subsequent edge receives the prior edges' artifacts as additional context entries in Context[].

**Acceptance**:
- After `run_edge(edge_1)` with `construct=True`, artifact is appended to context
- `run_edge(edge_2)` prompt contains `--- {edge_1} artifact ---` section
- Context grows monotonically through the traversal (no truncation)

**Traces To**: ADR-020 §Context Threading, REQ-ITER-001

---

### REQ-F-FPC-004: Engine Construct Integration

**Spec parent**: REQ-ITER-001 (iterate() must support construction as a first-class operation)

`engine.iterate_edge()` shall accept a `construct: bool` parameter. When `True`, it calls `fp_construct.run_construct()` before the evaluate phase. The constructed artifact is written to the filesystem before evaluators run against it.

**Acceptance**:
- `iterate_edge(edge, context, construct=False)` — default is evaluate-only (backward compatible)
- `iterate_edge(edge, context, construct=True)` — calls construct, writes artifact, then evaluates
- Sequence is strictly: construct → write → evaluate (REQ-BR-FPC-001)
- Construct result is included in the edge event

**Traces To**: ADR-020 §Engine Integration, REQ-BR-FPC-001

---

### REQ-F-FPC-005: CLI Construct Mode

**Spec parent**: REQ-TOOL-001 (Developer Tooling — the engine shall be operable from the command line)

`python -m genesis` shall expose a `construct` subcommand and a `--construct` flag on the `evaluate` subcommand to enable construct mode from the CLI.

**Acceptance**:
- `python -m genesis construct --edge "design→code" --feature REQ-F-* --asset path/` invokes construct
- `python -m genesis evaluate --edge ... --construct` is an alias
- Output JSON includes `construct_result` alongside `evaluators`
- Help text describes construct mode

**Traces To**: ADR-020 §CLI, `imp_claude/code/genesis/__main__.py`

---

### REQ-F-FPC-006: Construct Output Schema Validation

**Spec parent**: REQ-EVAL-002 (Evaluator Composition — evaluation results must be machine-parseable)

`fp_construct.parse_response()` shall validate the LLM response against the JSON schema: `{"artifact": string, "evaluations": array}`. Invalid JSON or schema violations shall trigger up to 2 retries. After 2 retries, the call returns an error outcome without crashing the engine.

**Acceptance**:
- Valid JSON + valid schema → `ConstructResult` returned
- Invalid JSON → retry up to 2 times (re-prompt with error context)
- After 2 retries → return `ConstructResult(status=ERROR, artifact=None)`
- Engine continues to next edge on ERROR (does not crash)

**Traces To**: ADR-020 §Schema Validation, REQ-ROBUST-003

---

### REQ-NFR-FPC-001: 4 LLM Calls Per Full Traversal

**Spec parent**: REQ-ITER-001 (efficiency of iterate() — cost model)

A full 4-edge traversal using F_P construct mode shall generate at most 4 `claude -p` subprocess calls — one per edge. This replaces the legacy ~33-call pattern (one call per agent check per edge).

**Acceptance**:
- `run()` over 4 edges with `construct=True` → exactly 4 subprocesses spawned
- Measurement via mock subprocess count in tests
- No additional `fp_evaluate.py` calls for agent checks (they are batched into the construct call)

**Traces To**: ADR-020 §Cost Model, FRAMEWORK_COMPARISON_ANALYSIS.md

---

### REQ-NFR-FPC-002: Backward Compatibility (Evaluate-Only Default)

**Spec parent**: REQ-ITER-001 (the iterate() function's evaluate-only path must remain valid)

`construct=False` (the default) must produce identical behaviour to the pre-ADR-020 engine. No existing evaluate-only calls shall break. All 950+ pre-existing tests shall pass without modification.

**Acceptance**:
- `iterate_edge(edge, context)` (no `construct` arg) behaves identically to pre-ADR-020
- All pre-existing tests pass with no changes
- `construct=False` path does not invoke `fp_construct.py` at all

**Traces To**: ADR-020 §Backward Compatibility

---

### REQ-NFR-FPC-003: Timeout and Retry Resilience

**Spec parent**: REQ-ROBUST-002 (Supervisor Pattern for F_P Calls)

`fp_construct.run_construct()` shall have a configurable wall-clock timeout (default 120s). On timeout, it retries once. On the second timeout, it returns `ConstructResult(status=TIMEOUT)`. This is a specialisation of REQ-ROBUST-002's supervisor pattern for the construct case.

**Acceptance**:
- Timeout triggers `SIGTERM` on the subprocess after N seconds
- First timeout → retry with same prompt
- Second timeout → return TIMEOUT outcome, emit failure event
- `fp_construct` timeout is independent of `fd_evaluate` timeouts

**Traces To**: REQ-ROBUST-002, REQ-ROBUST-007 (Failure Event Emission)

---

### REQ-DATA-FPC-001: ConstructResult Dataclass

**Spec parent**: REQ-ITER-001 (iterate() must return a typed result)

The construct phase shall return a typed `ConstructResult` object with at minimum: `artifact: str | None`, `evaluations: list[CheckResult]`, `status: ConstructStatus`, `edge: str`, `duration_s: float`.

**Acceptance**:
- `ConstructResult` is defined in `imp_claude/code/genesis/models.py`
- `status` is an enum: `SUCCESS | ERROR | TIMEOUT`
- `evaluations` is empty list on `ERROR` or `TIMEOUT`
- `artifact` is `None` on `ERROR` or `TIMEOUT`
- Immutable (frozen dataclass or equivalent)

**Traces To**: ADR-020 §Data Model, `imp_claude/code/genesis/models.py`

---

### REQ-BR-FPC-001: Construct-Before-Evaluate Sequence

**Spec parent**: REQ-ITER-001 (iterate() — construction must precede evaluation; you cannot evaluate what doesn't exist)

The engine shall enforce the invariant: construct artifact is written to the filesystem **before** any evaluator runs against it. A partial construct (ERROR/TIMEOUT) shall skip the evaluate phase for that edge and emit a failure event.

**Acceptance**:
- On `construct=True`: file write confirmed before `fd_evaluate` or `fp_evaluate` dispatch
- On `ConstructResult.status != SUCCESS`: evaluate phase is skipped, edge event contains `construct_failed: true`
- No evaluator can observe a partially-written artifact

**Traces To**: ADR-020 §Sequencing Invariant, REQ-ROBUST-007

---

## §2 Coverage Note for /gen-gaps

When `/gen-gaps` layer 1 scans `imp_claude/` for orphan REQ keys, it shall treat this file (`imp_claude/design/DESIGN_REQUIREMENTS.md`) as a valid requirements anchor. Any `REQ-F-FPC-*`, `REQ-NFR-FPC-*`, `REQ-BR-FPC-*`, or `REQ-DATA-FPC-*` key found in `imp_claude/` code or tests that has an entry in this document is **not orphaned** — it is anchored at the design tier.

The tier hierarchy for gap analysis:
1. **Spec tier**: `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (all `REQ-*` keys without platform prefix)
2. **Design tier**: `imp_claude/design/DESIGN_REQUIREMENTS.md` (Claude-specific `REQ-*-FPC-*` keys)
3. **Orphan**: key found in code/tests but absent from both tiers → genuine gap

---

## Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-03-04 | Initial: anchor 11 REQ-F-FPC-* orphan keys (INT-GAPS-001 resolution) |
