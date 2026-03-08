# AI SDLC — Project Genesis: Feature Vector Decomposition

**Version**: 1.9.0
**Date**: 2026-03-05
**Derived From**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) (v3.13.0)
**Method**: Asset Graph Model §6.4 (Task Planning as Trajectory Optimisation)

---

## Purpose

Decompose INT-AISDLC-001 (AI SDLC Methodology Implementation) into feature vectors that trace trajectories through the asset graph. This is the prerequisite for design — per the methodology, features are identified before architecture is drawn.

---

## Feature Vectors

### REQ-F-ENGINE-001: Asset Graph Engine

The core graph topology, iteration function, and convergence/promotion mechanism.

**Satisfies**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-ITER-001, REQ-ITER-002, REQ-ITER-003

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Asset type registry with typed interfaces and Markov criteria
- Admissible transition registry (directed, cyclic, extensible)
- `iterate(Asset<Tn>, Context[], Evaluators) → Asset<Tn.k+1>`
- `stable()` convergence check with configurable ε per evaluator
- Promotion: candidate → Markov object when all evaluators pass

**Dependencies**: None — this is the foundation.

---

### REQ-F-EVAL-001: Evaluator Framework

The three evaluator types and their composition per edge.

**Satisfies**: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Human evaluator interface (judgment, approval/rejection)
- Agent(intent, context) evaluator interface (LLM-based delta computation)
- Deterministic Test evaluator interface (pass/fail)
- Evaluator composition registry: edge type → set of evaluators
- Human accountability: AI assists, human decides

**Dependencies**: REQ-F-ENGINE-001.|design⟩ (evaluators plug into the iteration engine)

---

### REQ-F-CTX-001: Context Management

Context[] as constraint surface, hierarchy, and spec reproducibility.

**Satisfies**: REQ-CTX-001, REQ-CTX-002, REQ-INTENT-004

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Context store: ADRs, data models, templates, policy, graph topology, prior implementations
- Hierarchical composition: global → org → team → project (later overrides earlier)
- Context version control
- Spec canonical serialisation (deterministic, content-addressable hash)
- Spec immutability: evolution produces new versions, not mutations

**Dependencies**: REQ-F-ENGINE-001.|design⟩ (context feeds into iterate())

---

### REQ-F-TRACE-001: Feature Vector Traceability

Intent capture, REQ keys, trajectories, dependencies, and task planning.

**Satisfies**: REQ-INTENT-001, REQ-INTENT-002, REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Intent capture (INT-* format, structured, persisted)
- Intent + Context[] → Spec composition
- REQ key format and propagation across all graph assets
- Bidirectional navigation (intent → runtime, runtime → intent)
- Cross-feature dependency tracking
- Task graph generation from feature decomposition + dependency compression

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (needs graph engine), REQ-F-CTX-001.|design⟩ (needs context model)

---

### REQ-F-EDGE-001: Edge Parameterisations

TDD, BDD, ADR, and code tagging configurations for common graph edges.

**Satisfies**: REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- TDD co-evolution pattern (RED/GREEN/REFACTOR/COMMIT) at Code ↔ Tests edges
- BDD Given/When/Then at Design → Test Cases and Design → UAT Tests edges
- ADR generation at Requirements → Design edge
- Code tagging: `Implements: REQ-*` / `Validates: REQ-*` (platform-agnostic tag format)
- All parameterisations are evaluator configurations, not separate engines

**Dependencies**: REQ-F-EVAL-001.|code⟩ (edge params configure evaluators)

---

### REQ-F-LIFE-001: Full Lifecycle Closure

CI/CD, telemetry, homeostasis, feedback loop, and eco-intent generation.

**Satisfies**: REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008, REQ-LIFE-009, REQ-LIFE-010, REQ-LIFE-011, REQ-LIFE-012, REQ-LIFE-013, REQ-INTENT-003

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩ → |uat⟩

