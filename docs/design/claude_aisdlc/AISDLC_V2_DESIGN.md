# AI SDLC — Claude Code Implementation Design (v2.5)

**Version**: 2.0.0
**Date**: 2026-02-20
**Derived From**: [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) (v1.0.0)
**Model**: [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.5.0)
**Platform**: Claude Code (ADR-001 — carried forward from v1.x)

---

## Design Intent

This document is the |design⟩ asset for the AI SDLC tooling implementation on Claude Code. It covers all 7 feature vectors defined in FEATURE_VECTORS.md.

**Key shift from v1.x**: The v1.x design had 7 stage-specific agents (one per pipeline stage). The v2.1 model has **one operation** (`iterate`) parameterised per graph edge. The design must reflect this: a universal engine with edge-specific parameterisation, not stage-specific agents.

**What carries forward from v1.x**:
- Claude Code as platform (ADR-001)
- Plugin delivery mechanism
- Workspace file structure (adapted)
- Slash commands (adapted)
- Markdown-first approach

**What changes**:
- 7 stage agents → 1 iterate engine with edge parameterisations
- Linear pipeline → graph with admissible transitions
- Stage-specific skills → evaluator + constructor composition per edge
- Fixed topology → configurable graph in Context[]

**What v2.0.0 adds** (from spec v2.5.0):
- Three-layer conceptual model: Engine / Graph Package / Project Binding
- Constraint dimension taxonomy at the design edge
- Event sourcing as the formal execution model
- Methodology self-observation via TELEM signals

---

## 1. Architecture Overview

### 1.1 The Three Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Developer)                              │
│                   /aisdlc-* commands                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      COMMAND LAYER                                   │
│  Slash commands that invoke the engine for specific operations       │
│  /aisdlc-iterate  /aisdlc-status  /aisdlc-checkpoint  ...          │
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
│  .claude/                                                            │
│  ├── commands/        Slash commands                                  │
│  └── settings.json    Plugin configuration                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principle: Universal Engine, Parameterised Edges

The v1.x design had separate agents for each stage. The v2.1 design has:

- **One iterate() implementation** — a Claude Code agent that takes (asset, context, evaluators) and produces the next candidate
- **Edge parameterisation configs** — YAML files that define: which evaluators, which constructors, what convergence criteria
- **The graph topology** — a YAML config defining asset types and admissible transitions

The agent IS the iterate() function. It reads the edge parameterisation to know what role to adopt, what evaluators to run, what convergence looks like. Different edges produce different behaviour from the same agent.

### 1.3 Conceptual Model: Three Instantiation Layers (Spec §2.8)

The spec defines three conceptual layers. Here is how they map to the Claude Code implementation:

```
Spec Layer                    Implementation
──────────                    ──────────────
Layer 1: ENGINE (universal)   Plugin root:
  4 primitives                  agents/aisdlc-iterate.md     (the ONE agent)
  iterate() + evaluator types   config/evaluator_defaults.yml (evaluator taxonomy)
  event sourcing                commands/*.md                 (workflow operations)
                                config/feature_vector_template.yml

Layer 2: GRAPH PACKAGE          Plugin config:
  (domain-specific)             config/graph_topology.yml    (asset types + transitions)
  topology + edge configs       config/edge_params/*.yml     (10 edge parameterisations)
  constraint dimensions         config/graph_topology.yml    (constraint_dimensions section)
  projection profiles           config/profiles/*.yml        (6 named profiles)

Layer 3: PROJECT BINDING        Workspace:
  (instance-specific)           .ai-workspace/context/project_constraints.yml
  project constraints           .ai-workspace/context/adrs/
  context URIs                  .ai-workspace/context/data_models/
  threshold overrides           .ai-workspace/context/policy/
```

**Key design decision**: Layers 1 and 2 ship together in the plugin package. Layer 3 is scaffolded by `/aisdlc-init` into the project workspace. This means:

- Upgrading the plugin (Layer 1 + 2) does not overwrite project bindings (Layer 3)
- Different graph packages can be created by forking the `config/` directory
- The iterate agent reads Layer 2 config at runtime, never hard-codes domain knowledge

### 1.4 Constraint Dimensions at the Design Edge (Spec §2.6.1)

The Requirements → Design edge is the most consequential transition. The spec defines **constraint dimensions** — categories of disambiguation that design must resolve. In the implementation:

