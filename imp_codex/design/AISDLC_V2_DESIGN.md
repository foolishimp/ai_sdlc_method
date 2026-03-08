# AI SDLC — Codex Runtime Implementation Design (v2.2)

**Version**: 2.2.0
**Date**: 2026-03-09
**Derived From**: [FEATURE_VECTORS.md](../../specification/features/FEATURE_VECTORS.md) (v1.9.0)
**Model**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.8.0)
**Platform**: Codex (tool-calling coding agent runtime)

---

## Design Intent

This document is the |design⟩ asset for the AI SDLC tooling implementation on Codex. It covers all 17 feature vectors currently defined in FEATURE_VECTORS.md, including the ADR-scoped `CONSENSUS` and named-composition extensions.

**Key shift from v1.x**: The v1.x design had 7 stage-specific agents (one per pipeline stage). The current model has **one operation** (`iterate`) parameterised per graph edge. The design must reflect this: a universal engine with edge-specific parameterisation, not stage-specific agents.

**What carries forward from v1.x**:
- Codex runtime as target platform (ADR-CG-001)
- Plugin delivery mechanism
- Workspace file structure (adapted)
- Slash commands (adapted)
- Markdown-first approach

**What changes**:
- 7 stage agents → 1 iterate engine with edge parameterisations
- Linear pipeline → graph with admissible transitions
- Stage-specific skills → evaluator + constructor composition per edge
- Fixed topology → configurable graph in Context[]

**What the current design adds** (from spec v2.8.0 and current ADR-S series):
- Three-layer conceptual model: Engine / Graph Package / Project Binding
- Constraint dimension taxonomy at the design edge
- Event sourcing as the formal execution model
- Methodology self-observation via TELEM signals
- Two-command UX layer: Start (routing) + Status (observability)

**Document governance**:
- Accepted ADRs are authoritative for decisions in their scope.
- This top-level design is the integration layer showing how those ADR decisions compose.
- If this document conflicts with an accepted ADR, the ADR wins and this document must be reconciled.

---

## 1. Architecture Overview

### 1.1 The Three Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer)                              │
│                   /gen-* commands                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      COMMAND LAYER                                   │
│  Slash commands that invoke the engine for specific operations       │
│  /gen-iterate  /gen-status  /gen-checkpoint  ...          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ENGINE LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Asset Graph Engine                            │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │   │
│  │  │ Graph    │  │  iterate()   │  │ Evaluator Framework   │  │   │
│  │  │ Registry │  │  (universal) │  │ {Human,Agent,Tests}   │  │   │
│  │  └──────────┘  └──────────────┘  └───────────────────────┘  │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────────┐ │   │
│  │  │ Context Manager  │  │ Feature Vector Tracker           │ │   │
│  │  │ (constraint      │  │ (REQ keys, trajectories,        │ │   │
│  │  │  surface)        │  │  dependencies)                  │ │   │
│  │  └──────────────────┘  └──────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Edge Parameterisations                       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │   │
│  │  │ req→design │ │ design→    │ │ code↔tests │ │ run→     │ │   │
│  │  │ (Human+    │ │ code       │ │ (TDD       │ │ telemetry│ │   │
│  │  │  Agent)    │ │ (Agent+    │ │  co-evol)  │ │ (Det.    │ │   │
│  │  │            │ │  Tests)    │ │            │ │  Tests)  │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKSPACE LAYER                                 │
│  .ai-workspace/                                                      │
│  ├── graph/           Asset graph state (assets, transitions)        │
│  ├── context/         Context[] store (ADRs, models, policy)         │
│  ├── features/        Feature vector tracking (REQ keys)             │
│  ├── tasks/           Task management (active, completed)            │
│  └── snapshots/       Session recovery (immutable checkpoints)       │
│                                                                      │
│  .codex/                                                             │
│  ├── commands/        Command specs                                  │
│  └── settings.json    Runtime configuration                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principle: Universal Engine, Parameterised Edges

The v1.x design had separate agents for each stage. The current design has:

- **One iterate() implementation** — a Codex orchestration routine that takes (asset, context, evaluators) and produces the next candidate
- **Edge parameterisation configs** — YAML files that define: which evaluators, which constructors, what convergence criteria
- **The graph topology** — a YAML config defining asset types and admissible transitions

The agent IS the iterate() function. It reads the edge parameterisation to know what role to adopt, what evaluators to run, what convergence looks like. Different edges produce different behaviour from the same agent.

### 1.3 Conceptual Model: Three Instantiation Layers (Spec §2.8)

The spec defines three conceptual layers. Here is how they map to the Codex implementation:

```
Spec Layer                    Implementation
──────────                    ──────────────
Layer 1: ENGINE (universal)   Plugin root:
  4 primitives                  agents/gen-iterate.md     (the ONE agent)
  iterate() + evaluator types   config/evaluator_defaults.yml (evaluator taxonomy)
  event sourcing                commands/*.md                 (workflow operations)
                                config/feature_vector_template.yml

Layer 2: GRAPH PACKAGE          Plugin config:
  (domain-specific)             config/graph_topology.yml    (asset types + transitions)
  topology + edge configs       config/edge_params/*.yml     (14 edge parameterisations)
  constraint dimensions         config/graph_topology.yml    (constraint_dimensions section)
  projection profiles           config/profiles/*.yml        (6 named profiles)

Layer 3: PROJECT BINDING        Workspace:
  (instance-specific)           .ai-workspace/context/project_constraints.yml
  project constraints           .ai-workspace/context/adrs/
  context URIs                  .ai-workspace/context/data_models/
  threshold overrides           .ai-workspace/context/policy/
                                .ai-workspace/context/standards/
```

**Context sources** (`project_constraints.yml → context_sources[]`): URI references to external AD collections that are resolved and copied into `.ai-workspace/context/{scope}/` during `/gen-init`. Supported URI schemes: `file:///`, absolute paths, and relative paths (resolved from project root). Valid scopes: `adrs`, `data_models`, `templates`, `policy`, `standards`. Sources are copied (not symlinked) to preserve content-addressable hashing for spec reproducibility. The iterate agent discovers these files automatically — no agent changes needed, files just need to land in the context directories.

**Key design decision**: Layers 1 and 2 ship together in the plugin package. Layer 3 is scaffolded by `/gen-init` into the project workspace. This means:

- Upgrading the plugin (Layer 1 + 2) does not overwrite project bindings (Layer 3)
- Different graph packages can be created by forking the `config/` directory
- The iterate agent reads Layer 2 config at runtime, never hard-codes domain knowledge

#### 1.3.1 Graph Topology Update — Explicit Build Nodes (Spec §2.1, §6.7)

The specification promotes intermediate build nodes between Design and Code to first-class edges for parallelism and traceability:

```
Requirements → Feature Decomposition → Design → Module Decomposition → Basis Projections → Code ↔ Unit Tests
```

Implications for the plugin design:
- New asset types: `feature_decomp`, `module_decomp`, `basis_projections` with their own schemas and Markov criteria.
- New admissible transitions: `requirements→feature_decomp`, `feature_decomp→design`, `design→module_decomp`, `module_decomp→basis_projections`, `basis_projections→code`.
- Evaluators attach at each new edge, enabling explicit convergence of build architecture prior to implementation.

Current plugin configuration (v2.7.0 topology) still includes `design→code` directly for backward compatibility. This design document adopts the explicit nodes as the target model; subsequent config updates will align `graph_topology.yml`, edge parameterisations, and role authorisations to these edges.

References: ADR‑S‑006 (Feature Decomposition), ADR‑S‑007 (Module Decomposition & Basis Projections), AI_SDLC_ASSET_GRAPH_MODEL §2.1/§6.7.

### 1.4 Constraint Dimensions at the Design Edge (Spec §2.6.1)

The Requirements → Design edge is the most consequential transition. The spec defines **constraint dimensions** — categories of disambiguation that design must resolve. In the implementation:

1. **Graph topology** (`graph_topology.yml`) declares the dimension taxonomy with mandatory/advisory flags
2. **Edge config** (`requirements_design.yml`) includes checklist items that verify each mandatory dimension is resolved
3. **Project constraints** (`project_constraints.yml`) provides the concrete values for each dimension (e.g., `ecosystem.language: scala`, `ecosystem.version: "2.13"`)
4. **Iterate agent** checks that all mandatory dimensions have corresponding ADRs or design decisions

Unresolved mandatory dimensions are checklist failures — they block convergence. This directly addresses the dogfooding finding: 5/7 build bugs were in dimensions the design left implicit.

### 1.5 Event Sourcing Execution Model (Spec §7.4)

All methodology state changes are recorded as immutable events in `.ai-workspace/events/events.jsonl`. All observable state (STATUS.md, feature vectors, task lists) is a derived projection.

```
Source of Truth                    Derived Views (projections)
────────────────                   ──────────────────────────
events/events.jsonl           ──►  STATUS.md           (Gantt, telemetry, self-reflection)
  (append-only JSONL)         ──►  ACTIVE_TASKS.md     (convergence events as markdown)
                              ──►  features/active/*.yml  (latest trajectory per feature)
                              ──►  gap analysis         (findings aggregated across edges)
```

Canonical event schema is OpenLineage RunEvent (ADR-S-011): top-level `eventType` is one of `START|COMPLETE|FAIL|ABORT|OTHER`, with SDLC semantics carried in `sdlc:event_type` and related `sdlc:*` facets.

Required event taxonomy and universal causal fields follow ADR-S-012 (`instance_id`, `actor`, `causation_id`, `correlation_id`). Per ADR-S-015, edge traversal is a transaction: `START` opens, `COMPLETE` commits, `FAIL/ABORT` closes without commit.

Note: legacy v1 records with root `event_type` remain valid historical records and MUST NOT be rewritten. Consumers detect schema by key presence (`eventType` vs `event_type`) during migration.

All methodology commands emit events. The event log is the sole integration contract between the methodology and any external observer (e.g., genesis-monitor).

Operational command events remain part of the Codex-local compatibility surface: `project_initialized`, `spawn_created`, `spawn_folded_back`, `checkpoint_created`, `review_completed`, `gaps_validated`, and `release_created`.

This is an engine-level primitive (Layer 1) — it applies regardless of graph package.

#### 1.5.1 Runtime Robustness for Probabilistic Processing (Spec §14, REQ‑ROBUST‑001/002/003/007/008)

