# AI SDLC — MVP Scenarios

**Version**: 1.0.0
**Date**: 2026-02-23
**Derived From**: [AI_SDLC_ASSET_GRAPH_MODEL.md](AI_SDLC_ASSET_GRAPH_MODEL.md) (v2.8.0), [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md) (v3.11.0)
**Purpose**: End-to-end user scenarios that exercise the methodology as a product. Each scenario is a gap-analysis driver — mismatches between the scenario and the current implementation surface work items.

---

## Relationship to Other Spec Documents

| Document | What it specifies | This document's relationship |
|----------|------------------|------------------------------|
| [AI_SDLC_ASSET_GRAPH_MODEL.md](AI_SDLC_ASSET_GRAPH_MODEL.md) | The formal system (constraints, invariants, symmetries) | Scenarios must be **satisfiable** within the formal system |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | Platform-agnostic WHAT | Scenarios exercise requirements end-to-end; gaps drive new REQ keys |
| [UAT_TEST_CASES.md](UAT_TEST_CASES.md) | Exhaustive functional use cases per REQ key | Scenarios here are **cross-cutting** — each touches many REQ keys simultaneously |
| [FEATURE_VECTORS.md](FEATURE_VECTORS.md) | Feature decomposition | Scenarios may reveal missing feature vectors |
| [PROJECTIONS_AND_INVARIANTS.md](PROJECTIONS_AND_INVARIANTS.md) | Projection profiles and vector types | Scenarios exercise specific profiles end-to-end |

**This document is a gap amplifier.** Where UAT_TEST_CASES.md validates individual requirements in isolation, MVP scenarios validate that requirements compose into coherent user journeys. A scenario that cannot be completed exposes integration gaps — missing glue, unspecified transitions, implicit assumptions.

---

## Scenario Format

Each scenario follows this structure:

```
### SC-{NNN}: {Title}

**Profile**: {projection profile}
**Actor**: {who is performing the scenario}
**Precondition**: {starting state}
**REQ Keys Exercised**: {list of REQ keys touched}

#### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | ... | ... | REQ-* | COVERED / GAP-{id} |

#### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-{id} | ... | ... | REQ key or spec update |

#### Invariant Checks

Which of the 4 invariants (Projections doc §2) does this scenario exercise?
- [ ] Evaluator Existence
- [ ] Markov Property
- [ ] Convergence Monotonicity
- [ ] IntentEngine Composition
```

---

## SC-001: First-Time Developer — Green Field to Running System

**Profile**: standard
**Actor**: Developer with no prior Genesis experience, has a new project idea
**Precondition**: Developer has an empty directory and a development environment (Python, git). Genesis tooling is installed.
**REQ Keys Exercised**: REQ-INTENT-001, REQ-INTENT-002, REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005, REQ-GRAPH-001, REQ-GRAPH-002, REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003, REQ-CTX-001, REQ-CTX-002, REQ-FEAT-001, REQ-FEAT-002, REQ-EDGE-001, REQ-EDGE-002, REQ-EDGE-003, REQ-EDGE-004, REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004, REQ-LIFE-005, REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-004, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-SUPV-001, REQ-SUPV-002, REQ-SENSE-001, REQ-SENSE-002