**What converges**:
- CI/CD as graph edge (Code → CI/CD → Running System)
- Telemetry tagged with REQ keys (`req="REQ-*"` as structured field)
- Per-feature observability: latency, error rate, incidents queryable by REQ key
- Homeostasis: is running system within constraint bounds?
- Deviation → new INT-* intent → back into the graph
- Eco-intent: automatic intent generation from ecosystem changes
- Intent events as first-class objects (`intent_raised` with causal chain)
- Signal source classification (7 types: gap, test_failure, refactoring, source_finding, process_gap, runtime_feedback, ecosystem)
- Spec change events (`spec_modified` with trigger traceability, feedback loop detection)
- Protocol enforcement hooks (mandatory side effects verified at every iteration boundary — reflex phase)
- Spec review as gradient check (`delta(workspace, spec) → intents` — stateless, idempotent, affect-triaged)
- Dev observer agent: markdown agent spec triggered by hooks, watches events.jsonl, computes delta(workspace, spec) → intents
- CI/CD observer agent: markdown agent spec triggered after pipeline completion, maps build failures to REQ keys
- Ops observer agent: markdown agent spec on schedule/alert, reads production telemetry, correlates with REQ keys
- All observers are Markov objects: read inputs, emit events, no shared mutable state (actor model — event log is mailbox)

**Dependencies**: REQ-F-ENGINE-001.|code⟩, REQ-F-TRACE-001.|code⟩ (needs graph + REQ key propagation)

---

### REQ-F-SENSE-001: Sensory Systems

Continuous interoceptive and exteroceptive monitoring with affect triage pipeline, running as a long-running service with review boundary for draft-only autonomy.

**Satisfies**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006, REQ-SUPV-003

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Sensory service architecture: long-running service with workspace watcher, monitor scheduler, affect triage
- Interoceptive monitor framework (INTRO-001..007): event freshness, vector stall detection, test health, STATUS freshness, build health, spec/code drift, event log integrity
- Exteroceptive monitor framework (EXTRO-001..004): dependency freshness, CVE scanning, runtime telemetry deviation, API contract changes
- Affect triage pipeline: rule-based + agent-classified (tiered), severity weighting, escalation decision, profile-tunable thresholds
- Homeostatic responses: probabilistic agent generates draft proposals only (no file modifications)
- Review boundary: tool interface separates autonomous sensing from human-approved changes
- New event types: `interoceptive_signal`, `exteroceptive_signal`, `affect_triage`, `draft_proposal` in events.jsonl
- Monitor registry: configurable per project and per projection profile (`sensory_monitors.yml`, `affect_triage.yml`)
- Monitor health: meta-monitoring (senses that sensing has failed)
- Monitor/telemetry separation: Genesis produces events (sensing), genesis_monitor consumes telemetry (observing)

**Dependencies**: REQ-F-LIFE-001.|code⟩ (needs gradient mechanics and event sourcing), REQ-F-EVAL-001.|code⟩ (affect triage uses evaluator pattern)

---

### REQ-F-TOOL-001: Developer Tooling

Plugin architecture, workspace, commands, release, test gap analysis, hooks, scaffolding, snapshots.

**Satisfies**: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-004, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-007, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-TOOL-011, REQ-TOOL-012, REQ-TOOL-013, REQ-TOOL-014, REQ-TOOL-015

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Plugin architecture: installable, discoverable, versioned methodology delivery
- Developer workspace: task tracking, context preservation, git-integrated
- Workflow commands: task CRUD, checkpoint/restore, status/coverage
- Release management: semver, changelog, REQ key coverage in release notes
- Test gap analysis: REQ keys vs tests, uncovered trajectories
- Methodology hooks: commit/transition/session triggers, REQ tag validation
- Project scaffolding: graph config, context dirs, workspace templates
- Context snapshot: immutable session capture for recovery
- Feature views: per-REQ-key cross-artifact status (grep-based traceability)
- Spec/Design boundary enforcement: technology leakage detection, multiple design variants

**Dependencies**: REQ-F-ENGINE-001.|design⟩ (tooling wraps the engine), REQ-F-TRACE-001.|design⟩ (tooling uses REQ keys)

---

### REQ-F-UX-001: User Experience

Two-command UX layer: state-driven routing (Start), project-wide observability (Status), progressive disclosure, automatic feature/edge selection, recovery and self-healing, human gate awareness (escalation notification), edge zoom management.

