# Genesis Engine — Platform-Agnostic Specification

**Version**: 1.0.0
**Date**: 2026-02-26
**Foundation**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (§1–§5)
**Derived From**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) v3.13.0
**Parent Theory**: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology) (§V, §VIII-B)

---

## 0. Purpose

This document specifies the **Genesis Engine** — the platform-agnostic execution kernel that implements the four primitives of the Asset Graph Model. Every implementation (`imp_claude/`, `imp_gemini/`, `imp_codex/`, `imp_bedrock/`) binds this specification to a concrete platform. The specification defines WHAT; the implementations define HOW.

The Genesis Engine is not new functionality. It is the **extraction of shared semantics** already present in the Asset Graph Model (§3–§5) and Implementation Requirements (REQ-ITER-*, REQ-EVAL-*, REQ-CTX-*, REQ-SUPV-*), reorganised as an implementable contract.

### What This Document Covers

| Layer | Content | Drives |
|-------|---------|--------|
| **Data Model** | Types, enums, structures | `imp_<name>/design/` data model ADR |
| **Evaluation Pipeline** | Check resolution, dispatch, delta | `imp_<name>/design/` engine ADR |
| **Orchestration** | Edge loops, spawn, routing | `imp_<name>/design/` lifecycle ADR |
| **Event Contract** | Schema, emission guarantees, sourcing | `imp_<name>/design/` observability ADR |
| **Configuration** | $variable resolution, checklist composition | `imp_<name>/design/` configuration ADR |
| **Binding Points** | Platform-specific extension points | `imp_<name>/code/` |

### What This Document Does NOT Cover

- Platform-specific CLI commands, UX, or slash commands (see `specification/UX.md`)
- Graph topology instantiation (see `specification/AI_SDLC_ASSET_GRAPH_MODEL.md` §2)
- Feature vector semantics and projections (see `specification/PROJECTIONS_AND_INVARIANTS.md`)
- User journeys and validation scenarios (see `specification/UX.md`)

---

## 1. Data Model

The engine operates on a small set of types. All implementations must support structurally equivalent representations — the names may vary (Go structs, TypeScript interfaces, Python dataclasses) but the semantics must match.

### 1.1 Outcome

The result of executing a single evaluator check.

```
Outcome ∈ { PASS, FAIL, ERROR, SKIP }
```

| Value | Meaning | Delta impact |
|-------|---------|-------------|
| `PASS` | Check criterion satisfied | 0 |
| `FAIL` | Check criterion not satisfied | +1 if required |
| `ERROR` | Execution failure (timeout, crash, unavailable) | +1 if required |
| `SKIP` | Not executed (unresolved $variable, mode exclusion) | 0 |

**Invariant**: Every check execution produces exactly one Outcome.

### 1.2 Category (Functor Encoding)

The execution substrate for a functional unit (Asset Graph Model §2.9).

```
Category ∈ { F_D, F_P, F_H }
```

| Category | Name | Mechanism | Cost | Ambiguity |
|----------|------|-----------|------|-----------|
| `F_D` | Deterministic | Subprocess, test runner, schema check | Free | Zero |
| `F_P` | Probabilistic | LLM / agent reasoning | Moderate | Bounded |
| `F_H` | Human | Explicit human judgment | High | Persistent |

**Escalation** (natural transformation η): When a check at category C fails to resolve ambiguity, the engine may escalate: $F_D \to F_P \to F_H$.

**Category-fixed units**: `Emit` is always $F_D$. `Decide` is always $F_H$. These are structural constraints, not defaults.

### 1.3 Functional Unit

The 8 named operations in the functor encoding (Asset Graph Model §2.9).

```
FunctionalUnit ∈ { Evaluate, Construct, Classify, Route, Propose, Sense, Emit, Decide }
```

