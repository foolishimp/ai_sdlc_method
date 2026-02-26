# ADR-020: Genesis Engine Binding — Claude Code Platform Design

**Status**: Accepted
**Date**: 2026-02-26
**Deciders**: Methodology Author
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-ITER-003, REQ-EVAL-001, REQ-EVAL-002, REQ-CTX-001, REQ-CTX-002, REQ-SUPV-001, REQ-SUPV-003
**Implements**: [GENESIS_ENGINE_SPEC.md](../../../specification/GENESIS_ENGINE_SPEC.md) v1.0.0
**Extends**: imp_claude ADR-008 (Universal Iterate Agent), ADR-017 (Functor-Based Execution Model), ADR-019 (Orthogonal Projection Reliability)

---

## Context

The Genesis Engine Specification (`genesis_core/specification/GENESIS_ENGINE_SPEC.md`) defines the platform-agnostic contract for the iterate() operation — data model, evaluation pipeline, orchestration, event contract, configuration, and binding points.

This ADR binds that specification to Claude Code. It is the design document that the code in `imp_claude/code/genesis/` implements. Every section traces back to a specific section of the engine spec.

### What Already Exists

The Claude Code implementation preceded the genesis_core specification. The engine code is working (987 tests, delta=0). This ADR formalises the existing binding and identifies where the current implementation deviates from or extends the spec.

| Module | Engine Spec Section | Status |
|--------|-------------------|--------|
| `models.py` | §1 Data Model | `[IMPLEMENTED]` — structurally matches |
| `engine.py` | §2 Evaluation Pipeline, §3 Orchestration | `[IMPLEMENTED]` — iterate_edge, run_edge, run |
| `config_loader.py` | §5 Configuration | `[IMPLEMENTED]` — $variable resolution |
| `fd_evaluate.py` | §6.1 F_D Binding | `[IMPLEMENTED]` — subprocess dispatch |
| `fp_evaluate.py` | §6.2 F_P Binding | `[IMPLEMENTED]` — claude -p subprocess |
| `fd_emit.py` | §4 Event Contract, §6.4 Event Store | `[IMPLEMENTED]` — JSONL + fcntl.flock |
| `fd_route.py` | §3.4 Profile Selection | `[IMPLEMENTED]` — select_profile, select_next_edge |
| `fd_classify.py` | §1.3 Classify unit | `[IMPLEMENTED]` — REQ tag + signal classification |
| `fd_sense.py` | §1.3 Sense unit | `[IMPLEMENTED]` — 5 monitors |
| `dispatch.py` | §1.3 Functional Unit dispatch | `[IMPLEMENTED]` — (unit, category) → callable |
| `__main__.py` | §6.5 CLI entry point | `[IMPLEMENTED]` — evaluate + run-edge subcommands |
| `workspace_state.py` | (no spec section — Claude-specific) | `[IMPLEMENTED]` — workspace discovery |

---

## Decision

**The Claude Code implementation binds the Genesis Engine Specification through Python dataclasses, subprocess dispatch for F_D checks, `claude -p` subprocess for F_P checks, JSONL file with `fcntl.flock` for the event store, and a `python -m genesis` CLI entry point. All binding points are satisfied by subprocess-based mechanisms — no in-process SDK calls, no network APIs, no cloud services.**

The binding philosophy: **everything is a subprocess.** F_D runs shell commands. F_P runs `claude -p`. The engine itself is invocable via `python -m genesis`. This is consistent with Claude Code's architecture as a local CLI tool.

---

## Binding Details

### B1. Data Model Binding (Engine Spec §1)

The engine spec defines 9 types. Claude Code implements them as Python dataclasses and enums in `models.py`:

| Spec Type | Python Implementation | Notes |
|-----------|----------------------|-------|
| Outcome | `class CheckOutcome(Enum)` | PASS, FAIL, ERROR, SKIP |
| Category | `class Category(Enum)` | F_D = "deterministic", F_P = "probabilistic", F_H = "human" |
| FunctionalUnit | `class FunctionalUnit(Enum)` | 8 values matching spec exactly |
| ResolvedCheck | `@dataclass class ResolvedCheck` | Fields match spec; `unresolved: list[str]` |
| CheckResult | `@dataclass class CheckResult` | Fields match spec; stdout/stderr for F_D |
| EvaluationResult | `@dataclass class EvaluationResult` | Fields match spec; spawn_requested as Optional |
| SpawnRequest | `@dataclass class SpawnRequest` | Fields match spec |
| IterationRecord | `@dataclass class IterationRecord` | Fields match spec |
| EngineConfig | `@dataclass class EngineConfig` | Spec fields + `model`, `claude_timeout` (Claude-specific) |

