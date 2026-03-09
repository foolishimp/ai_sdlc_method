# Genesis User Guide

**Version**: 2.10.0 | **Platform**: Claude Code | **Date**: 2026-03-10 (updated)

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
6. [CONSENSUS: Multi-Stakeholder Evaluation](#6-consensus-multi-stakeholder-evaluation)
7. [Releasing](#7-releasing)
8. [Working with Multiple Features](#8-working-with-multiple-features)
9. [Spawning Child Vectors](#9-spawning-child-vectors)
10. [Getting Unstuck](#10-getting-unstuck)
11. [Command Reference](#11-command-reference)
12. [Workspace Reference](#12-workspace-reference)
13. [Pitfalls and FAQ](#13-pitfalls-and-faq)
14. [Glossary](#14-glossary)

---

## 1. How Genesis Works

Genesis gives you a structured way to build software with AI. Instead of ad-hoc prompting, every piece of work follows a graph of typed assets, connected by transitions, each with defined quality checks.

### 1.1 The Asset Graph

Ten typed assets connected by directed transitions. The graph is cyclic — telemetry feeds back to intent.

```
Intent ──> Requirements ──> Design ──> Code <──> Unit Tests
                              │
                              ├──> Test Cases
                              └──> UAT Tests

Code ──> CI/CD ──> Running System ──> Telemetry ──> Intent (feedback)
```

| Asset Type | Definition |
|-----------|-----------|
| Intent | Problem/opportunity statement |
| Requirements | Structured, testable requirements with unique REQ keys |
| Design | Technical architecture — components, ADRs, data models |
| Code | Source code tagged with REQ keys |
| Unit Tests | Tests co-evolved with code via TDD |
| Test Cases | Integration/system tests derived from design |
| UAT Tests | Business acceptance tests in business language (BDD) |
| CI/CD | Pipeline configuration and build artifacts |
| Running System | Deployed system with health checks |
| Telemetry | Runtime metrics and alerts tagged with REQ keys |

### 1.2 The Only Operation: iterate()

One operation:

```
iterate(Asset, Context[], Evaluators) -> Asset'
```

| Parameter | Role |
|-----------|------|
| **Asset** | Current state of a typed artifact |
| **Context[]** | Constraints bounding construction (project constraints, ADRs, standards) |
| **Evaluators** | Quality checks defining convergence |

The agent generates a candidate, runs evaluators, and reports results. When all required checks pass (delta = 0), the edge **converges** and the feature advances to the next transition. Otherwise, iterate again.

### 1.3 Three Evaluator Types

| Type | Mechanism | Example |
|------|-----------|---------|
| **Deterministic** | Execute command, check exit code | `pytest --tb=short` exits 0 |
| **Agent** | LLM assesses against criterion | "All REQ keys have corresponding code" |
| **Human** | Practitioner reviews and approves/rejects | "Does this design meet requirements?" |

Evaluators compose per edge. Execution order: deterministic (cheap) → agent (moderate) → human (expensive, only when needed).

### 1.4 Feature Vectors and REQ Keys

A **feature vector** is a single capability's trajectory through the graph. Each feature carries a unique REQ key that threads through every artifact:

```
Spec:       REQ-F-AUTH-001 defined
Design:     Implements: REQ-F-AUTH-001
Code:       # Implements: REQ-F-AUTH-001
Tests:      # Validates: REQ-F-AUTH-001
Telemetry:  logger.info("login", req="REQ-F-AUTH-001")
```

REQ keys provide end-to-end traceability from intent to runtime.

### 1.5 Profiles

**Profiles** select which transitions and evaluators apply to a given feature:

| Profile | Edges | When to Use |
|---------|-------|-------------|
| **full** | All 10 | Regulated/audited systems, full governance |
| **standard** | Intent through Unit Tests (4 edges) | Normal feature development |
| **poc** | Intent through Code (3 edges) | Prove feasibility before committing |
| **spike** | Intent through Code (3 edges) | Research a technical question |
| **hotfix** | Intent + Code + Unit Tests (3 edges) | Emergency production fix |
| **minimal** | Intent + Code (2 edges) | Smallest valid methodology instance |

### 1.6 Event Sourcing

All state derives from an append-only event log: `.ai-workspace/events/events.jsonl`. STATUS.md, feature vectors, and task lists are projections of this log, regenerable at any time.

### 1.7 The Two-Command Interface

Two commands cover daily workflow:

- **`/gen-start`** — State detection and routing. Determines what to do next and delegates.
- **`/gen-status`** — Progress, health, and observability.

The remaining 17 commands address specific scenarios; `/gen-start` handles routing automatically.

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

Or inside Claude Code, run `/gen-start`. State detection will report `NO_FEATURES` (the installer creates a template intent) and guide you to create your first feature vector.

### 2.3 What Gets Created

The installer creates a minimal workspace. Additional configs (evaluator defaults, edge params, profiles, hooks) are delivered by the plugin at runtime.

```
your-project/
├── .claude/
│   └── settings.json                  # Plugin config (marketplace reference)
├── .ai-workspace/                     # Genesis workspace
│   ├── events/events.jsonl            # Event log (source of truth)
│   ├── features/
│   │   ├── active/                    # Feature vectors in progress
│   │   └── completed/                 # Converged feature vectors
│   ├── graph/
│   │   └── graph_topology.yml         # Asset types + transitions
│   ├── context/
│   │   └── project_constraints.yml    # Toolchain + thresholds
│   ├── agents/                        # Per-agent working state
│   ├── spec/                          # Derived spec views
│   ├── tasks/
│   │   ├── active/ACTIVE_TASKS.md     # Current work
│   │   └── finished/                  # Completed task docs
│   └── STATUS.md                      # Auto-generated status view
├── specification/
│   └── INTENT.md                      # Intent document template
└── CLAUDE.md                          # Genesis Bootloader (appended)
```

The plugin provides at runtime:
- **Hooks**: session health, edge detection, artifact observation, stop-check enforcement
- **Edge configs**: per-edge evaluator checklists (10 files in `edge_params/`)
- **Profiles**: projection profiles (full, standard, poc, spike, hotfix, minimal)
- **Evaluator defaults**: evaluator types and processing phases

### 2.4 Alternative Installation

**Marketplace (commands only, no hooks):**

Add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "genesis": {
      "source": { "source": "github", "repo": "foolishimp/ai_sdlc_method" }
    }
  },
  "enabledPlugins": { "genesis@genesis": true }
}
```

Then run `/gen-init` to create the workspace.

**Local/air-gapped:**

Clone the repo and point to the local path:

```json
{
  "extraKnownMarketplaces": {
    "genesis": {
      "source": {
        "source": "local",
        "path": "/path/to/ai_sdlc_method/imp_claude/code/.claude-plugin"
      }
    }
  },
  "enabledPlugins": { "genesis@genesis": true }
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

Running example throughout: **tasktracker** — a Python REST API for task management.

### 3.1 Create Project Directory

```bash
mkdir tasktracker && cd tasktracker
```

### 3.2 Install Genesis

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 -
```

Restart Claude Code. The installer creates `.ai-workspace/`, a template `specification/INTENT.md`, and `project_constraints.yml`.

### 3.3 Run /gen-start

```
/gen-start
```

Post-install state is `NO_FEATURES` (template intent exists). Genesis prompts for a feature description.

Alternative: without the installer, `/gen-init` detects `UNINITIALISED` and runs a 5-question progressive init (project name, kind, language, test runner, intent).

### 3.4 Configure Your Project

Edit `specification/INTENT.md`:

```markdown
# Intent: tasktracker

A REST API for creating, listing, completing, and deleting tasks
with user authentication.

## Source
Developer input

## Priority
High
```

Edit `.ai-workspace/context/project_constraints.yml`:

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

### 3.5 Create Your First Feature

`/gen-start` detects `NO_FEATURES` and creates the first feature vector:

```
Feature vector created: REQ-F-TASK-001
Title: Task Management CRUD
Profile: standard
Status: pending
```

Written to `.ai-workspace/features/active/REQ-F-TASK-001.yml`. Contains: REQ key, profile (standard — 4 edges), trajectory, and acceptance criteria derived from intent.

### 3.6 Check Status

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

---

## 4. Working Through the Graph

### 4.1 Intent to Requirements

`/gen-start` detects `IN_PROGRESS`, selects `REQ-F-TASK-001`, identifies `intent_requirements` as the first unconverged edge, and delegates to the iterate agent.

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

5. **Requests human review** — spec-boundary edge requires human approval. Options: approve, reject with feedback, or refine.

On approval: edge converges, event emitted, feature vector updated.

### 4.2 Requirements to Design

Next unconverged edge: `requirements_design`.

Genesis prompts for **constraint dimensions** — mandatory technical decisions not yet resolved:

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

Answers for this example:
- **ecosystem**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **deployment**: Docker containers on AWS ECS
- **security**: JWT with bcrypt password hashing
- **build_system**: pip + pyproject.toml

The iterate agent produces: component architecture, ADRs per constraint dimension, data models, and API endpoint specifications. Agent evaluator checks completeness and fidelity; human evaluator reviews. On approval, edge converges.

### 4.3 Design to Code

Next edge: `design_code`. The iterate agent scaffolds code from design:

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

Evaluators: deterministic (compile, lint), agent (REQ tag coverage, design conformance). On failure, the agent remediates and re-evaluates. delta = 0 → converge.

### 4.4 Code and Unit Tests (TDD Co-evolution)

Next edge: `code_unit_tests`. Bidirectional — code and tests co-evolve via TDD:

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

The agent loops RED→GREEN→REFACTOR until all checks pass. `--auto` suppresses inter-iteration pauses.

### 4.5 Checking Progress

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

Trace a REQ key:

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

Validate traceability:

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

Edges with `human` evaluators pause for review:

```
/gen-review --feature REQ-F-TASK-001
```

Actions:

| Action | What Happens |
|--------|-------------|
| **Approve** | Edge converges; feature moves to next transition |
| **Reject** | Feedback recorded; next iteration uses your feedback as context |
| **Refine** | Specific changes captured; iterate agent applies them |

### 5.2 Spec-Boundary Reviews

Spec-boundary edges (intent→requirements, requirements→design) include a **gradient check** across three dimensions:

```
/gen-spec-review --feature REQ-F-TASK-001 --edge "requirements→design"
```

| Dimension | What It Checks | Example |
|-----------|---------------|---------|
| **Completeness** | Does target cover everything in source? | 15/16 REQ keys have design bindings |
| **Fidelity** | Does target faithfully represent source? | No requirements weakened or narrowed |
| **Boundary** | Does target stay within its specification level? | Design doesn't introduce implementation details |

Disposition: **Approve** (minor issues), **Reject** (rework edge), or **Escalate** (source asset needs revision — blocks edge, re-opens upstream).

### 5.3 Traceability Validation

`/gen-gaps` validates three traceability layers:

| Layer | What It Checks | When to Run |
|-------|---------------|-------------|
| **1: REQ Tags** | Code has `Implements:`, tests have `Validates:` | After code/tests edges |
| **2: Test Coverage** | Every REQ key in spec has at least one test | Before release |
| **3: Telemetry** | Every REQ key in code has telemetry tagging | Before production |

```
/gen-gaps --layer all
```

Gaps emit `intent_raised` events, feeding the consciousness loop.

### 5.4 Checkpoints

```
/gen-checkpoint --message "All CRUD tests passing, auth next"
```

Creates an immutable snapshot at `.ai-workspace/snapshots/snapshot-{timestamp}.yml` containing context hash (SHA-256), feature states, and git ref. Recommended before risky changes or at session end.

---

## 6. CONSENSUS: Multi-Stakeholder Evaluation

CONSENSUS is a parameterisation of the human evaluator (`F_H`) for multi-party evaluation. Instead of a single reviewer approving an edge, a roster of participants votes; convergence requires a quorum. Use it for ADR acceptance, spec reviews, release gates, or any decision needing broader accountability.

### 6.1 When to Use CONSENSUS

| Situation | Why CONSENSUS | Quorum |
|-----------|--------------|--------|
| Major ADR (architecture decision) | Multiple tenants affected | majority |
| Spec-level change (updates CLAUDE.md bootloader) | Shared contract — all tenants vote | supermajority |
| Release gate for external users | Business sign-off required | unanimity |
| Cross-agent design review | Claude + Gemini + Codex + human | majority |

### 6.2 CONSENSUS Lifecycle

```
/gen-consensus-open  →  participants receive consensus_requested event
                     →  each participant runs /gen-vote
                     →  optionally /gen-comment to raise concerns
                     →  /gen-dispose to resolve gating comments
                     →  quorum observer emits consensus_reached or consensus_failed
                     →  if failed: /gen-consensus-recover selects recovery path
```

### 6.3 Opening a Review

```
/gen-consensus-open \
  --artifact "specification/adrs/ADR-S-027-foo.md" \
  --roster "gen-dev-observer,gen-cicd-observer,human:jim" \
  --quorum majority \
  --review-closes-in 86400
```

This emits a `consensus_requested` event and stops. Observer relays react independently — no polling, no orchestration.

| Option | Default | Description |
|--------|---------|-------------|
| `--artifact` | required | Path to document under review |
| `--roster` | required | Comma-separated participant IDs |
| `--quorum` | majority | `majority`, `supermajority`, or `unanimity` |
| `--review-closes-in` | 86400 (24h) | Seconds until window closes |

### 6.4 Casting Votes

Each participant calls:

```
/gen-vote --review-id REVIEW-ADR-S-027-1 --verdict approve --rationale "Design is sound"
```

Verdicts: `approve`, `reject`, `abstain`. Votes are **most-recent-per-relay** — a participant may revise their vote as the artifact evolves; only the latest vote counts toward quorum.

### 6.5 Comments and Gating

To raise a concern that must be addressed before consensus can be reached:

```
/gen-comment \
  --review-id REVIEW-ADR-S-027-1 \
  --content "Section 3.2 conflicts with REQ-F-AUTH-001 — needs clarification"
```

A comment submitted within the review window is **gating** — it blocks `consensus_reached` until dispositioned. Late comments (after window closes) are recorded as context only.

### 6.6 Dispositioning Gating Comments

The proposer disposes of each gating comment:

```
/gen-dispose \
  --review-id REVIEW-ADR-S-027-1 \
  --comment-ts 2026-03-10T14:30:00Z \
  --disposition resolved \
  --rationale "Updated §3.2 to align with REQ-F-AUTH-001"
```

| Disposition | When to Use |
|-------------|------------|
| `resolved` | Concern addressed in the artifact |
| `rejected` | Concern not valid or not applicable |
| `acknowledged` | Noted; accepted as known risk or deferred |
| `scope_change` | Valid concern but out of scope — triggers `spec_modified` |

When all gating comments are dispositioned and quorum is satisfied, the quorum observer emits `consensus_reached`.

### 6.7 Recovery After Failure

If consensus is not reached (`consensus_failed` event), choose a recovery path:

```
/gen-consensus-recover \
  --review-id REVIEW-ADR-S-027-1 \
  --path re_open \
  --rationale "Extend window — two participants didn't have time to review"
```

| Path | When to Use |
|------|-------------|
| `re_open` | Low participation or relays need more time |
| `narrow_scope` | Extract contested section; rest is agreed |
| `abandon` | Proposal not viable in current form |

### 6.8 Feature Proposals Queue

The consciousness loop produces draft feature proposals when `/gen-gaps` or sensory monitors detect signals:

```
/gen-review-proposal --list
```

```
Pending Feature Proposals
=========================
PROP-001  high    "Add tests for REQ-F-AUTH-002"   2d ago
PROP-002  medium  "Telemetry for REQ-F-DB-001"      1d ago
```

Act on each:

```
/gen-review-proposal --approve PROP-001
/gen-review-proposal --dismiss PROP-002 --reason "Telemetry deferred to v1.1 sprint"
```

Approved proposals inflate the workspace trajectory (new feature vector created). Dismissed proposals are archived.

---

## 7. Releasing

### 7.1 Pre-Release Checklist

```
/gen-gaps                    # Traceability across all layers
/gen-status --health         # Workspace integrity
/gen-escalate                # Unactioned signals
```

### 7.2 Create a Release

```
/gen-release --version "1.0.0"
```

Sequence: validate readiness → generate changelog (commits with REQ keys since last tag) → create release manifest with REQ coverage → git tag `v1.0.0` → emit `release_created` event.

### 7.3 Dry Run

```
/gen-release --version "1.0.0" --dry-run
```

Preview only — no tags or artifacts created.

---

## 8. Working with Multiple Features

### 8.1 Adding Features

Run `/gen-start` to add features at any time. Genesis creates a new feature vector and trajectory (e.g., `REQ-F-AUTH-001`).

### 8.2 Feature Selection

With multiple active features, `/gen-start` selects by priority:

1. **Time-boxed spawns approaching expiry** (< 25% budget remaining)
2. **Closest to complete** (fewest unconverged edges)
3. **Highest priority** (critical > high > medium > low)
4. **Most recently touched** (from event timestamps)

### 8.3 Feature Dependencies

Dependencies block downstream features at the declared edge. Example: `REQ-F-AUTH-001` must complete before `REQ-F-TASK-001` can proceed past design.

`/gen-status` output:

```
Active Features:
  REQ-F-TASK-001  Task CRUD        design       iter 1  standard  BLOCKED (depends: REQ-F-AUTH-001)
  REQ-F-AUTH-001  Authentication   code_tests   iter 2  standard
```

### 8.4 Overriding Selection

```
/gen-start --feature REQ-F-AUTH-001
```

Direct edge targeting:

```
/gen-iterate --edge "code↔unit_tests" --feature REQ-F-AUTH-001
```

---

## 9. Spawning Child Vectors

Child vectors branch from a parent feature for investigation, then fold results back as context.

### 9.1 When to Spawn

| Situation | Vector Type | Profile |
|-----------|------------|---------|
| Knowledge gap — "How does X work?" | discovery | minimal |
| Technical risk — "Can we use library Y?" | spike | spike |
| Feasibility — "Will approach Z scale?" | poc | poc |
| Production incident — "Fix this now" | hotfix | hotfix |

### 9.2 Creating a Spawn

```
/gen-spawn --type spike --parent REQ-F-TASK-001 \
  --reason "Evaluate SQLAlchemy async vs sync for our workload" \
  --duration "3 days"
```

Creates child vector `REQ-F-SPIKE-001`: limited graph (spike profile, 3 edges), time-box (3 days), linked to parent.

### 9.3 Time-Boxes

Non-feature child vectors are time-boxed. On expiry: child converges with partial results, fold-back payload packaged, parent unblocked.

Remaining time:

```
/gen-status --feature REQ-F-SPIKE-001
```

```
REQ-F-SPIKE-001  SQLAlchemy async evaluation
  Type: spike
  Time-box: 1d 4h remaining (3d total)
  Parent: REQ-F-TASK-001 (blocked at design)
```

### 9.4 Fold-Back

On child convergence or time-box expiry:

1. Outputs written to `.ai-workspace/features/fold-back/REQ-F-SPIKE-001.md`
2. Parent's Context[] updated with findings
3. Parent's blocked edge unblocked
4. `spawn_folded_back` event emitted

Subsequent parent iterations include child findings in context.

### 9.5 Vector Type Quick Reference

| Type | Default Duration | Convergence | Fold-Back |
|------|-----------------|-------------|-----------|
| feature | None (unbounded) | All required checks pass | Permanent assets |
| discovery | Configurable | Question answered OR time-box | Findings as context |
| spike | 1 week | Risk assessed OR time-box | ADR + findings |
| poc | 3 weeks | Hypothesis confirmed/rejected OR time-box | Prototype + assessment |
| hotfix | 4 hours | Fix verified in production | Fix + spawns remediation feature |

---

## 10. Getting Unstuck

### 10.1 How Stuck Detection Works

Same delta persisting for 3+ consecutive iterations on one edge → feature marked `STUCK`.

`/gen-start` detects automatically:

```
STATE: STUCK

REQ-F-TASK-001 on code_unit_tests: delta=2 unchanged for 4 iterations
  Failing: test_coverage_minimum, all_req_keys_have_tests
```

### 10.2 The Escalation Queue

View queue:

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

### 10.3 Recovery Options

Interactive processing via `/gen-escalate --action`. Per-item options:

| Option | When to Use |
|--------|-------------|
| **Spawn discovery** | Investigate root cause |
| **Force iterate** | Retry with additional context |
| **Relax convergence** | Mark failing checks as advisory (report but do not block) |
| **Escalate to human** | Direct review with specific guidance |
| **Dismiss** | Acknowledge, log reason, proceed |

### 10.4 Zooming In

Decompose an edge into sub-steps:

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

Identifies which TDD phase is failing.

---

## 11. Command Reference

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

Scaffolds `.ai-workspace/` with graph topology, edge configs, profiles, templates, and event log. Auto-detects project metadata.

---

### /gen-start

**State-driven router. The primary entry point.**

```
/gen-start [--feature "REQ-F-*"] [--edge "source→target"] [--auto] [--profile "standard"]
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
/gen-iterate --edge "source→target" --feature "REQ-F-*" [--auto] [--profile "name"]
```

| Option | Description |
|--------|-------------|
| `--edge` | The graph transition (e.g., `design→code`, `code↔unit_tests`) |
| `--feature` | The feature vector being worked on |
| `--auto` | Auto-iterate until convergence (pauses at human gates) |
| `--profile` | Override projection profile |

Agent sequence: load edge config → build effective checklist → analyse source (backward gaps) → generate/evaluate target → run evaluators → report delta → emit events → converge when delta = 0.

Output:

```
ITERATION REPORT
════════════════
Edge: design → code
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
/gen-spawn --type {discovery|spike|poc|hotfix} --parent "REQ-F-*" --reason "why" [--duration "time"]
```

| Option | Description |
|--------|-------------|
| `--type` | Vector type: discovery, spike, poc, or hotfix |
| `--parent` | Parent feature vector (required) |
| `--reason` | Why this child is needed |
| `--duration` | Time-box override (e.g., "3 days", "4 hours") |

Note: Top-level feature vectors are created by `/gen-start` when it detects `NO_FEATURES` state, not by `/gen-spawn`.

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
/gen-review --feature "REQ-F-*" [--edge "source→target"]
```

| Option | Description |
|--------|-------------|
| `--feature` | Feature to review |
| `--edge` | Specific edge (defaults to current active) |

Presents candidate with evaluator results. Actions: approve, reject (with feedback), or refine.

---

### /gen-spec-review

**Formal spec-boundary review with gradient checks.**

```
/gen-spec-review --feature "REQ-F-*" --edge "source→target" [--diff] [--checklist-only]
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
/gen-zoom [in|out|show] --edge "source→target" [--feature "REQ-F-*"] [--depth n]
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

Reports REQ key presence or absence across all asset types.

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

### /gen-consensus-open

**Open a multi-stakeholder CONSENSUS review session.**

```
/gen-consensus-open --artifact <path> --roster <participants> [--quorum majority|supermajority|unanimity] [--review-closes-in <seconds>] [--review-id <id>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--artifact` | required | Path to document under review |
| `--roster` | required | Comma-separated participant IDs (`agent-id` or `human:name`) |
| `--quorum` | majority | Convergence threshold |
| `--review-closes-in` | 86400 | Seconds until window closes (default: 24h) |
| `--review-id` | auto | Override the session ID |

Emits `consensus_requested` and stops. Observer relays react independently — no orchestration.

---

### /gen-vote

**Cast a vote in an open CONSENSUS review session.**

```
/gen-vote --review-id <id> --verdict <approve|reject|abstain> [--rationale "<text>"] [--gating]
```

| Option | Description |
|--------|-------------|
| `--review-id` | The review session ID |
| `--verdict` | `approve`, `reject`, or `abstain` |
| `--rationale` | Explanation for your vote (strongly recommended) |
| `--gating` | Also emit a gating comment from the rationale |

Votes are most-recent-per-relay — a participant may revise before the window closes.

---

### /gen-comment

**Submit a comment in an open CONSENSUS review session.**

```
/gen-comment --review-id <id> --content "<text>" [--participant <id>]
```

Comments submitted within the review window are **gating** — they block `consensus_reached` until dispositioned by the proposer. Late comments are recorded as context only.

---

### /gen-dispose

**Disposition a gating comment in a CONSENSUS review session.**

```
/gen-dispose --review-id <id> --comment-ts <timestamp> --disposition <type> --rationale "<text>"
```

| Option | Description |
|--------|-------------|
| `--comment-ts` | Timestamp of the `comment_received` event |
| `--disposition` | `resolved`, `rejected`, `acknowledged`, or `scope_change` |
| `--rationale` | Non-empty explanation (required) |

When all gating comments are dispositioned and quorum is satisfied, the quorum observer emits `consensus_reached`.

---

### /gen-consensus-recover

**Select a recovery path after a CONSENSUS failure.**

```
/gen-consensus-recover --review-id <id> --path <re_open|narrow_scope|abandon> [--rationale "<text>"]
```

| Path | When to Use |
|------|-------------|
| `re_open` | Low participation or relays need more time — new window, same roster |
| `narrow_scope` | Extract contested section; rest is agreed — fold-back and re-review |
| `abandon` | Proposal not viable in current form |

Only valid after a `consensus_failed` event for the review ID.

---

### /gen-review-proposal

**Review draft feature proposals from the consciousness loop.**

```
/gen-review-proposal [--list] [--show PROP-NNN] [--approve PROP-NNN] [--dismiss PROP-NNN --reason "..."]
```

| Option | Description |
|--------|-------------|
| `--list` | List pending proposals (default) |
| `--show PROP-NNN` | Show full proposal detail |
| `--approve PROP-NNN` | Approve — creates a new feature vector |
| `--dismiss PROP-NNN --reason` | Archive with reason |

Proposals are generated by `/gen-gaps` (Layers 1–3) and sensory monitors when they detect signals.

---

## 12. Workspace Reference

### 12.1 Directory Structure

```
.ai-workspace/
├── events/events.jsonl           # Source of truth — append-only event log
├── features/
│   ├── active/                   # Feature vectors in progress (YAML)
│   ├── completed/                # Converged feature vectors
│   └── fold-back/                # Child vector results
├── graph/
│   └── graph_topology.yml        # 10 asset types, 10 transitions
├── context/
│   ├── project_constraints.yml   # Toolchain, thresholds, standards
│   └── context_manifest.yml      # Content-addressable hash tracking
├── agents/                       # Per-agent working state
├── spec/                         # Derived spec views
├── tasks/
│   ├── active/ACTIVE_TASKS.md    # Current work (derived view)
│   └── finished/                 # Completed task documentation
├── snapshots/                    # Immutable checkpoints
└── STATUS.md                     # Auto-generated status (derived view)
```

Additional configs (evaluator defaults, edge params, profiles) are loaded from the plugin at runtime, not stored in the workspace.

### 12.2 Key Files

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
| `consensus_requested` | `/gen-consensus-open` — review session opened |
| `vote_cast` | `/gen-vote` — participant vote recorded |
| `comment_received` | `/gen-comment` — gating or context comment added |
| `comment_dispositioned` | `/gen-dispose` — gating comment resolved |
| `consensus_reached` | Quorum satisfied and all gating comments resolved |
| `consensus_failed` | Quorum not reached or window closed |
| `recovery_path_selected` | `/gen-consensus-recover` — recovery action chosen |
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

**project_constraints.yml** (in `.ai-workspace/context/`) — Your toolchain and thresholds. Evaluator checks resolve `$variables` from this file (e.g., `$tools.test_runner.command` becomes `pytest`).

### 12.3 Profiles

Profiles live in `.ai-workspace/graph/profiles/`. To customize:

1. Copy an existing profile (e.g., `standard.yml`)
2. Modify edges, evaluators, or convergence rules
3. Reference it with `--profile your_profile`

---

## 13. Pitfalls and FAQ

| Question | Answer |
|----------|--------|
| `/gen-start` does nothing | Verify plugin in `settings.json`. Restart Claude Code after install. |
| Undo an iteration? | No undo. Iterate again with feedback. Events are append-only. |
| `/gen-start` vs `/gen-iterate`? | `/gen-start` for automatic routing. `/gen-iterate` for targeting a specific edge/feature. |
| Skip edges? | Use profiles. `standard` skips UAT/CI/CD/telemetry. `hotfix` targets code+tests only. |
| Existing codebase? | Install, write intent, create features for new capabilities. Existing code is context. |
| Disagree with agent output? | Reject in review with specific feedback. Next iteration uses it as context. |
| `/gen-review` vs `/gen-spec-review`? | `/gen-spec-review` adds gradient checks (completeness, fidelity, boundary) at spec-boundary edges. `/gen-review` is the general human gate. |
| Change graph topology? | Edit `.ai-workspace/graph/graph_topology.yml`. Existing features retain their original topology. |
| Event log growing large? | Append-only by design. `/gen-checkpoint` marks known-good states. Views are derived projections. |
| REQ key format? | `REQ-{TYPE}-{DOMAIN}-{SEQ}`. TYPE: `F` (functional), `NFR` (non-functional). Sub-reqs: `REQ-F-AUTH-001.1`. |

---

## 14. Glossary

| Term | Definition |
|------|-----------|
| **Asset** | A typed artifact in the graph (intent, requirements, design, code, etc.) |
| **Candidate** | An asset produced by iterate() that has not yet passed all evaluators |
| **CONSENSUS** | A multi-stakeholder F_H evaluation: roster + quorum rule + review window |
| **Convergence** | When all required evaluators pass (delta = 0) on an edge |
| **Constraint dimension** | A mandatory or advisory technical decision resolved at design time |
| **Delta** | The count of failing required evaluator checks |
| **Disposition** | The resolution of a gating comment (resolved, rejected, acknowledged, scope_change) |
| **Edge** | A transition between two asset types in the graph |
| **Evaluator** | A quality check — deterministic, agent, or human |
| **Feature vector** | A single capability's trajectory through the asset graph |
| **Fold-back** | When a child vector's results are returned to its parent's context |
| **Gating comment** | A comment submitted within the review window that blocks consensus until dispositioned |
| **Graph** | The topology of asset types and admissible transitions |
| **Intent** | The raw problem/opportunity statement that spawns development |
| **Iterate** | The single operation: `iterate(Asset, Context[], Evaluators) -> Asset'` |
| **Profile** | A projection that selects which edges and evaluators apply |
| **Quorum** | The participation threshold required for consensus: majority, supermajority, or unanimity |
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
- **[Implementation Requirements](AISDLC_IMPLEMENTATION_REQUIREMENTS.md)** — All 83 platform-agnostic requirements
- **[Feature Vectors](FEATURE_VECTORS.md)** — Feature decomposition and dependency graph
- **[UX Specification](UX.md)** — User journeys and validation scenarios