**Satisfies**: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005, REQ-UX-006, REQ-UX-007

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- State-driven routing: 8-state machine derived from workspace filesystem + event log
- Progressive disclosure: ≤5 inputs at init, constraints deferred to design edge
- Project-wide observability: "you are here" indicators, cross-feature rollup, signals, health
- Automatic feature/edge selection: priority-based selection, topological edge walk
- Recovery and self-healing: detect and guide recovery from inconsistent workspace states
- Human gate awareness: escalation notification channels, pending review queue, zero-query awareness via status
- Edge zoom management: expand edges to sub-graphs, collapse sub-graphs, selective zoom with mandatory waypoints

**Dependencies**: REQ-F-TOOL-001.|design⟩ (UX layer wraps tooling commands), REQ-F-ENGINE-001.|design⟩ (state detection reads graph)

---

### REQ-F-COORD-001: Multi-Agent Coordination

Event-sourced agent coordination: agent identity, feature assignment via claims, work isolation with promotion gates, Markov-aligned parallelism, role-based evaluator authority.

**Satisfies**: REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Agent identity: `agent_id` + `agent_role` on all events, self-declared via registry
- Feature assignment via events: `edge_claim` → serialiser → `edge_started` or `claim_rejected`; no lock files
- Inbox/serialiser: agents emit to private inbox, single-writer serialiser resolves claims and appends to events.jsonl
- Work isolation: agent drafts in `agents/<id>/drafts/`, promotion via evaluator gate + human review
- Markov-aligned parallelism: inner product determines safe parallel assignment
- Role-based authority: roles define convergence scope, escalation for out-of-scope edges

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (event sourcing infrastructure), REQ-F-EVAL-001.|code⟩ (evaluator framework for authority scoping), REQ-F-TOOL-001.|code⟩ (start/status commands need multi-agent awareness)

---

### REQ-F-SUPV-001: IntentEngine Formalization

The universal observer/evaluator composition law — fractal processing on every edge, ambiguity classification, three output types, chaining with affect propagation, consciousness-as-relative.

**Satisfies**: REQ-SUPV-001, REQ-SUPV-002

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- IntentEngine interface: `observer → evaluator → typed_output(reflex.log | specEventLog | escalate)` parameterised by intent+affect
- Ambiguity classification: zero (reflex), bounded nonzero (probabilistic), persistent (escalate) — maps to three evaluator types
- Three output types exhaustively classify all possible observation outcomes — mapped to existing event types
- Observer/evaluator on every edge: every edge traversal is an IntentEngine invocation, producing classified observation + typed output
- Chaining: one unit's output becomes next unit's intent+affect — the supervision hierarchy
- Affect propagation: urgency/valence carried forward and transformed at each level
- Consciousness-as-relative: Level N's escalate = Level N+1's reflex; Level N's reflex.log invisible to Level N+1
- Fractal application table: single iteration → edge → feature → sensory → production → spec review
- Constraint tolerances: every constraint has a measurable threshold; tolerances make the gradient operational; breach → optimization intent

**Dependencies**: REQ-F-ENGINE-001.|design⟩ (IntentEngine composes over the four primitives), REQ-F-EVAL-001.|design⟩ (ambiguity classification maps to evaluator types)

---

### REQ-F-ROBUST-001: Runtime Robustness

Resilient F_P invocation with isolation, timeouts, stall detection, and crash recovery.

**Satisfies**: REQ-ROBUST-001, REQ-ROBUST-002, REQ-ROBUST-003, REQ-ROBUST-007, REQ-ROBUST-008

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- F_P invocation isolation: isolated boundaries for all probabilistic calls
- Supervisor pattern: wall-clock timeout enforcement, stall detection, transient retry
- Crash recovery: engine startup gap detection for abandoned iterations
- Failure event emission: guaranteed emission of classification, duration, and error detail
- Session gap detection: cross-session abandonment events on startup

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (wraps iterate() invocation path), REQ-F-SUPV-001.|design⟩ (failure events feed triage pipeline)

### REQ-F-FP-001: F_P Construct & Batched Evaluate

LLM judgment construction loop for the engine — construct via single claude invocation per edge, then evaluate.