The engine enforces runtime robustness around probabilistic processing (F_P):
- Isolation: each F_P invocation executes in an isolated boundary so callers can terminate it cleanly on timeout/error without cascading stalls.
- Supervisor pattern: enforce wall‑clock timeouts, detect stalls (no observable progress), retry on transient failures (bounded), and return structured error on persistent failure.
- Failure event emission: guarantee emission of structured failure events (classification: timeout/error/stall, duration, retry count, edge, feature) to `events.jsonl`.
- Crash/session gap recovery: on startup, scan for `START` runs without terminal `COMPLETE|FAIL|ABORT` by `runId`; compare current hashes to `sdlc:inputManifest` and emit `gap_detected` for uncommitted writes (ADR-S-015).

These behaviours integrate with the IntentEngine pipeline (observer → evaluator → typed_output). Failure observability is a prerequisite for homeostasis: unobserved failure yields a zero delta. See ADR‑CG‑009 and ADR‑S‑008 (Sensory‑Triage‑Intent) for the triage path.

### 1.6 Methodology Self-Observation (Spec §7.5)

The methodology observes itself through the same evaluator pattern it uses for artifacts:

```
Level 1 (product):     |running_system⟩ → |telemetry⟩ → |observer⟩ → |new_intent⟩
Level 2 (methodology): |methodology_run⟩ → |TELEM_signals⟩ → |observer⟩ → |graph_package_update⟩
```

TELEM signals are emitted by the iterate agent as `process_gaps` in each event. The `/gen-status` command aggregates these into the Self-Reflection section of STATUS.md. Over time, persistent process gaps become candidates for graph package updates (new evaluator checks, refined constraint dimensions, additional context guidance).

### 1.7 Gradient at Spec Scale (Spec §7.1, §7.3, ADR-011)

**Implements**: REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008, REQ-LIFE-009

The gradient — `delta(state, constraints) → work` — operates at every scale (Spec §7.1). At the spec scale, this becomes: `delta(workspace_state, spec) → intents`. Every evaluator running at every edge is an observer. When an observer detects a delta that cannot be resolved within the current iteration scope, that delta becomes a formal `intent_raised` event.

The gradient at spec scale spans all three processing phases (Spec §4.3). The **reflex phase** produces the sensory substrate: event emission, feature vector updates, and STATUS regeneration fire unconditionally at every iteration boundary. The **affect phase** triages those signals: classifying deltas by source (gap, discovery, ecosystem, optimisation, user, TELEM), assessing severity, and deciding which signals warrant escalation. The **conscious phase** performs deliberative review on escalated signals: interpreting deltas, generating intents, modifying the spec, spawning vectors. Protocol enforcement hooks (§1.7.4) are the mechanism that guarantees the reflex substrate operates — they are the methodology's autonomic nervous system.

#### 1.7.1 Signal Flow

```
Any edge, any iteration
        │
        ▼
┌─────────────────────────┐
│  Three-Direction Gaps   │
│  ┌───────────────────┐  │
│  │ Backward (source)  │──┼──► source_finding signal
│  │ Forward (output)   │──┼──► test_failure signal
│  │ Inward (process)   │──┼──► process_gap signal
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ Refactor phase     │──┼──► refactoring signal
│  └───────────────────┘  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│  Delta threshold met?   │  (e.g., >3 iterations stuck,
│  Scope exceeded?        │   cross-cutting debt,
│  Escalation needed?     │   upstream deficiency)
└─────────┬───────────────┘
          │ yes
          ▼
┌─────────────────────────┐
│  intent_raised event    │  signal_source classified
│  → events.jsonl         │  prior_intents chain recorded
│  → present to human     │  affected_req_keys tagged
└─────────┬───────────────┘
          │ human approves
          ▼
    New feature vector
    enters the graph
```

Plus two production-time signals:
- `/gen-gaps` → `gap` signal (traceability validation)
- telemetry→intent edge → `runtime_feedback` and `ecosystem` signals

#### 1.7.2 Seven Signal Sources

| Signal Source | Development/Production | Observer | Trigger |
|---|---|---|---|
| `gap` | Development | `/gen-gaps` | REQ keys without test/telemetry coverage |
| `test_failure` | Development | Forward evaluation | Same check fails > 3 iterations |
| `refactoring` | Development | TDD refactor phase | Structural debt exceeds current scope |
| `source_finding` | Development | Backward evaluation | Upstream asset deficient, escalate_upstream |
| `process_gap` | Development | Inward evaluation | Evaluator missing/vague, context missing |
| `runtime_feedback` | Production | Telemetry | SLA violation, error rate spike |
| `ecosystem` | Production | External monitoring | Dependency deprecated, API changed |

Each source has an intent template in `feedback_loop.yml` and is recorded in the `signal_source` field of the `intent_raised` event.

#### 1.7.3 Event Flow: intent_raised → spec_modified

```
intent_raised event
    │
    ├── Human reviews: create vector? acknowledge? dismiss?
    │
    ├── If create vector:
    │   ├── New feature vector spawned (or existing one re-opened)
    │   ├── Spec updated (REQ keys added/modified/deprecated)
    │   └── spec_modified event emitted
    │
    └── If acknowledge:
        └── Logged as TELEM signal for telemetry analysis
```

The `prior_intents` field on both events enables reflexive loop detection:
- If intent A → spec change → new delta → intent B, and B traces back to A, the system detects its own modification caused a new deviation
- This distinguishes spec review from a simple feedback loop: awareness of the consequences of one's own constraint surface changes

#### 1.7.4 Protocol Enforcement

After every `iterate()` invocation, five mandatory side effects must occur:

1. Event emitted to `events.jsonl`
2. Feature vector state updated
3. STATUS.md regenerated (or marked stale)
4. `source_findings` array present in the event (may be empty)
5. `process_gaps` array present in the event (may be empty)

The iterate agent instructions mandate these. Protocol violations are logged as `process_gap` with type `PROTOCOL_VIOLATION`. A circuit breaker prevents infinite regression: if enforcement itself fails, it logs a TELEM signal rather than blocking iteration.

#### 1.7.5 Implementation in Plugin

| File | What was added |
|---|---|
| `agents/gen-iterate.md` | Event Type Reference (command, coordination, operational, and sensory types including `checkpoint_created`), gradient observer table, `intent_raised` emission from backward/inward gap detection |
| `commands/gen-iterate.md` | Stuck delta detection (>3 iterations), refactoring signal, source escalation → `intent_raised` |
| `commands/gen-gaps.md` | Gap cluster → `intent_raised` per domain group |
| `config/edge_params/feedback_loop.yml` | 7 signal sources with intent templates and `intent_raised` schema |
| `config/edge_params/tdd.yml` | Intent generation from stuck failures and refactoring needs |
| All 13 commands | OpenLineage envelope (`eventType`) + `sdlc:event_type` facet standardised; event emission mandatory |

### 1.8 Sensory Service (Spec §4.5.4)

**Implements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005

The sensory systems run as a **long-running service** that operates independently of the interactive Claude session and iterate() invocations. Sensing is part of Genesis itself — not a separate bolt-on. The service watches the workspace, runs monitors, performs affect triage, and produces draft proposals via Claude headless. It exposes MCP tools that the interactive session uses at the review boundary.

