# ADR-029: Testbed Snapshot/Restore Environment for MVP Validation

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-TOOL-005 (E2E Validation), REQ-ITER-001 (Convergence), REQ-EVAL-001 (Evaluator Execution)
**Extends**: E2E tests (`imp_claude/tests/e2e/`) — different tool, different purpose
**Supersedes**: Nothing — complements, does not replace, the e2e suite

---

## Context

### The E2E Gap

The existing e2e tests (`imp_claude/tests/e2e/`) run the full methodology via headless Claude and archive the output:

```
spawn temp project → run /gen-start --auto (live Claude) → archive run → validate artifacts
```

This is **one-shot**. There is no mechanism to:
- Restore the project to the state it was in after the `requirements→design` edge converged
- Re-run the engine evaluation from a known-good intermediate state
- Test F_D evaluation independently of F_P construction (without live Claude)
- Reproduce a specific convergence failure deterministically

### The Need

The transition from theoretical system to practical MVP requires an environment where:

1. **First principles**: Start from a clean installation, no pre-existing state
2. **Named checkpoints**: The workspace state at each convergence point is captured and named
3. **Reset to any point**: `restore design` → workspace is exactly as it was after design converged
4. **F_D-only validation**: The engine evaluates deterministically from any checkpoint without Claude
5. **Hamiltonian tracking**: H = T + V is visible at each checkpoint — shows cost of traversal

### Why This Is Different from E2E Tests

| Dimension | E2E Tests | Testbed |
|-----------|-----------|---------|
| Purpose | Validate full workflow via live Claude | Validate individual edges; prove convergence is deterministic |
| Claude required | Yes — for F_P construction | No — snapshots include pre-constructed artifacts |
| Resettable | No — archives are read-only | Yes — any snapshot can be restored |
| Intermediate states | Not accessible | Named snapshots at every edge convergence |
| CI use | Yes (with Claude API key) | Yes for F_D validation; optional for F_P |
| Speed | 10–30 minutes | Seconds (F_D only) |

---

## Decision

### 1. Testbed Location

```
projects/eco_system/
├── README.md
├── Makefile                   # init, snapshot, restore, validate, status
├── project/                   # The target project (genesis operates here)
│   └── (genesis workspace + generated artifacts)
├── snapshots/                 # Named checkpoint archive (git-committed)
│   ├── 00_installed/          # gen-setup.py complete, workspace initialised
│   ├── 01_requirements_done/  # intent→requirements edge converged
│   ├── 02_design_done/        # requirements→design edge converged
│   ├── 03_code_tests_done/    # code↔unit_tests edge converged (MVP complete)
│   └── manifest.yml           # snapshot registry: name, edge, H, timestamp
└── scripts/
    ├── snapshot.py            # Capture project/ → snapshots/<name>/
    ├── restore.py             # Restore snapshots/<name>/ → project/
    └── validate.py            # Run F_D evaluators, report H, delta_curve
```

### 2. The Target Project

A minimal Python library: **unit converter** (temperature, length, mass). Chosen because:
- Matches the existing e2e test domain (reuse artifacts / knowledge)
- Small: 3 REQ keys, 1 feature vector, ≤4 edges
- Clear deterministic test suite (pytest, no mocking needed)
- Exercises all standard profile edges: intent→req→design→code↔tests

### 3. Snapshot Mechanism

A snapshot is a **directory copy** of the target project's workspace and generated code:

```
snapshots/02_design_done/
├── .ai-workspace/             # full workspace state at this checkpoint
│   ├── events/events.jsonl    # event log up to this point
│   ├── features/active/*.yml  # feature vectors at this state
│   └── (all other workspace files)
├── src/                       # generated source files (if any at this edge)
├── tests/                     # generated test files (if any at this edge)
└── snapshot_meta.json         # {edge, timestamp, H, T, V, context_hash}
```

`restore <name>` copies the snapshot directory back to `project/`, replacing the current workspace. The restored state is **identical** to the moment the snapshot was taken.

### 4. Validate Script

`validate.py` runs the genesis engine in `--deterministic-only` mode from the current workspace state:

```bash
PYTHONPATH=<methodology>/imp_claude/code \
  python -m genesis evaluate \
    --edge "code↔unit_tests" \
    --feature "REQ-F-CONV-001" \
    --workspace project/.ai-workspace \
    --deterministic-only \
    --fd-timeout 60
```

Reports:
- Delta (failing checks)
- H = T + V (Hamiltonian — current iteration cost)
- Each evaluator: pass / fail / skip
- Recommendation: converged / iterate / escalate

### 5. MVP Proof Criteria

The testbed proves the MVP when:

| Test | Pass Condition |
|------|---------------|
| `make init` | Clean workspace initialised, `00_installed` snapshot valid |
| Restore `00_installed`, run `gen-start` | State machine detects correct state, begins intent→req |
| Restore `02_design_done`, run `validate` | Engine reports delta=0 or actionable delta on code↔unit_tests |
| Restore `03_code_tests_done`, run `validate` | Engine reports delta=0, H=T (V=0), pytest passes |
| Restore any snapshot, modify code, run `validate` | Delta increases correctly (regression detection) |

### 6. Hamiltonian Visible at Each Snapshot

`snapshot_meta.json` records H, T, V at capture time. `manifest.yml` shows the full H trajectory:

```yaml
snapshots:
  - name: 00_installed
    edge: null
    T: 0
    V: 0
    H: 0
  - name: 01_requirements_done
    edge: intent→requirements
    T: 2
    V: 0
    H: 2
  - name: 02_design_done
    edge: requirements→design
    T: 5
    V: 0
    H: 5
  - name: 03_code_tests_done
    edge: code↔unit_tests
    T: 11
    V: 0
    H: 11
```

This makes the full cost of the traversal visible as a historical record. Each future run of the testbed can be compared against this baseline.

---

## Consequences

### Positive

- **Isolates F_D from F_P**: Test the engine evaluator independently of agent construction — validate the convergence criteria without spending tokens
- **Reproducible failures**: When the engine fails on a real project, capture the workspace as a snapshot, add to the testbed, reproduce deterministically
- **MVP gate**: The testbed is the acceptance gate for the MVP — when `03_code_tests_done` validates with delta=0, the methodology works end-to-end
- **Regression detection**: Modifying a snapshot and re-validating catches evaluator regressions
- **H baseline**: Each snapshot records H at capture time — future testbed runs can be compared against the baseline trajectory

### Negative

- **Snapshots go stale**: When the workspace schema changes (edge params, topology), snapshots may need regeneration. Mitigated by `snapshot_meta.json` recording the schema version.
- **Not a substitute for e2e**: The testbed validates F_D convergence from pre-constructed artifacts. It does not validate that Claude correctly constructs those artifacts. E2E tests are still needed for that.

### Neutral

- The testbed target project (unit converter) reuses the temperature-converter domain from the e2e fixture — reducing the number of unfamiliar domains in the test infrastructure
- The testbed is in `ai_sdlc_examples/` (not `imp_claude/`) — it is itself a genesis-managed project, dogfooding the methodology

---

## References

- E2E tests: `imp_claude/tests/e2e/` — complementary, not replaced
- Engine CLI: `imp_claude/code/genesis/__main__.py` — the `--deterministic-only` evaluator
- ADR-S-020: Hamiltonian as iteration cost — tracked in snapshot manifests
- Genesis monitor: `projects/genesis_monitor/imp_fastapi` — can point at testbed project/