This is the canonical end-to-end scenario. A developer takes a project from nothing to a running, monitored system using only Genesis tooling. Every edge of the standard profile graph is traversed.

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Install Genesis** — single command installs methodology tooling into a development environment | Tooling available, version verifiable, commands/agents/configs loaded | REQ-TOOL-001 | GAP-001 |
| 2 | **Start in empty directory** — `genesis start` (or `/gen-start`) | Progressive init: detect project name, language, test runner. Ask 5 questions. Create `.ai-workspace/`, write `project_constraints.yml` (mandatory dimensions deferred), emit `project_initialized` event. | REQ-UX-001, REQ-UX-002, REQ-TOOL-003 | COVERED (spec: `/gen-start` Step 1, `/gen-init`) |
| 3 | **Describe intent** — "I want to build a REST API for task management with user authentication" | Write `specification/INTENT.md` with structured template. Emit `intent_raised` event with `INT-001`. State transitions to `NO_FEATURES`. | REQ-INTENT-001, REQ-INTENT-002, REQ-LIFE-005 | COVERED (spec: `/gen-start` Step 3) |
| 4 | **System creates feature vectors** — `genesis start` (auto-continues) | Parse intent, propose feature decomposition (e.g., REQ-F-AUTH-001, REQ-F-TASK-001, REQ-F-API-001). Create feature vector files in `features/active/`. Emit `spawn_created` events. State transitions to `IN_PROGRESS`. | REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003, REQ-TOOL-004 | GAP-002 |
| 5 | **Iterate intent→requirements** — `genesis start` (selects closest-to-complete feature, determines edge) | Load intent, generate structured requirements with REQ-F-* and REQ-NFR-* keys. Run evaluator checklist (completeness, format, gap check). Present for human review via gradient check (completeness, fidelity, boundary). Human approves. Edge converges. Emit `iteration_completed`, `edge_converged` events. | REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003, REQ-GRAPH-002 | GAP-003 |
| 6 | **Iterate requirements→design** — `genesis start` (next unconverged edge) | Prompt for mandatory constraint dimensions (ecosystem, deployment, security, build). Generate ADRs binding technology decisions. Produce design document with `Implements: REQ-*` tags. Run gradient check. Human approves. Edge converges. | REQ-CTX-001, REQ-CTX-002, REQ-EDGE-003, REQ-UX-002, REQ-EVAL-003 | GAP-003 |
| 7 | **Iterate design→code + code↔unit_tests** — `genesis start` (enters TDD co-evolution) | Scaffold project structure. Enter TDD cycle: write failing test (`Validates: REQ-*`), write code (`Implements: REQ-*`), refactor. Repeat until all REQ keys have tests. Deterministic evaluators (compile, lint, test pass). Edge converges. | REQ-EDGE-001, REQ-EDGE-004, REQ-ITER-001, REQ-EVAL-001 | GAP-003 |
| 8 | **Iterate code→uat_tests** — `genesis start` | Generate BDD acceptance tests from requirements. Run against constructed code. Deterministic + agent evaluators. Edge converges. | REQ-EDGE-002, REQ-EVAL-002 | GAP-003 |
| 9 | **Iterate uat_tests→cicd** — `genesis start` | Generate CI/CD pipeline configuration (GitHub Actions / similar). Wire test suites. Run pipeline. Deterministic evaluator (pipeline passes). Edge converges. | REQ-LIFE-001 | GAP-003 |
| 10 | **Iterate cicd→running_system→telemetry** — `genesis start` | Deploy (or simulate deployment). Add telemetry tagging (`req="REQ-*"` in logs/metrics). Verify running system emits feature-keyed telemetry. Edge converges. | REQ-LIFE-002, REQ-LIFE-004 | GAP-003 |
| 11 | **Observe running system** — genesis_monitor dashboard | Open `genesis-monitor --watch-dir .ai-workspace --port 8000`. See real-time dashboard: feature progress, convergence Gantt, event stream, regime classification (reflex/conscious), consciousness loop signals. Telemetry deviations surface as `intent_raised` events, closing the feedback loop. | REQ-LIFE-003, REQ-SENSE-001, REQ-SENSE-002, REQ-SUPV-001 | PARTIAL (genesis_monitor exists but schema-stale — see GAP-004) |

### Post-Condition