#### 1.8.1 Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SENSORY SERVICE (MCP Server)                          │
│                                                                           │
│  ┌────────────────────┐                                                  │
│  │ Workspace Watcher   │  inotify / polling on:                          │
│  │                     │    .ai-workspace/events/events.jsonl            │
│  │                     │    .ai-workspace/features/active/*.yml          │
│  │                     │    .ai-workspace/STATUS.md                      │
│  │                     │    src/**  tests/**  (configurable globs)       │
│  └─────────┬───────────┘                                                 │
│            │ file change events                                           │
│            ▼                                                              │
│  ┌────────────────────┐                                                  │
│  │ Monitor Scheduler   │  cron-style intervals per monitor               │
│  │                     │  + on-workspace-open trigger                    │
│  │                     │  + on-file-change reactive trigger              │
│  └─────────┬───────────┘                                                 │
│            │ scheduled / triggered                                        │
│            ▼                                                              │
│  ┌────────────────────┐  ┌────────────────────┐                          │
│  │ Interoceptive      │  │ Exteroceptive      │                          │
│  │ Monitors           │  │ Monitors           │                          │
│  │ (INTRO-001..007)   │  │ (EXTRO-001..004)   │                          │
│  └─────────┬───────────┘  └─────────┬──────────┘                         │
│            └─────────┬──────────────┘                                     │
│                      │ typed signals                                      │
│                      ▼                                                    │
│  ┌──────────────────────────────────────────┐                            │
│  │ Affect Triage Pipeline                     │                           │
│  │ 1. Rule-based classification (fast)        │                           │
│  │ 2. Agent-classified for ambiguous (slow)   │                           │
│  │ 3. Severity + escalation decision          │                           │
│  └─────────┬────────────────────────┬─────────┘                          │
│            │ [below threshold]      │ [above threshold]                   │
│            ▼                        ▼                                     │
│      log + defer           ┌──────────────────┐                          │
│                            │ Claude Headless   │                          │
│                            │ (draft proposals) │                          │
│                            └────────┬──────────┘                         │
│                                     │                                     │
│  ═══════════════════ REVIEW BOUNDARY ═══════════════════════════════════  │
│                                     │                                     │
│                          MCP Tools exposed:                               │
│                          • /sensory-status                                │
│                          • /sensory-proposals                             │
│                          • /sensory-approve                               │
│                          • /sensory-dismiss                               │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │
                                      ▼
                        Interactive Claude Session
                        (human reviews, approves/dismisses)
```

**Process lifecycle:**
- Starts on workspace open (or on-demand via MCP tool)
- Runs continuously in the background
- Produces no file modifications — only observes and drafts
- Stops on workspace close or explicit shutdown

**Configuration:** The service reads its configuration from:
- `sensory_monitors.yml` — monitor registry (which monitors, schedules, thresholds)
- `affect_triage.yml` — triage rules (classification patterns, severity mapping, escalation thresholds)
- Profile-level overrides from the active projection profile

#### 1.8.2 Interoceptive Monitors

Concrete monitors that observe the system's own health state:

| Monitor ID | What it reads | Signal on | Default schedule |
|------------|--------------|-----------|-----------------|
| **INTRO-001** Event freshness | `events.jsonl` last timestamp | > 7 days since last event | daily |
| **INTRO-002** Feature vector stall | `features/active/*.yml` iteration timestamps | Any vector with no iteration > 14 days | daily |
| **INTRO-003** Test health | Test runner output (pytest, jest, etc.) | Coverage < threshold OR flaky rate > 5% | on-change (test files) |
| **INTRO-004** STATUS freshness | `STATUS.md` mtime vs `events.jsonl` last timestamp | STATUS older than last event by > 1 day | daily |
| **INTRO-005** Build health | CI/CD pass rate from build logs or API | Failure rate > 20% over last 10 builds | daily |
| **INTRO-006** Spec/code drift | REQ tags in code vs REQ keys in spec | Any untagged code in traced modules | on-change (source files) |
| **INTRO-007** Event log integrity | `events.jsonl` structure | Malformed JSON lines, missing required fields | on-change (events.jsonl) |

Each monitor produces a typed signal:
```yaml
# interoceptive_signal schema (OpenLineage semantic facet payload)
eventType: OTHER
'sdlc:event_type': interoceptive_signal
timestamp: ISO-8601
monitor_id: "INTRO-001"
observation: "Last event 12 days ago"
metric_value: 12
threshold: 7
unit: days
severity: warning  # info | warning | critical
affected_req_keys: []  # if applicable
```

#### 1.8.3 Exteroceptive Monitors

Concrete monitors that observe the external environment:

| Monitor ID | What it runs | Signal on | Default schedule |
|------------|-------------|-----------|-----------------|
| **EXTRO-001** Dependency freshness | `pip list --outdated` / `npm outdated` / lockfile analysis | Major version update available | weekly |
| **EXTRO-002** CVE scanning | `pip-audit` / `npm audit` / GHSA API | Any CVE severity >= medium | daily |
| **EXTRO-003** Runtime telemetry | Telemetry endpoint query (if configured) | Error rate > baseline + 2σ, latency p99 > SLA | hourly (when configured) |
| **EXTRO-004** API contract changes | Upstream API schema diff (OpenAPI, GraphQL introspection) | Breaking change detected | daily (when configured) |

Each monitor produces a typed signal:
```yaml
# exteroceptive_signal schema (OpenLineage semantic facet payload)
eventType: OTHER
'sdlc:event_type': exteroceptive_signal
timestamp: ISO-8601
monitor_id: "EXTRO-002"
external_source: "pip-audit"
finding: "CVE-2026-1234 in requests==2.31.0 (severity: high)"
severity: critical
affected_packages: ["requests"]
affected_req_keys: ["REQ-F-AUTH-001"]  # if traceable
```

#### 1.8.4 Affect Triage Pipeline

Classification rules, severity levels, and escalation thresholds:

**Classification (rule-based, fast):**

| Signal pattern | Classification | Default severity |
|---------------|---------------|-----------------|
| CVE severity >= high | `vulnerability` | critical |
| CVE severity == medium | `vulnerability` | warning |
| Test coverage drop > 5% | `degradation` | warning |
| Feature vector stall > 14 days | `staleness` | warning |
| Event freshness > 7 days | `staleness` | info |
| Major dependency update | `ecosystem_change` | info |
| Breaking API change | `contract_break` | critical |
| Runtime error rate spike | `runtime_deviation` | critical |

**Agent-classified (slow, for ambiguous signals):**
When rule-based classification is insufficient (signal doesn't match any pattern, or multiple patterns conflict), the triage pipeline invokes Claude headless for classification. This is the "tiered" approach: rules handle the common cases cheaply; the agent handles edge cases that require judgment.

**Escalation thresholds (profile-tunable):**

| Profile | Escalation threshold | Effect |
|---------|---------------------|--------|
| full | Low — escalate warning and above | Maximum sensitivity |
| standard | Medium — escalate warning and above | Balanced |
| hotfix | Very low — escalate everything | Emergency mode |
| spike | High — escalate only critical | Suppress noise during exploration |
| poc | High — escalate only critical | Focus on construction |
| minimal | Medium — escalate warning and above | Sensible defaults |

**Triage output:**
```yaml
# affect_triage schema (OpenLineage semantic facet payload)
eventType: OTHER
'sdlc:event_type': affect_triage
timestamp: ISO-8601
signal_id: "ref to interoceptive_signal or exteroceptive_signal"
source_monitor: "INTRO-003"
classification: degradation
severity: warning
escalation_decision: escalate  # escalate | defer | log_only
recommended_action: "Review test coverage drop — 3 modules below 80%"
affected_req_keys: ["REQ-F-AUTH-001", "REQ-F-PERF-001"]
profile_threshold: "warning"  # the active threshold that caused escalation
```

#### 1.8.5 Homeostatic Responses

For signals that escalate past triage, the sensory service invokes **Claude headless** to generate mechanical draft proposals:

**What Claude headless produces (draft only):**
- Proposed `intent_raised` event (with suggested signal_source, affected_req_keys, vector_type)
- Proposed diff (for mechanical fixes — e.g., dependency version bump)
- Proposed spec modification (for spec-level changes — e.g., new requirement for CVE remediation)

**What Claude headless does NOT do:**
- Modify any file in the workspace
- Emit events to `events.jsonl`
- Update feature vectors
- Change STATUS.md

All proposals are stored in the service's internal state and surfaced via MCP tools. The human reviews through the interactive session.

**Draft proposal schema:**
```yaml
# draft_proposal schema (OpenLineage semantic facet payload)
eventType: OTHER
'sdlc:event_type': draft_proposal
timestamp: ISO-8601
trigger_signal: "ref to affect_triage event"
proposal_type: intent | diff | spec_modification
summary: "Bump requests to 2.32.0 to address CVE-2026-1234"
proposed_intent:  # if proposal_type == intent
  signal_source: vulnerability
  affected_req_keys: ["REQ-F-AUTH-001"]
  vector_type: hotfix
  description: "Remediate CVE-2026-1234 in requests dependency"
proposed_diff:  # if proposal_type == diff
  file: "requirements.txt"
  change: "requests==2.31.0 → requests==2.32.0"
status: pending  # pending | approved | dismissed
```

#### 1.8.6 Review Boundary

The review boundary is the MCP tool interface that separates autonomous sensing from human-approved changes:

**MCP tools exposed by the sensory service:**

| Tool | Purpose | Returns |
|------|---------|---------|
| `/sensory-status` | Current state of all monitors, last run times, signal counts | Monitor health dashboard |
| `/sensory-proposals` | List pending draft proposals with full context | Proposal list with trigger chains |
| `/sensory-approve --id <proposal_id>` | Approve a proposal — the interactive session applies the change | Confirmation + events emitted |
| `/sensory-dismiss --id <proposal_id> --reason <reason>` | Dismiss a proposal with reason (logged for learning) | Dismissal logged |
| `/sensory-config` | View/modify monitor configuration, thresholds | Current config |

**Approval flow:**
1. Human invokes `/sensory-proposals` in interactive session
2. Reviews each pending proposal (sees trigger signal → triage → draft)
3. Approves: interactive session applies the change (file modification, event emission, feature vector update)
4. Dismisses: reason logged as `affect_triage` event with `escalation_decision: dismissed`

The review boundary ensures that **all file modifications go through the interactive session with human oversight**, preserving REQ-EVAL-003 (Human Accountability).

#### 1.8.7 Event Contracts

Four new event types added to the event sourcing model (§1.5):

| Event type | When emitted | Emitter | Example |
|-----------|-------------|---------|---------|
| `interoceptive_signal` | Monitor detects internal deviation | Sensory service | Test coverage dropped below 80% |
| `exteroceptive_signal` | Monitor detects external change | Sensory service | CVE-2026-1234 found in dependency |
| `affect_triage` | Signal classified and escalation decided | Sensory service | Signal escalated as "vulnerability/critical" |
| `draft_proposal` | Homeostatic response drafted | Sensory service (Claude headless) | Proposed hotfix vector for CVE remediation |

These events are logged to `events.jsonl` by the sensory service. They are **observation events** — they record what was sensed and how it was classified. They do NOT record changes to the workspace (that remains the domain of `intent_raised`, `spec_modified`, `iteration_completed`, etc., which are emitted by the interactive session after human approval).

**Total event types**: 12 (existing) + 4 (sensory) = 16.

#### 1.8.8 Monitor ↔ Telemetry Separation

A critical architectural distinction:

| | Genesis (the methodology) | genesis_monitor (the observer) |
|---|---|---|
| **Role** | Produces events as it operates (iterate, converge, emit) | Consumes the event stream that Genesis produces |
| **Is the sensor?** | Yes — the sensory service (§1.8.1) IS part of Genesis | No — it reads telemetry, it doesn't sense |
| **Produces** | events.jsonl entries, feature vectors, STATUS.md, sensory signals | Dashboards, alerts, reports, trend analysis |
| **Modifies workspace?** | Yes (through interactive session with human approval) | No — read-only observer |

The sensory service is **part of Genesis** — it is the methodology's own nervous system. `genesis_monitor` is an **external observer** that consumes the telemetry Genesis produces (including sensory signals). The monitor rides the telemetry; it does not generate it.

**OpenLineage is canonical; OTLP is optional projection:** The event log format (`events.jsonl`) uses OpenLineage as the canonical write schema (ADR-S-011/012/015). OTLP export remains an optional downstream projection for observability platforms (Grafana, Datadog, etc.) without changing the methodology's internal contract.

**Config schema specifications (design-level, not yet executable):**

```yaml
# sensory_monitors.yml schema
version: "1.0.0"
service:
  start_on: workspace_open
  stop_on: workspace_close

monitors:
  interoceptive:
    - id: INTRO-001
      name: event_freshness
      description: "Time since last event in events.jsonl"
      schedule: daily
      threshold:
        metric: days_since_last_event
        warning: 7
        critical: 14
      enabled: true

    - id: INTRO-002
      name: feature_vector_stall
      description: "In-progress vectors with no iteration for > N days"
      schedule: daily
      threshold:
        metric: days_since_last_iteration
        warning: 14
        critical: 30
      enabled: true

    # ... INTRO-003 through INTRO-007

  exteroceptive:
    - id: EXTRO-001
      name: dependency_freshness
      description: "Check for major version updates in dependencies"
      schedule: weekly
      command: "pip list --outdated --format=json"
      enabled: true

    # ... EXTRO-002 through EXTRO-004

# Profile-level overrides
profile_overrides:
  hotfix:
    disable: [EXTRO-001, EXTRO-004]  # disable non-critical exteroception
    threshold_overrides:
      INTRO-001: { warning: 1, critical: 3 }  # tighter freshness in hotfix
  spike:
    disable: [EXTRO-001, EXTRO-002, EXTRO-003, EXTRO-004]  # all exteroception off
    threshold_overrides:
      INTRO-002: { warning: 30, critical: 60 }  # relax stall detection
```

```yaml
# affect_triage.yml schema
version: "1.0.0"

classification_rules:
  - pattern: { severity: "critical", monitor_type: "exteroceptive" }
    classification: vulnerability
    default_severity: critical
    escalation: always

  - pattern: { monitor_id: "INTRO-003", metric_delta: "> 5%" }
    classification: degradation
    default_severity: warning
    escalation: threshold

  - pattern: { monitor_id: "INTRO-001", metric_value: "> threshold" }
    classification: staleness
    default_severity: info
    escalation: threshold

  # Fallback: unclassified signals go to agent classification
  - pattern: { unmatched: true }
    classification: agent_classify
    escalation: agent_decides

escalation_thresholds:
  full: info        # escalate everything info and above
  standard: warning
  hotfix: info
  spike: critical
  poc: critical
  minimal: warning

agent_classification:
  model: claude-sonnet  # cheaper model for triage classification
  max_tokens: 500
  prompt_template: |
    Classify this signal and recommend an action:
    Monitor: {monitor_id}
    Finding: {finding}
    Context: {affected_req_keys}
    Respond with: classification, severity, recommended_action
```

### 1.9 Two-Command UX Layer (ADR-012)

**Implements**: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005

The methodology exposes 9 commands. UX gap analysis identified this as the primary adoption barrier. Two verbs replace the 9-command learning curve: **Status** ("Where am I?") and **Start** ("Go."). The 9 commands remain as a power-user escape hatch.

#### 1.9.1 State Machine

Start detects project state from the workspace filesystem and event log (never from a stored variable — consistent with §1.5 Event Sourcing). Eight states:

| State | Detection | Action |
|-------|-----------|--------|
| `UNINITIALISED` | No `.ai-workspace/` directory | Delegate to `/gen-init` |
| `NEEDS_CONSTRAINTS` | `project_constraints.yml` has unresolved mandatory dimensions | Prompt for constraint dimensions |
| `NEEDS_INTENT` | No intent file or empty intent | Prompt for intent description |
| `NO_FEATURES` | Intent exists but no feature vectors in `features/active/` | Delegate to `/gen-spawn` |
| `IN_PROGRESS` | Active features with unconverged edges | Select feature + edge, delegate to `/gen-iterate` |
| `ALL_CONVERGED` | All active features fully converged | Delegate to `/gen-release` or suggest `/gen-gaps` |
| `ALL_BLOCKED` | All features blocked (spawn dependency, human review) | Surface blockers, suggest `/gen-review` or `/gen-spawn` |
| `STUCK` | Feature with δ unchanged for 3+ iterations | Surface stuck features, suggest spawn discovery or human review |

State transitions delegate to existing commands — Start does not duplicate their logic.

#### 1.9.2 Progressive Init

When state is `UNINITIALISED`, Start runs a 5-question progressive init:

1. **Project name** (auto-detect from directory or `package.json`/`pyproject.toml`)
2. **Project kind** (application / library / service / data-pipeline)
3. **Language** (auto-detect from existing files)
4. **Test runner** (auto-detect from config files — `pytest.ini`, `jest.config.*`, `build.sbt`)
5. **Intent description** (one sentence — what are you building?)

From these 5 inputs, Start:
- Delegates to `/gen-init` with detected values
- Infers a default profile (application → standard, library → full, data-pipeline → standard)
- Defers constraint dimensions until the `requirements→design` edge

#### 1.9.3 Deferred Constraint Prompting

At the `requirements→design` edge (and only then), Start prompts for unresolved mandatory constraint dimensions:

- **ecosystem_compatibility**: language, version, runtime, frameworks (pre-populated from init detection)
- **deployment_target**: platform, cloud provider, environment tiers
- **security_model**: authentication, authorisation, data protection
- **build_system**: tool, module structure, CI integration

Advisory dimensions are mentioned but not required. This implements REQ-UX-002 (progressive disclosure).

#### 1.9.4 Feature Selection Algorithm

When multiple features are active (state `IN_PROGRESS`), Start selects the highest-priority actionable feature:

1. **Time-boxed spawns** — urgency (approaching or expired time box)
2. **Closest-to-complete** — reduce WIP (fewest unconverged edges remaining)
3. **Feature priority** — from feature vector `priority` field
4. **Most recently touched** — from last event timestamp

User can override with `--feature "REQ-F-*"`.

#### 1.9.5 Edge Determination Algorithm

Given a selected feature, Start determines the next edge:

1. Load active profile's graph (which edges are included)
2. Walk edges in topological order
3. Skip converged edges
4. Skip edges not in the active profile
5. Return the first unconverged, non-skipped edge

For co-evolution edges (code↔unit_tests), both sides are presented as a single unit.

#### 1.9.6 Auto-Mode Loop

With `--auto` flag, Start loops: select feature → determine edge → delegate to iterate → check convergence → repeat. Loop pauses at:

- **Human gates**: edges where `human_required: true` (e.g., requirements→design)
- **Spawn decisions**: when iterate recommends spawning a sub-vector
- **Stuck detection**: when δ unchanged for 3+ iterations
- **Profile time-box expiry**: when the feature's time box expires

#### 1.9.7 Status Enhancements

Status is enhanced with:

- **Step 0: State Detection** — compute and display current project state (same algorithm as Start)
- **Project Rollup** — aggregate edge convergence counts across all features
- **"You Are Here" indicators** — compact graph path per feature: `intent ✓ → req ✓ → design ✓ → code ● → tests ● → uat ○`
- **Signals** — unactioned `intent_raised` events surfaced as pending signals
- **"What Start Would Do"** — preview of next action Start would take
- **`--health` flag** — workspace health check: event log integrity, feature vector consistency, orphaned spawns, stuck detection

#### 1.9.8 Recovery Logic

When state detection finds inconsistencies (REQ-UX-005), Start offers guided recovery:

| Issue | Detection | Recovery |
|-------|-----------|----------|
| Corrupted event log | Malformed JSON lines | Offer to truncate at last valid line |
| Missing feature vectors | Event log references features with no `.yml` | Offer to regenerate from events |
| Orphaned spawns | Child vectors with no parent reference | Offer to link or archive |
| Stuck features | δ unchanged 3+ iterations | Suggest spawn discovery or human review |
| Unresolved constraints | Mandatory dimensions empty at design edge | Prompt for values |

All recovery is non-destructive — Start never silently deletes user data.

---

### 1.10 Multi-Agent Coordination (ADR-013)

**Implements**: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005

Multiple Claude agents (or mixed Claude/Gemini/Codex agents) can work concurrently on the same project. Coordination uses no lock files, no mutexes — only the immutable event log.

#### 1.10.1 Workspace Structure (Multi-Agent)

```
.ai-workspace/
├── events/
│   ├── events.jsonl             # Shared: single-writer append-only source of truth
│   └── inbox/
│       ├── <agent_id_1>/        # Agent-private event staging
│       └── <agent_id_2>/
├── features/active/             # Shared: derived from events by serialiser
├── spec/                        # Shared: tech-agnostic (human-gated mutations)
├── agents/
│   ├── agent_roles.yml          # Role registry (project-configurable)
│   ├── <agent_id_1>/
│   │   ├── drafts/              # In-progress artifacts (private)
│   │   └── scratch/             # Transient reasoning (ephemeral)
│   └── <agent_id_2>/
│       ├── drafts/
│       └── scratch/
├── <design_name>/               # Design tenant (standards, ADRs, constraints)
└── ...
```

**Key invariant**: `events/events.jsonl` has exactly one writer. In multi-agent mode, agents emit events to their inbox and a single-writer serialiser resolves claims and appends to the shared log. In single-agent mode, the agent is the sole writer (no inbox, no serialiser). Both modes satisfy the invariant. The serialiser also updates derived views on convergence.

#### 1.10.2 Event-Sourced Claims

No lock files. Assignment is a projection of the event stream:

1. Agent emits `edge_claim` to inbox: `{agent_id, agent_role, feature, edge}`
2. Serialiser reads all inboxes in **ingestion order** (lexicographic `agent_id` order, then filesystem modification time within each inbox — no clock-skew dependency). Implementations MAY use monotonic sequence numbers on inbox entries for strict replay-stability across platforms.
3. Unclaimed → serialiser writes `edge_started` with `agent_id` to events.jsonl
4. Already claimed → serialiser writes `claim_rejected` with reason and holding agent
5. Agent reads events.jsonl (or its projection) to confirm assignment before iterating
6. On convergence → `edge_converged` → claim released
7. On abandonment → agent emits `edge_released` → claim freed

**Inbox semantics**: The inbox (`events/inbox/<agent_id>/`) is a non-authoritative write buffer. If an inbox is deleted, only unprocessed events are lost — the event log retains all truth. Inboxes are not replayed during recovery — only `events.jsonl` is.

Stale detection: no event from an active agent within configurable timeout → `claim_expired` telemetry signal emitted to events.jsonl. Stale claims are not auto-released — human decides.

#### 1.10.3 Work Isolation and Promotion

Agents iterate in `agents/<agent_id>/drafts/`. Promotion to shared state requires:

- All evaluators for the edge pass
- Human review for: spec mutations, new ADRs, edges with `human_required: true`
- Serialiser updates feature vector and derived views on `edge_converged`

Agent state is ephemeral. On crash, only emitted events persist. Drafts and scratch are disposable.

#### 1.10.4 Role-Based Authority

`agent_roles.yml` maps roles to convergence authority:

```yaml
roles:
  architect:
    converge_edges: [intent_requirements, requirements_design, design_code]
  tdd_engineer:
    converge_edges: [code_unit_tests, design_test_cases]
  full_stack:
    converge_edges: [all]  # backward-compatible single-agent default
```

Convergence outside authority → `convergence_escalated` event → held for human approval.

#### 1.10.5 Markov-Aligned Parallelism

`/gen-start` in multi-agent mode uses the inner product (§6.7 of the spec) to route agents:

- **Zero inner product** (no shared modules): freely assign to parallel agents
- **Non-zero inner product** (shared modules): warn, suggest sequential or shared-module-first ordering
- Feature priority tiers (closest-to-complete first) apply per-agent, skipping already-claimed features

#### 1.10.6 Single-Agent Backward Compatibility

In single-agent mode (the default), the agent IS the sole writer — satisfying the "exactly one writer" invariant directly:
- `agent_id` defaults to `"primary"`, `agent_role` defaults to `"full_stack"`
- No serialiser needed — agent writes events.jsonl directly (existing behaviour)
- No inbox staging, no claim protocol, no role checks
- All multi-agent event fields are optional and additive
- The event log format is identical — multi-agent mode adds fields, never changes existing ones

#### 1.10.7 Design-Level vs Agent-Level Tenancy

Two orthogonal concerns:

| Level | What varies | Shared | Mechanism |
|-------|-----------|--------|-----------|
| **Design tenancy** | Standards, ADRs, constraints, toolchain | Spec, features, events | `.ai-workspace/<design_name>/` (ADR-GG-006) |
| **Agent tenancy** | Working state, current task, role | All of above + design assets | `.ai-workspace/agents/<agent_id>/` (this section) |

A project may have one design with multiple agents, or multiple designs each with their own agents. The event log is shared across all.

---

### 1.11 Observer Agents (Spec §7.1, §7.2, §7.6)

**Implements**: REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012

Three observer agents close the right side of the abiogenesis loop: `act → emit event → observe → judge → feed back`. Each observer is a markdown agent spec — the same delivery mechanism as the iterate agent (§2.3). No new infrastructure. Claude reads the agent spec and executes it, just as it reads `gen-iterate.md` today.

Each observer is a **Markov object**: it reads its inputs (event log, build artifacts, telemetry), emits events, and has no shared mutable state. The event log IS the mailbox (actor model). Observers run in parallel — zero inner product between them because they read different signal sources and write non-conflicting event types.

#### 1.11.1 Observer Architecture

```
                          ┌──────────────────────┐
                          │     Event Log         │
                          │   events.jsonl        │
                          └───┬──────┬──────┬─────┘
                              │      │      │
                    ┌─────────┘      │      └─────────┐
                    │                │                  │
                    ▼                ▼                  ▼
          ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
          │ Dev Observer │  │ CI/CD        │  │ Ops Observer │
          │ Agent        │  │ Observer     │  │ Agent        │
          │              │  │ Agent        │  │              │
          │ Reads:       │  │ Reads:       │  │ Reads:       │
          │ • events.jsonl│  │ • build logs │  │ • telemetry  │
          │ • features/  │  │ • test results│ │ • metrics    │
          │ • STATUS.md  │  │ • coverage   │  │ • alerts     │
          │ • spec       │  │ • deploy log │  │ • SLA data   │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 │                 │                   │
                 ▼                 ▼                   ▼
          observer_signal    observer_signal     observer_signal
          → events.jsonl     → events.jsonl      → events.jsonl
                 │                 │                   │
                 └────────┬────────┘───────────────────┘
                          ▼
                  Human reviews draft intents
                  (approve → new vector / dismiss)
```

#### 1.11.2 Dev Observer Agent

**Trigger**: Hooks after `iteration_completed`, `edge_converged`, `release_created`, `gaps_validated` events.

**Inputs**: `events.jsonl`, `features/active/*.yml`, `STATUS.md`, `specification/`

**Algorithm**:
1. Read latest workspace state (feature vectors, convergence status, event log tail)
2. Read spec (requirements, feature vectors, constraint surface)
3. Compute delta: what spec asserts vs what workspace contains
4. Classify non-zero deltas by signal source (gap, discovery, ecosystem, optimisation, user, TELEM)
5. For each significant delta, generate draft `intent_raised` event
6. Present to human for approval

**Output event schema**:
```yaml
eventType: OTHER
'sdlc:event_type': observer_signal
observer_id: dev_observer
timestamp: ISO-8601
signal_source: gap | discovery | TELEM
delta_description: "3 REQ keys in spec have no test coverage"
affected_req_keys: ["REQ-LIFE-010", "REQ-LIFE-011", "REQ-LIFE-012"]
severity: high | medium | low
recommended_action: "Spawn feature vector or iterate on code↔unit_tests"
draft_intents: [{...}]  # optional — pre-formed intent_raised events
```

**Delivery**: `agents/gen-dev-observer.md` — markdown agent spec.

#### 1.11.3 CI/CD Observer Agent

**Trigger**: Hooks after CI/CD pipeline completion (post-push, post-merge).

**Inputs**: Build logs, test results, coverage reports, deployment status.

**Algorithm**:
1. Read build/test results from CI/CD output
2. Map failures to REQ keys via `Implements:` / `Validates:` tags
3. Compute delta: expected green vs actual red, coverage thresholds
4. Generate draft intents for regressions, coverage drops, deployment failures
5. Present to human for approval

**Output event schema**:
```yaml
eventType: OTHER
'sdlc:event_type': observer_signal
observer_id: cicd_observer
timestamp: ISO-8601
signal_source: test_failure | process_gap
build_status: pass | fail
failing_req_keys: ["REQ-F-AUTH-001"]
coverage_delta: -3.2  # percentage point change
severity: critical | high | medium
recommended_action: "Fix failing tests for REQ-F-AUTH-001"
draft_intents: [{...}]
```

**Delivery**: `agents/gen-cicd-observer.md` — markdown agent spec.

#### 1.11.4 Ops Observer Agent

**Trigger**: Scheduled (configurable interval) or on monitoring alert.

**Inputs**: Production telemetry — latency, error rates, resource utilisation, incident reports.

**Algorithm**:
1. Read production telemetry (metrics endpoints, log aggregation, alert API)
2. Correlate anomalies with REQ keys via `req=` structured logging tags
3. Compute delta: running system vs spec constraints (SLAs, performance envelopes)
4. Consume interoceptive signals from REQ-SENSE-001 as additional input
5. Generate draft intents for SLA breaches, performance regressions, resource trends
6. Present to human for approval

**Output event schema**:
```yaml
eventType: OTHER
'sdlc:event_type': observer_signal
observer_id: ops_observer
timestamp: ISO-8601
signal_source: runtime_feedback
metric_deltas:
  - metric: p99_latency_ms
    current: 450
    threshold: 200
    req_key: REQ-NFR-PERF-001
severity: critical | high | medium
recommended_action: "Investigate latency regression on REQ-NFR-PERF-001"
draft_intents: [{...}]
```

**Delivery**: `agents/gen-ops-observer.md` — markdown agent spec.

#### 1.11.5 Integration with Existing Systems

| Observer | Integrates with | How |
|----------|----------------|-----|
| Dev observer | §1.7 (Gradient at Spec Scale) | Operationalises spec review — same `delta(workspace, spec) → intents` |
| Dev observer | §1.5 (Event Sourcing) | Reads and writes to events.jsonl |
| CI/CD observer | §1.3 (Graph Topology) | Observes code→cicd→running_system edges |
| CI/CD observer | §1.4 (REQ Key Traceability) | Maps failures back to REQ keys |
| Ops observer | §1.8 (Sensory Service) | Consumes interoceptive/exteroceptive signals |
| Ops observer | §1.7.2 (Signal Sources) | Produces `runtime_feedback` signals |
| All observers | §1.10 (Multi-Agent) | Each observer is a Markov object with agent_id |

#### 1.11.6 ADR

**ADR-014: Observer Agents as Markdown Specs**

**Context**: The abiogenesis loop requires observers that watch events, compute deltas, and feed back intents. Options: (a) executable code (Python/TypeScript service), (b) MCP server extension, (c) markdown agent specs.

**Decision**: Markdown agent specs — same delivery as the iterate agent.

**Rationale**:
- Claude already reads markdown agent specs and executes them. No new infrastructure.
- Observers are Markov objects — stateless functions from inputs to events. They don't need persistent runtime.
- Hooks trigger the observer after relevant events. The hook invokes Claude with the observer agent spec.
- Consistent with ADR-008 (Universal Iterate Agent) — one mechanism for all agents.

**Consequences**:
- Observers are as testable as the iterate agent (spec validation + BDD scenarios)
- No additional deployment, no separate process, no MCP server for observers
- Latency: observer runs after hook fires, adds ~seconds to post-iteration processing
- Composable: new observers can be added by dropping a new markdown file into `agents/`

### 1.12 Telemetry as Functor Product (ADR-017, Spec §4.5, §7.5)

**Implements**: REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004, REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-005

#### The Paradigm

Operational telemetry and self-monitoring are constitutive properties of a product, not deferred capabilities. A product that does not monitor itself is not yet a product.

Every product (including Genesis) has:
1. **Spec** — features and operational parameters
2. **Traceability** — REQ keys threading through build artifacts
3. **Operational telemetry** — the product emits structured events as it operates
4. **Monitors** — interoceptive and exteroceptive, deployed as part of the product
5. **Feedback loop** — telemetry feeds back as new intent

Genesis is a product builder AND a product. It complies to the same paradigm it enforces on products it builds. Products built by Genesis comply to this paradigm.

#### Telemetry as Functor

The telemetry system is not a bolt-on. It is another **functor product**: a spec-level definition of what to monitor, encoded into technology-specific implementations via the same functor mechanism (ADR-017) that maps product specs to code.

```
Telemetry Spec (WHAT to monitor — tech-agnostic)
    │
    │  F_telemetry: Spec → Implementation
    │
    ├── imp_codex/  → events.jsonl + hooks + workspace_state.py + sensory_monitors.yml
    ├── imp_gemini/  → (their monitoring stack)
    └── imp_codex/   → (their monitoring stack)
```

The telemetry functor uses the same functional units as the primary product functor, rendered through the same three categories (F_D, F_P, F_H):

| Functional Unit | Telemetry Role | Claude Encoding (F_D / F_P / F_H) |
|----------------|---------------|-----------------------------------|
| **Sense** | Monitors detect signals | F_D: `workspace_state.py` pure functions, file watchers, `pip-audit` / F_P: LLM anomaly detection / F_H: human notices something |
| **Classify** | Affect triage | F_D: `affect_triage.yml` rules / F_P: LLM classifies ambiguous signals / F_H: human triages manually |
| **Evaluate** | Convergence check on telemetry | F_D: threshold comparisons / F_P: LLM coherence review / F_H: human judgment |
| **Emit** | Events to log | F_D: append to `events.jsonl` — always deterministic (category-fixed) |
| **Route** | Escalation decision | F_D: rule-based severity routing / F_P: LLM context-sensitive routing / F_H: human decides (category-fixed at review boundary) |
| **Propose** | Homeostatic response | F_D: template-driven proposals / F_P: Claude headless drafts intent/diff / F_H: human writes proposal |

#### Genesis Self-Monitoring: Claude Encoding

Genesis already has operational telemetry. The encoding maps to existing artifacts:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     TELEMETRY PRODUCT (Claude Encoding)                    │
│                                                                           │
│  SENSE (F_D)                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ workspace_state.py (23 pure functions)                            │    │
│  │  detect_stuck_features()     → INTRO-002                         │    │
│  │  detect_corrupted_events()   → INTRO-007                         │    │
│  │  detect_orphaned_spawns()    → REQ-UX-005                        │    │
│  │  detect_missing_feature_vectors() → INTRO-006                    │    │
│  │  get_unactioned_escalations() → signal tracking                  │    │
│  │  compute_aggregated_view()   → INTRO-004 (staleness)             │    │
│  ├──────────────────────────────────────────────────────────────────┤    │
│  │ hooks (reflex phase — fires unconditionally)                      │    │
│  │  on-iterate-start.sh  → protocol injection                       │    │
│  │  on-stop-check-protocol.sh → 4 mandatory side effects            │    │
│  ├──────────────────────────────────────────────────────────────────┤    │
│  │ sensory_monitors.yml (config — schedule + thresholds)             │    │
│  │  7 interoceptive monitors (INTRO-001..007)                        │    │
│  │  4 exteroceptive monitors (EXTRO-001..004)                        │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  CLASSIFY + ROUTE (F_D → η_D→P → F_P)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ affect_triage.yml (14 rules, 6 profile thresholds)                │    │
│  │  classify_tolerance_breach() in workspace_state.py                │    │
│  │  Rule-based (F_D) → Agent-classified for ambiguous (F_P)         │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  EMIT (F_D — category-fixed)                                             │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ events.jsonl — 13+ event types, append-only                       │    │
│  │  interoceptive_signal, exteroceptive_signal                       │    │
│  │  affect_triage, draft_proposal                                    │    │
│  │  telemetry_signal_emitted (TELEM-*)                               │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  EVALUATE + PROPOSE (F_P → η_P→H → F_H)                                 │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Observer agents (markdown specs — ADR-014)                        │    │
│  │  gen-dev-observer.md   → delta(workspace, spec) → intents     │    │
│  │  gen-cicd-observer.md  → delta(build, quality) → intents      │    │
│  │  gen-ops-observer.md   → delta(running, spec) → intents       │    │
│  ├──────────────────────────────────────────────────────────────────┤    │
│  │ Review boundary (F_H — category-fixed)                            │    │
│  │  MCP tools: /sensory-status, /sensory-proposals, /sensory-approve │    │
│  │  Human approves/dismisses all workspace modifications             │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  FEEDBACK (telemetry → new intent)                                       │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ intent_raised events with signal_source classification            │    │
│  │  7 signal sources → intent templates in feedback_loop.yml         │    │
│  │  prior_intents chain → reflexive loop detection                   │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Operational Status: What's Wired vs What's Not

The building blocks exist. The gap is wiring, not building.

| Component | Built | Wired | What to wire |
|-----------|:-----:|:-----:|-------------|
| Event log (13 types, 99 events) | ✓ | ✓ | Add REQ keys to TELEM signals; enforce `source_findings`/`process_gaps` in all iteration events |
| Protocol hooks (iterate-start, stop-check) | ✓ | ✓ | Already operational |
| Pure function monitors (23 in workspace_state.py) | ✓ | — | Add session-start hook that invokes monitors, emits `interoceptive_signal` events |
| Sensory monitor config (11 monitors) | ✓ | — | Build thin runner script; schedule via hooks |
| Affect triage config (14 rules) | ✓ | — | Build rule-matching pipeline that reads signals, emits `affect_triage` events |
| Observer agents (3 markdown specs) | ✓ | — | Add hook after `edge_converged` that invokes dev-observer agent |
| Review boundary (5 MCP tools) | ✓ | — | Build MCP server exposing sensory tools |
| Feedback loop (7 signal sources) | ✓ | partial | `gap` source operational; wire remaining 6 sources |

#### Wiring Priority (Phase 1a telemetry)

Zero new code — connect existing pieces:

1. **Hook: dev-observer after convergence** — Add to `hooks.json`: fire `gen-dev-observer.md` after `edge_converged` events. Closes the abiogenesis loop.
2. **Hook: health check at session start** — Invoke `detect_stuck_features()`, `detect_corrupted_events()`, `detect_orphaned_spawns()` on workspace open. Emit `interoceptive_signal` events.
3. **Schema discipline** — Add `affected_req_keys` to all `telemetry_signal_emitted` events. Enforce non-empty `source_findings` and `process_gaps` arrays in iteration events.
4. **Run exteroceptive monitors** — `pip-audit` and `npm audit` as periodic scripts. Genesis has real dependencies to monitor.

Light integration (Phase 1b telemetry):

5. **Sensory runner script** — Read `sensory_monitors.yml`, invoke matching pure functions or shell commands, emit typed signal events.
6. **Affect triage evaluator** — Read signal events, apply `affect_triage.yml` rules, emit `affect_triage` events with escalation decisions.
7. **MCP sensory service** — Expose `/sensory-status`, `/sensory-proposals`, `/sensory-approve`, `/sensory-dismiss` as MCP tools.

#### Products Built by Genesis

Products built using Genesis inherit the same telemetry functor structure. The `code→cicd→running_system→telemetry→intent` edges in the graph topology are not "Genesis features" — they are the product's own telemetry lifecycle:

| Graph Edge | Product's Telemetry Role |
|-----------|-------------------------|
| `code→cicd` | Product builds with instrumentation |
| `cicd→running_system` | Product deploys with monitors |
| `running_system→telemetry` | Product emits REQ-key-tagged telemetry |
| `telemetry→intent` | Product's telemetry feeds back as new intent |

The edge parameterisations for these edges are the **product's telemetry encoding spec**. When Genesis iterates on these edges, it is helping the product define and implement its own monitoring — not Genesis's monitoring. Genesis monitors itself; the product monitors itself. Same paradigm, same functor, different instantiations.

---

## 2. Component Design

### 2.1 Asset Graph Engine (REQ-F-ENGINE-001)

**Implements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002

#### Asset Type Registry

```yaml
# .ai-workspace/graph/asset_types.yml
asset_types:
  intent:
    schema: { id: "INT-*", description: string, source: enum, priority: enum }
    markov_criteria: [ "has_id", "has_description", "has_source" ]

  requirements:
    schema: { id: "REQ-*", type: enum, acceptance_criteria: list }
    markov_criteria: [ "has_id", "has_type", "has_acceptance_criteria", "human_approved" ]

  design:
    schema: { components: list, adrs: list, data_models: list }
    markov_criteria: [ "has_components", "traces_to_requirements", "adrs_documented" ]

  code:
    schema: { files: list, language: string, req_tags: list }
    markov_criteria: [ "compiles", "has_req_tags", "style_compliant" ]

  unit_tests:
    schema: { files: list, coverage: float, req_tags: list }
    markov_criteria: [ "all_pass", "coverage_above_threshold", "has_req_tags" ]

  uat_tests:
    schema: { scenarios: list, format: "gherkin", req_tags: list }
    markov_criteria: [ "all_pass", "business_language", "has_req_tags" ]

  cicd:
    schema: { pipeline: string, artifacts: list, release_manifest: object }
    markov_criteria: [ "build_passes", "deploy_succeeds" ]

  running_system:
    schema: { endpoints: list, health: object, slas: list }
    markov_criteria: [ "healthy", "within_sla" ]

  telemetry:
    schema: { metrics: list, alerts: list, req_tags: list }
    markov_criteria: [ "collecting", "tagged_with_req_keys" ]

  # Extensible — add new types without changing the engine
```

#### Admissible Transitions

```yaml
# .ai-workspace/graph/transitions.yml
transitions:
  - source: intent
    target: requirements
    evaluators: [ human, agent ]
    constructor: agent  # LLM generates requirements from intent

  - source: requirements
    target: design
    evaluators: [ human, agent ]
    constructor: agent  # LLM generates design from requirements

  - source: design
    target: code
    evaluators: [ agent, deterministic ]
    constructor: agent  # LLM generates code from design

  - source: code
    target: unit_tests
    edge_type: co_evolution  # TDD: tests and code iterate together
    evaluators: [ agent, deterministic ]
    constructor: agent

  - source: design
    target: uat_tests
    evaluators: [ human, agent ]
    constructor: agent  # LLM generates BDD scenarios from design

  - source: design
    target: test_cases
    evaluators: [ agent, deterministic ]
    constructor: agent

  - source: code
    target: cicd
    evaluators: [ deterministic ]
    constructor: deterministic  # CI/CD pipeline

  - source: cicd
    target: running_system
    evaluators: [ deterministic ]
    constructor: deterministic  # Deployment

  - source: running_system
    target: telemetry
    evaluators: [ deterministic ]
    constructor: deterministic  # Monitoring setup

  - source: telemetry
    target: intent  # Feedback loop closes
    evaluators: [ human, agent ]
    constructor: agent  # LLM + human detect new intents from telemetry

  # Extensible — add new edges without changing the engine
```

#### The iterate() Agent

In Codex, the iterate() function is the universal constructor routine. It reads edge parameterisation to determine role and convergence logic.

```markdown
<!-- imp_codex/code/agents/gen-iterate.md -->
# AISDLC Iterate Agent

You are the universal iteration function for the AI SDLC Asset Graph Model.

## Your Operation

You receive:
1. **Current asset** — the artifact being constructed (carries intent, lineage, history)
2. **Context[]** — standing constraints (ADRs, data models, templates, policy, graph topology)
3. **Edge parameterisation** — which evaluators to satisfy, what convergence looks like

You produce:
- The **next candidate** for this asset, closer to convergence

## How You Work

1. Read the edge parameterisation for this transition
2. Load relevant Context[] elements
3. Assess the current asset against evaluator criteria (compute delta)
4. If delta > 0: construct the next candidate that reduces the delta
5. If delta ≈ 0: report convergence — asset is ready for promotion

## Evaluator Types You Work With

- **Human**: You present your work for human review. Human approves, rejects, or refines.
- **Agent (you)**: You assess coherence, completeness, gap analysis
- **Deterministic Tests**: You run or invoke tests, check schemas, validate formats

## Key Constraint

You are the SAME agent for every edge. Your behaviour is parameterised by:
- The edge type (which transition)
- The evaluator configuration (which evaluators constitute stable())
- The context (which constraints bound construction)
- The asset type (what schema the output must satisfy)

You do NOT have hard-coded knowledge of "stages". You read the graph configuration.
```

#### Convergence Loop

The outer loop is managed by a command or by the user invoking the iterate agent repeatedly:

```
User invokes: /gen-iterate --edge "design→code" --feature "REQ-F-AUTH-001"

1. Command loads:
   - Current asset (the design doc for REQ-F-AUTH-001)
   - Context[] (ADRs, data models, code standards)
   - Edge config (design→code: evaluators=[agent, deterministic])

2. Iterate agent runs:
   - Reads design, generates code candidate
   - Self-evaluates (agent evaluator): is this coherent with the design?
   - Runs tests (deterministic evaluator): does the code compile? pass lint?

3. If not converged:
   - Agent reports delta: "Missing error handling for edge case X"
   - User can re-invoke or agent auto-iterates

4. If converged:
   - Asset promoted: code asset created, tagged with REQ-F-AUTH-001
   - Lineage updated: design→code transition recorded
```

---

### 2.2 Evaluator Framework (REQ-F-EVAL-001)

**Implements**: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003

#### Evaluator Configuration Per Edge

```yaml
# .ai-workspace/graph/evaluators.yml
evaluator_defaults:
  human:
    type: human
    processing_phase: conscious     # Spec §4.3 — deliberative (frontal cortex)
    mechanism: "Present work to user, await approval/rejection/refinement"
    convergence: "User explicitly approves"

  agent:
    type: agent
    processing_phase: conscious     # Spec §4.3 — deliberative (frontal cortex)
    # Note: agent also operates at affect phase for signal classification/triage
    mechanism: "LLM assesses coherence, completeness, gap analysis"
    convergence: "No gaps detected, all criteria met"

  deterministic:
    type: deterministic
    processing_phase: reflex        # Spec §4.3 — autonomic (spinal cord)
    mechanism: "Run tests, validate schemas, check formats"
    convergence: "All checks pass"

# Per-edge evaluator composition
edge_evaluators:
  intent→requirements:
    evaluators: [ agent, human ]
    convergence_order: "agent first (draft), then human (approve)"
    human_required: true

  requirements→design:
    evaluators: [ agent, human ]
    convergence_order: "agent first (draft), then human (approve)"
    human_required: true

  design→code:
    evaluators: [ agent, deterministic ]
    convergence_order: "agent generates, deterministic validates"
    human_required: false  # Can auto-converge if tests pass

  code↔unit_tests:
    evaluators: [ agent, deterministic ]
    convergence_order: "TDD co-evolution: RED→GREEN→REFACTOR"
    human_required: false

  design→uat_tests:
    evaluators: [ agent, human ]
    convergence_order: "agent drafts BDD, human validates business language"
    human_required: true
```

#### Human Accountability

The iterate agent ALWAYS presents work for human review on edges where `human_required: true`. On edges where `human_required: false`, the agent can auto-iterate, but the human can always intervene via `/gen-review`.

---

### 2.3 Context Management (REQ-F-CTX-001)

**Implements**: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004

#### Context Store

```
.ai-workspace/context/
├── adrs/                    # Architecture Decision Records
│   ├── ADR-CG-001-codex-runtime-as-platform.md
│   └── ...
├── data_models/             # Schemas, contracts
├── templates/               # Code patterns, standards
├── policy/                  # Security, compliance rules
├── prior/                   # Previous implementations
├── graph/                   # Graph topology (is Context[])
│   ├── asset_types.yml
│   └── transitions.yml
└── context_manifest.yml     # Index + hashes for reproducibility
```

#### Context Manifest (Spec Reproducibility)

```yaml
# .ai-workspace/context/context_manifest.yml
version: "1.0.0"
timestamp: "2026-02-19T10:30:00Z"
hash: "sha256:a1b2c3d4..."  # Hash of canonical serialisation

entries:
  - path: "adrs/ADR-CG-001-codex-runtime-as-platform.md"
    hash: "sha256:..."
    type: adr

  - path: "graph/asset_types.yml"
    hash: "sha256:..."
    type: graph_topology

  - path: "graph/transitions.yml"
    hash: "sha256:..."
    type: graph_topology

# Canonical serialisation: sorted entries, deterministic YAML
# Independent tools compute same hash from same Context[]
```

#### Context Hierarchy

```yaml
# Project-level context inherits from higher levels
hierarchy:
  - source: "corporate"    # Corporate standards (if configured)
  - source: "team"         # Team conventions
  - source: "project"      # Project-specific (this workspace)
# Later sources override earlier (deep merge)
```

---

### 2.4 Feature Vector Traceability (REQ-F-TRACE-001)

**Implements**: REQ-INTENT-001, REQ-INTENT-002, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003

#### Feature Tracking

```
.ai-workspace/features/
├── active/
│   ├── REQ-F-AUTH-001.yml    # Feature vector state
│   └── REQ-F-PERF-001.yml
├── completed/
│   └── REQ-F-SETUP-001.yml
└── feature_index.yml         # Summary + dependency graph
```

#### Feature Vector State

```yaml
# .ai-workspace/features/active/REQ-F-AUTH-001.yml
feature_id: REQ-F-AUTH-001
title: "User authentication with email/password"
intent: INT-AISDLC-042
status: in_progress

trajectory:
  requirements:
    status: converged
    asset: "docs/requirements/auth_requirements.md"
    converged_at: "2026-02-19T10:00:00Z"

  design:
    status: converged
    asset: "imp_auth/design/auth_design.md"
    converged_at: "2026-02-19T11:30:00Z"

  code:
    status: iterating
    asset: "src/auth/service.py"
    iteration: 3
    delta: "Missing password hashing"

  unit_tests:
    status: iterating  # Co-evolving with code
    asset: "tests/test_auth.py"
    iteration: 3

  uat_tests:
    status: pending

dependencies:
  - feature: REQ-F-DB-001
    type: "code depends on database schema"
    status: resolved
```

#### Intent Capture

```yaml
# .ai-workspace/intents/INT-042.yml
intent_id: INT-042
source: human  # or: runtime_feedback, ecosystem
description: "Fix auth timeout issue"
timestamp: "2026-02-19T09:00:00Z"
priority: high
spawns_features: [ REQ-F-AUTH-002 ]
triggered_by: "telemetry alert: REQ-F-AUTH-001 timeout rate > 5%"
```

---

### 2.5 Edge Parameterisations (REQ-F-EDGE-001)

**Implements**: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004

These are **configurations**, not separate engines. They parameterise the iterate agent.

#### TDD Co-Evolution (Code ↔ Tests)

```yaml
# .ai-workspace/graph/edges/code_tests.yml
edge: "code↔unit_tests"
pattern: tdd_co_evolution

phases:
  red:
    action: "Write failing test first"
    evaluator: deterministic
    convergence: "Test exists and fails (expected)"

  green:
    action: "Write minimal code to pass"
    evaluator: deterministic
    convergence: "All tests pass"

  refactor:
    action: "Improve code quality"
    evaluator: [ agent, deterministic ]
    convergence: "Tests still pass, agent confirms quality"

  commit:
    action: "Save with REQ key"
    evaluator: deterministic
    convergence: "Commit message includes REQ-* tag"

coverage_threshold: 0.80
```

#### BDD (Design → Tests)

```yaml
# .ai-workspace/graph/edges/design_tests.yml
edge: "design→uat_tests"
pattern: bdd

scenario_format: gherkin
language: business  # No technical jargon for UAT
req_tag_required: true
min_scenarios_per_req: 1
```

#### ADR Generation (Requirements → Design)

```yaml
# .ai-workspace/graph/edges/req_design.yml
edge: "requirements→design"
pattern: adr_generation

adr_template: "context/templates/adr_template.md"
req_reference_required: true
alternatives_required: true
```

#### Code Tagging

```yaml
# .ai-workspace/graph/edges/code_tagging.yml
tag_format:
  implementation: "Implements: REQ-*"
  validation: "Validates: REQ-*"
  # Comment syntax is language-specific; tag format is the contract
commit_tag_required: true
validation_enabled: true  # Tooling parses tag format, not comment syntax
```

---

### 2.6 Developer Tooling (REQ-F-TOOL-001)

**Implements**: REQ-TOOL-001 through REQ-TOOL-008

#### Commands

| Command | Purpose | Engine Operation |
|---------|---------|-----------------|
| `/gen-iterate` | Invoke iterate() on a specific edge | Core engine |
| `/gen-status` | Show feature vector progress | Read feature tracking |
| `/gen-checkpoint` | Save session snapshot | Create immutable checkpoint |
| `/gen-review` | Human evaluator review point | Present asset for approval |
| `/gen-trace` | Show trajectory for a REQ key | Navigate feature graph |
| `/gen-gaps` | Test gap analysis | Compare REQ keys vs tests |
| `/gen-release` | Create release with REQ coverage | Generate release manifest |
| `/gen-start` | State-driven routing entry point | Detect state, select feature/edge, delegate |
| `/gen-init` | Scaffold new project | Create workspace structure |

#### Plugin Delivery

```
imp_codex/code/
├── plugin.json                  # Metadata (v2.1.0)
├── config/
│   ├── graph_topology.yml       # Default SDLC graph
│   ├── evaluator_defaults.yml   # Default evaluator configs
│   └── edge_params/             # Per-edge parameterisations
│       ├── tdd.yml
│       ├── bdd.yml
│       ├── adr.yml
│       └── code_tagging.yml
├── agents/
│   └── gen-iterate.md        # The ONE agent
├── commands/
│   ├── gen-start.md
│   ├── gen-iterate.md
│   ├── gen-status.md
│   ├── gen-checkpoint.md
│   ├── gen-review.md
│   ├── gen-trace.md
│   ├── gen-gaps.md
│   ├── gen-release.md
│   └── gen-init.md
└── docs/
    └── methodology_reference.md  # Quick reference
```

#### Workspace Structure (Scaffolded by /gen-init)

```
.ai-workspace/
├── graph/                                # Layer 2: Graph Package (copied from plugin)
│   ├── graph_topology.yml                #   Asset types, transitions, constraint dimensions
│   ├── evaluator_defaults.yml            #   Evaluator type definitions
│   └── edges/                            #   Edge parameterisation configs
├── context/                              # Layer 3: Project Binding
│   ├── project_constraints.yml           #   Tech stack, tools, thresholds, dimensions
│   ├── adrs/                             #   Architecture Decision Records
│   ├── data_models/                      #   Schemas, contracts
│   ├── templates/                        #   Patterns, standards
│   ├── policy/                           #   Compliance, security
│   └── context_manifest.yml              #   Reproducibility hash
├── features/
│   ├── active/                           #   In-progress feature vectors
│   ├── completed/                        #   Converged feature vectors
│   ├── fold-back/                        #   Child vector fold-back results
│   └── feature_index.yml                 #   Dependency graph
├── profiles/                             #   Projection profiles (from plugin)
├── events/                               #   Source of truth (append-only)
│   └── events.jsonl                      #   Immutable event log
├── intents/
│   └── INT-*.yml                         #   Captured intents
├── tasks/
│   ├── active/
│   │   └── ACTIVE_TASKS.md               #   Current work items (derived view)
│   └── finished/                         #   Completed task docs
├── snapshots/
│   └── snapshot-*.yml                    #   Immutable session checkpoints
└── STATUS.md                             #   Computed projection (derived view)
```

---

## 3. Lifecycle Closure

**Implements**: REQ-LIFE-001 through REQ-LIFE-012, REQ-INTENT-003

### Phase 1 — Gradient Mechanics (REQ-LIFE-005 through REQ-LIFE-009)

The gradient at spec scale is Phase 1. The iterate agent, commands, and edge configs already implement:

- **`intent_raised` events** (REQ-LIFE-005) — emitted when any observer detects a delta warranting action beyond current iteration scope. Seven signal sources classified (REQ-LIFE-006).
- **`spec_modified` events** (REQ-LIFE-007) — emitted when specification absorbs a signal and updates. `prior_intents` chain enables reflexive loop detection.
- **Protocol enforcement** (REQ-LIFE-008) — five mandatory side effects after every `iterate()`. Circuit breaker prevents infinite regression.
- **Development-time homeostasis** — gap analysis, test failures, refactoring, source findings, and process gaps are formal signals that enter the intent system via the same mechanism as production telemetry.

See §1.7 for detailed design and ADR-011 for the architectural decision.

- **Spec review as gradient check** (REQ-LIFE-009) — stateless `delta(workspace, spec) → intents`, invocable on demand or after completion events.

### Phase 1b — Telemetry Wiring (REQ-LIFE-001 through REQ-LIFE-004)

Telemetry is not a future phase — it is a constitutive property of being a product (§1.12). The building blocks are all built; Phase 1b wires them.

**Genesis self-monitoring (already operational):**
- Event log with 13+ event types — this IS operational telemetry
- Protocol enforcement hooks — reflex-phase mandatory side effects
- 23 pure functions in `workspace_state.py` — monitor implementations
- TELEM signals — self-observation at methodology scale

**Genesis self-monitoring (to wire):**
- Hook dev-observer after `edge_converged` events (closes abiogenesis loop)
- Hook health checks at session start (invoke pure function monitors)
- Run `pip-audit`/`npm audit` for exteroceptive monitoring
- Sensory runner script that reads `sensory_monitors.yml` and invokes monitors on schedule

**Product telemetry (when products traverse production edges):**
- `code→cicd` — product builds with instrumentation (CI/CD evaluators)
- `cicd→running_system` — product deploys with monitors
- `running_system→telemetry` — product emits REQ-key-tagged telemetry
- `telemetry→intent` — product telemetry feeds back as new intent via `runtime_feedback` and `ecosystem` signal sources

The graph topology already includes these edges. The iterate agent can traverse them. What Phase 1b adds is the wiring that makes Genesis eat its own dog food — the same telemetry paradigm Genesis enforces on products, applied to itself.

### Phase 2a — Observer Agents (REQ-LIFE-010 through REQ-LIFE-012)

Three observer agents close the abiogenesis loop. Each is a markdown agent spec (ADR-014) triggered by hooks:

- **Dev observer** (REQ-LIFE-010) — `delta(workspace, spec) → intents`. Triggered after iterate/converge events. Operationalises the spec review (REQ-LIFE-009) as an automated agent.
- **CI/CD observer** (REQ-LIFE-011) — `delta(build_state, quality_spec) → intents`. Triggered after CI/CD pipeline completion. Maps build failures back to REQ keys.
- **Ops observer** (REQ-LIFE-012) — `delta(running_system, spec) → intents`. Triggered on schedule/alert. Consumes sensory signals and production telemetry.

See §1.11 for detailed design and ADR-014 for the architectural decision. All observers are Markov objects (actor model — event log is the mailbox).

---

## 4. Migration from v1.x

### What Changes

| v1.x | v2.1 |
|------|------|
| 7 agent files (one per stage) | 4 agent files (iterate + 3 observers) |
| 42→11 skills | Edge parameterisation configs (YAML) |
| stages_config.yml (1,273 lines) | graph_topology.yml + edge_params/ (~200 lines) |
| Fixed 7-stage pipeline | Configurable graph in Context[] |
| 9 commands | 13 commands (12 power-user + Start routing layer) |
| .ai-workspace with task focus | .ai-workspace with graph/context/features/tasks |

### What Carries Forward

- Codex runtime as platform (ADR-CG-001)
- Plugin delivery mechanism (`imp_codex/code/` package)
- Markdown-first approach
- Workspace under .ai-workspace/
- ACTIVE_TASKS.md for task tracking
- Slash commands for workflow integration
- Federated context hierarchy concept

### Migration Path

1. New projects: `/gen-init` creates v2.1 workspace
2. Existing v1.x projects: v1.x agents/commands continue to work; v2.1 can be installed alongside
3. No breaking changes to user workflow — commands change but concept is familiar

---

## 5. ADR Baseline

### Active Codex Platform ADRs
- **ADR-CG-001**: Codex runtime as target platform
- **ADR-CG-002**: Universal iterate orchestrator
- **ADR-CG-003**: Review boundary and disambiguation
- **ADR-CG-004**: Event replay and recovery strategy
- **ADR-CG-005**: Sensory operating modes
- **ADR-CG-008**: Module decomposition and basis projections
- **ADR-CG-009**: Runtime robustness for probabilistic processing

### Core Methodology ADRs Referenced by This Design
- **ADR-008..017**: Iterate agent, topology/config, reproducibility, UX, coordination, IntentEngine, sensory binding, tolerances, functor execution
- **ADR-S-011/012/015/016/017**: OpenLineage schema, event stream contract, transaction model, invocation contract, zoom morphism
- **Note**: ADR-015 is currently kept as a transitional reference binding; Codex-native sensory technology binding should be captured in a future ADR-CG decision.

---

## 6. Feature Vector Coverage

| Feature Vector | Design Section | Status |
|---------------|---------------|--------|
| REQ-F-ENGINE-001 | §2.1 Asset Graph Engine | Implemented runtime baseline |
| REQ-F-EVAL-001 | §2.2 Evaluator Framework | Implemented runtime baseline |
| REQ-F-CTX-001 | §2.3 Context Management | Implemented runtime baseline |
| REQ-F-TRACE-001 | §2.4 Feature Vector Traceability | Implemented runtime baseline |
| REQ-F-EDGE-001 | §2.5 Edge Parameterisations | Implemented config surface |
| REQ-F-TOOL-001 | §2.6 Developer Tooling | Implemented command/runtime surface |
| REQ-F-LIFE-001 | §3 Lifecycle Closure, §1.12 Telemetry | Implemented baseline, product-scale loops pending |
| REQ-F-SENSE-001 | §1.8 Sensory Service | Implemented monitor/projection baseline |
| REQ-F-UX-001 | §1.9 Two-Command UX Layer | Implemented state/routing baseline |
| REQ-F-COORD-001 | §1.10 Multi-Agent Coordination | Implemented event-sourced coordination baseline |
| REQ-F-SUPV-001 | §1.12 Telemetry Functor, [FUNCTOR_FRAMEWORK_DESIGN.md](./FUNCTOR_FRAMEWORK_DESIGN.md) | Implemented baseline, formal extension pending |
| REQ-F-ROBUST-001 | §1.5.1 Runtime Robustness, [ENGINE_DESIGN_GAP.md](./ENGINE_DESIGN_GAP.md) | Partial; invocation hardening remains open |
| REQ-F-EVENT-001 | §1.5 Event Sourcing + ADR-S-011/012/015 mapping | Implemented OpenLineage-normalized event baseline |
| REQ-F-EVOL-001 | §1.6/§1.7 consciousness loop + protocol enforcement | Partial; full spec evolution workflow pending |
| REQ-F-FP-001 | [DESIGN_REQUIREMENTS.md](./DESIGN_REQUIREMENTS.md), [FUNCTOR_FRAMEWORK_DESIGN.md](./FUNCTOR_FRAMEWORK_DESIGN.md) | Planned; runtime still lacks true construct+batches path |
| REQ-F-CONSENSUS-001 | [DESIGN_REQUIREMENTS.md](./DESIGN_REQUIREMENTS.md), [ENGINE_DESIGN_GAP.md](./ENGINE_DESIGN_GAP.md) | Design-tier only; no executable package yet |
| REQ-F-NAMEDCOMP-001 | [DESIGN_REQUIREMENTS.md](./DESIGN_REQUIREMENTS.md), [ENGINE_DESIGN_GAP.md](./ENGINE_DESIGN_GAP.md) | Partial; named composition registry + typed `intent_raised` payloads implemented, execution layer still pending |

**Design coverage target updated to 17/17 feature vectors. Current executable baseline is the `imp_codex` runtime plus the tenant test suite; `REQ-F-NAMEDCOMP-001` now has a baseline executable slice, while `CONSENSUS` and deeper phase-2 functors remain open.**

---

## 7. Implementation Priority

Per FEATURE_VECTORS.md task graph, updated to reflect telemetry-as-constitutive:

```
Phase 1a: ✓ COMPLETE — graph engine, configs, edge params, commands, tenant test harness
Phase 1b: Wire telemetry — connect existing monitors, hooks, observer agents (§1.12)
Phase 1c: Executable iterate() — runtime engine from iterate agent spec
Phase 1d: Executable commands — 13 commands as executable agents, not markdown specs
Phase 2:  Product telemetry edges — CI/CD, running system, production homeostasis
```

**Key paradigm shift**: Telemetry is not Phase 2. Phase 1b wires Genesis's own self-monitoring using building blocks already built in Phase 1a. Phase 2 is when *products built by Genesis* traverse production telemetry edges — which is a different instantiation of the same functor.

**Next deliverable**: Wire the dev-observer hook after `edge_converged` events. Zero new code — just a hook entry that closes the abiogenesis loop.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical methodology (v2.8.0)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — 83 implementation requirements (v3.13.0)
- [FEATURE_VECTORS.md](../../specification/features/FEATURE_VECTORS.md) — Feature vector decomposition (v1.9.0, 17 vectors)
- [DESIGN_REQUIREMENTS.md](./DESIGN_REQUIREMENTS.md) — Codex-specific design-tier requirements
- [ENGINE_DESIGN_GAP.md](./ENGINE_DESIGN_GAP.md) — Current executable/runtime gap analysis
- [FUNCTOR_FRAMEWORK_DESIGN.md](./FUNCTOR_FRAMEWORK_DESIGN.md) — Codex functor/runtime mapping
- [ADR-S-011](../../specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md) — Unified OpenLineage metadata standard
- [ADR-S-012](../../specification/adrs/ADR-S-012-event-stream-as-formal-model-medium.md) — Event stream as formal model
- [ADR-S-015](../../specification/adrs/ADR-S-015-unit-of-work-transaction-model.md) — Unit-of-work transaction model
- [ADR-S-016](../../specification/adrs/ADR-S-016-invocation-contract.md) — Invocation contract
- [ADR-S-017](../../specification/adrs/ADR-S-017-variable-grain-zoom-morphism.md) — Variable grain zoom morphism
- [ADR-017](adrs/ADR-017-functor-based-execution-model.md) — Functor-based execution model (telemetry encoding)
- [ADR-CG-001](adrs/ADR-CG-001-codex-runtime-as-platform.md) — Codex runtime platform binding
- Prior v1.x design (AISDLC_IMPLEMENTATION_DESIGN.md) — superseded, recoverable at tag `v1.x-final`
