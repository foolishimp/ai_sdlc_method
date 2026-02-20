# /aisdlc-status - Show Feature Vector Progress

Display the current state of all feature vectors and their trajectories through the graph.

<!-- Implements: REQ-TOOL-002, REQ-FEAT-002 -->
<!-- Reference: AI_SDLC_ASSET_GRAPH_MODEL.md v2.3.0 §7.5 Event Sourcing, §7.6 Self-Observation -->

## Usage

```
/aisdlc-status [--feature "REQ-F-*"] [--verbose] [--gantt]
```

| Option | Description |
|--------|-------------|
| (none) | Show summary of all feature vectors |
| `--feature` | Show detailed status for a specific feature |
| `--verbose` | Show iteration history and evaluator details |
| `--gantt` | Show Mermaid Gantt chart of feature build schedule |

## Instructions

### Default View (No Arguments)

Read `.ai-workspace/features/feature_index.yml` and all feature files to produce:

```
AI SDLC Status — {project_name}
================================

Active Features:
  REQ-F-AUTH-001  "User authentication"      design→code (iter 3)
  REQ-F-DB-001    "Database schema"           code↔tests (converged)
  REQ-F-API-001   "REST API endpoints"        requirements (iter 1)

Completed Features:
  REQ-F-SETUP-001 "Project scaffolding"       all edges converged

Graph Coverage:
  Requirements:  12/15 (80%)
  Design:         8/12 (67%)
  Code:           5/8  (63%)
  Tests:          5/5  (100%)

Next Actions:
  - REQ-F-AUTH-001: iterate on design→code edge
  - REQ-F-API-001: human review pending on requirements
```

### Detailed View (--feature)

Read the specific feature vector file and show:

```
Feature: REQ-F-AUTH-001 — "User authentication"
================================================

Intent:  INT-042
Status:  in_progress

Trajectory:
  intent         ✓ converged (2026-02-19T09:00)
  requirements   ✓ converged (2026-02-19T10:00)  [human approved]
  design         ✓ converged (2026-02-19T11:30)  [human approved]
  code           → iterating (iteration 3)       [delta: missing error handling]
  unit_tests     → iterating (iteration 3)       [co-evolving with code]
  uat_tests      ○ pending

Dependencies:
  REQ-F-DB-001   ✓ resolved (database schema available)

Constraint Dimensions (at design edge):
  ecosystem_compatibility  ✓ resolved (ADR-003: Python 3.12 + Django 5.0)
  deployment_target        ✓ resolved (ADR-004: Kubernetes on AWS EKS)
  security_model           ✓ resolved (ADR-005: OAuth2 + RBAC)
  build_system             ✓ resolved (ADR-006: pip + Docker multi-stage)
  data_governance          ~ advisory (acknowledged — GDPR not applicable)
  performance_envelope     ~ advisory (p99 < 200ms target documented)
  observability            ~ advisory (OpenTelemetry planned)
  error_handling           ~ advisory (fail-fast strategy documented)

Context Hash: sha256:a1b2c3...
```

### Gantt Chart View (--gantt)

Read the event stream from `.ai-workspace/events/events.jsonl` (source of truth). Fall back to feature vector files in `.ai-workspace/features/active/` and `.ai-workspace/features/completed/` if the event log doesn't exist yet. Extract timestamps to build a Mermaid Gantt chart.

#### Step 1: Collect Phase Data

For each feature vector file, extract:
- Feature ID and title
- For each trajectory entry (requirements, design, code, unit_tests, uat_tests):
  - `started_at` — when iteration began on this edge
  - `converged_at` — when the edge converged (null if still in progress)
  - `status` — pending, iterating, converged
  - `iteration` — current iteration count

#### Step 2: Generate Mermaid Gantt

Produce a Mermaid Gantt diagram. Each feature is a section; each edge traversal is a task bar.

```mermaid
gantt
    title Feature Build Schedule
    dateFormat YYYY-MM-DD HH:mm
    axisFormat %m-%d %H:%M

    section REQ-F-AUTH-001
    requirements     :done,    auth-req, 2026-02-19 09:00, 2026-02-19 10:00
    design           :done,    auth-des, after auth-req, 2026-02-19 11:30
    code             :active,  auth-cod, after auth-des, 90m
    unit_tests       :active,  auth-tst, after auth-des, 90m
    uat_tests        :         auth-uat, after auth-cod, 60m

    section REQ-F-DB-001
    requirements     :done,    db-req, 2026-02-19 08:00, 2026-02-19 08:30
    design           :done,    db-des, after db-req, 2026-02-19 09:00
    code             :done,    db-cod, after db-des, 2026-02-19 10:00
    unit_tests       :done,    db-tst, after db-des, 2026-02-19 10:00
    uat_tests        :done,    db-uat, after db-cod, 2026-02-19 10:30
```

#### Step 3: Status-to-Gantt Mapping

Map feature vector trajectory status to Gantt task states:

| Trajectory Status | Gantt State | Display |
|-------------------|-------------|---------|
| `converged` | `:done` | Solid bar with start→end timestamps |
| `iterating` | `:active` | Highlighted bar, end = now or estimated |
| `blocked` | `:crit` | Red bar, blocked on dependency or spawn |
| `pending` | (no prefix) | Grey bar, estimated duration |
| `time_box_expired` | `:done` | Solid bar (completed via time-box) |

#### Step 4: Handle Missing Timestamps

- If `started_at` is missing but status is `converged`: use `converged_at - estimated_duration`
- If `converged_at` is missing but status is `iterating`: use current time as provisional end
- For `pending` phases: estimate duration from profile or use 1 hour default, chain with `after {previous_phase_id}`
- Co-evolution edges (code↔unit_tests): show as parallel bars starting at the same time

