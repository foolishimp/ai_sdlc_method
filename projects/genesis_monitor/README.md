# Genesis Monitor — Observer Interface

Real-time dashboard for Genesis methodology projects. Consumes `.ai-workspace/events/events.jsonl` (OpenLineage format) and renders convergence status, phase space (H = T + V), Gantt, spawn tree, instance graph, TELEM signals, and consciousness loop projections.

## Observer Contract

The observer interface is defined in `specification/requirements/REQUIREMENTS.md`. Any compliant observer must:

- Discover Genesis workspaces by scanning for `.ai-workspace/events/events.jsonl`
- Parse OpenLineage events (ADR-S-011, ADR-S-012)
- Compute H = T + V from `iteration` and `delta` fields in `iteration_completed` events
- Render the required projections (convergence table, delta curve, Gantt, instance graph)
- Be **read-only**: never write to any target workspace

The interface is defined against open standards. A Grafana dashboard, Jupyter notebook, or custom CLI that consumes `events.jsonl` is a valid observer.

## Reference Implementation

[`imp_fastapi/`](imp_fastapi/) — Python + FastAPI + HTMX + SSE. Zero build step, single process, filesystem-watching via watchdog.

```bash
cd imp_fastapi
pip install -e ".[dev]"
uvicorn genesis_monitor.server.app:app --reload
# or
genesis-monitor --watch /path/to/.ai-workspace
```

### Structure

```
imp_fastapi/
├── code/src/genesis_monitor/
│   ├── models/          # core.py, events.py, features.py
│   ├── parsers/         # events, features, tasks, status, topology, adrs,
│   │                    # bootloader, constraints, reviews, traceability
│   ├── projections/     # convergence, graph, gantt, spawn_tree, telem,
│   │                    # edge_runs, feature_module_map, consciousness,
│   │                    # compliance, dimensions, intent_engine, regimes,
│   │                    # sensory, temporal, traceability, tree
│   ├── server/          # app.py, routes.py, broadcaster.py
│   ├── watcher/         # watchdog filesystem observer → SSE bridge
│   ├── scanner.py       # workspace discovery
│   ├── registry.py      # workspace hierarchy
│   ├── config.py
│   └── templates/       # Jinja2 + HTMX partials
├── tests/               # 33 test files, ~600 tests
├── design/
│   └── adrs/            # ADR-001 through ADR-009
└── pyproject.toml
```

### Converged Features

| Feature | Description |
|---------|-------------|
| GMON-001 | Workspace discovery and project list |
| GMON-002 | Asset graph visualisation (D3) |
| GMON-003 | Edge convergence table |
| GMON-004 | Feature matrix |
| GMON-005 | Workspace hierarchy (CQRS multi-tenant) |
| GMON-006 | STATUS.md panel with SSE auto-refresh |
| GVIZ-001 | D3 lifecycle timeline with executor arc styling |
| MTEN-001 | Multi-tenant workspace support |
| NAV-001 | Project navigation |
| NAV-005 | Feature trajectory view |
| UX-006 | Consciousness loop panel |

### Panels (project view)

Asset Graph · Edge Convergence · Edge Status · Feature Matrix · TELEM Signals · STATUS.md · Recent Events · Spawn Tree · Constraint Dimensions · Processing Phases · Compliance · Traceability · Feature→Module Map · ADR Register · Feature Trajectory · Consensus Reviews · Consciousness Loop · Workspace Hierarchy

### Design Decisions (ADRs)

| ADR | Topic |
|-----|-------|
| ADR-001 | FastAPI + HTMX + SSE architecture |
| ADR-002 | Read-only observer contract |
| ADR-003 | Single-process, no external DB |
| ADR-004 | CSS tooltips + scalable event index |
| ADR-005 | Event-sourced state reconstruction |
| ADR-006 | Dual-range slider (temporal filter) |
| ADR-007 | D3 event trail graph |
| ADR-008 | D3 lifecycle timeline |
| ADR-009 | Executor attribution — inference, arc styling, convergence badge |

## Specification

- [`specification/INTENT.md`](specification/INTENT.md) — why this tool exists (INT-GMON-001..009)
- [`specification/requirements/REQUIREMENTS.md`](specification/requirements/REQUIREMENTS.md) — REQ-GMON-* keys

## Technology

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Backend | FastAPI | Async-native, minimal, excellent SSE support |
| Frontend | HTMX + Jinja2 | Server-rendered partials, no JS framework, no build step |
| Push | SSE | Unidirectional, auto-reconnects, works through proxies |
| Filesystem watching | watchdog | OS-level events (inotify/kqueue/FSEvents), no polling |
| Diagrams | D3.js + Mermaid.js (CDN) | Zero build, renders asset graph, timeline, Gantt |

## REQ Key Convention

```
Code:    # Implements: REQ-GMON-*
Tests:   # Validates: REQ-GMON-*
Commits: include REQ-GMON-* in message
```
