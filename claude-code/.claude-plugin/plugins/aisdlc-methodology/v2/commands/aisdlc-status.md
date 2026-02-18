# /aisdlc-status - Show Feature Vector Progress

Display the current state of all feature vectors and their trajectories through the graph.

<!-- Implements: REQ-TOOL-002, REQ-FEAT-002 -->

## Usage

```
/aisdlc-status [--feature "REQ-F-*"] [--verbose]
```

| Option | Description |
|--------|-------------|
| (none) | Show summary of all feature vectors |
| `--feature` | Show detailed status for a specific feature |
| `--verbose` | Show iteration history and evaluator details |

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

Context Hash: sha256:a1b2c3...
```