**Satisfies**: REQ-ITER-001, REQ-ITER-002, REQ-ITER-003, REQ-EVAL-002

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- `run_construct()` produces valid artifact via single LLM call per edge (Strategy C unlock)
- `iterate_edge()` calls construct before evaluate when construct=True
- Full 4-edge traversal uses ≤4 LLM calls (vs 37 cold-start calls today)
- Cross-validating hybrid: engine delta_D as hard gate, LLM delta_P as soft construction

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (engine loop, evaluate, emit), REQ-F-EVAL-001.|code⟩ (evaluator framework for F_P agent checks)

### REQ-F-EVOL-001: Spec Evolution Pipeline

The event-sourced pipeline for proposing, reviewing, and promoting new features from homeostasis signals into the specification.

**Satisfies**: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Workspace vector schema enforcement: trajectory fields only (no `satisfies`, no convergence descriptions) — REQ-EVOL-001
- Feature display JOIN: `gen-status` computes ACTIVE (spec+workspace), PENDING (spec only), ORPHAN (workspace only) across `specification/features/` and `.ai-workspace/features/active/` — REQ-EVOL-002
- `feature_proposal` event type: emitted by homeostasis pipeline, event-log-only persistence, fields: `proposal_id` (PROP-{SEQ}), `proposed_feature_id`, `proposed_satisfies`, `trigger_intent_id`, `rationale`, `status: "draft"` — REQ-EVOL-003
- `spec_modified` event type: emitted on any `specification/` change, fields: `file`, `what_changed`, `previous_hash`, `new_hash`, `trigger_event_id`, `trigger_type` — REQ-EVOL-004
- Draft Features Queue: computed from event log as unresolved `feature_proposal` events; surfaced in `gen-status`; promote → appends to `specification/features/`, emits `spec_modified`, inflates workspace trajectory — REQ-EVOL-005

**Phase**: 1 (REQ-EVOL-001, 002, 004) + 2 (REQ-EVOL-003, 005)

**Dependencies**: REQ-F-LIFE-001.|code⟩ (homeostasis pipeline emits proposals), REQ-F-ENGINE-001.|code⟩ (event log infrastructure), REQ-F-TOOL-001.|code⟩ (gen-status JOIN display, gen-review-proposal command)

---

### REQ-F-EVENT-001: Event Stream & Projections

The formal event stream contract — append-only durability, projection semantics, required taxonomy, and saga compensation.

**Satisfies**: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004, REQ-EVENT-005

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Append-only event stream: immutable, ordered, storage-agnostic — REQ-EVENT-001
- Projection contract: Determinism (same stream → same state), Completeness (any prior state reconstructable by replay), Isolation (by `instance_id`); materialised views permitted if kept in sync — REQ-EVENT-002
- Required event taxonomy (aligned with OpenLineage / ADR-S-011): `IterationStarted`, `IterationCompleted`, `IterationFailed`, `EvaluatorVoted`, `ConsensusReached`, `ConvergenceAchieved`, `ContextArrived`; mandatory fields: `instance_id`, `actor`, `timestamp` — REQ-EVENT-003
- Saga invariant: if `IterationFailed(B→C)` after `IterationCompleted(A→B)`, system MUST emit `CompensationTriggered` then `CompensationCompleted(A→B)` before any further `IterationStarted(A→B)` — REQ-EVENT-004

**Note (ADR-S-012 binding)**: REQ-EVENT-002 is the formal expression of ADR-S-012. The MVP implementation passes `asset_content: str` rather than deriving assets by event replay. A design ADR (ADR-025) will record the pragmatic exception and define the 3.x migration path to full event-sourced projection.

**Phase**: 1 (REQ-EVENT-001, 002, 003) + 2 (REQ-EVENT-004)

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (engine emits the stream), REQ-F-ROBUST-001.|code⟩ (failure events are part of the taxonomy)

---

### REQ-F-CONSENSUS-001: CONSENSUS Functor Implementation

Multi-stakeholder F_H evaluator with roster, quorum rule, participation floor, and typed convergence outcomes. Implements ADR-S-025.