- All features converged across all standard profile edges
- `events.jsonl` contains complete audit trail
- Feature vector trajectories show REQ key traceability from intent to telemetry
- `genesis-monitor` displays full Gantt, convergence, and consciousness loop
- `/gen-gaps` reports Layer 1 (tags) and Layer 2 (tests) at 100%
- `/gen-status` shows `ALL_CONVERGED` state

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-001 | **No installability requirement.** REQ-TOOL-001 says "tooling exists" but doesn't require that the tooling be installable via a single command into any project. v1.x had this (curl installer + marketplace registration) but the v2 spec dropped it. A methodology that cannot be installed into a project is not usable — installability is a spec-level constraint, not a design detail. | Step 1 has no spec backing. Users must manually configure IDE settings and copy files. | New REQ key (e.g., REQ-TOOL-011: "Tooling must be installable into any project directory via a single platform-appropriate command. Installation must be idempotent, preserve existing work, and emit a `project_initialized` event.") |
| GAP-002 | **No automated feature decomposition from intent.** `/gen-spawn` creates one feature at a time. No agent parses intent into multiple feature proposals automatically. | Step 4 requires manual feature creation — workable but not the seamless UX this scenario describes. | REQ-FEAT-001, REQ-UX-001. Consider: should `/gen-start` in `NO_FEATURES` state offer "auto-decompose intent into features"? |
| GAP-003 | **No executable orchestration engine.** The iterate agent (`gen-iterate.md`), commands, and hooks are specification-grade markdown + YAML. There is no runtime that executes `iterate(Asset, Context[], Evaluators) → Asset'` as a function call. The "system response" column describes intended behaviour, not current behaviour. | Steps 5-10 require a human-in-the-loop manually invoking `/gen-start` in an IDE with the specs loaded as context. The agent interprets the specs and acts accordingly — but this is F_P (probabilistic) execution of what should be F_D (deterministic) orchestration. | Central gap. Addressed by Phase 2 of implementation. Two paths: (a) build a Python runtime engine that reads configs and orchestrates, or (b) accept that the LLM-as-runtime IS the engine (F_P encoding) and focus on making the specs precise enough that any LLM can execute them reliably. Path (b) is the current de facto architecture. |
| GAP-004 | **genesis_monitor schema drift.** The monitor (v2.5) recognises 9 event types. Current methodology (v2.8/3.0) emits 12+ types. Field structures have drifted for `edge_converged` (expects `convergence_time`, gets `iteration` + `convergence_type`) and `iteration_completed` (expects flat evaluator map, gets nested object). 4 new event types (`edge_started`, `exteroceptive_signal`, `gaps_validated`, `release_created`) render as raw untyped JSON. | Dashboard displays incomplete/degraded information. Not broken (graceful fallback) but not showing full methodology state. | genesis_monitor upgrade. ~2-3h estimated. Add 4 event types, update 3 field extractors. |

### Invariant Checks

- [x] **Evaluator Existence** — Every edge traversal (steps 5-10) invokes at least one evaluator
- [x] **Markov Property** — Each step depends only on current asset state, not history of how we got there
- [x] **Convergence Monotonicity** — Delta decreases monotonically within each edge (or stuck detection triggers)
- [x] **IntentEngine Composition** — Step 11 closes the loop: telemetry deviation → intent_raised → back to step 5

### Gap Analysis Summary

```
Steps:       11
COVERED:      2 (steps 2, 3 — init + intent authoring)
GAP-001:      1 (step 1 — no installability requirement)
GAP-002:      1 (step 4 — no auto-decomposition)
GAP-003:      6 (steps 5-10 — no executable engine)
PARTIAL:      1 (step 11 — genesis_monitor exists but stale)

Methodology completeness: 18% of this scenario executable today
                          (rising to ~27% if genesis_monitor is updated)
```

---

## SC-002: Returning Developer — Resume Work After Context Loss

**Profile**: standard
**Actor**: Developer who worked on a project yesterday, closed their IDE, and returns today with no memory of where they left off
**Precondition**: `.ai-workspace/` exists with 3 features at various stages. `events.jsonl` has ~50 events. No IDE state preserved.
**REQ Keys Exercised**: REQ-UX-001, REQ-UX-003, REQ-UX-004, REQ-UX-005, REQ-TOOL-002, REQ-TOOL-009, REQ-GRAPH-003, REQ-SUPV-001

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Open project** — `cd my-project && genesis start` | SessionStart hook fires: validate event log integrity, check feature vector consistency, detect staleness. Report health status. | REQ-UX-005, REQ-TOOL-002 | COVERED (spec: `on-session-start.sh`, `/gen-start` Step 0) |
| 2 | **State detection** — (automatic, part of start) | Detect state: `IN_PROGRESS`. Display: 3 features, 1 converged, 1 at code↔tests, 1 at requirements. Show "you are here" indicators. Select closest-to-complete feature. | REQ-UX-001, REQ-UX-003, REQ-GRAPH-003 | COVERED (spec: `/gen-start` Step 5, `/gen-status`) |
| 3 | **Check status for detail** — `genesis status` (or `/gen-status`) | Show feature trajectories with convergence markers (checkmark/dot/circle). Project rollup: edges converged, features by status, unactioned signals. Gantt chart. | REQ-TOOL-002, REQ-TOOL-009, REQ-UX-003 | COVERED (spec: `/gen-status`) |
| 4 | **Resume iteration** — (automatic from step 1, or `genesis start` again) | Load feature context (prior events, evaluator history, context hash). Resume iteration on the selected edge. Asset state is reconstructed from events, not from memory. | REQ-UX-004, REQ-GRAPH-003 | GAP-003 |
| 5 | **Check what's blocking** — if features are blocked, user sees why | Display blocked features with reasons (spawn dependency, pending human review). Recommend unblocking action. | REQ-UX-005, REQ-SUPV-001 | COVERED (spec: `/gen-start` Step 8, `/gen-escalate`) |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine (same as SC-001) | Step 4 requires LLM interpretation of specs | Phase 2 |