**Claude-specific extensions to EngineConfig**:
- `model: str = "sonnet"` — which Claude model for F_P checks
- `claude_timeout: int = 120` — timeout for `claude -p` subprocess

These extensions do not violate the spec — EngineConfig is a binding point, not a fixed schema.

### B2. Evaluation Pipeline Binding (Engine Spec §2)

The spec's 5-phase pipeline maps directly to `iterate_edge()` in `engine.py`:

```
Spec Phase               Claude Code Implementation
──────────               ──────────────────────────
Phase 1: PRE-FLIGHT      config_loader.resolve_checklist(edge_config, constraints)
                          Validates edge exists in graph_topology
                          Returns List[ResolvedCheck]

Phase 2: EXECUTE CHECKS  For each check:
                            F_D → fd_evaluate.fd_run_check(check, cwd, timeout)
                            F_P → fp_evaluate.fp_run_check(check, asset, context, model, timeout)
                                  (or SKIP if deterministic_only)
                            F_H → SKIP (Phase 1a — no interactive mode yet)

Phase 3: COMPUTE DELTA   delta = sum(1 for cr in results
                               if cr.required and cr.outcome in (FAIL, ERROR))
                          converged = (delta == 0)

Phase 4: ESCALATIONS     For each failed required check:
                            F_D FAIL → "η_D→P: {name}"
                            F_P FAIL → "η_P→H: {name}"

Phase 5: EMIT EVENT       fd_emit.emit_event(events_path, event)
                          Level 4 — guaranteed by program execution
                          fcntl.flock for file locking
```

**No deviations from spec.** The pipeline is implemented exactly as specified.

### B3. F_D Binding — Subprocess Dispatch (Engine Spec §6.1)

**Input**: ResolvedCheck + workspace path + timeout
**Mechanism**: `subprocess.run(check.command, shell=True, cwd=workspace, capture_output=True, timeout=fd_timeout)`

**Pass criterion interpretation** (implemented in `_interpret_result()`):

| Criterion Pattern | Implementation |
|-------------------|---------------|
| `"exit code 0"` | `result.returncode == 0` |
| `"coverage percentage >= N"` | Regex match on `TOTAL\s+\d+\s+\d+\s+(\d+)%` — the pytest-cov TOTAL line |
| `"zero violations"` | `result.returncode == 0` |
| (default) | `result.returncode == 0` |

**Platform-specific**: Uses `/bin/sh` (macOS/Linux). No Windows support. Subprocess timeout via Python's `subprocess.run(timeout=N)`.

**Bug history**: The coverage parser initially matched pytest progress indicators (`[7%]`) instead of the TOTAL line. Fixed with a specific regex for `TOTAL ... N%`.

### B4. F_P Binding — Claude CLI Subprocess (Engine Spec §6.2)

**Input**: ResolvedCheck + asset content + context
**Mechanism**: `subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--model", model], ...)`

**Prompt construction**:
```
You are an evaluator for the "{check.name}" check.

CRITERION: {check.criterion}

ASSET:
{asset_content}

CONTEXT:
{context}

Evaluate whether the asset satisfies the criterion.
Respond as JSON: {"outcome": "pass"|"fail", "reason": "..."}
```

**Platform-specific**:
- Uses `claude -p` (Claude Code CLI) — requires `claude auth login`
- One subprocess per check (cold-start per invocation)
- No context sharing between F_P checks (each is a separate session)
- JSON output parsing for structured response
- Timeout controlled by `config.claude_timeout`

**Cost model**: Each F_P check is a separate LLM invocation. For a typical TDD edge with 2 agent checks, that's 2 cold-start `claude -p` calls (~$0.02-0.05 each). This is the cost of subprocess isolation — no shared context, but no shared failure modes either.

### B5. F_H Binding — Not Yet Implemented (Engine Spec §6.3)

**Status**: `[STUB]` — Phase 1a skips human evaluation checks (Outcome = SKIP).

**Design intent**: The `/gen-review` command (ADR-012) will present candidates to the user via Claude Code's interactive session. The user approves/rejects via natural language. The command translates the decision into a CheckResult.

**Implementation path**: When F_H checks are needed, the engine sets Outcome = SKIP and the orchestrator defers to the interactive LLM session (Strategy A) for human evaluation. The cross-validation protocol (ADR-019) does not require F_H to go through the engine.

### B6. Event Store Binding (Engine Spec §6.4)