| Unit | Purpose | Category constraint |
|------|---------|-------------------|
| Evaluate | Assess quality, detect gaps | Any |
| Construct | Generate next candidate | Any (typically F_P) |
| Classify | Determine signal type/severity | Any |
| Route | Select next edge or action | Any |
| Propose | Draft a change or intent | Any (typically F_P) |
| Sense | Observe system state | Any (typically F_D) |
| Emit | Record event | F_D only |
| Decide | Approve or reject | F_H only |

### 1.4 ResolvedCheck

A single evaluator check after $variable resolution.

```
ResolvedCheck {
    name:            string        # unique within edge checklist
    check_type:      Category      # F_D | F_P | F_H
    functional_unit: FunctionalUnit
    criterion:       string        # what the check evaluates (human-readable)
    required:        boolean       # if true, FAIL/ERROR increments delta
    command:         string?       # for F_D: shell command to execute
    pass_criterion:  string?       # for F_D: how to interpret command output
    unresolved:      string[]      # $variables that could not be resolved
}
```

**Invariant**: If `unresolved` is non-empty, the check Outcome must be SKIP.

### 1.5 CheckResult

The output of executing one ResolvedCheck.

```
CheckResult {
    name:            string
    outcome:         Outcome
    required:        boolean
    check_type:      Category
    functional_unit: FunctionalUnit
    message:         string        # diagnostic or reason
    command:         string?       # what was executed (F_D)
    exit_code:       int?          # subprocess exit code (F_D)
    stdout:          string?       # captured stdout (F_D)
    stderr:          string?       # captured stderr (F_D)
}
```

### 1.6 EvaluationResult

The aggregate result of one iteration across all checks.

```
EvaluationResult {
    edge:             string           # e.g. "code↔unit_tests"
    checks:           CheckResult[]    # ordered, one per ResolvedCheck
    delta:            int              # count of required FAIL + ERROR
    converged:        boolean          # delta == 0 AND NOT spawn_requested
    escalations:      string[]         # η transitions triggered
    spawn_requested:  SpawnRequest?    # if stuck detection fired
}
```

**Delta computation** (deterministic, always same result for same inputs):
```
delta = |{ c ∈ checks : c.required ∧ c.outcome ∈ {FAIL, ERROR} }|
```

**Convergence**:
```
converged = (delta == 0) ∧ (spawn_requested == null)
```

### 1.7 SpawnRequest

Raised when an edge is stuck — delta unchanged for N consecutive iterations.

```
SpawnRequest {
    question:         string        # what needs investigation
    vector_type:      string        # Discovery | Spike | PoC
    parent_feature:   string        # REQ-F-* of the blocked parent
    triggered_at_edge: string       # edge where stuck was detected
    context_hints:    string[]      # guidance for the child vector
}
```

### 1.8 IterationRecord

The complete record of one `iterate()` invocation.

```
IterationRecord {
    edge:        string
    iteration:   int               # 1-based within this edge traversal
    evaluation:  EvaluationResult
}
```

### 1.9 EngineConfig

The configuration surface for the engine.

```
EngineConfig {
    project_name:           string
    workspace_path:         Path
    edge_params_dir:        Path       # where edge checklist configs live
    profiles_dir:           Path       # where projection profiles live
    constraints:            Dict       # resolved project_constraints.yml
    graph_topology:         Dict       # resolved graph_topology.yml
    max_iterations_per_edge: int       # budget ceiling (default: 10)
    deterministic_only:     boolean    # if true, skip F_P and F_H checks
    fd_timeout:             int        # subprocess timeout in seconds (default: 120)
}
```

---

## 2. Evaluation Pipeline

The core of the engine: load checks, execute them, compute delta. This is the `iterate()` operation (Asset Graph Model §3).

### 2.1 Signature