**Satisfies**: ADR-S-025 (CONSENSUS functor — multi-party F_H with quorum semantics)

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- Review publication schema with asset_version, config invariant (`review_closes_at >= published_at + min_duration`), roster
- Comment collection with gating snapshot (frozen at `review_closes_at`)
- Vote schema: approve | reject | abstain | non_response (silence ≠ abstain)
- Quorum gate: five deterministic checks (min_duration_elapsed, window_closed, participation_floor_met, quorum_reached, gating_comments_dispositioned)
- Typed outcomes: `consensus_reached` | `consensus_failed` (with failure_reason)
- Three recovery paths: re_open | narrow_scope | abandon
- Seven OL event types emitted across all phases

**Phase**: 2 (after EVAL + TOOL foundation)

**Dependencies**: REQ-F-ENGINE-001.|code⟩ (CONSENSUS invokes iterate()), REQ-F-EVAL-001.|code⟩ (F_H evaluator interface), REQ-F-TOOL-001.|code⟩ (gen-iterate, gen-status, gen-review commands)

**Feature decomposition**: [CONSENSUS_FEATURE_DECOMPOSITION.md](CONSENSUS_FEATURE_DECOMPOSITION.md) — 9 sub-features (8 MVP + CONS-004 deferred)

**Design recommendations**: [CONSENSUS_DESIGN_RECOMMENDATIONS.md](CONSENSUS_DESIGN_RECOMMENDATIONS.md) — 6 design phases

---

### REQ-F-NAMEDCOMP-001: Named Composition Library and Intent Vector Envelope

The five-level compositional stack and intent vector envelope specified in ADR-S-026. Covers: named composition registry, typed gap.intent output, intent vector schema extension, project convergence vocabulary, and PLAN edge parameter template.

**Satisfies**: ADR-S-026 (Named Compositions and Intent Vectors — five-level stack, PLAN/POC/SCHEMA_DISCOVERY/DATA_DISCOVERY, typed gap.intent, intent vector tuple, project convergence vocabulary)

**Trajectory**: |req⟩ → |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩

**What converges**:
- `config/named_compositions.yml` — library registry with 4 macros (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY) + gap_type dispatch table
- `config/feature_vector_template.yml` extended — source_kind, trigger_event, target_asset_type, produced_asset_ref, disposition fields
- `intent_raised` events carry `composition` field: `{macro, version, bindings}` (not free text)
- gen-status: three-state project convergence — ITERATING | QUIESCENT | CONVERGED | BOUNDED
- `config/named_compositions/plan.yml` — shared PLAN edge parameter template behind feature_decomp and design_rec edges
- ~95 new tests across registry, schema, event typing, convergence states, template validation
- NC-006 (composition governance) explicitly deferred — depends on REQ-F-CONSENSUS-001.|code⟩

**Phase**: 2 (after ENGINE, EVAL, TOOL, TRACE — schema touches all of these)

**Dependencies**: REQ-F-ENGINE-001.|code⟩, REQ-F-EVAL-001.|code⟩, REQ-F-TOOL-001.|code⟩, REQ-F-TRACE-001.|code⟩, REQ-F-SENSE-001.|code⟩ (for typed observer output); NC-006 also depends on REQ-F-CONSENSUS-001.|code⟩

**Feature decomposition**: [NAMEDCOMP_FEATURE_DECOMPOSITION.md](NAMEDCOMP_FEATURE_DECOMPOSITION.md) — 6 sub-features (5 MVP + NC-006 deferred)

**Design recommendations**: [NAMEDCOMP_DESIGN_RECOMMENDATIONS.md](NAMEDCOMP_DESIGN_RECOMMENDATIONS.md) — 6 design phases

---

## Dependency Graph