**Mechanism**: Append-only JSONL file at `.ai-workspace/events/events.jsonl`

**Implementation** (`fd_emit.py`):
```python
def emit_event(events_path: Path, event: dict) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "a") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(json.dumps(event) + "\n")
        # flock released on file close
```

**Guarantees**:
- **Atomicity**: `fcntl.flock(LOCK_EX)` ensures single-writer on macOS/Linux
- **Durability**: Write + implicit flush on close
- **Ordering**: Lock ensures sequential appends (no interleaving)

**Platform-specific**: `fcntl` is Unix-only. Not portable to Windows. For cloud deployments (Bedrock, etc.), the event store binding would use Firestore, DynamoDB, or Pub/Sub instead.

### B7. Workspace Discovery Binding (Engine Spec §6.5)

**Mechanism**: Walk up the directory tree looking for `.ai-workspace/` marker.

**Implementation** (`__main__.py` + `workspace_state.py`):
1. Start from `--workspace` flag or current directory
2. Walk up until `.ai-workspace/` is found
3. Load `project_constraints.yml` from `.ai-workspace/<tenant>/context/`
4. Load edge params from plugin's `config/edge_params/`
5. Load profiles from plugin's `config/profiles/`
6. Load graph topology from plugin's `config/graph_topology.yml`
7. Build `EngineConfig` from all loaded data

**Tenant resolution**: Claude Code uses `.ai-workspace/claude/` as its tenant directory. The workspace_state module handles the discovery logic.

### B8. CLI Entry Point (Engine Spec §6.5)

**Module**: `python -m genesis` → `__main__.py`

**Subcommands**:

```bash
# Single iteration — evaluate an asset against one edge's checklist
python -m genesis evaluate \
  --edge "code↔unit_tests" \
  --feature "REQ-F-ENGINE-001" \
  --asset imp_claude/code/genesis/engine.py \
  --workspace . \
  --deterministic-only \
  --fd-timeout 120

# Edge loop — iterate until convergence, spawn, or budget exhaustion
python -m genesis run-edge \
  --edge "code↔unit_tests" \
  --feature "REQ-F-ENGINE-001" \
  --asset imp_claude/code/genesis/engine.py \
  --workspace . \
  --max-iterations 10
```

**Output**: JSON matching `IterationRecord` structure:
```json
{
  "edge": "code↔unit_tests",
  "iteration": 1,
  "evaluation": {
    "delta": 0,
    "converged": true,
    "checks": [...],
    "escalations": []
  }
}
```

**PYTHONPATH**: The CLI requires `PYTHONPATH=imp_claude/code` because `genesis` is not installed as a pip package. This is a known limitation of Phase 1a — the plugin installer does not install Python dependencies.

---

## Orchestration Binding (Engine Spec §3)

### O1. run_edge Implementation

`engine.py::run_edge()` implements the spec's single-edge loop:

```python
def run_edge(edge, config, feature_id, profile, asset_content, context=""):
    edge_config = load_edge_config(edge, config.edge_params_dir)
    records = []
    for iteration in range(1, config.max_iterations_per_edge + 1):
        record = iterate_edge(edge, edge_config, config, feature_id,
                              asset_content, context, iteration)
        records.append(record)
        if record.evaluation.converged:
            break
        # Spawn detection at orchestrator level
        if _detect_stuck(events, feature_id, edge, threshold=3):
            record.evaluation.spawn_requested = _build_spawn(...)
            break
    return records
```

**Deviation from spec**: None. Spawn detection is in the orchestrator, not in iterate_edge. This matches ADR-019's principle that iterate is pure evaluation.

### O2. Profile Selection

`fd_route.py::select_profile()` implements the spec's mapping:

| feature_type | Profile |
|-------------|---------|
| feature | standard |
| discovery | spike |
| spike | spike |
| poc | poc |
| hotfix | hotfix |
| (default) | standard |

### O3. Context Accumulation

**Decision** (per ENGINE_DESIGN_GAP.md Gap 3): The engine does NOT accumulate context across edges. The LLM agent accumulates context naturally within its session. When calling the engine for cross-validation, the LLM passes the current asset. The engine is stateless per invocation.

This is a **deliberate design choice**, not a gap. The engine's statelessness is what makes it a reliable cross-validator — it cannot carry forward bias from prior edges.

---

## Cross-Validation Protocol (ADR-019 Binding)

### CV1. Protocol Implementation

The cross-validation protocol defined in ADR-019 binds to Claude Code as follows:

