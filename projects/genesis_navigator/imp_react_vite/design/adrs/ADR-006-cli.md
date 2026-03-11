# ADR-006: Click CLI, Uvicorn, Browser Auto-Open

**Status**: Accepted | **Date**: 2026-03-12

## Decision

The `genesis-nav` CLI uses Click 8.x. It starts the FastAPI app via uvicorn and opens
the browser via `webbrowser.open()`.

## Interface

```bash
genesis-nav [ROOT_DIR] [--port PORT] [--no-browser] [--dev]
```

| Option | Default | Description |
|--------|---------|-------------|
| ROOT_DIR | `.` (cwd) | Root directory to scan for Genesis projects |
| --port | 8765 | Port for the API server |
| --no-browser | false | Skip browser auto-open |
| --dev | false | Start Vite dev server alongside API (for frontend development) |

## Start sequence

1. Validate ROOT_DIR exists and is readable
2. Start uvicorn with `genesis_nav.main:app`, passing ROOT_DIR as env var or startup config
3. Wait for server to be ready (poll `GET /health`, max 5s)
4. Open `http://localhost:{PORT}` in default browser (unless `--no-browser`)
5. Block on uvicorn; handle Ctrl-C gracefully

## Consequences

- Single command to start the full tool — practitioner UX matches the intent
- ROOT_DIR is passed to the FastAPI app via a startup config object (not env var, to avoid process pollution)
- The `--dev` flag is for contributor workflow only — not documented in user-facing help