```
REQ-F-ENGINE-001 (Asset Graph Engine)
    │
    ├──→ REQ-F-EVAL-001 (Evaluator Framework)
    │        │
    │        ├──→ REQ-F-EDGE-001 (Edge Parameterisations)
    │        │
    │        ├──→ REQ-F-SUPV-001 (IntentEngine Formalization) ←── also depends on ENGINE
    │        │
    │        └──→ REQ-F-SENSE-001 (Sensory Systems) ←── also depends on LIFE-001
    │
    ├──→ REQ-F-CTX-001 (Context Management)
    │
    ├──→ REQ-F-TRACE-001 (Feature Traceability)
    │        │
    │        └──→ REQ-F-LIFE-001 (Lifecycle Closure)
    │                 │
    │                 └──→ REQ-F-SENSE-001 (Sensory Systems)
    │
    ├──→ REQ-F-ROBUST-001 (Runtime Robustness) ←── ENGINE.|code⟩ + SUPV.|design⟩ (failure event flow)
    │
    └──→ REQ-F-TOOL-001 (Developer Tooling)
              │
              ├──→ REQ-F-UX-001 (User Experience)
              │
              └──→ REQ-F-COORD-001 (Multi-Agent Coordination) ←── also depends on ENGINE, EVAL
    │
    └──→ REQ-F-EVENT-001 (Event Stream & Projections) ←── ENGINE + ROBUST (failure taxonomy)
              │
              └──→ REQ-F-EVOL-001 (Spec Evolution Pipeline) ←── also depends on LIFE-001, TOOL-001

REQ-F-EVAL-001 + REQ-F-TOOL-001 + REQ-F-ENGINE-001
    └──→ REQ-F-CONSENSUS-001 (CONSENSUS Functor) ←── Phase 2: multi-stakeholder F_H

REQ-F-ENGINE-001 + REQ-F-EVAL-001 + REQ-F-TOOL-001 + REQ-F-TRACE-001 + REQ-F-SENSE-001
    └──→ REQ-F-NAMEDCOMP-001 (Named Compositions + Intent Vectors) ←── Phase 2: Level 3 macro layer
              │
              (NC-006 also depends on REQ-F-CONSENSUS-001.|code⟩ — deferred)
```

**Parallel work** (zero inner product — independent once ENGINE.|design⟩ converges):
- REQ-F-EVAL-001 ∥ REQ-F-CTX-001 ∥ REQ-F-TRACE-001 ∥ REQ-F-ROBUST-001 ∥ REQ-F-EVENT-001

**Sequential constraints**:
- ENGINE.|design⟩ < EVAL.|code⟩ (evaluators need engine interface)
- ENGINE.|design⟩ < CTX.|code⟩ (context needs engine interface)
- EVAL.|code⟩ < EDGE.|code⟩ (edge params configure evaluators)
- TRACE.|code⟩ < LIFE.|code⟩ (lifecycle needs REQ key propagation)
- LIFE.|code⟩ + EVAL.|code⟩ < SENSE.|code⟩ (sensory systems need gradient mechanics + evaluator pattern)
- ENGINE.|design⟩ + TRACE.|design⟩ < TOOL.|code⟩ (tooling wraps both)
- ENGINE.|code⟩ < ROBUST.|code⟩ (robustness wraps iterate() invocation path)
- ENGINE.|code⟩ + ROBUST.|code⟩ < EVENT.|code⟩ (event stream needs engine + failure taxonomy)
- LIFE.|code⟩ + EVENT.|code⟩ + TOOL.|code⟩ < EVOL.|code⟩ (spec evolution needs homeostasis + event stream + gen-status/gen-review commands)
- EVAL.|code⟩ + TOOL.|code⟩ + ENGINE.|code⟩ < CONSENSUS.|code⟩ (CONSENSUS functor wraps F_H evaluator + iterate() + gen-review)
- ENGINE.|code⟩ + EVAL.|code⟩ + TOOL.|code⟩ + TRACE.|code⟩ < NAMEDCOMP.|code⟩ (named compositions touch schema, events, commands, and engine)
- SENSE.|code⟩ < NAMEDCOMP.|code⟩ (typed observer intent_raised requires affect_triage and gap_type resolution)
- CONSENSUS.|code⟩ < NAMEDCOMP-NC006.|code⟩ (composition governance gate requires CONSENSUS functor)

---

## Task Graph (Compressed)

```
Phase 1a: ENGINE |feat_decomp⟩ → |design⟩ → |mod_decomp⟩ → |basis_proj⟩ → |code⟩ ↔ |tests⟩
                                    ↓
          ROBUST |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  (∥ with EVAL/CTX/TRACE once ENGINE.|design⟩)
                                    ↓
Phase 1b: EVAL   |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  ┐
          CTX    |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  ├ parallel
          TRACE  |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  ┘
          SUPV   |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩
                    ↓                                       ↓
Phase 1c: EDGE   |code⟩ ↔ |tests⟩              TOOL |code⟩ ↔ |tests⟩
          UX     |code⟩ ↔ |tests⟩  (∥ EDGE)
                                                            ↓
Phase 1b: EVENT  |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  (∥ EVAL/CTX/TRACE — depends on ENGINE)
                    ↓
Phase 2:  LIFE   |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩ → |uat⟩
          COORD  |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  (∥ LIFE)
          EVOL   |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩  (∥ LIFE — depends on LIFE + EVENT + TOOL)
                    ↓
Phase 3:  SENSE  |feat_decomp⟩ → |design⟩ → ... → |code⟩ ↔ |tests⟩
```