1. **Graph topology** (`graph_topology.yml`) declares the dimension taxonomy with mandatory/advisory flags
2. **Edge config** (`requirements_design.yml`) includes checklist items that verify each mandatory dimension is resolved
3. **Project constraints** (`project_constraints.yml`) provides the concrete values for each dimension (e.g., `ecosystem.language: scala`, `ecosystem.version: "2.13"`)
4. **Iterate agent** checks that all mandatory dimensions have corresponding ADRs or design decisions

Unresolved mandatory dimensions are checklist failures — they block convergence. This directly addresses the dogfooding finding: 5/7 build bugs were in dimensions the design left implicit.

### 1.5 Event Sourcing Execution Model (Spec §7.5)

All methodology state changes are recorded as immutable events in `.ai-workspace/events/events.jsonl`. All observable state (STATUS.md, feature vectors, task lists) is a derived projection.

```
Source of Truth                    Derived Views (projections)
────────────────                   ──────────────────────────
events/events.jsonl           ──►  STATUS.md           (Gantt, telemetry, self-reflection)
  (append-only JSONL)         ──►  ACTIVE_TASKS.md     (convergence events as markdown)
                              ──►  features/active/*.yml  (latest trajectory per feature)
                              ──►  gap analysis         (findings aggregated across edges)
```

Event types (12): `project_initialized`, `iteration_completed`, `edge_started`, `edge_converged`, `spawn_created`, `spawn_folded_back`, `checkpoint_created`, `review_completed`, `gaps_validated`, `release_created`, `intent_raised`, `spec_modified`.

All methodology commands emit events. The event log is the sole integration contract between the methodology and any external observer (e.g., genesis-monitor). See the iterate agent's **Event Type Reference** for the canonical schema catalogue.

This is an engine-level primitive (Layer 1) — it applies regardless of graph package.

### 1.6 Methodology Self-Observation (Spec §7.6)

The methodology observes itself through the same evaluator pattern it uses for artifacts:

```
Level 1 (product):     |running_system⟩ → |telemetry⟩ → |observer⟩ → |new_intent⟩
Level 2 (methodology): |methodology_run⟩ → |TELEM_signals⟩ → |observer⟩ → |graph_package_update⟩
```

TELEM signals are emitted by the iterate agent as `process_gaps` in each event. The `/aisdlc-status` command aggregates these into the Self-Reflection section of STATUS.md. Over time, persistent process gaps become candidates for graph package updates (new evaluator checks, refined constraint dimensions, additional context guidance).

### 1.7 Consciousness Loop at Every Observer Point (Spec §7.7, ADR-011)

**Implements**: REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008

The consciousness loop is not a single edge (telemetry→intent). It is a structural property that emerges at **every observer point**. Every evaluator running at every edge is an observer. When an observer detects a delta that cannot be resolved within the current iteration scope, that delta becomes a formal `intent_raised` event.

The consciousness loop operates in the **conscious processing regime** (Spec §4.3) — it requires deliberative judgment to interpret deltas and generate intents. But it depends entirely on the **reflex substrate**: event emission, feature vector updates, and STATUS regeneration fire unconditionally at every iteration boundary (the reflex regime). Without these autonomic reflexes, the conscious system has no data to reason about. Protocol enforcement hooks (§1.7.4) are the mechanism that guarantees the reflex substrate operates — they are the methodology's autonomic nervous system.

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
- `/aisdlc-gaps` → `gap` signal (traceability validation)
- telemetry→intent edge → `runtime_feedback` and `ecosystem` signals

#### 1.7.2 Seven Signal Sources

| Signal Source | Development/Production | Observer | Trigger |
|---|---|---|---|
| `gap` | Development | `/aisdlc-gaps` | REQ keys without test/telemetry coverage |
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
- This distinguishes the consciousness loop from a simple feedback loop: awareness of the consequences of one's own awareness

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
| `agents/aisdlc-iterate.md` | Event Type Reference (12 types), consciousness loop observer table, `intent_raised` emission from backward/inward gap detection |
| `commands/aisdlc-iterate.md` | Stuck delta detection (>3 iterations), refactoring signal, source escalation → `intent_raised` |
| `commands/aisdlc-gaps.md` | Gap cluster → `intent_raised` per domain group |
| `config/edge_params/feedback_loop.yml` | 7 signal sources with intent templates and `intent_raised` schema |
| `config/edge_params/tdd.yml` | Intent generation from stuck failures and refactoring needs |
| All 8 commands | `event_type` field standardised, event emission mandatory |

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

