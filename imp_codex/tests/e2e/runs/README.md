# Codex E2E Run Archive

Persistent archive of Codex Genesis e2e convergence runs.

## Naming Convention

```text
runs/
  e2e_<version>_<YYYYMMDDTHHMMSS>_<NNNN>/          # successful run
  e2e_FAILED_<version>_<YYYYMMDDTHHMMSS>_<NNNN>/   # failed run
```

- `version` from `imp_codex/code/plugin.json`
- `datetime` in UTC
- `sequence` is global and monotonic

## Per-Run Artifacts

```text
<run>/
  .ai-workspace/events/events.jsonl
  .ai-workspace/features/...
  src/
  tests/
  .e2e-meta/
    run_manifest.json
    test_results.json
```

