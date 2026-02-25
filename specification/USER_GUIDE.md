# Genesis User Guide

**Version**: v3.0.0-beta.1 | **Platform**: Claude Code | **Date**: 2026-02-25

A practitioner guide for building software with the Genesis Asset Graph Model methodology.

**Audience**: Developers using Claude Code who want Genesis to structure their AI-augmented development workflow.

**Prerequisites**: Claude Code installed and working in your terminal.

---

## Table of Contents

1. [How Genesis Works](#1-how-genesis-works)
2. [Installation](#2-installation)
3. [Your First Project](#3-your-first-project)
4. [Working Through the Graph](#4-working-through-the-graph)
5. [Reviews and Quality Gates](#5-reviews-and-quality-gates)
6. [Releasing](#6-releasing)
7. [Working with Multiple Features](#7-working-with-multiple-features)
8. [Spawning Child Vectors](#8-spawning-child-vectors)
9. [Getting Unstuck](#9-getting-unstuck)
10. [Command Reference](#10-command-reference)
11. [Workspace Reference](#11-workspace-reference)
12. [Pitfalls and FAQ](#12-pitfalls-and-faq)
13. [Glossary](#13-glossary)

---

## 1. How Genesis Works

Genesis gives you a structured way to build software with AI. Instead of ad-hoc prompting, every piece of work follows a graph of typed assets, connected by transitions, each with defined quality checks.

### 1.1 The Asset Graph

Your project moves through 10 asset types connected by transitions:

```
Intent ──> Requirements ──> Design ──> Code <──> Unit Tests
                              │
                              ├──> Test Cases
                              └──> UAT Tests

Code ──> CI/CD ──> Running System ──> Telemetry ──> Intent (feedback)
```

Each node is a typed asset. Each arrow is a transition that transforms one asset into the next. The graph is cyclic — telemetry feeds back into new intents.

| Asset Type | What It Is |
|-----------|-----------|
| Intent | Raw problem statement — what you want to build and why |
| Requirements | Structured, testable requirements with unique REQ keys |
| Design | Technical architecture — components, ADRs, data models |
| Code | Implementation source code tagged with REQ keys |
| Unit Tests | Tests co-evolved with code via TDD |
| Test Cases | Integration/system tests derived from design |
| UAT Tests | Business acceptance tests in plain language (BDD) |
| CI/CD | Pipeline configuration and build artifacts |
| Running System | Deployed system with health checks |
| Telemetry | Runtime metrics and alerts tagged with REQ keys |

### 1.2 The Only Operation: iterate()

Genesis has exactly one operation:

```
iterate(Asset, Context[], Evaluators) -> Asset'
```

- **Asset**: The current state of a typed artifact (e.g., your requirements document)
- **Context[]**: Constraints that bound construction (project constraints, ADRs, standards)
- **Evaluators**: Quality checks that determine when the asset is good enough

The iterate agent generates a candidate, runs the evaluators, and reports what passed and what failed. If all required checks pass (delta = 0), the edge **converges** and you move to the next transition. If not, you iterate again.

### 1.3 Three Evaluator Types

Every quality check on every edge is one of three types:

| Type | What It Does | Example |
|------|-------------|---------|
| **Deterministic** | Runs a command, checks the output | `pytest --tb=short` must exit 0 |
| **Agent** | Claude assesses against a criterion | "All REQ keys have corresponding code" |
| **Human** | You review and approve/reject | "Does this design meet your needs?" |

Evaluators compose: an edge can have all three types. Deterministic runs first (cheap, fast), then agent (moderate), then human (expensive, only when needed).

### 1.4 Feature Vectors and REQ Keys

A **feature vector** is a single capability's journey through the graph. Each feature gets a unique REQ key (e.g., `REQ-F-AUTH-001`) that threads through every artifact:

```
Spec:       REQ-F-AUTH-001 defined
Design:     Implements: REQ-F-AUTH-001
Code:       # Implements: REQ-F-AUTH-001
Tests:      # Validates: REQ-F-AUTH-001
Telemetry:  logger.info("login", req="REQ-F-AUTH-001")
```

This gives you end-to-end traceability from intent to runtime.

### 1.5 Profiles

Not every feature needs every edge. **Profiles** control which transitions are included and what evaluators apply:

| Profile | Edges | When to Use |
|---------|-------|-------------|
| **full** | All 10 | Regulated/audited systems, full governance |
| **standard** | Intent through Unit Tests (4 edges) | Normal feature development |
| **poc** | Intent through Code (3 edges) | Prove feasibility before committing |
| **spike** | Requirements through Code (2 edges) | Research a technical question |
| **hotfix** | Code + Unit Tests, CI/CD (2 edges) | Emergency production fix |
| **minimal** | Code only (1 edge) | Smallest valid methodology instance |

### 1.6 Event Sourcing

All state in Genesis is derived from an append-only event log:

```
.ai-workspace/events/events.jsonl
```

Every iteration emits events. STATUS.md, feature vector files, and task lists are all projections of this log — they can be regenerated at any time.

### 1.7 The Two-Command Interface

You only need two commands for daily work:

- **`/gen-start`** — "Go." Detects project state and routes to the right action.
- **`/gen-status`** — "Where am I?" Shows feature progress, health, and next steps.

The other 11 commands exist for specific scenarios, but `/gen-start` handles routing for you.

---

## 2. Installation

### 2.1 One-Command Install

In your project directory:

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 -
```

Restart Claude Code after installation.

### 2.2 Verify

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 - verify
```

Or inside Claude Code, run `/gen-start`. State detection will report `NEEDS_INTENT` or `UNINITIALISED` and guide you through setup.

### 2.3 What Gets Created

```
your-project/
├── .claude/
│   ├── settings.json                  # Plugin config + hook wiring
│   └── hooks/                         # Protocol enforcement hooks
│       ├── on-session-start.sh        # Workspace health check
│       ├── on-iterate-start.sh        # Edge detection + context injection
│       ├── on-artifact-written.sh     # File-write observation
│       └── on-stop-check-protocol.sh  # Mandatory side-effect enforcement
├── .ai-workspace/                     # Genesis workspace
│   ├── events/events.jsonl            # Event log (source of truth)
│   ├── features/
│   │   ├── active/                    # Feature vectors in progress
│   │   └── completed/                 # Converged feature vectors
│   ├── graph/
│   │   ├── graph_topology.yml         # Asset types + transitions
│   │   ├── evaluator_defaults.yml     # Evaluator types + phases
│   │   ├── edges/                     # Per-edge evaluator configs
│   │   └── profiles/                  # Projection profiles (6)
│   ├── {impl}/context/
│   │   └── project_constraints.yml    # Toolchain + thresholds
│   ├── tasks/
│   │   ├── active/ACTIVE_TASKS.md     # Current work
│   │   └── finished/                  # Completed task docs
│   └── STATUS.md                      # Auto-generated status view
├── specification/
│   └── INTENT.md                      # Intent document template
└── CLAUDE.md                          # Genesis Bootloader (appended)
```

### 2.4 Alternative Installation

**Marketplace (commands only, no hooks):**

Add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "genisis": {
      "source": { "source": "github", "repo": "foolishimp/ai_sdlc_method" }
    }
  },
  "enabledPlugins": { "genisis@genisis": true }
}
```

Then run `/gen-init` to create the workspace.

**Local/air-gapped:**

Clone the repo and point to the local path:

```json
{
  "extraKnownMarketplaces": {
    "genisis": {
      "source": {
        "source": "local",
        "path": "/path/to/ai_sdlc_method/imp_claude/code/.claude-plugin"
      }
    }
  },
  "enabledPlugins": { "genisis@genisis": true }
}
```

### 2.5 Troubleshooting

| Problem | Solution |
|---------|----------|
| `python3: command not found` | Install Python 3.8+ |
| Existing `settings.json` not merged | Re-run installer; it merges, not overwrites |
| Commands not appearing after install | Restart Claude Code (required for plugin discovery) |
| Hook permissions denied | Run `chmod +x .claude/hooks/*.sh` |

---

## 3. Your First Project

We will use a running example throughout this guide: **tasktracker**, a Python REST API for managing tasks.

### 3.1 Start in Your Project Directory

```bash
mkdir tasktracker && cd tasktracker
```

Open Claude Code in this directory.

### 3.2 Run /gen-start

```
/gen-start
```

Genesis detects `UNINITIALISED` (no `.ai-workspace/` directory) and starts the progressive initialization flow. It asks 5 questions:

1. **Project name?** — `tasktracker` (auto-detected from directory)
2. **Project kind?** — `service` (application/library/service/data-pipeline)
3. **Primary language?** — `Python`
4. **Test runner?** — `pytest`
5. **What are you building?** — "A REST API for creating, listing, completing, and deleting tasks with user authentication"

Genesis creates the workspace, writes your intent to `specification/INTENT.md`, configures `project_constraints.yml` with your toolchain, and emits a `project_initialized` event.

### 3.3 What Was Generated

**specification/INTENT.md** — Your intent, captured:

```markdown
# Intent: tasktracker

A REST API for creating, listing, completing, and deleting tasks
with user authentication.

## Source
Developer input during /gen-init

## Priority
High
```

**project_constraints.yml** — Your toolchain configuration (excerpt):

```yaml
project:
  name: tasktracker
  language: Python
  kind: service

tools:
  test_runner:
    command: pytest
    args: --tb=short -q
    pass_criterion: exit_code_zero
  coverage:
    command: pytest --cov=tasktracker --cov-report=term-missing
    pass_criterion: exit_code_zero
  linter:
    command: ruff check .
    pass_criterion: exit_code_zero

thresholds:
  test_coverage_minimum: 80
  max_function_lines: 50
```

### 3.4 Create Your First Feature

Run `/gen-start` again. Genesis detects `NO_FEATURES` — intent exists but no feature vectors. It creates your first feature vector:

```
Feature vector created: REQ-F-TASK-001
Title: Task Management CRUD
Profile: standard
Status: pending
```

The feature vector YAML is written to `.ai-workspace/features/active/REQ-F-TASK-001.yml`. It defines:
- The REQ key (`REQ-F-TASK-001`)
- The profile (`standard` — 4 edges)
- The trajectory (which edges to traverse)
- Acceptance criteria (derived from intent)

### 3.5 Check Status

```
/gen-status
```

```
STATE: IN_PROGRESS

You Are Here:
  Intent ──[○]──> Requirements ──[○]──> Design ──[○]──> Code <──[○]──> Unit Tests

Active Features:
  REQ-F-TASK-001  Task Management CRUD  requirements  iter 0  standard

Project:
  Features: 1 active, 0 converged
  Edges: 0/4 converged
```

You are ready to iterate.

---

## 4. Working Through the Graph

### 4.1 Intent to Requirements

Run `/gen-start`. Genesis detects `IN_PROGRESS`, selects `REQ-F-TASK-001`, identifies `intent_requirements` as the first unconverged edge, and delegates to the iterate agent.

The iterate agent:

1. **Loads context** — reads your intent, project constraints, and edge config (`intent_requirements.yml`)
2. **Analyses the source** — flags ambiguities, gaps, and underspecification in your intent
3. **Generates requirements** — produces structured requirements with REQ keys:

```markdown
# Requirements: tasktracker

## REQ-F-TASK-001: Task CRUD Operations
- REQ-F-TASK-001.1: Create task (title, description, due_date)
- REQ-F-TASK-001.2: List tasks with filtering (status, due_date)
- REQ-F-TASK-001.3: Complete task (status transition)
- REQ-F-TASK-001.4: Delete task (soft delete)

## REQ-F-AUTH-001: User Authentication
- REQ-F-AUTH-001.1: Register with email/password
- REQ-F-AUTH-001.2: Login returns JWT token
- REQ-F-AUTH-001.3: Protected endpoints require valid token
```

4. **Runs evaluators** — the edge checklist for `intent_requirements` includes:

| Check | Type | Result |
|-------|------|--------|
| all_intent_aspects_covered | agent | PASS |
| requirements_are_testable | agent | PASS |
| acceptance_criteria_specific | agent | PASS |
| correct_key_format | agent | PASS |
| human_validates_completeness | human | -- |

5. **Requests human review** — this is a spec-boundary edge. You review the requirements and either approve, reject with feedback, or request refinements.

On approval, the edge converges. Event emitted. Feature vector updated.

### 4.2 Requirements to Design

Run `/gen-start` again. The next unconverged edge is `requirements_design`.

At this boundary, Genesis prompts for **constraint dimensions** — mandatory technical decisions that haven't been made yet:

```
The following constraint dimensions must be resolved at design:

[MANDATORY]
  ecosystem_compatibility: (not set) — What language, runtime, and frameworks?
  deployment_target: (not set) — Where does this deploy?
  security_model: (not set) — How is authentication/authorization handled?
  build_system: (not set) — What build/package tooling?

[OPTIONAL]
  data_governance: (not set)
  performance_envelope: (not set)
  observability: (not set)
  error_handling: (not set)
```

You provide answers:
- **ecosystem**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **deployment**: Docker containers on AWS ECS
- **security**: JWT with bcrypt password hashing
- **build_system**: pip + pyproject.toml

The iterate agent generates:
- Component architecture (API layer, service layer, data layer)
- ADRs for each constraint dimension decision
- Data models (Task, User schemas)
- API endpoint specifications

The agent evaluator checks completeness and fidelity against the requirements. The human evaluator asks you to review. On approval, the edge converges.

### 4.3 Design to Code

Run `/gen-start`. Next edge: `design_code`.

The iterate agent scaffolds code from your design:

```python
# src/tasktracker/models/task.py
# Implements: REQ-F-TASK-001

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from tasktracker.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    completed = Column(Boolean, default=False)
    ...
```

Evaluators run:
- **Deterministic**: Does it compile/parse? Does the linter pass?
- **Agent**: Are all REQ keys tagged? Does code match design?

If the linter fails, the iterate agent fixes the issue and re-evaluates. When delta = 0, the edge converges.

### 4.4 Code and Unit Tests (TDD Co-evolution)

Run `/gen-start`. Next edge: `code_unit_tests`.

This is a **bidirectional** edge — code and tests co-evolve. The iterate agent follows the TDD cycle:

**RED**: Write a failing test first:

```python
# tests/test_task_crud.py
# Validates: REQ-F-TASK-001.1

def test_create_task(client):
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    assert response.json()["title"] == "Buy milk"
```

**GREEN**: Write minimal code to pass:

```python
# src/tasktracker/routes/tasks.py
# Implements: REQ-F-TASK-001.1

@router.post("/tasks", status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    return db_task
```

**REFACTOR**: Improve quality while tests stay green.

**COMMIT**: Save with REQ key in the commit message.

The edge evaluators include deterministic checks:

| Check | Type | Command |
|-------|------|---------|
| tests_pass | deterministic | `pytest --tb=short -q` |
| coverage_meets_threshold | deterministic | `pytest --cov=tasktracker` (>= 80%) |
| lint_passes | deterministic | `ruff check .` |

And agent checks:

| Check | Type | Criterion |
|-------|------|-----------|
| req_tags_present | agent | All code files have `Implements:` tags |
| all_req_keys_covered | agent | Every REQ key in spec has a test |
| code_quality | agent | Functions under 50 lines, clear naming |

The iterate agent loops (RED-GREEN-REFACTOR) until all checks pass. With `--auto`, it continues without pausing between iterations.

### 4.5 Checking Progress

At any point, check where you are:

```
/gen-status
```

```
STATE: IN_PROGRESS

You Are Here:
  Intent ──[done]──> Requirements ──[done]──> Design ──[done]──> Code <──[iter 3]──> Unit Tests

Active Features:
  REQ-F-TASK-001  Task Management CRUD  code_unit_tests  iter 3  standard

Project:
  Features: 1 active, 0 converged
  Edges: 3/4 converged
```

Trace a specific REQ key end-to-end:

```
/gen-trace REQ-F-TASK-001.1
```

```
REQ-F-TASK-001.1: Create task

  Intent        specification/INTENT.md                        [FOUND]
  Requirements  specification/REQUIREMENTS.md:15               [FOUND]
  Design        imp_claude/design/DESIGN.md:42                 [FOUND]
  Code          src/tasktracker/routes/tasks.py:8               [FOUND]  Implements: REQ-F-TASK-001.1
  Tests         tests/test_task_crud.py:5                       [FOUND]  Validates: REQ-F-TASK-001.1
  Telemetry     --                                              [GAP]
```

Check traceability across all REQ keys:

```
/gen-gaps --layer 1
```

```
Layer 1: REQ Tag Coverage

| REQ Key             | Code | Tests | Status   |
|---------------------|------|-------|----------|
| REQ-F-TASK-001.1    | Y    | Y     | COMPLETE |
| REQ-F-TASK-001.2    | Y    | Y     | COMPLETE |
| REQ-F-TASK-001.3    | Y    | N     | GAP      |
| REQ-F-TASK-001.4    | Y    | Y     | COMPLETE |

Coverage: 3/4 REQ keys fully covered (75%)
```

---

## 5. Reviews and Quality Gates

### 5.1 Human Reviews

At edges where the evaluator config includes `human`, the iterate agent pauses and presents the candidate for your review.

```
/gen-review --feature REQ-F-TASK-001
```

You see the current asset with evaluator results and choose:

| Action | What Happens |
|--------|-------------|
| **Approve** | Edge converges; feature moves to next transition |
| **Reject** | Feedback recorded; next iteration uses your feedback as context |
| **Refine** | Specific changes captured; iterate agent applies them |

### 5.2 Spec-Boundary Reviews

At transitions between specification levels (intent to requirements, requirements to design), Genesis runs a **gradient check** with three dimensions:

```
/gen-spec-review --feature REQ-F-TASK-001 --edge "requirements->design"
```

| Dimension | What It Checks | Example |
|-----------|---------------|---------|
| **Completeness** | Does target cover everything in source? | 15/16 REQ keys have design bindings |
| **Fidelity** | Does target faithfully represent source? | No requirements weakened or narrowed |
| **Boundary** | Does target stay within its specification level? | Design doesn't introduce implementation details |

If the review finds issues, you can:
- **Approve** (issues are minor)
- **Reject** (rework this edge)
- **Escalate** (the source asset needs revision — block this edge, re-open upstream)

### 5.3 Traceability Validation

Three layers of traceability, checked by `/gen-gaps`:

| Layer | What It Checks | When to Run |
|-------|---------------|-------------|
| **1: REQ Tags** | Code has `Implements:`, tests have `Validates:` | After code/tests edges |
| **2: Test Coverage** | Every REQ key in spec has at least one test | Before release |
| **3: Telemetry** | Every REQ key in code has telemetry tagging | Before production |

```
/gen-gaps --layer all
```

Gaps found are emitted as `intent_raised` events, feeding the consciousness loop.

### 5.4 Checkpoints

Save a snapshot of your workspace state:

```
/gen-checkpoint --message "All CRUD tests passing, auth next"
```

This creates an immutable snapshot at `.ai-workspace/snapshots/snapshot-{timestamp}.yml` with:
- Context hash (SHA-256 of all context files)
- Feature states (which edges converged, iteration counts)
- Git ref (current commit)

Use checkpoints before risky changes or at the end of work sessions.

---

## 6. Releasing

### 6.1 Pre-Release Checklist

Before creating a release:

```
/gen-gaps                    # Check traceability across all layers
/gen-status --health         # Workspace integrity check
/gen-escalate                # Review any unactioned signals
```

### 6.2 Create a Release

```
/gen-release --version "1.0.0"
```

Genesis:
1. Validates release readiness (all critical features converged, gaps reviewed)
2. Generates changelog from git log (commits with REQ keys since last release)
3. Creates release manifest with REQ coverage report
4. Creates git tag `v1.0.0`
5. Emits `release_created` event

### 6.3 Dry Run

Preview without creating tags or artifacts:

```
/gen-release --version "1.0.0" --dry-run
```

---

## 7. Working with Multiple Features

### 7.1 Adding Features

After your first feature converges (or while it is still in progress), spawn additional features:

```
/gen-spawn --type feature --reason "User authentication for the task API"
```

This creates a new feature vector (e.g., `REQ-F-AUTH-001`) with its own trajectory through the graph.

### 7.2 Feature Selection

When you run `/gen-start` with multiple active features, Genesis picks the most important one:

1. **Time-boxed spawns approaching expiry** (< 25% budget remaining)
2. **Closest to complete** (fewest unconverged edges)
3. **Highest priority** (critical > high > medium > low)
4. **Most recently touched** (from event timestamps)

### 7.3 Feature Dependencies

Features can depend on each other. If `REQ-F-AUTH-001` must complete before `REQ-F-TASK-001` can proceed past design, the dependency blocks the downstream feature at that edge.

`/gen-status` shows blocked features:

```
Active Features:
  REQ-F-TASK-001  Task CRUD        design       iter 1  standard  BLOCKED (depends: REQ-F-AUTH-001)
  REQ-F-AUTH-001  Authentication   code_tests   iter 2  standard
```

### 7.4 Overriding Selection

Skip the automatic selection:

```
/gen-start --feature REQ-F-AUTH-001
```

Or go directly to a specific edge:

```
/gen-iterate --edge "code->unit_tests" --feature REQ-F-AUTH-001
```

---

## 8. Spawning Child Vectors

Sometimes a feature gets stuck because you need to investigate something first. Child vectors let you branch off, investigate, and fold results back.

### 8.1 When to Spawn

| Situation | Vector Type | Profile |
|-----------|------------|---------|
| Knowledge gap — "How does X work?" | discovery | minimal |
| Technical risk — "Can we use library Y?" | spike | spike |
| Feasibility — "Will approach Z scale?" | poc | poc |
| Production incident — "Fix this now" | hotfix | hotfix |

### 8.2 Creating a Spawn

```
/gen-spawn --type spike --parent REQ-F-TASK-001 \
  --reason "Evaluate SQLAlchemy async vs sync for our workload" \
  --duration "3 days"
```

This creates a child vector (`REQ-F-SPIKE-001`) with:
- A limited graph (spike profile: 2 edges)
- A time-box (3 days)
- A link to the parent feature

### 8.3 Time-Boxes

Child vectors (except features) are **time-boxed**. When the time-box expires:
- The child converges with whatever results it has
- Partial findings are packaged as the fold-back payload
- The parent is unblocked

Check remaining time:

```
/gen-status --feature REQ-F-SPIKE-001
```

```
REQ-F-SPIKE-001  SQLAlchemy async evaluation
  Type: spike
  Time-box: 1d 4h remaining (3d total)
  Parent: REQ-F-TASK-001 (blocked at design)
```

### 8.4 Fold-Back

When a child vector converges (or its time-box expires), its results fold back to the parent:

1. Child outputs are written to `.ai-workspace/features/fold-back/REQ-F-SPIKE-001.md`
2. Parent's Context[] is updated with the findings
3. Parent's blocked edge is unblocked
4. `spawn_folded_back` event is emitted

The next time you iterate on the parent, the child's findings are in context.

### 8.5 Vector Type Quick Reference

| Type | Default Duration | Convergence | Fold-Back |
|------|-----------------|-------------|-----------|
| feature | None (unbounded) | All required checks pass | Permanent assets |
| discovery | Configurable | Question answered OR time-box | Findings as context |
| spike | 1 week | Risk assessed OR time-box | ADR + findings |
| poc | 3 weeks | Hypothesis confirmed/rejected OR time-box | Prototype + assessment |
| hotfix | 4 hours | Fix verified in production | Fix + spawns remediation feature |

---

## 9. Getting Unstuck

### 9.1 How Stuck Detection Works

If the same delta (number of failing checks) persists for 3 or more consecutive iterations on the same edge, Genesis marks the feature as `STUCK`.

`/gen-start` detects this automatically:

```
STATE: STUCK

REQ-F-TASK-001 on code_unit_tests: delta=2 unchanged for 4 iterations
  Failing: test_coverage_minimum, all_req_keys_have_tests
```

### 9.2 The Escalation Queue

View all items needing attention:

```
/gen-escalate
```

```
ESCALATION QUEUE (3 items)

[C1] STUCK  REQ-F-TASK-001 on code_unit_tests
     delta=2 unchanged for 4 iterations
     Failing: test_coverage_minimum, all_req_keys_have_tests

[H1] INTENT  INT-OBS-042 "Missing test for REQ-F-TASK-001.3"
     Source: gap observer
     Raised: 2026-02-25T10:30:00Z

[M1] REVIEW  REQ-F-AUTH-001 on requirements_design
     Human review pending since 2026-02-24
```

### 9.3 Recovery Options

Process items interactively:

```
/gen-escalate --action
```

For each item, you choose:

| Option | When to Use |
|--------|-------------|
| **Spawn discovery** | You need to investigate *why* it is stuck |
| **Force iterate** | Try once more with additional context or a different approach |
| **Relax convergence** | Mark failing checks as advisory (they still report but do not block) |
| **Escalate to human** | Review the asset yourself and provide specific guidance |
| **Dismiss** | Acknowledge the signal, log a reason, and move on |

### 9.4 Zooming In

If an edge feels too coarse, zoom in to see sub-steps:

```
/gen-zoom in --edge "code_unit_tests"
```

```
code <-> unit_tests decomposes into:

  RED      Write failing test (Validates: REQ-*)
  GREEN    Write minimal code to pass (Implements: REQ-*)
  REFACTOR Improve quality while tests green
  COMMIT   Save with REQ key in commit message
```

This can help identify which phase of the TDD cycle is causing problems.

---

## 10. Command Reference

### /gen-init

**Initialize a Genesis workspace.**

```
/gen-init [--force] [--backup] [--impl "name"]
```

| Option | Description |
|--------|-------------|
| (none) | Create missing files only (safe default) |
| `--force` | Overwrite framework files (preserves user content) |
| `--backup` | Create backup before changes |
| `--impl` | Implementation name (auto-detected if omitted) |

Creates `.ai-workspace/` with graph topology, edge configs, profiles, project constraints template, feature vector template, and event log. Auto-detects project name, language, and test runner.

---

### /gen-start

**State-driven router. The primary entry point.**

```
/gen-start [--feature "REQ-F-*"] [--edge "source->target"] [--auto] [--profile "standard"]
```

| Option | Description |
|--------|-------------|
| (none) | Detect state, select feature/edge, run one iteration |
| `--feature` | Override automatic feature selection |
| `--edge` | Override automatic edge determination |
| `--auto` | Loop until convergence or human gate |
| `--profile` | Override profile for new features |

State detection (first match wins):

| State | Detection | Action |
|-------|-----------|--------|
| UNINITIALISED | No `.ai-workspace/` | Progressive init (5 questions) |
| NEEDS_CONSTRAINTS | Mandatory constraint dimensions empty | Prompt for constraints |
| NEEDS_INTENT | No intent or placeholder only | Intent authoring |
| NO_FEATURES | Intent exists, no feature vectors | Feature creation |
| STUCK | Same delta for 3+ iterations | Stuck recovery guidance |
| ALL_BLOCKED | All features blocked | Show blockers |
| IN_PROGRESS | Active features with work to do | Select feature/edge, iterate |
| ALL_CONVERGED | All features converged | Suggest `/gen-gaps` then `/gen-release` |

---

### /gen-iterate

**Run one iteration on a specific graph edge.**

```
/gen-iterate --edge "source->target" --feature "REQ-F-*" [--auto] [--profile "name"]
```

| Option | Description |
|--------|-------------|
| `--edge` | The graph transition (e.g., `design->code`, `code<->unit_tests`) |
| `--feature` | The feature vector being worked on |
| `--auto` | Auto-iterate until convergence (pauses at human gates) |
| `--profile` | Override projection profile |

The iterate agent:
1. Loads edge config and project constraints
2. Builds the effective evaluator checklist
3. Analyses the source asset for gaps and ambiguities
4. Generates or evaluates the target asset
5. Runs all evaluators (deterministic, agent, human)
6. Reports delta (failing required checks)
7. Emits events and updates feature vector
8. Converges when delta = 0

Output:

```
ITERATION REPORT
════════════════
Edge: design -> code
Feature: REQ-F-TASK-001
Iteration: 2

CHECKLIST: 6/6 required checks pass
  tests_pass           deterministic  PASS
  lint_passes          deterministic  PASS
  coverage_threshold   deterministic  PASS
  req_tags_present     agent          PASS
  all_req_keys_covered agent          PASS
  code_quality         agent          PASS

DELTA: 0
STATUS: CONVERGED
```

---

### /gen-status

**Show feature vector progress and project health.**

```
/gen-status [--feature "REQ-F-*"] [--verbose] [--gantt] [--health] [--functor]
```

| Option | Description |
|--------|-------------|
| (none) | Summary of all features with state detection |
| `--feature` | Detailed status for a specific feature |
| `--verbose` | Iteration history and evaluator details |
| `--gantt` | Mermaid Gantt chart of build schedule |
| `--health` | Workspace integrity check |
| `--functor` | Functor encoding registry and escalation history |

---

### /gen-spawn

**Spawn a child vector for investigation or risk mitigation.**

```
/gen-spawn --type {discovery|spike|poc|hotfix|feature} --parent "REQ-F-*" --reason "why" [--duration "time"]
```

| Option | Description |
|--------|-------------|
| `--type` | Vector type (determines profile and time-box) |
| `--parent` | Parent feature vector (omit for top-level features) |
| `--reason` | Why this child is needed |
| `--duration` | Time-box override (e.g., "3 days", "4 hours") |

---

### /gen-gaps

**Traceability validation across three layers.**

```
/gen-gaps [--layer 1|2|3|all] [--scope code|tests|telemetry|all] [--feature "REQ-F-*"]
```

| Option | Description |
|--------|-------------|
| `--layer` | Which layer to validate (default: all) |
| `--scope` | Focus on specific asset type |
| `--feature` | Limit to specific feature |

Layer 1: REQ tag coverage (code + tests). Layer 2: Test gap analysis (spec vs tests). Layer 3: Telemetry gap analysis (code vs telemetry).

---

### /gen-review

**Human evaluator review point.**

```
/gen-review --feature "REQ-F-*" [--edge "source->target"]
```

| Option | Description |
|--------|-------------|
| `--feature` | Feature to review |
| `--edge` | Specific edge (defaults to current active) |

Presents the current candidate with evaluator results. You approve, reject with feedback, or request refinements.

---

### /gen-spec-review

**Formal spec-boundary review with gradient checks.**

```
/gen-spec-review --feature "REQ-F-*" --edge "source->target" [--diff] [--checklist-only]
```

| Option | Description |
|--------|-------------|
| `--feature` | Feature to review |
| `--edge` | Spec-boundary edge |
| `--diff` | Show source vs target side-by-side |
| `--checklist-only` | Print checklist without running it |

Checks three dimensions: completeness (coverage), fidelity (faithfulness), and boundary (level separation).

---

### /gen-zoom

**Navigate zoom levels in the graph.**

```
/gen-zoom [in|out|show] --edge "source->target" [--feature "REQ-F-*"] [--depth n]
```

| Option | Description |
|--------|-------------|
| `in` | Zoom into edge sub-steps |
| `out` | Zoom out to aggregate view |
| `show` | Show current level (default) |
| `--edge` | Edge to zoom |
| `--depth` | Levels to zoom (default: 1) |

---

### /gen-escalate

**View and process the escalation queue.**

```
/gen-escalate [--feature "REQ-F-*"] [--severity critical|high|medium|all] [--action]
```

| Option | Description |
|--------|-------------|
| (none) | Show current queue |
| `--feature` | Filter to specific feature |
| `--severity` | Filter by minimum severity |
| `--action` | Interactive mode — process items one by one |

Queue sources: stuck features, tolerance breaches, unactioned intents, pending reviews, max iteration breaches.

---

### /gen-checkpoint

**Save an immutable workspace snapshot.**

```
/gen-checkpoint [--message "description"]
```

Creates a snapshot at `.ai-workspace/snapshots/snapshot-{timestamp}.yml` with context hash, feature states, and git ref.

---

### /gen-trace

**Trace a REQ key through the asset graph.**

```
/gen-trace "REQ-*" [--direction forward|backward|both]
```

| Option | Description |
|--------|-------------|
| `--direction` | Trace direction (default: both) |

Shows where a REQ key appears (or is missing) across all asset types.

---

### /gen-release

**Create a release with changelog and REQ coverage.**

```
/gen-release --version "semver" [--dry-run]
```

| Option | Description |
|--------|-------------|
| `--version` | Semantic version (e.g., "1.0.0") |
| `--dry-run` | Preview without creating tags/artifacts |

Validates readiness, generates changelog, creates release manifest, tags the commit.

---

## 11. Workspace Reference

### 11.1 Directory Structure

```
.ai-workspace/
├── events/events.jsonl           # Source of truth — append-only event log
├── features/
│   ├── active/                   # Feature vectors in progress (YAML)
│   ├── completed/                # Converged feature vectors
│   └── fold-back/                # Child vector results
├── graph/
│   ├── graph_topology.yml        # 10 asset types, 10 transitions
│   ├── evaluator_defaults.yml    # 3 evaluator types, processing phases
│   ├── edges/                    # Per-edge evaluator configs (10 files)
│   └── profiles/                 # Projection profiles (6 files)
├── {impl}/context/
│   ├── project_constraints.yml   # Toolchain, thresholds, standards
│   └── context_manifest.yml      # Content-addressable hash tracking
├── tasks/
│   ├── active/ACTIVE_TASKS.md    # Current work (derived view)
│   └── finished/                 # Completed task documentation
├── snapshots/                    # Immutable checkpoints
└── STATUS.md                     # Auto-generated status (derived view)
```

### 11.2 Key Files

**events.jsonl** — Every operation emits events. Common event types:

| Event | When |
|-------|------|
| `project_initialized` | `/gen-init` completes |
| `edge_started` | First iteration on an edge for a feature |
| `iteration_completed` | Every iteration (includes evaluator results, delta) |
| `edge_converged` | Edge passes all required checks |
| `spawn_created` | Child vector spawned |
| `spawn_folded_back` | Child results folded back to parent |
| `intent_raised` | Gap observer detects a signal |
| `review_completed` | Human review decision recorded |
| `checkpoint_created` | Workspace snapshot saved |
| `release_created` | Version released |

**Feature vector YAML** — Each active feature has a YAML file:

```yaml
feature:
  id: REQ-F-TASK-001
  title: Task Management CRUD
  intent: INT-TASK-001
  vector_type: feature
  profile: standard
  status: iterating

trajectory:
  intent_requirements: converged
  requirements_design: converged
  design_code: converged
  code_unit_tests: iterating (iter 3, delta 1)
```

**project_constraints.yml** — Your toolchain and thresholds. Evaluator checks resolve `$variables` from this file (e.g., `$tools.test_runner.command` becomes `pytest`).

### 11.3 Profiles

Profiles live in `.ai-workspace/graph/profiles/`. To customize:

1. Copy an existing profile (e.g., `standard.yml`)
2. Modify edges, evaluators, or convergence rules
3. Reference it with `--profile your_profile`

---

## 12. Pitfalls and FAQ

**Q: I ran `/gen-start` and nothing happened.**
A: Check that the plugin is installed (`settings.json` has genisis enabled). Restart Claude Code after installation.

**Q: How do I undo an iteration?**
A: You don't undo — you iterate again. Provide feedback on what was wrong and the next iteration uses your feedback as context. Events are append-only.

**Q: When should I use `/gen-start` vs `/gen-iterate`?**
A: Use `/gen-start` almost always — it detects state and routes automatically. Use `/gen-iterate` only when you want to target a specific edge and feature directly.

**Q: Can I skip edges?**
A: Yes, use profiles. The `standard` profile skips UAT, CI/CD, and telemetry edges. The `hotfix` profile goes straight to code + tests. Or create a custom profile.

**Q: How do I use this with an existing codebase?**
A: Install Genesis, write your intent, spawn features for the capabilities you want to add. Existing code is context — Genesis does not require starting from zero.

**Q: What if I disagree with the agent's output?**
A: Reject it in the human review step. Provide specific feedback. The next iteration uses your feedback as additional context.

**Q: What is the difference between `/gen-review` and `/gen-spec-review`?**
A: `/gen-spec-review` is for spec-boundary edges (intent to requirements, requirements to design) and adds gradient checks (completeness, fidelity, boundary). `/gen-review` is the general human gate.

**Q: Can I change the graph topology?**
A: Yes. Edit `.ai-workspace/graph/graph_topology.yml`. You can add asset types, transitions, or constraint dimensions. Existing features will continue with their original topology.

**Q: The event log is getting large.**
A: It is append-only by design. Use `/gen-checkpoint` to mark known-good states. Old events are not deleted but are rarely read directly — all views are derived projections.

**Q: What are the REQ key naming conventions?**
A: Format: `REQ-{TYPE}-{DOMAIN}-{SEQ}` where TYPE is `F` (functional), `NFR` (non-functional). Examples: `REQ-F-AUTH-001`, `REQ-NFR-PERF-001`. Sub-requirements use dots: `REQ-F-AUTH-001.1`.

---

## 13. Glossary

| Term | Definition |
|------|-----------|
| **Asset** | A typed artifact in the graph (intent, requirements, design, code, etc.) |
| **Candidate** | An asset produced by iterate() that has not yet passed all evaluators |
| **Convergence** | When all required evaluators pass (delta = 0) on an edge |
| **Constraint dimension** | A mandatory or advisory technical decision resolved at design time |
| **Delta** | The count of failing required evaluator checks |
| **Edge** | A transition between two asset types in the graph |
| **Evaluator** | A quality check — deterministic, agent, or human |
| **Feature vector** | A single capability's trajectory through the asset graph |
| **Fold-back** | When a child vector's results are returned to its parent's context |
| **Graph** | The topology of asset types and admissible transitions |
| **Intent** | The raw problem/opportunity statement that spawns development |
| **Iterate** | The single operation: `iterate(Asset, Context[], Evaluators) -> Asset'` |
| **Profile** | A projection that selects which edges and evaluators apply |
| **REQ key** | A unique, immutable identifier for a requirement (e.g., `REQ-F-AUTH-001`) |
| **Spawn** | Creating a child vector (discovery, spike, poc, hotfix) from a parent feature |
| **Stable (Markov object)** | An asset that has converged — it will not change unless new intent arrives |
| **Time-box** | A duration limit on child vectors; on expiry, fold-back with partial results |
| **Trajectory** | The sequence of edges a feature vector traverses through the graph |
| **Vector type** | The kind of work: feature, discovery, spike, poc, or hotfix |

---

## Further Reading

- **[Quick Start](../imp_claude/QUICKSTART.md)** — One-page install and first run
- **[Genesis Bootloader](GENESIS_BOOTLOADER.md)** — Minimal context for LLM sessions
- **[Executive Summary](EXECUTIVE_SUMMARY.md)** — Condensed formal system overview
- **[Asset Graph Model](AI_SDLC_ASSET_GRAPH_MODEL.md)** — Full formal specification
- **[Projections & Invariants](PROJECTIONS_AND_INVARIANTS.md)** — Projection theory and vector types
- **[Implementation Requirements](AISDLC_IMPLEMENTATION_REQUIREMENTS.md)** — All 69 platform-agnostic requirements
- **[Feature Vectors](FEATURE_VECTORS.md)** — Feature decomposition and dependency graph
- **[UX Specification](UX.md)** — User journeys and validation scenarios