Note: `...` abbreviates `|mod_decomp⟩ → |basis_proj⟩ →` for readability.

ENGINE design is the critical path. Once it converges, four features parallelise (EVAL, CTX, TRACE, ROBUST).

---

## Coverage Check

| Implementation Requirement | Feature Vector |
|---------------------------|---------------|
| REQ-INTENT-001 | REQ-F-TRACE-001 |
| REQ-INTENT-002 | REQ-F-TRACE-001 |
| REQ-INTENT-003 | REQ-F-LIFE-001 |
| REQ-INTENT-004 | REQ-F-CTX-001 |
| REQ-GRAPH-001 | REQ-F-ENGINE-001 |
| REQ-GRAPH-002 | REQ-F-ENGINE-001 |
| REQ-GRAPH-003 | REQ-F-ENGINE-001 |
| REQ-ITER-001 | REQ-F-ENGINE-001 |
| REQ-ITER-002 | REQ-F-ENGINE-001 |
| REQ-ITER-003 | REQ-F-ENGINE-001 |
| REQ-EVAL-001 | REQ-F-EVAL-001 |
| REQ-EVAL-002 | REQ-F-EVAL-001 |
| REQ-EVAL-003 | REQ-F-EVAL-001 |
| REQ-CTX-001 | REQ-F-CTX-001 |
| REQ-CTX-002 | REQ-F-CTX-001 |
| REQ-FEAT-001 | REQ-F-TRACE-001 |
| REQ-FEAT-002 | REQ-F-TRACE-001 |
| REQ-FEAT-003 | REQ-F-TRACE-001 |
| REQ-LIFE-001 | REQ-F-LIFE-001 |
| REQ-LIFE-002 | REQ-F-LIFE-001 |
| REQ-LIFE-003 | REQ-F-LIFE-001 |
| REQ-EDGE-001 | REQ-F-EDGE-001 |
| REQ-EDGE-002 | REQ-F-EDGE-001 |
| REQ-EDGE-003 | REQ-F-EDGE-001 |
| REQ-EDGE-004 | REQ-F-EDGE-001 |
| REQ-TOOL-001 | REQ-F-TOOL-001 |
| REQ-TOOL-002 | REQ-F-TOOL-001 |
| REQ-TOOL-003 | REQ-F-TOOL-001 |
| REQ-TOOL-004 | REQ-F-TOOL-001 |
| REQ-TOOL-005 | REQ-F-TOOL-001 |
| REQ-TOOL-006 | REQ-F-TOOL-001 |
| REQ-TOOL-007 | REQ-F-TOOL-001 |
| REQ-TOOL-008 | REQ-F-TOOL-001 |
| REQ-TOOL-009 | REQ-F-TOOL-001 |
| REQ-TOOL-010 | REQ-F-TOOL-001 |
| REQ-TOOL-011 | REQ-F-TOOL-001 |
| REQ-TOOL-012 | REQ-F-TOOL-001 |
| REQ-TOOL-013 | REQ-F-TOOL-001 |
| REQ-TOOL-014 | REQ-F-TOOL-001 |
| REQ-LIFE-004 | REQ-F-LIFE-001 |
| REQ-LIFE-005 | REQ-F-LIFE-001 |
| REQ-LIFE-006 | REQ-F-LIFE-001 |
| REQ-LIFE-007 | REQ-F-LIFE-001 |
| REQ-LIFE-008 | REQ-F-LIFE-001 |
| REQ-LIFE-009 | REQ-F-LIFE-001 |
| REQ-LIFE-010 | REQ-F-LIFE-001 |
| REQ-LIFE-011 | REQ-F-LIFE-001 |
| REQ-LIFE-012 | REQ-F-LIFE-001 |
| REQ-LIFE-013 | REQ-F-LIFE-001 |
| REQ-SENSE-001 | REQ-F-SENSE-001 |
| REQ-SENSE-002 | REQ-F-SENSE-001 |
| REQ-SENSE-003 | REQ-F-SENSE-001 |
| REQ-SENSE-004 | REQ-F-SENSE-001 |
| REQ-SENSE-005 | REQ-F-SENSE-001 |
| REQ-SENSE-006 | REQ-F-SENSE-001 |
| REQ-UX-001 | REQ-F-UX-001 |
| REQ-UX-002 | REQ-F-UX-001 |
| REQ-UX-003 | REQ-F-UX-001 |
| REQ-UX-004 | REQ-F-UX-001 |
| REQ-UX-005 | REQ-F-UX-001 |
| REQ-UX-006 | REQ-F-UX-001 |
| REQ-UX-007 | REQ-F-UX-001 |
| REQ-COORD-001 | REQ-F-COORD-001 |
| REQ-COORD-002 | REQ-F-COORD-001 |
| REQ-COORD-003 | REQ-F-COORD-001 |
| REQ-COORD-004 | REQ-F-COORD-001 |
| REQ-COORD-005 | REQ-F-COORD-001 |
| REQ-SUPV-001 | REQ-F-SUPV-001 |
| REQ-SUPV-002 | REQ-F-SUPV-001 |
| REQ-SUPV-003 | REQ-F-SENSE-001 |
| REQ-ROBUST-001 | REQ-F-ROBUST-001 |
| REQ-ROBUST-002 | REQ-F-ROBUST-001 |
| REQ-ROBUST-003 | REQ-F-ROBUST-001 |
| REQ-ROBUST-007 | REQ-F-ROBUST-001 |
| REQ-ROBUST-008 | REQ-F-ROBUST-001 |
| REQ-EVOL-001 | REQ-F-EVOL-001 |
| REQ-EVOL-002 | REQ-F-EVOL-001 |
| REQ-EVOL-003 | REQ-F-EVOL-001 |
| REQ-EVOL-004 | REQ-F-EVOL-001 |
| REQ-EVOL-005 | REQ-F-EVOL-001 |
| REQ-EVENT-001 | REQ-F-EVENT-001 |
| REQ-EVENT-002 | REQ-F-EVENT-001 |
| REQ-EVENT-003 | REQ-F-EVENT-001 |
| REQ-EVENT-004 | REQ-F-EVENT-001 |
| REQ-EVENT-005 | REQ-F-EVENT-001 |
| REQ-TOOL-015 | REQ-F-TOOL-001 |
| **85/85 requirements covered. No orphans.**