### Invariant Checks

- [ ] Evaluator Existence — not directly tested (no iteration in this scenario's core path)
- [x] **Markov Property** — Central to this scenario: state is derived from filesystem + events, not from session memory
- [ ] Convergence Monotonicity — tested only if step 4 completes an iteration
- [ ] IntentEngine Composition — not directly tested

---

## SC-003: Stuck Feature — Escalation and Recovery

**Profile**: standard
**Actor**: Developer whose feature has been iterating on the same edge with no progress
**Precondition**: REQ-F-AUTH-001 on `code↔unit_tests` edge. Delta=3 unchanged for 4 consecutive iterations (above `stuck_threshold=3`). 3 failing checks: `test_coverage_minimum`, `all_req_keys_have_tests`, `no_secrets_in_code`.
**REQ Keys Exercised**: REQ-UX-005, REQ-SUPV-001, REQ-SUPV-002, REQ-LIFE-005, REQ-LIFE-006, REQ-FEAT-002, REQ-FEAT-003, REQ-ITER-003

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Start** — `genesis start` | State detection: `STUCK`. Display stuck feature with delta history and failing checks. | REQ-UX-005, REQ-SUPV-001 | COVERED (spec: `/gen-start` Step 7) |
| 2 | **View escalation queue** — `genesis escalate` (or `/gen-escalate`) | Build queue from events: 1 stuck feature (critical), 0 tolerance breaches, 0 unactioned intents. Display with context and recommended actions. | REQ-SUPV-001, REQ-SUPV-002 | COVERED (spec: `/gen-escalate` Steps 1-2) |
| 3 | **Choose: spawn discovery vector** — user selects option 1 | Emit `intent_raised` (trigger: stuck_escalation). Create discovery vector: REQ-F-SPIKE-AUTH-001 with `parent: REQ-F-AUTH-001`. Discovery vector uses `spike` profile (reduced convergence). Emit `spawn_created`. | REQ-FEAT-002, REQ-LIFE-005, REQ-FEAT-003 | GAP-003 |
| 4 | **Investigate via spike** — `genesis start` (routes to discovery vector) | Discovery vector iterates: investigate root cause (e.g., test is checking wrong module path, or requirement is ambiguous). Produce spike report. Spike converges. | REQ-ITER-003 | GAP-003 |
| 5 | **Fold back findings** — discovery vector completes | Fold spike outputs back to parent feature. Update parent's context with findings. Emit `spawn_folded_back`. Resume parent iteration with new context. Delta decreases. | REQ-FEAT-002, REQ-LIFE-005 | GAP-003 |
| 6 | **Parent unsticks** — `genesis start` continues | Parent feature iterates with enriched context. Failing checks resolve. Delta reaches 0. Edge converges. | REQ-ITER-001, REQ-ITER-002 | GAP-003 |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine | Steps 3-6 require orchestration | Phase 2 |
| GAP-005 | **No automated root-cause investigation.** The spike profile is defined, but no agent specialises in diagnosing why a feature is stuck. Currently the human must investigate manually. | Discovery vectors are a framework without a diagnostic engine. | Consider: should the `spike` profile's iterate agent include diagnostic heuristics (check evaluator output, diff last N iterations, identify unchanged failing checks)? |

### Invariant Checks

- [x] **Evaluator Existence** — stuck detection is itself an evaluator (meta-level)
- [x] **Markov Property** — spike depends only on current state of parent + failing checks, not on how the parent got stuck
- [x] **Convergence Monotonicity** — tested: delta was stuck, then decreases after fold-back
- [x] **IntentEngine Composition** — stuck → escalate → intent_raised → spawn → fold-back → resume

---

## SC-004: Multi-Feature Coordination — Parallel Work with Dependencies

**Profile**: standard
**Actor**: Developer working on 3 features where REQ-F-API-001 depends on REQ-F-DB-001 (database schema needed for API implementation)
**Precondition**: 3 features active. REQ-F-DB-001 at `design→code`. REQ-F-API-001 at `requirements→design` (blocked on DB schema). REQ-F-UI-001 at `design→code` (independent).
**REQ Keys Exercised**: REQ-FEAT-002, REQ-FEAT-003, REQ-UX-004, REQ-COORD-001, REQ-COORD-002, REQ-COORD-003, REQ-COORD-004, REQ-COORD-005

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Start** — `genesis start` | State: `IN_PROGRESS`. Feature selection: REQ-F-DB-001 (closest-to-complete AND blocks REQ-F-API-001). Display dependency graph. | REQ-UX-004, REQ-FEAT-002 | COVERED (spec: `/gen-start` Step 5a) |
| 2 | **Complete DB schema** — iterate through `design→code`, `code↔unit_tests` | DB feature converges. Emit `edge_converged` for each edge. PostEvent hook fires dev-observer. | REQ-ITER-001, REQ-ITER-002 | GAP-003 |
| 3 | **Dependency unblocks** — `genesis start` (re-routes) | REQ-F-API-001 dependency resolved. Feature selection shifts: now either API (dependency just resolved) or UI (independent, also close to complete). System explains routing decision. | REQ-FEAT-002, REQ-FEAT-003 | COVERED (spec: `/gen-start` Step 5a priority tiers) |
| 4 | **Status check** — `genesis status` | Show: DB converged, API unblocked and in-progress, UI in-progress. Gantt shows parallel tracks. "You are here" shows three features at different positions. | REQ-TOOL-002, REQ-UX-003 | COVERED (spec: `/gen-status`) |
| 5 | **Multi-agent coordination** — (if multi-agent enabled) | Each feature claims edges via event-sourced assignment. No two agents work the same edge. Work isolation via separate staging areas. | REQ-COORD-001 through REQ-COORD-005 | GAP-006 |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine | Steps 2, 3 require orchestration | Phase 2 |
| GAP-006 | **Multi-agent coordination is spec-only.** ADR-013 defines the architecture (immutable events, inbox staging, serialiser) but no runtime implements it. Single-agent sequential operation is the current reality. | Step 5 is aspirational. Does not block single-developer use. | REQ-COORD-001 through REQ-COORD-005. Deferred to Phase 3 (post-executable-engine). |

### Invariant Checks

- [x] **Evaluator Existence** — each edge traversal has evaluators
- [x] **Markov Property** — API feature depends on DB feature's converged state, not on how DB converged
- [ ] Convergence Monotonicity — not the focus of this scenario
- [ ] IntentEngine Composition — not directly tested

---

## SC-005: Spec-Boundary Review — Human Gate at Requirements→Design

**Profile**: full
**Actor**: Tech lead reviewing a developer's design against requirements
**Precondition**: REQ-F-AUTH-001 has converged requirements. Design document drafted. `requirements→design` edge at iteration 1. `human_required: true` for this edge.
**REQ Keys Exercised**: REQ-EVAL-003, REQ-EDGE-003, REQ-CTX-001, REQ-CTX-002, REQ-LIFE-005, REQ-UX-006

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Auto-mode pauses** — `genesis start --auto` reaches human gate | Auto-mode detects `human_required: true` on `requirements→design`. Pauses. Announces: "Human gate: requirements→design requires spec-boundary review." | REQ-UX-006, REQ-EVAL-003 | COVERED (spec: `/gen-start` Step 9) |
| 2 | **Invoke spec review** — `genesis spec-review --feature REQ-F-AUTH-001 --edge requirements→design` | Load source (requirements) and target (design). Run gradient check: completeness (REQ key mapping), fidelity (intent preservation), boundary (no spec-level violations in design). Present structured review. | REQ-EVAL-003, REQ-EDGE-003 | COVERED (spec: `/gen-spec-review` Steps 2-3) |
| 3 | **Reviewer finds gap** — "REQ-F-AUTH-002 has no design binding" | Completeness gradient shows 4/5 REQ keys covered (80%). Fidelity shows REQ-F-AUTH-003 weakened ("error handling requirement softened"). Boundary clean. | REQ-CTX-001 | COVERED (spec: `/gen-spec-review` Step 2a) |
| 4 | **Reviewer chooses: Refine** — provides specific feedback | Record decision in feature vector: `human.decision: refined`, feedback text, gradient scores. Emit `review_completed` event. Edge does NOT converge — returns to iterate with feedback as context. | REQ-EVAL-003, REQ-LIFE-005 | GAP-003 |
| 5 | **Design iterates with feedback** — `genesis start` | Iterate agent reads previous feedback from feature vector. Produces revised design addressing gaps. Re-runs gradient check. Delta decreases. | REQ-ITER-001, REQ-ITER-002 | GAP-003 |
| 6 | **Second review — approve** | All gradients pass. Reviewer approves. Edge converges. Emit `review_completed` + `edge_converged`. | REQ-EVAL-003, REQ-ITER-002 | GAP-003 |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine | Steps 4-6 require orchestration | Phase 2 |

### Invariant Checks

- [x] **Evaluator Existence** — human evaluator is the focus
- [x] **Markov Property** — review depends on current design + requirements, not iteration history
- [x] **Convergence Monotonicity** — delta decreases from iteration 1 to iteration 2
- [x] **IntentEngine Composition** — not tested (review is within an edge, not cross-edge feedback)

---

## SC-006: Projection Switch — From Standard to Spike Mid-Flight

**Profile**: standard → spike
**Actor**: Developer who discovers mid-project that a requirement needs feasibility investigation before full implementation
**Precondition**: REQ-F-ML-001 "ML prediction engine" at `design→code` edge. Developer realises the ML approach may not work and wants to spike it first.
**REQ Keys Exercised**: REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003, REQ-ITER-003, REQ-TOOL-004, REQ-LIFE-005

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Recognise uncertainty** — developer decides to spike | User invokes: `genesis spawn --type spike --parent REQ-F-ML-001 --reason feasibility` | REQ-FEAT-002, REQ-TOOL-004 | COVERED (spec: `/gen-spawn`) |
| 2 | **Spike created** — system switches profile | Create spike vector with `spike` profile (code + unit_tests only, relaxed convergence, time-boxed). Parent feature paused at `design→code`. Emit `spawn_created`. | REQ-FEAT-001, REQ-ITER-003 | COVERED (spec: `/gen-spawn`, feature vector template) |
| 3 | **Spike iterates** — `genesis start` routes to spike | Spike uses reduced graph: skip intent→requirements→design, go straight to code↔unit_tests. Evaluate feasibility: does the ML approach work? Time-box: 4 hours. | REQ-FEAT-003, REQ-ITER-001 | GAP-003 |
| 4 | **Spike concludes** — time-box expires or converges | Spike produces: feasibility report, prototype code, go/no-go recommendation. Emit `iteration_completed` with spike metadata. | REQ-ITER-002 | GAP-003 |
| 5 | **Fold back to parent** — `genesis fold-back` (or automatic) | Fold spike outputs into parent context. If go: parent resumes with prototype as starting point. If no-go: parent's design pivots (emits `intent_raised` for alternative approach). Emit `spawn_folded_back`. | REQ-FEAT-002, REQ-LIFE-005 | GAP-003 |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine | Steps 3-5 require orchestration | Phase 2 |
| GAP-007 | **No fold-back command.** `/gen-spawn` creates vectors but there is no `/gen-fold-back` command to merge spike outputs back to the parent. The iterate agent spec mentions fold-back conceptually but no command implements it. | Spike lifecycle is incomplete — creation without completion. | New command: `/gen-fold-back`. Add to commands/. Update graph_topology.yml if needed. |

### Invariant Checks

- [x] **Evaluator Existence** — spike has evaluators (even if relaxed)
- [x] **Markov Property** — spike depends on current parent state, not parent history
- [ ] Convergence Monotonicity — spike may use time-box convergence (not delta-based)
- [x] **IntentEngine Composition** — no-go result → intent_raised → design pivot

---

## SC-007: Telemetry Feedback — Production Anomaly Closes the Loop

**Profile**: full
**Actor**: Operations engineer monitoring a running system built with Genesis
**Precondition**: System deployed and emitting feature-keyed telemetry (`req="REQ-F-AUTH-001"` in logs/metrics). `genesis-monitor` watching `.ai-workspace/`.
**REQ Keys Exercised**: REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004, REQ-SENSE-001, REQ-SENSE-002, REQ-SUPV-001, REQ-SUPV-002, REQ-INTENT-003

### Steps

| # | User Action | System Response | REQ Keys | Gap Status |
|---|-------------|-----------------|----------|------------|
| 1 | **Anomaly detected** — auth endpoint latency spikes, p99 > 500ms (threshold: 200ms) | Exteroceptive monitor detects tolerance breach on REQ-F-AUTH-001. Emit `exteroceptive_signal` event with `severity: high`. | REQ-SENSE-001, REQ-SUPV-002 | GAP-008 |
| 2 | **IntentEngine classifies signal** — automatic | Signal classified: `bounded_nonzero` ambiguity (known requirement, unknown root cause). Output: `spec_event_log` (needs investigation, not immediate reflex). Emit `affect_triage` event. | REQ-SUPV-001, REQ-LIFE-006 | GAP-003 |
| 3 | **Intent raised** — automatic | Emit `intent_raised`: trigger=runtime_feedback, delta="REQ-F-AUTH-001 p99 latency 523ms exceeds 200ms threshold", signal_source=exteroceptive, severity=high. | REQ-LIFE-005, REQ-INTENT-003 | GAP-003 |
| 4 | **Developer sees intent** — `genesis status` or `genesis escalate` | Escalation queue shows: 1 high-severity item. Unactioned intent from runtime telemetry. Recommended action: spawn hotfix or discovery vector. | REQ-SUPV-001, REQ-LIFE-003 | COVERED (spec: `/gen-escalate`, `/gen-status`) |
| 5 | **Spawn hotfix** — developer chooses to spawn hotfix vector | Create hotfix vector: REQ-F-HOTFIX-AUTH-001, profile `hotfix` (code + unit_tests + cicd only). Emit `spawn_created`. | REQ-FEAT-002, REQ-LIFE-005 | GAP-003 |
| 6 | **Hotfix iterates and deploys** — `genesis start --auto` | Hotfix vector traverses code↔tests→cicd. Minimal edges, fast convergence. Deploy fix. Verify telemetry returns to normal. | REQ-ITER-001, REQ-LIFE-001 | GAP-003 |
| 7 | **Loop closes** — telemetry confirms fix | Telemetry shows p99 back to 150ms. Exteroceptive monitor confirms tolerance restored. Hotfix vector converges. Fold back to parent if applicable. | REQ-LIFE-002, REQ-LIFE-003 | GAP-003, GAP-008 |

### Gaps

| Gap ID | Description | Impact | Drives |
|--------|-------------|--------|--------|
| GAP-003 | No executable engine | Steps 2, 3, 5, 6 require orchestration | Phase 2 |
| GAP-008 | **No runtime telemetry integration.** Exteroceptive monitors are spec'd (sensory_monitors.yml) but only npm-audit and pip-audit have hook implementations. No integration with application-level telemetry (Prometheus, OpenTelemetry, CloudWatch). | The feedback loop from running_system→telemetry→intent is entirely manual. | REQ-SENSE-001, REQ-LIFE-002. Consider: is this in-scope for Genesis, or is it the user's responsibility to wire telemetry? Genesis could provide the event schema and let users emit `exteroceptive_signal` events from their monitoring stack. |

### Invariant Checks

- [x] **Evaluator Existence** — hotfix edges have evaluators
- [x] **Markov Property** — hotfix depends on current telemetry state
- [x] **Convergence Monotonicity** — telemetry deviation → fix → deviation resolved
- [x] **IntentEngine Composition** — canonical: anomaly → signal → triage → intent → spawn → iterate → deploy → observe → confirm

---

## Gap Registry

Consolidated gap registry across all scenarios. Each gap appears once; scenarios reference it.

| Gap ID | Title | Scenarios | Severity | Drives |
|--------|-------|-----------|----------|--------|
| GAP-001 | No installability requirement | SC-001 | **High** | New REQ-TOOL-011 |
| GAP-002 | No automated feature decomposition from intent | SC-001 | Low | REQ-FEAT-001, REQ-UX-001 |
| GAP-003 | No executable orchestration engine | SC-001 through SC-007 | **Critical** | Phase 2 implementation |
| GAP-004 | genesis_monitor schema drift (v2.5 → v2.8/3.0) | SC-001 | Medium | genesis_monitor upgrade |
| GAP-005 | No automated root-cause investigation for stuck features | SC-003 | Low | Spike profile diagnostic heuristics |
| GAP-006 | Multi-agent coordination is spec-only | SC-004 | Low | Phase 3 (post-engine) |
| GAP-007 | No fold-back command | SC-006 | Medium | New `/gen-fold-back` command |
| GAP-008 | No runtime telemetry integration | SC-007 | Medium | REQ-SENSE-001 scope clarification |

### Gap Impact Matrix

```
              SC-001  SC-002  SC-003  SC-004  SC-005  SC-006  SC-007
GAP-001         X
GAP-002         X
GAP-003         X       X       X       X       X       X       X
GAP-004         X
GAP-005                         X
GAP-006                                 X
GAP-007                                                 X
GAP-008                                                         X
```

**GAP-003 dominates.** It appears in every scenario. This is expected — the methodology is fully specified but not yet executable. The remaining gaps are spec-level (drive new REQ keys or spec clarifications) and independently addressable.

Note: GAP-001 (installability) is a spec gap, not merely a packaging concern. v1.x had a working installer (curl + marketplace); v2 dropped the requirement. A methodology that cannot be installed into a project cannot be used — installability is constitutive, like telemetry (§0).

### The F_P Question (GAP-003 Commentary)

GAP-003 — "no executable engine" — deserves deeper analysis because it may not be a gap at all. It depends on which encoding is considered primary:

**If F_D (deterministic) is the target encoding**: GAP-003 is a real gap. The specs describe a state machine, and no code implements that state machine. The human must manually drive the loop. This is the traditional software engineering view.

**If F_P (probabilistic) is the target encoding**: GAP-003 is a *feature*. The specs are the program — they are loaded into an LLM's context, and the LLM executes them. The "executable engine" is the LLM itself, parameterised by the spec documents. The iterate agent markdown IS the code. This is the current de facto architecture.

**If both encodings are valid** (ADR-017 functor model): then the question is which edges benefit from F_D and which from F_P. State detection, event emission, and evaluator checklists are good F_D candidates. Asset generation (writing requirements, design, code) is inherently F_P. The engine is a hybrid — and partially exists today.

This is not a question this document can answer. It is a design decision that belongs in the implementation design docs (per spec/design separation). But the scenarios should be satisfiable regardless of encoding choice.

---

## Scenario Backlog

Future scenarios to add as the methodology matures:

| ID | Title | Profile | Key Focus |
|----|-------|---------|-----------|
| SC-008 | Enterprise Compliance — Audit Trail Generation | full | REQ-LIFE-004, REQ-EVAL-003, regulatory traceability |
| SC-009 | Library Release — Full Profile with Versioning | full | REQ-TOOL-008, REQ-LIFE-001, semver, changelog |
| SC-010 | Cross-Platform — Same Spec, Claude + Gemini Implementations | standard | Multi-tenancy, spec/design separation |
| SC-011 | Methodology Self-Application — Genesis Builds Genesis | full | §0 recursive compliance, dogfooding |
| SC-012 | Time-Boxed Exploration — PoC with Expiry | poc | Time-box mechanics, fold-back-or-discard |
| SC-013 | Context Window Pressure — Large Project Scaling | standard | REQ-CTX-002 hierarchy, context selection |
| SC-014 | Ecosystem Shock — Major Dependency Breaks | standard | REQ-INTENT-003, REQ-SENSE-001, exteroceptive response |
