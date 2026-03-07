# Genesis Ecosystem — Methodology Validation Environment

A first-principles ecosystem for the Genesis methodology. Hosts reference projects executed edge-by-edge using Genesis, with **named snapshots** at each convergence point. The event streams produced here are what `genesis_monitor` observes.

Unlike the one-shot E2E tests, the ecosystem supports resetting to any prior convergence point and re-validating — enabling regression detection, cost analysis (H = T + V), and incremental proof of methodology edges.

## Purpose

Prove the transition from theoretical system to practical MVP:
- Each snapshot is a proven convergence point
- F_D evaluation runs in seconds without Claude
- H = T + V tracks the cost of traversal across the trajectory
- Regressions in evaluators are detectable by restoring a snapshot and re-validating

## Target Project

**Temperature Converter Library** — a minimal Python library (3 REQ keys, 1 feature, standard profile):
- `REQ-F-CONV-001`: 6 bidirectional conversion functions (C↔F↔K)
- `REQ-F-CONV-002`: Input validation (TypeError, ValueError)
- Single module: `src/temperature_converter.py`
- Standard profile: 4 edges (intent→req, req→design, design→code, code↔tests)

## Quick Start

```bash
# See available snapshots
make list

# Start from clean install
make init

# Open project/ in Claude Code, run:
#   /gen-start --feature REQ-F-CONV-001
# (iterates intent→requirements edge)

# After requirements edge converges, capture snapshot
make snapshot NAME=01_requirements_done EDGE='intent→requirements'

# Validate current state with F_D evaluators (no Claude needed)
make validate

# Restore to any prior checkpoint and re-run
make restore SNAP=02_design_done
make validate EDGE='code↔unit_tests'
```

## Snapshots

| Snapshot | Edge | H | Description |
|----------|------|---|-------------|
| `00_installed` | (none) | 0 | Clean install — workspace initialised, no edges traversed |
| `01_requirements_done` | intent→requirements | TBD | Requirements spec written and converged |
| `02_design_done` | requirements→design | TBD | Design ADRs written and converged |
| `03_code_tests_done` | code↔unit_tests | TBD | Code + tests generated, all evaluators pass |

`03_code_tests_done` with H=T (V=0) = **MVP proven**.

## MVP Proof Criteria

| Test | Pass condition |
|------|---------------|
| `make init` + `/gen-start` | State detected correctly, begins intent→req |
| Restore `02_design_done` + `make validate` | Engine reports actionable delta or delta=0 |
| Restore `03_code_tests_done` + `make validate` | `H=T`, `V=0`, pytest passes |
| Restore any snap, corrupt code, `make validate` | Delta increases correctly |

## Hamiltonian (H = T + V)

At each snapshot, `snapshot_meta.json` records:
- **T** = total iterations spent (kinetic energy)
- **V** = failing evaluator count (potential energy, = 0 at convergence)
- **H** = T + V (total traversal cost)

The trajectory of H across snapshots shows the cost of convergence at each edge. See `snapshots/manifest.yml` for the full trajectory.

## Structure

```
eco_system/
├── projects/                    # Hosted reference projects (each is a Genesis sub-project)
│   └── temperature_converter/   # Minimal Python library — standard profile, 4 edges
│       ├── CLAUDE.md
│       ├── pyproject.toml
│       ├── specification/INTENT.md
│       ├── src/                 # Generated code
│       ├── tests/               # Generated tests
│       └── .ai-workspace/       # Project's Genesis workspace (events.jsonl here)
├── snapshots/                   # Named convergence checkpoints
│   ├── 00_installed/            # Clean base state (H=0)
│   └── manifest.yml             # H trajectory across all snapshots
├── scripts/
│   ├── snapshot.py              # Capture project → snapshots/<name>/
│   ├── restore.py               # Restore snapshots/<name>/ → project
│   └── validate.py              # Run F_D evaluators, report H
└── Makefile                     # init / list / snapshot / restore / validate
```

## Relationship to Other Components

| | E2E Tests | Ecosystem |
|-|-----------|-----------|
| Location | `imp_claude/tests/e2e/` | `projects/eco_system/` |
| Claude required | Yes | No (F_D validation only) |
| Resettable | No | Yes — any named snapshot |
| Intermediate states | Not accessible | Named snapshots at each edge |
| Purpose | Validate full workflow once | Prove each edge; generate event streams for monitor |

See ADR-029 for the full design rationale.