#### Step 5: Write STATUS.md

Write the full Gantt output to `.ai-workspace/STATUS.md` so it is viewable as a workspace artifact:

1. **Write** `.ai-workspace/STATUS.md` with the following structure:

```markdown
# Project Status — {project_name}

Generated: {ISO timestamp}

## Feature Build Schedule

{Mermaid Gantt chart as a fenced code block}

## Phase Completion Summary

| Phase | Converged | In Progress | Pending | Blocked |
|-------|-----------|-------------|---------|---------|
| requirements | 3 | 1 | 0 | 0 |
| design | 2 | 1 | 1 | 0 |
| code | 1 | 1 | 2 | 0 |
| unit_tests | 1 | 1 | 2 | 0 |
| uat_tests | 0 | 0 | 3 | 1 |
| **Total** | **7** | **4** | **8** | **1** |

## Active Features

{List of active features with current edge and iteration}

## Next Actions

{Recommended next actions from graph topology}

---

## Process Telemetry

{Auto-generated observations from the iterate history}

### Convergence Pattern
- Iteration counts per edge (flag anomalies: 1-iteration convergence, >5 iterations)
- Evaluator pass/skip/fail ratios
- Deterministic check execution vs skip rates

### Traceability Coverage
- REQ key counts: defined vs tagged in code vs tested
- Gaps identified (cross-reference with /aisdlc-gaps output if available)

### Constraint Surface Observations
- $variable resolution: which resolved, which undefined
- Skipped evaluators and why

## Self-Reflection — Feedback → New Intent

{Signals derived from telemetry that could become new intents or methodology improvements}

| Signal | Observation | Recommended Action |
|--------|-------------|-------------------|
| TELEM-NNN | {what the data shows} | {what to do about it} |
```

2. **Report** to the user: print the file path and a one-line summary (e.g., "Status written to `.ai-workspace/STATUS.md` — 3 features, 7/20 phases converged")
3. The file is viewable in VS Code with Mermaid preview extensions, or renderable to PDF via `md2pdf .ai-workspace/STATUS.md`

**Important**: The status command always OVERWRITES `STATUS.md` — it is a derived snapshot, not a log. The source of truth is `events/events.jsonl`.

### Event Sourcing Architecture

The methodology uses **event sourcing** for all observability:

```
Source of Truth              Derived Views (projections)
─────────────────            ──────────────────────────
events/events.jsonl    ───►  STATUS.md          (computed: Gantt, telemetry, self-reflection)
  (append-only JSONL)  ───►  ACTIVE_TASKS.md    (filtered: convergence events as markdown)
                       ───►  features/active/*.yml  (state: latest trajectory per feature)
```

- **Events** are immutable facts: every `iterate()` invocation appends one event
- **Views** are projections that can be regenerated from the event stream at any time
- If a view gets corrupted or lost, replay `events.jsonl` to reconstruct it

### Process Telemetry Guidelines

The telemetry section is NOT free-form commentary. The iterate agent reads `events.jsonl` and produces structured observations:

1. **Convergence Pattern**: Compare iteration counts against profile expectations. Flag 1-iteration convergence (evaluators may be too lenient) and >5 iterations (may indicate blocked or under-specified requirements).
2. **Traceability Coverage**: Count REQ keys at each stage. Report coverage gaps.
3. **Constraint Surface**: Report $variable resolution rates and skipped deterministic checks.
4. **Self-Reflection**: Each TELEM signal is a potential new intent. The methodology observes itself and feeds back — this closes the `Telemetry / Observer → feedback → new Intent` loop in the bootstrap graph.

## Event Schema

Each event in `events.jsonl` follows this schema:

```json
{
  "type": "iteration_completed",
  "timestamp": "2026-02-19T10:30:00Z",
  "feature": "REQ-F-AUTH-001",
  "edge": "intent→requirements",
  "iteration": 2,
  "status": "converged",
  "convergence_type": "standard",
  "evaluators": {
    "passed": 9, "failed": 0, "skipped": 0, "total": 9,
    "details": [{"name": "check_name", "type": "agent", "result": "pass", "required": true}]
  },
  "asset": "docs/specification/REQUIREMENTS.md",
  "context_hash": "sha256:a1b2c3...",
  "delta": 0,
  "source_findings": [
    {"description": "INT-003 'universal applicability' — target domain set undefined",
     "classification": "SOURCE_UNDERSPEC", "disposition": "resolved_with_assumption"}
  ],
  "process_gaps": [
    {"description": "No check for terminology dictionary in requirements",
     "type": "EVALUATOR_MISSING", "action": "Add document_structure check to intent_requirements.yml"}
  ]
}
```

### Event Fields

| Field | Description |
|-------|-------------|
| `evaluators` | Forward gap detection — checklist pass/fail/skip counts + details |
| `source_findings` | Backward gap detection — ambiguities, gaps, underspecification found in the source asset |
| `process_gaps` | Inward gap detection — missing evaluators, vague criteria, missing context, missing guidance |
| `delta` | Count of failing required checks (forward only) |

Feature vector timestamps (`started_at`, `converged_at`) are derived from the first and last events for a given feature+edge combination.

### Telemetry Projections from Gap Data

The STATUS.md telemetry section aggregates gap data from `events.jsonl`:

- **Source quality**: Count of source findings per edge, per classification. High `SOURCE_GAP` counts on a downstream edge indicate the upstream edge's evaluators are too lenient.
- **Process maturity**: Count of process gaps per type. High `EVALUATOR_MISSING` counts indicate the methodology needs more checks. Declining counts across iterations indicate the methodology is self-improving.
- **Assumption register**: All `resolved_with_assumption` dispositions — these are decisions that should be validated by a human or confirmed by downstream evidence.