```
┌──────────────────────────────────────────────────────────────┐
│  /gen-iterate (LLM session — Strategy A)                     │
│                                                              │
│  1. LLM reads edge config, asset, context                    │
│  2. LLM constructs next candidate (F_P Construct)            │
│  3. LLM self-evaluates (produces delta_P)                    │
│  4. LLM invokes engine:                                      │
│     $ PYTHONPATH=imp_claude/code python -m genesis evaluate \ │
│       --edge "code↔unit_tests" \                             │
│       --feature "REQ-F-AUTH-001" \                           │
│       --asset <path> \                                       │
│       --deterministic-only --fd-timeout 120                  │
│  5. Engine returns delta_D (Level 4 event emitted)           │
│  6. LLM compares delta_P vs delta_D:                         │
│     - Agreement → trust result                               │
│     - delta_P=0, delta_D>0 → LLM missed failures, fix them  │
│     - delta_P>0, delta_D=0 → LLM stricter, log for review   │
│  7. If delta_D > 0: LLM fixes and re-invokes engine          │
│  8. Converged when delta_D == 0 (hard gate)                  │
│                                                              │
│  Event: engine emits "iteration_completed" (Level 4)         │
│  Event: LLM records both deltas in session log               │
└──────────────────────────────────────────────────────────────┘
```

### CV2. Convergence Gate

**delta_D == 0** is the hard convergence gate. The engine's deterministic checks must all pass. The LLM's delta_P is advisory — it captures judgment-level concerns (code coherence, requirement coverage) that deterministic checks cannot assess.

### CV3. Status

| Protocol Step | Status |
|--------------|--------|
| Engine CLI entry point | `[IMPLEMENTED]` — `python -m genesis evaluate` |
| Engine evaluates assets | `[IMPLEMENTED]` — 5 F_D checks converge (delta=0) |
| LLM invokes engine | `[PARTIAL]` — gen-iterate command spec needs update |
| Delta comparison | `[PLANNED]` — not yet in gen-iterate command |
| Disagreement event type | `[PLANNED]` — event schema extension needed |

---

## Configuration Binding (Engine Spec §5)

### C1. Project Constraints Location

```
.ai-workspace/claude/context/project_constraints.yml
```

This is the Claude Code tenant's constraint file. Other tenants use their own paths (e.g., `.ai-workspace/gemini/context/project_constraints.yml`).

### C2. Edge Params Location

```
imp_claude/code/.claude-plugin/plugins/genesis/config/edge_params/*.yml
```

12 edge parameter files, one per graph edge. Shipped with the plugin, not per-project.

### C3. Profiles Location

```
imp_claude/code/.claude-plugin/plugins/genesis/config/profiles/*.yml
```

6 named profiles: standard, poc, spike, hotfix, full, minimal.

### C4. Dogfooding Configuration

For Genesis validating itself, the project constraints at `.ai-workspace/claude/context/project_constraints.yml` map:

```yaml
tools:
  test_runner:
    command: "python -m pytest"
    args: "imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
    pass_criterion: "exit code 0"
  coverage:
    command: "python -m pytest"
    args: "--cov=imp_claude/code/genesis --cov-report=term-missing imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
    pass_criterion: "coverage percentage >= 0.70"
  linter:
    command: "ruff check"
    args: "imp_claude/code/genesis/"
    pass_criterion: "exit code 0"
  formatter:
    command: "ruff format"
    args: "--check imp_claude/code/genesis/"
    pass_criterion: "exit code 0"
thresholds:
  test_coverage_minimum: 0.70
```

---

## Deviations and Extensions

### D1. workspace_state.py — No Spec Equivalent

`workspace_state.py` (377 lines) handles Claude Code-specific workspace management: directory discovery, YAML loading, feature vector read/write, event log access. The engine spec's §6.5 (Workspace Discovery) covers the contract; this module is the Claude-specific implementation.

**Note**: This module is excluded from coverage metrics (`pyproject.toml [tool.coverage.run] omit`) because it is infrastructure code with complex filesystem interactions that are better validated by E2E tests than unit tests.

### D2. dispatch.py — Functional Unit Table

The spec defines 8 functional units and 3 categories. Claude Code implements a dispatch table mapping `(FunctionalUnit, Category)` → callable. Currently only F_D entries are populated (5 entries). F_P and F_H dispatch through dedicated modules (`fp_evaluate.py`, future F_H module).

### D3. Sensory Monitors — Beyond Spec

`fd_sense.py` implements 5 interoceptive monitors not explicitly in the engine spec:

