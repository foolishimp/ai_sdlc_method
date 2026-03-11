# ADR-007: Session History — Archived Run Discovery

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-F-HISTENGINE-001, REQ-BR-003

## Decision

Archived runs are discovered in two locations:
1. `{project_root}/tests/e2e/runs/e2e_VERSION_TIMESTAMP_SEQ/` — e2e test runs (existing convention)
2. `{workspace}/.ai-workspace/runs/` — manually archived runs (future use)

The current live workspace appears as run_id `current`.

## Run identity

`run_id` is derived from the directory name: `e2e_VERSION_TIMESTAMP_SEQ` → the SEQ portion.
For `current`, run_id is always the literal string `"current"`.

## Isolation invariant (REQ-BR-003)

The `GET /api/projects/{id}` endpoint reads only from `.ai-workspace/`. It never reads from `tests/e2e/runs/`. Archived run events never influence live project state.

The `GET /api/projects/{id}/runs` endpoint reads from `tests/e2e/runs/` and `.ai-workspace/runs/` — but only for the history view.

## Event timeline construction

For each run directory, the backend reads `events.jsonl` (or equivalent) and groups events:
```
run → features (by feature field) → edges (by edge field) → events (by timestamp)
```

## Consequences

- Projects without `tests/e2e/runs/` directory show only "Current Session" in history
- Run comparison aligns by edge name string — edges that appear in one run but not the other show a "not present" placeholder