In Claude Code, the iterate() function IS a single agent — the universal constructor. It reads the edge parameterisation to know its role.

```markdown
<!-- .claude/agents/aisdlc-iterate.md -->
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
User invokes: /aisdlc-iterate --edge "design→code" --feature "REQ-F-AUTH-001"

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
    processing_regime: conscious    # Spec §4.3 — deliberative
    mechanism: "Present work to user, await approval/rejection/refinement"
    convergence: "User explicitly approves"

  agent:
    type: agent
    processing_regime: conscious    # Spec §4.3 — deliberative
    mechanism: "LLM assesses coherence, completeness, gap analysis"
    convergence: "No gaps detected, all criteria met"

  deterministic:
    type: deterministic
    processing_regime: reflex       # Spec §4.3 — autonomic
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

The iterate agent ALWAYS presents work for human review on edges where `human_required: true`. On edges where `human_required: false`, the agent can auto-iterate, but the human can always intervene via `/aisdlc-review`.

---

### 2.3 Context Management (REQ-F-CTX-001)

**Implements**: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004

#### Context Store

```
.ai-workspace/context/
├── adrs/                    # Architecture Decision Records
│   ├── ADR-001-platform.md
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
  - path: "adrs/ADR-001-platform.md"
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
    asset: "docs/design/auth_design.md"
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
| `/aisdlc-iterate` | Invoke iterate() on a specific edge | Core engine |
| `/aisdlc-status` | Show feature vector progress | Read feature tracking |
| `/aisdlc-checkpoint` | Save session snapshot | Create immutable checkpoint |
| `/aisdlc-review` | Human evaluator review point | Present asset for approval |
| `/aisdlc-trace` | Show trajectory for a REQ key | Navigate feature graph |
| `/aisdlc-gaps` | Test gap analysis | Compare REQ keys vs tests |
| `/aisdlc-release` | Create release with REQ coverage | Generate release manifest |
| `/aisdlc-init` | Scaffold new project | Create workspace structure |

#### Plugin Delivery

```
claude-code/.claude-plugin/plugins/aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json              # Metadata (v2.5.0)
├── config/
│   ├── graph_topology.yml       # Default SDLC graph
│   ├── evaluator_defaults.yml   # Default evaluator configs
│   └── edge_params/             # Per-edge parameterisations
│       ├── tdd.yml
│       ├── bdd.yml
│       ├── adr.yml
│       └── code_tagging.yml
├── agents/
│   └── aisdlc-iterate.md        # The ONE agent
├── commands/
│   ├── aisdlc-iterate.md
│   ├── aisdlc-status.md
│   ├── aisdlc-checkpoint.md
│   ├── aisdlc-review.md
│   ├── aisdlc-trace.md
│   ├── aisdlc-gaps.md
│   ├── aisdlc-release.md
│   └── aisdlc-init.md
└── docs/
    └── methodology_reference.md  # Quick reference
```

#### Workspace Structure (Scaffolded by /aisdlc-init)

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

**Implements**: REQ-LIFE-001 through REQ-LIFE-008, REQ-INTENT-003

### Phase 1 — Consciousness Loop Mechanics (REQ-LIFE-005 through REQ-LIFE-008)

The consciousness loop at every observer point is Phase 1. The iterate agent, commands, and edge configs already implement:

- **`intent_raised` events** (REQ-LIFE-005) — emitted when any observer detects a delta warranting action beyond current iteration scope. Seven signal sources classified (REQ-LIFE-006).
- **`spec_modified` events** (REQ-LIFE-007) — emitted when specification absorbs a signal and updates. `prior_intents` chain enables reflexive loop detection.
- **Protocol enforcement** (REQ-LIFE-008) — five mandatory side effects after every `iterate()`. Circuit breaker prevents infinite regression.
- **Development-time homeostasis** — gap analysis, test failures, refactoring, source findings, and process gaps are formal signals that enter the intent system via the same mechanism as production telemetry.

See §1.7 for detailed design and ADR-011 for the architectural decision.

### Phase 2 — Production Lifecycle (REQ-LIFE-001 through REQ-LIFE-004)

The production lifecycle features (CI/CD edge, runtime telemetry, production homeostasis, eco-intent) are Phase 2. The graph topology already includes these transitions — the engine supports them. Phase 2 adds the constructor and evaluator implementations for these edges.

