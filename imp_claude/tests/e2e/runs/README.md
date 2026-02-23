# E2E Run Archive

Persistent archive of headless Claude convergence runs. Each run is a full copy of the test project after Claude finishes (or fails).

## Naming Convention

```
runs/
  e2e_<version>_<YYYYMMDDTHHMMSS>_<NNNN>/         # successful run
  e2e_FAILED_<version>_<YYYYMMDDTHHMMSS>_<NNNN>/   # failed run
```

- **e2e_** prefix: groups runs visually in Genesis Monitor alongside real projects
- **version**: from `plugin.json` (e.g. `2.8.0`)
- **datetime**: UTC compact ISO 8601
- **sequence**: 4-digit global counter across all versions

Example:

```
runs/
  e2e_2.8.0_20260223T143000_0001/
  e2e_2.8.0_20260224T091500_0002/
  e2e_FAILED_2.8.0_20260225T120000_0003/
```

## Per-Run Directory Structure

Each archived run contains the full project tree:

```
<run>/
  specification/INTENT.md
  src/                          # Generated source code
  tests/                        # Generated test files
  .ai-workspace/
    events/events.jsonl          # Event log (edge convergence, etc.)
    features/active/             # Feature vectors with trajectory
    graph/                       # Graph topology + edge params
  .e2e-meta/
    stdout.log                   # Claude stdout
    stderr.log                   # Claude stderr
    meta.json                    # Run metadata (returncode, elapsed, timed_out)
    run_manifest.json            # Archive metadata (version, timestamp, source)
```

## Genesis Monitor Discovery

Point Genesis Monitor at the runs directory to observe historical convergence:

```bash
genesis-monitor --watch-dir imp_claude/tests/e2e/runs/
```

Each subdirectory appears as a separate project with its own `events.jsonl`.

## Cleanup

Runs are git-ignored. To reclaim disk space:

```bash
# Remove all archived runs
rm -rf imp_claude/tests/e2e/runs/*/

# Remove only failed runs
rm -rf imp_claude/tests/e2e/runs/e2e_FAILED_*/

# Remove runs older than 7 days
find imp_claude/tests/e2e/runs/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```