| Monitor | What it senses |
|---------|---------------|
| freshness | Test staleness (time since last run) |
| stall | Stuck feature vectors (delta unchanged) |
| integrity | Event log consistency |
| coverage | REQ key traceability gaps |
| health | Workspace structure validity |

These implement `specification/AI_SDLC_ASSET_GRAPH_MODEL.md` §6 (Sensory Systems) rather than the engine spec. They are Claude-specific implementations of a methodology-level concern.

### D4. No F_P Construct in Engine

The engine evaluates but does not construct. F_P Construct (generating code, specs, tests) happens in the LLM session (Strategy A). This is by design — the engine is the verifier, the LLM is the builder. The cross-validation protocol (ADR-019, CV1 above) formalises this separation.

---

## Consequences

### Positive

- **Spec traceability**: Every module maps to a section of the engine spec. Future maintainers can trace from spec → design → code.
- **Cross-tenant learning**: Other implementations (Gemini, Codex, Bedrock) can read this ADR to understand how one tenant binds the spec, then make different binding decisions for their platform.
- **Gap visibility**: The status tags (`[IMPLEMENTED]`, `[PARTIAL]`, `[PLANNED]`, `[STUB]`) make it clear what works and what doesn't.
- **Formalises existing work**: The engine code existed before the spec. This ADR retroactively establishes the spec→design→code traceability chain.

### Negative

- **Retroactive design risk**: The spec was extracted from the implementation, not the other way around. If the spec evolves, the implementation may lag.
- **Subprocess overhead**: Everything-is-a-subprocess means cold starts for every F_P check. Mitigated by `--deterministic-only` mode for fast F_D-only runs.
- **Unix dependency**: `fcntl.flock` is Unix-only. If Claude Code ever runs on Windows, the event store binding needs replacement.

### Mitigation

- **Spec drift**: Run engine dogfood (`python -m genesis evaluate`) in CI to detect when implementation diverges from spec expectations.
- **F_P cold starts**: Strategy C cross-validation (LLM constructs in session, engine evaluates F_D only) avoids unnecessary F_P subprocess calls. F_P evaluation stays in the LLM session.
- **Portability**: Event store binding is isolated in `fd_emit.py`. Replacing `fcntl` with a platform-appropriate mechanism affects one file.

---

## References

- [GENESIS_ENGINE_SPEC.md](../../../specification/GENESIS_ENGINE_SPEC.md) — the genesis_core specification this ADR designs against
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3–§5 — iterate(), evaluators, convergence
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — 69 platform-agnostic requirements
- [imp_claude ADR-008](../../../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (the LLM projection)
- [imp_claude ADR-009](../../../../imp_claude/design/adrs/ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration
- [imp_claude ADR-017](../../../../imp_claude/design/adrs/ADR-017-functor-based-execution-model.md) — Functor-Based Execution Model (F_D/F_P/F_H, escalation)
- [imp_claude ADR-019](../../../../imp_claude/design/adrs/ADR-019-orthogonal-projection-reliability.md) — Orthogonal Projection Reliability (cross-validation protocol)
- [imp_claude ENGINE_DESIGN_GAP.md](../../../../imp_claude/design/ENGINE_DESIGN_GAP.md) — Gap analysis that preceded this binding (4 gaps, all resolved)
- [imp_claude FUNCTOR_FRAMEWORK_DESIGN.md](../../../../imp_claude/design/FUNCTOR_FRAMEWORK_DESIGN.md) — Execution strategies (A, B, C)

---

## Requirements Addressed

- **REQ-ITER-001**: iterate() signature and contract — bound to `engine.py::iterate_edge()` (§B2)
- **REQ-ITER-002**: Delta computation and convergence — bound to Phase 3 arithmetic (§B2)
- **REQ-ITER-003**: Functor encoding — bound to `models.py` enums and `dispatch.py` table (§B1, §D2)
- **REQ-EVAL-001**: Three evaluator types — F_D via subprocess (§B3), F_P via claude -p (§B4), F_H stub (§B5)
- **REQ-EVAL-002**: Per-edge composition — bound to `config/edge_params/*.yml` and `resolve_checklist()` (§C2)
- **REQ-CTX-001**: $variable resolution — bound to `config_loader.py` (§C1)
- **REQ-CTX-002**: Checklist composition — bound to `resolve_checklist()` layering (§C1)
- **REQ-SUPV-001**: Event emission — bound to `fd_emit.py` with fcntl.flock (§B6)
- **REQ-SUPV-003**: Failure observability — Level 4 emission guaranteed; cross-validation detects LLM hallucinations (§CV1)