What Phase 1 delivers:
- Graph topology includes CI/CD → Running System → Telemetry → New Intent edges
- Feature vectors can be traced through these edges (status: pending)
- The iterate agent can be manually invoked on these edges
- **Development-time consciousness loop fully operational** — all signal sources except `runtime_feedback` and `ecosystem` are active

What Phase 2 adds:
- Automated CI/CD evaluators (build/deploy checks)
- Telemetry integration (REQ key tagging in monitoring)
- Production homeostasis checks (SLA monitoring, drift detection)
- Eco-intent generation (ecosystem change detection)
- Production feedback loop automation (telemetry → new intent via `runtime_feedback` and `ecosystem` signal sources)

---

## 4. Migration from v1.x

### What Changes

| v1.x | v2.1 |
|------|------|
| 7 agent files (one per stage) | 1 agent file (aisdlc-iterate.md) |
| 42→11 skills | Edge parameterisation configs (YAML) |
| stages_config.yml (1,273 lines) | graph_topology.yml + edge_params/ (~200 lines) |
| Fixed 7-stage pipeline | Configurable graph in Context[] |
| 8 commands | 8 commands (different operations) |
| .ai-workspace with task focus | .ai-workspace with graph/context/features/tasks |

### What Carries Forward

- Claude Code as platform (ADR-001)
- Plugin delivery mechanism (.claude-plugin/)
- Markdown-first approach
- Workspace under .ai-workspace/
- ACTIVE_TASKS.md for task tracking
- Slash commands for workflow integration
- Federated context hierarchy concept

### Migration Path

1. New projects: `/aisdlc-init` creates v2.5 workspace
2. Existing v1.x projects: v1.x agents/commands continue to work; v2.5 can be installed alongside
3. No breaking changes to user workflow — commands change but concept is familiar

---

## 5. ADR Disposition

### Carried Forward (still valid)
- **ADR-001**: Claude Code as MVP Platform
- **ADR-002**: Commands for Workflow Integration (commands change, mechanism same)
- **ADR-006**: Plugin Configuration and Discovery

### Superseded
- **ADR-003**: Agents for Stage Personas → replaced by single iterate agent
- **ADR-004**: Skills for Reusable Capabilities → replaced by edge parameterisations
- **ADR-005**: Iterative Refinement Feedback Loops → now inherent in iterate() engine
- **ADR-007**: Hooks for Methodology Automation → hooks now driven by graph transitions

### New ADRs Needed
- **ADR-008**: Universal Iterate Agent (single agent, edge-parameterised)
- **ADR-009**: Graph Topology as Configuration (YAML-based, extensible)
- **ADR-010**: Spec Reproducibility (canonical serialisation, content-addressable hashing)

---

## 6. Feature Vector Coverage

| Feature Vector | Design Section | Status |
|---------------|---------------|--------|
| REQ-F-ENGINE-001 | §2.1 Asset Graph Engine | Designed |
| REQ-F-EVAL-001 | §2.2 Evaluator Framework | Designed |
| REQ-F-CTX-001 | §2.3 Context Management | Designed |
| REQ-F-TRACE-001 | §2.4 Feature Vector Traceability | Designed |
| REQ-F-EDGE-001 | §2.5 Edge Parameterisations | Designed |
| REQ-F-TOOL-001 | §2.6 Developer Tooling | Designed |
| REQ-F-LIFE-001 | §3 Lifecycle Closure | Designed (Phase 2 scope) |

**7/7 feature vectors covered.**

---

## 7. Implementation Priority

Per FEATURE_VECTORS.md task graph:

```
Phase 1a: Implement graph engine (asset types, transitions, iterate agent)
Phase 1b: Implement evaluator configs ∥ context store ∥ feature tracking
Phase 1c: Implement edge params (TDD/BDD/ADR) + tooling commands
Phase 2:  Implement lifecycle closure (CI/CD, telemetry, homeostasis)
```

**First deliverable**: The iterate agent + graph topology config + /aisdlc-init command. This bootstraps everything else.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical methodology (v2.5.0)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — 32 implementation requirements (v3.1.0)
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) — Feature vector decomposition (v1.0.0)
- [AISDLC_IMPLEMENTATION_DESIGN.md](AISDLC_IMPLEMENTATION_DESIGN.md) — Prior v1.x design (superseded)
- [adrs/ADR-001-claude-code-as-mvp-platform.md](adrs/ADR-001-claude-code-as-mvp-platform.md) — Platform choice (carried forward)