```
iterate(edge, edge_config, config, feature_id, asset_content, context, iteration)
    → IterationRecord
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `edge` | string | The graph edge being traversed (e.g. `"code↔unit_tests"`) |
| `edge_config` | Dict | Loaded edge parameter YAML (checklist, convergence rules) |
| `config` | EngineConfig | Engine configuration |
| `feature_id` | string | REQ-F-* key |
| `asset_content` | string | The current candidate artifact (source code, spec text, etc.) |
| `context` | string | Additional context (upstream assets, constraints) |
| `iteration` | int | 1-based iteration counter |

**Returns**: `IterationRecord` — the evaluation results without side effects beyond event emission.

### 2.2 Algorithm

The iterate function follows a 5-phase pipeline. Each phase is deterministic given its inputs — no hidden state, no ambient side effects.

```
Phase 1: PRE-FLIGHT
    Load edge config
    Resolve checklist: apply $variable substitution from config.constraints
    Validate edge exists in config.graph_topology
    → On failure: return IterationRecord(delta=-1, converged=false)

Phase 2: EXECUTE CHECKS
    For each ResolvedCheck in resolved_checklist:
        dispatch by check_type:
            F_D → invoke platform binding for deterministic execution
            F_P → invoke platform binding for LLM evaluation
                   (or SKIP if config.deterministic_only)
            F_H → invoke platform binding for human judgment
                   (or SKIP if config.deterministic_only or headless)
        → CheckResult

Phase 3: COMPUTE DELTA
    delta = count(required checks with outcome FAIL or ERROR)
    converged = (delta == 0)
    This phase is pure arithmetic — platform-independent.

Phase 4: DETECT ESCALATIONS
    For each failed required check:
        if F_D failed → record η_D→P escalation signal
        if F_P failed → record η_P→H escalation signal
    Escalations are advisory — they inform the orchestrator, not the iterate function.

Phase 5: EMIT EVENT
    Emit "iteration_completed" event (see §4 Event Contract)
    If converged, also emit "edge_converged" event.
    Event emission is GUARANTEED — it fires regardless of delta value.
    Emission is F_D (deterministic code), not agent-instructed.
```

### 2.3 Separation of Concerns

**Iterate is pure evaluation.** It does NOT:
- Construct the next candidate (that's the orchestrator's job via F_P Construct)
- Detect spawn conditions (that's the orchestrator reading event history)
- Route to the next edge (that's the orchestrator applying the profile)
- Fold back child vector results (that's the orchestrator + human review)

This separation is a structural invariant, not an implementation convenience. The iterate function is the $F_D$ ground truth against which $F_P$ construction is validated. If iterate also constructed, the system would lack a fixed point for convergence detection (ADR-019 in the Claude implementation).

---

## 3. Orchestration

The orchestrator calls `iterate()` in a loop, handles lifecycle decisions, and routes between edges.

### 3.1 run_edge: Single Edge Loop

```
run_edge(edge, config, feature_id, profile, asset_content, context)
    → IterationRecord[]

    records = []
    for iteration in 1..config.max_iterations_per_edge:
        record = iterate(edge, edge_config, config, feature_id, asset_content, context, iteration)
        records.append(record)

        if record.evaluation.converged:
            break

        # Spawn detection: orchestrator reads event history
        if stuck_for_n_iterations(events, feature_id, edge, threshold=3):
            spawn_request = build_spawn_request(feature_id, edge, record)
            emit "spawn_created" event
            record.evaluation.spawn_requested = spawn_request
            break  # parent blocked until child resolves

    return records
```

**Key principle**: Spawn detection lives here, not inside iterate(). The orchestrator has the full event history; iterate() sees only the current iteration.

### 3.2 run: Full Graph Traversal

```
run(feature_id, feature_type, config, asset_content, context)
    → IterationRecord[]

    profile = select_profile(feature_type)  # standard, poc, spike, etc.
    all_records = []

    for edge in profile.edges:
        records = run_edge(edge, config, feature_id, profile, asset_content, context)
        all_records.extend(records)

        last = records[-1]
        if last.evaluation.spawn_requested:
            break  # blocked on child vector
        if not last.evaluation.converged:
            break  # stalled, escalate to human
        # else: edge converged, continue to next

    return all_records
