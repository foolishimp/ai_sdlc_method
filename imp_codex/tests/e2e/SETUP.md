# Codex E2E Setup

Run Codex Genesis e2e tests (default deterministic mode):

```bash
pytest -q imp_codex/tests/e2e -m e2e
```

Run real Codex CLI e2e (live agent execution):

```bash
CODEX_E2E_MODE=real pytest -q imp_codex/tests/e2e -m e2e
```

Real mode defaults to model `gpt-5-codex`.

Optional model override for real mode:

```bash
CODEX_E2E_MODE=real CODEX_E2E_MODEL=<your_model_alias> pytest -q imp_codex/tests/e2e -m e2e
```

Or run the full Codex suite (includes e2e):

```bash
pytest -q imp_codex/tests
```

The e2e harness:

1. Scaffolds a temporary project with `.ai-workspace`
2. Copies Codex plugin graph/config/command/agent assets
3. Runs either:
   - `mock` mode (default): deterministic convergence simulation
   - `real` mode: `codex exec` with watchdog timeouts (executes the seeded real-driver script)
4. Validates events, feature vectors, generated code/tests, and cross-artifact consistency

## Run Archive

Each e2e run is archived to `imp_codex/tests/e2e/runs/`:

- `runs/e2e_<version>_<timestamp>_<seq>/` for passing runs
- `runs/e2e_FAILED_<version>_<timestamp>_<seq>/` for failing runs

Forensics files are written to `.e2e-meta/run_manifest.json` and
`.e2e-meta/test_results.json` inside each archived run.