---

## Summary

| Feature Vector | Impl Reqs | Phase | Dependencies |
|---------------|-----------|-------|-------------|
| REQ-F-ENGINE-001 | 6 | 1a | None |
| REQ-F-EVAL-001 | 3 | 1b | ENGINE |
| REQ-F-CTX-001 | 3 | 1b | ENGINE |
| REQ-F-TRACE-001 | 5 | 1b | ENGINE, CTX |
| REQ-F-EDGE-001 | 4 | 1c | EVAL |
| REQ-F-LIFE-001 | 13 | 2 | ENGINE, TRACE |
| REQ-F-SENSE-001 | 7 | 3 | LIFE, EVAL |
| REQ-F-TOOL-001 | 14 | 1c | ENGINE, TRACE |
| REQ-F-UX-001 | 7 | 1c | TOOL, ENGINE |
| REQ-F-COORD-001 | 5 | 2 | ENGINE, EVAL, TOOL |
| REQ-F-SUPV-001 | 2 | 1b | ENGINE, EVAL |
| REQ-F-ROBUST-001 | 5 | 1a | ENGINE |
| REQ-F-EVENT-001 | 4 | 1b+2 | ENGINE, ROBUST |
| REQ-F-EVOL-001 | 5 | 1+2 | LIFE, EVENT, TOOL |
| REQ-F-FP-001 | 4 | 2 | ENGINE, EVAL |
| **Total** | **83** | | |

15 feature vectors. 83 implementation requirements. Full coverage. Critical path: ENGINE design.