```

### 3.3 Stuck Detection

A feature is **stuck** on an edge when delta remains unchanged for N consecutive iterations (default N=3).

```
stuck(events, feature_id, edge, threshold) → boolean:
    recent = last N events for (feature_id, edge)
    return all(e.delta == recent[0].delta for e in recent) AND recent[0].delta > 0
```

**Response**: The orchestrator raises a SpawnRequest. The parent feature is blocked until the child vector (Discovery, Spike, or PoC) resolves and folds back.

### 3.4 Profile Selection

Profiles are named projections (Projections doc §3). The profile determines which edges exist, which evaluators are active, and what convergence criteria apply.

```
select_profile(feature_type) → profile_name:
    feature    → "standard"
    discovery  → "spike"
    spike      → "spike"
    poc        → "poc"
    hotfix     → "hotfix"
```

---

## 4. Event Contract

Every engine action emits an immutable event to the event log. Events are the **sole integration contract** between the engine and all observability tools (status views, Gantt charts, health checks, telemetry).

### 4.1 Event Structure

All events share a common envelope:

```
Event {
    event_type:  string       # one of the defined types (see §4.2)
    timestamp:   ISO 8601     # when the event was emitted
    project:     string       # project name from EngineConfig
    data:        Dict         # event-type-specific payload
}
```

### 4.2 Core Event Types

| Event Type | Emitted By | Payload |
|------------|-----------|---------|
| `project_initialized` | init command | workspace_path, profile |
| `iteration_completed` | iterate() — Phase 5 | feature, edge, iteration, delta, status, evaluators, checks, escalations |
| `edge_started` | orchestrator — first iteration | feature, edge |
| `edge_converged` | iterate() — when delta=0 | feature, edge, iteration, total_iterations |
| `spawn_created` | orchestrator — stuck detection | parent_feature, child_feature, vector_type, triggered_at_edge |
| `spawn_folded_back` | orchestrator — child resolved | parent_feature, child_feature, resolution |
| `checkpoint_created` | checkpoint command | feature, description |
| `review_completed` | human evaluator | feature, edge, decision, feedback |
| `gaps_validated` | gaps command | coverage_pct, missing_reqs |
| `release_created` | release command | version, features_included |
| `health_checked` | health check | passed, failed, failed_checks, genesis_compliant |

### 4.3 iteration_completed Payload

The richest event type. Every iterate() invocation produces exactly one.

```json
{
    "event_type": "iteration_completed",
    "timestamp": "2026-02-26T10:30:00Z",
    "project": "my-project",
    "feature": "REQ-F-AUTH-001",
    "edge": "code↔unit_tests",
    "iteration": 2,
    "delta": 1,
    "status": "iterating",
    "evaluators": {
        "passed": 4,
        "failed": 1,
        "skipped": 0,
        "total": 5,
        "details": [
            {
                "name": "tests_pass",
                "type": "deterministic",
                "outcome": "pass",
                "required": true
            }
        ]
    },
    "checks": [ ... ],
    "escalations": [],
    "error": null
}
```

### 4.4 Emission Guarantees

Events are the system's memory. Without them, status views, health checks, and telemetry projections cannot be computed.

**Reliability hierarchy** (from most to least trustworthy):

| Level | Mechanism | Guarantee |
|-------|-----------|-----------|
| **Level 4** | Deterministic code (engine emit) | Guaranteed by program execution |
| **Level 3** | Observer pattern (hooks, watchers) | Guaranteed by framework if running |
| **Level 2** | Instrumented hooks (pre/post commit) | Depends on hook installation |
| **Level 1** | Agent instruction (LLM told to emit) | Best effort — LLM may forget |

The engine MUST emit at Level 4. Agent-mode iterate (interactive LLM session) operates at Level 1 and should be cross-validated against Level 4 engine runs.

### 4.5 Event Sourcing

The event log (`events.jsonl`) is an **append-only immutable log**. All views are projections:

```
Source of Truth              Derived Views (projections)
─────────────────            ──────────────────────────
events/events.jsonl    ───►  STATUS.md          (Gantt, telemetry)
  (append-only JSONL)  ───►  ACTIVE_TASKS.md    (convergence events)
                       ───►  features/*.yml     (trajectory per feature)
```

If a view gets corrupted, replay `events.jsonl` to reconstruct it. Views are ephemeral; the log is permanent.

---

## 5. Configuration

### 5.1 $Variable Resolution

Edge checklists reference project-specific values through `$variable` syntax. The engine resolves these at pre-flight (Phase 1) using the project's constraint file.

```
$variable.path  →  project_constraints.yml :: variable.path
```

**Examples**:
```yaml
# In edge config (tdd.yml):
command: "$tools.test_runner.command $tools.test_runner.args"
pass_criterion: "coverage percentage >= $thresholds.test_coverage_minimum"

# In project constraints:
tools:
  test_runner:
    command: "python -m pytest"
    args: "imp_claude/tests/ --ignore=imp_claude/tests/e2e -q"
thresholds:
  test_coverage_minimum: 0.70
```

**Resolution algorithm**:
1. For each `$ref` in the check's `command`, `criterion`, or `pass_criterion` fields
2. Walk the constraints dict by dotted path
3. If found: substitute the resolved value
4. If not found: add to `unresolved[]`, check Outcome becomes SKIP

### 5.2 Checklist Composition

A resolved checklist is built by layering:

1. **Edge defaults** — from `edge_params/<edge>.yml`
2. **$variable resolution** — from `project_constraints.yml`
3. **Feature overrides** — from the feature vector's `threshold_overrides` field
4. **Feature additions** — from the feature vector's `additional_checks` field

**Most-restrictive rule**: `required: true` at any layer stays `true`. A feature override cannot make a required check optional.

### 5.3 Pass Criterion Interpretation (F_D)

Deterministic checks execute a shell command and interpret the result:

| Criterion Pattern | Interpretation |
|-------------------|---------------|
| `"exit code 0"` | Return code must be 0 |
| `"coverage percentage >= N"` | Parse `TOTAL ... N%` from pytest-cov output |
| `"zero violations"` | Return code 0 (linter/formatter found nothing) |
| (default) | Return code 0 |

Implementations may add platform-specific criterion parsers. The patterns above are the minimum required set.

---

## 6. Binding Points

These are the extension points where platform-specific implementations plug in. Each binding point has a contract (what it receives, what it must return) but no prescribed implementation.

### 6.1 F_D Binding (Deterministic Execution)

**Input**: `ResolvedCheck` + working directory + timeout
**Output**: `CheckResult` with `exit_code`, `stdout`, `stderr`
**Contract**: Execute `check.command` as a subprocess, capture all output, apply `check.pass_criterion` to determine Outcome.

Platform variation: subprocess invocation, shell selection, sandboxing.

### 6.2 F_P Binding (LLM Evaluation)

**Input**: `ResolvedCheck` + asset content + context
**Output**: `CheckResult` with `outcome` and `message`
**Contract**: Build a prompt from `check.criterion` + asset + context, invoke an LLM, parse structured response into Outcome.

Platform variation: Claude CLI, Gemini SDK, Bedrock API, OpenAI SDK.

### 6.3 F_H Binding (Human Evaluation)

**Input**: `ResolvedCheck` + asset content + context
**Output**: `CheckResult` with `outcome` and `message`
**Contract**: Present the candidate and criterion to a human, collect approval/rejection/refinement.

Platform variation: interactive CLI, web UI, Slack integration, email queue.

### 6.4 Event Store Binding

**Input**: Event data (type, project, feature, edge, delta, payload)
**Output**: Persisted event
**Contract**: Append a single event atomically to the event log. Must be durable across process crashes.

Platform variation: local JSONL file, Firestore, DynamoDB, Pub/Sub.

### 6.5 Workspace Discovery Binding

**Input**: Current working directory
**Output**: `EngineConfig` (workspace path, constraints, edge params, profiles, graph topology)
**Contract**: Locate the workspace root, load all configuration files, validate structure.

Platform variation: `.ai-workspace/` directory structure, cloud storage, git-based discovery.

---

## 7. Multi-Tenant Contract

### 7.1 Directory Structure

```
ai_sdlc_method/
├── specification/           # Methodology spec (WHAT the SDLC model is)
├── genesis_core/
│   └── specification/       # Engine spec (WHAT the shared engine does)  ← THIS DOCUMENT
├── imp_claude/              # Claude Code: design/ + code/ + tests/
├── imp_gemini/              # Gemini: design/ + code/ + tests/
├── imp_codex/               # Codex: design/ + code/ + tests/
└── imp_bedrock/             # Bedrock: design/ + code/ + tests/
```

### 7.2 Isolation Rules

1. **Spec is shared, code is tenanted.** `specification/` and `genesis_core/specification/` are read by all implementations. Code lives exclusively in `imp_<name>/`.
2. **No cross-tenant imports.** `imp_claude/` must never import from `imp_gemini/` or vice versa. If two implementations need the same code, the shared semantics belong in `genesis_core/specification/` as a contract, and each implementation satisfies it independently.
3. **No code in genesis_core/.** This directory contains only specification documents. Python packages, CLI tools, and shared libraries are implementation concerns — each tenant builds its own.
4. **Config schemas are shared, config files are tenanted.** `genesis_core/specification/` defines the YAML schemas for edge params, profiles, and graph topology. Each `imp_<name>/` ships its own config files conforming to those schemas.

### 7.3 Design Traceability

Each implementation's design documents (`imp_<name>/design/`) should trace back to this specification:

```
genesis_core/specification/GENESIS_ENGINE_SPEC.md §2  →  imp_claude/design/adrs/ADR-019.md
genesis_core/specification/GENESIS_ENGINE_SPEC.md §4  →  imp_gemini/design/adrs/ADR-GG-005.md
genesis_core/specification/GENESIS_ENGINE_SPEC.md §6  →  imp_bedrock/design/adrs/ADR-AB-003.md
```

---

## 8. Requirements Traceability

This specification derives from and covers the following implementation requirements:

| Requirement | Section | Coverage |
|-------------|---------|----------|
| REQ-ITER-001 | §2.1 | iterate() signature and contract |
| REQ-ITER-002 | §1.6, §2.2 | Delta computation and convergence |
| REQ-ITER-003 | §1.2, §1.3 | Functor encoding and functional units |
| REQ-EVAL-001 | §1.2, §6.1–6.3 | Three evaluator types and bindings |
| REQ-EVAL-002 | §5.2 | Per-edge evaluator composition |
| REQ-EVAL-003 | §6.3 | Human accountability (F_H decide) |
| REQ-CTX-001 | §5.1 | $variable resolution |
| REQ-CTX-002 | §5.2 | Checklist composition layers |
| REQ-FEAT-001 | §1.8 | Feature vector data model |
| REQ-FEAT-003 | §3.3, §1.7 | Spawn detection and SpawnRequest |
| REQ-FEAT-004 | §3.1 | Fold-back at orchestrator level |
| REQ-SUPV-001 | §4 | Event emission contract |
| REQ-SUPV-002 | §4.5 | Event sourcing and integrity |
| REQ-SUPV-003 | §4.3, §4.4 | Failure observability and reliability hierarchy |

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **Asset** | A typed artifact produced by the methodology (code, spec, tests, etc.) |
| **Edge** | An admissible transition between asset types in the graph |
| **Delta (δ)** | Count of failing required checks — the distance from convergence |
| **Convergence** | δ = 0 for all required checks on an edge |
| **Binding point** | A platform-specific extension where implementations plug in |
| **Projection** | A valid subset of the full graph that preserves all four invariants |
| **Profile** | A named projection (standard, poc, spike, hotfix, minimal, full) |
| **Spawn** | Creating a child feature vector when the parent is stuck |
| **Fold-back** | Merging a child vector's results back into the parent |
| **Escalation (η)** | Natural transformation from one functor category to a higher one |
| **Tenant** | A platform-specific implementation (`imp_<name>/`) |

---

## 10. Structural Constraints

These are invariants that all implementations must preserve. They are not design choices — a tenant that violates them is non-conformant.

### 10.1 Iterate Is Pure Evaluation

`iterate()` evaluates and emits. It does NOT construct candidates, detect spawn conditions, route to next edges, or update feature vector state. Lifecycle decisions belong to the orchestrator.

| Responsibility | Owner | Rationale |
|---------------|-------|-----------|
| Evaluate asset | **Evaluator** (iterate) | Stateless, deterministic given inputs |
| Emit event | **Evaluator** (iterate) | Level 4, guaranteed by execution |
| Construct next candidate | **Orchestrator** (or LLM) | Requires context, creativity, judgment |
| Detect spawn | **Orchestrator** | Requires event history (spans iterations) |
| Route to next edge | **Orchestrator** | Requires profile and trajectory state |
| Update feature vector | **Orchestrator** | Derived view, not evaluator concern |

**Why**: Cross-validation (§6, Engine Spec) requires an independent evaluator. If iterate() also constructs, its evaluation is correlated with its construction — not orthogonal. The engine's delta is meaningful only if the engine didn't build the thing it's evaluating.

### 10.2 Event-Sourced State

All engine state is derived from an append-only event log. Feature vector files, status views, Gantt charts, and task lists are projections — derived views that can be regenerated from the log at any time.

```
Source of Truth              Derived Views (projections)
─────────────────            ──────────────────────────
events/events.jsonl    ───►  STATUS.md
  (append-only)        ───►  features/active/*.yml
                       ───►  ACTIVE_TASKS.md
                       ───►  Gantt charts, telemetry
```

**Append-only contract**: Events are immutable once written. The engine NEVER modifies, deletes, or reorders existing events.

**Projection contract**: Projections are ephemeral. They may be regenerated, cached, stale, or missing — the system still functions because the log is the source of truth.

**Why**: Multi-agent safety (append-only writes don't conflict), full audit trail (every iteration recorded), recoverability (regenerate any view from the log).

### 10.3 Binding Points Are Contracts, Not Abstractions

The 5 binding points (§6) are input/output contracts. There are no shared base classes, interfaces, plugin registries, or runtime libraries between tenants. Each tenant reads the contract and builds its own implementation independently.

```
genesis_core/specification/   → Read by all tenants (documents only)
imp_claude/code/              → Claude's implementation (imports nothing from genesis_core)
imp_gemini/code/              → Gemini's implementation (imports nothing from genesis_core)
```

**No code in genesis_core/**: This directory contains only specification documents. No Python packages, no shared libraries, no config files.

**Why**: True multi-tenant isolation (no cross-tenant imports), language-agnostic (each tenant uses its own language), independent evolution (tenants can be updated without affecting others).

**Cross-tenant validation**: To verify contract conformance without sharing code, define a set of test fixtures (edge config + asset + expected delta). Each tenant runs its engine against the same fixtures. All must produce the same delta. Disagreement indicates a contract violation.

---

*This specification is versioned independently of the Asset Graph Model. It tracks the engine contract that all implementations must satisfy. Changes to this document require corresponding updates to all active tenant designs.*
