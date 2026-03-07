# Genesis Monitor — Observer Interface

Real-time dashboard for Genesis methodology projects. Consumes `events.jsonl` (OpenLineage format) and renders convergence, phase space (H = T + V), Gantt, spawn tree, and instance graph projections.

## Observer Contract

The observer interface is defined in `specification/requirements/REQUIREMENTS.md`. Any compliant observer must:

- Discover Genesis workspaces by scanning for `.ai-workspace/events/events.jsonl`
- Parse OpenLineage events (ADR-S-011, ADR-S-012)
- Compute H = T + V from `iteration` and `delta` fields in `iteration_completed` events
- Render the required projections (convergence table, delta curve, Gantt, instance graph)
- Be **read-only**: never write to any target workspace

The interface is defined against open standards. A Grafana dashboard, Jupyter notebook, or custom CLI that consumes `events.jsonl` is a valid observer.

## Reference Implementation

[`imp_fastapi/`](imp_fastapi/) — FastAPI + HTMX + SSE. Zero build step, single process, filesystem-watching via watchdog.

```bash
cd imp_fastapi
pip install -e ".[dev]"
genesis-monitor --watch /path/to/project/.ai-workspace
```

## Specification

- [`specification/INTENT.md`](specification/INTENT.md) — why this tool exists (INT-GMON-001..009)
- [`specification/requirements/REQUIREMENTS.md`](specification/requirements/REQUIREMENTS.md) — REQ-GMON-* keys

## Technology (reference impl)

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Backend | FastAPI | Async-native, minimal, excellent SSE support |
| Frontend | HTMX + Jinja2 | Server-rendered partials, no JS framework, no build step |
| Push | SSE | Unidirectional, auto-reconnects, works through proxies |
| Filesystem watching | watchdog | OS-level events (inotify/kqueue/FSEvents), no polling |
| Diagrams | Mermaid.js (CDN) | Zero build, renders asset graph and Gantt |
