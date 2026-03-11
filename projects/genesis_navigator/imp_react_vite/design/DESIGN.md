# Genesis Navigator — Implementation Design

**Version**: 1.0.0 | **Date**: 2026-03-12 | **Status**: Draft
**Implements**: REQ-F-GNAV-001 (Genesis Navigator Application)
**Traces To**: specification/features/FEATURE_VECTORS.md

---

## Overview

Genesis Navigator is a local web application with a React + Vite frontend and
a FastAPI Python backend. The two are decoupled by a REST API contract (OpenAPI 3.1).

This document covers the binding decisions: module structure, component architecture,
API contract, state management, and CLI entry point.

See ADRs in `adrs/` for individual architectural decisions.

---

## Technology Binding

| Layer | Technology | Version | Decision |
|-------|-----------|---------|---------|
| Frontend framework | React | 19.x | ADR-001 |
| Frontend build | Vite | 6.x | ADR-001 |
| Frontend language | TypeScript | 5.x | ADR-001 |
| Routing | React Router | v7 | ADR-002 |
| Server state | TanStack Query | v5 | ADR-003 |
| Backend framework | FastAPI | 0.115+ | ADR-004 |
| Backend language | Python | 3.12+ | ADR-004 |
| YAML parsing | PyYAML | 6.x | ADR-004 |
| API contract | OpenAPI | 3.1 | ADR-005 |
| CLI entry point | Click | 8.x | ADR-006 |

---

## Module Structure

```
imp_react_vite/
├── frontend/                          # React + Vite application
│   ├── src/
│   │   ├── main.tsx                   # App entry point
│   │   ├── App.tsx                    # Router and query client setup
│   │   ├── api/
│   │   │   ├── client.ts              # Axios/fetch wrapper, base URL config
│   │   │   ├── projects.ts            # GET /api/projects
│   │   │   ├── projectDetail.ts       # GET /api/projects/{id}
│   │   │   ├── gaps.ts                # GET /api/projects/{id}/gaps
│   │   │   ├── queue.ts               # GET /api/projects/{id}/queue
│   │   │   └── history.ts             # GET /api/projects/{id}/runs
│   │   ├── components/
│   │   │   ├── ProjectList/
│   │   │   │   ├── ProjectList.tsx    # Sortable/filterable list
│   │   │   │   ├── ProjectCard.tsx    # Single project card
│   │   │   │   └── StateBadge.tsx     # ITERATING/QUIESCENT/CONVERGED/BOUNDED
│   │   │   ├── ProjectDetail/
│   │   │   │   ├── ProjectDetail.tsx  # Tab container for all views
│   │   │   │   └── RefreshButton.tsx  # Manual refresh with timestamp
│   │   │   ├── StatusView/
│   │   │   │   ├── StatusView.tsx     # Feature vector list
│   │   │   │   ├── FeatureRow.tsx     # Single feature with trajectory
│   │   │   │   ├── TrajectoryGraph.tsx # Edge nodes inline
│   │   │   │   └── HamiltonianBadge.tsx # H/T/V display
│   │   │   ├── GapView/
│   │   │   │   ├── GapView.tsx        # All three layers
│   │   │   │   ├── GapSummary.tsx     # Header with signal badge
│   │   │   │   ├── GapTable.tsx       # REQ key → coverage table
│   │   │   │   └── HealthSignal.tsx   # GREEN/AMBER/RED
│   │   │   ├── QueueView/
│   │   │   │   ├── QueueView.tsx      # Ranked item list
│   │   │   │   ├── QueueItem.tsx      # Expandable item with command
│   │   │   │   └── CommandBlock.tsx   # Monospace + copy button
│   │   │   ├── HistoryView/
│   │   │   │   ├── HistoryView.tsx    # Run list
│   │   │   │   ├── RunCard.tsx        # Single run summary
│   │   │   │   ├── RunTimeline.tsx    # Event timeline
│   │   │   │   └── RunComparison.tsx  # Side-by-side diff
│   │   │   └── shared/
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       └── EmptyState.tsx
│   │   ├── hooks/
│   │   │   ├── useProjects.ts         # TanStack Query for project list
│   │   │   ├── useProjectDetail.ts    # TanStack Query for project detail
│   │   │   ├── useGaps.ts             # TanStack Query for gap analysis
│   │   │   ├── useQueue.ts            # TanStack Query for decision queue
│   │   │   └── useHistory.ts          # TanStack Query for run history
│   │   ├── types/
│   │   │   └── api.ts                 # TypeScript types matching OpenAPI schema
│   │   └── pages/
│   │       ├── ProjectListPage.tsx    # Route: /
│   │       └── ProjectDetailPage.tsx  # Route: /projects/:id
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                           # FastAPI Python application
│   ├── genesis_nav/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, OpenAPI config
│   │   ├── cli.py                     # genesis-nav CLI (Click)
│   │   ├── routers/
│   │   │   ├── projects.py            # GET /api/projects
│   │   │   ├── detail.py              # GET /api/projects/{id}
│   │   │   ├── gaps.py                # GET /api/projects/{id}/gaps
│   │   │   ├── queue.py               # GET /api/projects/{id}/queue
│   │   │   └── history.py             # GET /api/projects/{id}/runs
│   │   ├── scanner/
│   │   │   ├── workspace_scanner.py   # Recursive scan, prune dirs
│   │   │   └── project_identity.py    # project_id derivation, dedup
│   │   ├── readers/
│   │   │   ├── event_reader.py        # Parse events.jsonl (skip malformed)
│   │   │   ├── feature_reader.py      # Parse feature vector YAML
│   │   │   └── state_computer.py      # Derive project state, Hamiltonian
│   │   ├── analyzers/
│   │   │   ├── gap_analyzer.py        # L1/L2/L3 gap computation
│   │   │   └── queue_builder.py       # Decision queue ranking
│   │   └── models/
│   │       └── schemas.py             # Pydantic models (= OpenAPI schema)
│   ├── tests/
│   │   ├── conftest.py                # Shared fixtures (fake workspace dirs)
│   │   ├── test_scanner.py            # Validates: REQ-F-SCANNER-001
│   │   ├── test_projdata.py           # Validates: REQ-F-PROJDATA-001
│   │   ├── test_gapengine.py          # Validates: REQ-F-GAPENGINE-001
│   │   ├── test_queueengine.py        # Validates: REQ-F-QUEUEENGINE-001
│   │   └── test_histengine.py         # Validates: REQ-F-HISTENGINE-001
│   └── pyproject.toml
```

---

## Component Architecture

### Page → View composition

```
App.tsx (QueryClient + Router)
└── ProjectListPage  (route: /)
    └── ProjectList
        └── ProjectCard × N  (name, StateBadge, counts, timestamp)
└── ProjectDetailPage  (route: /projects/:id)
    ├── ProjectHeader  (name, StateBadge, RefreshButton, last-refresh ts)
    └── Tabs: Status | Gaps | Queue | History
        ├── StatusView
        │   └── FeatureRow × N
        │       ├── TrajectoryGraph  (edge nodes)
        │       └── HamiltonianBadge (H/T/V)
        ├── GapView
        │   ├── GapSummary  (health signal, counts)
        │   ├── GapTable L1 (REQ key → code/tests)
        │   ├── GapTable L2 (test gaps)
        │   └── GapTable L3 (telemetry, advisory)
        ├── QueueView
        │   └── QueueItem × N  (expandable, CommandBlock)
        └── HistoryView
            ├── RunCard × N
            └── RunTimeline (or RunComparison in compare mode)
```

### State management strategy (ADR-003)

- **TanStack Query** owns all server state (projects list, project detail, gaps, queue, history)
- Each `useXxx` hook wraps one API call with `staleTime: Infinity` (data is fresh until user refreshes)
- Manual refresh = `queryClient.invalidateQueries({ queryKey: ['project', id] })` for all sub-queries
- No global state store (Redux/Zustand) — all state is either server state (Query) or local UI state (useState)

---

## API Contract (OpenAPI 3.1)

The full schema is served at `GET /openapi.json`. Key response shapes:

### ProjectSummary
```typescript
{
  project_id: string        // derived from dir name
  name: string
  path: string              // absolute path on server
  state: "ITERATING" | "QUIESCENT" | "CONVERGED" | "BOUNDED" | "uninitialized"
  active_feature_count: number
  converged_feature_count: number
  last_event_at: string | null   // ISO 8601
  scan_duration_ms: number
}
```

### ProjectDetail
```typescript
{
  project_id: string
  name: string
  state: ProjectState
  features: FeatureVector[]
  total_edges: number
  converged_edges: number
}
```

### FeatureVector
```typescript
{
  feature_id: string        // REQ-F-*
  title: string
  status: "iterating" | "converged" | "blocked" | "stuck" | "pending" | "error"
  current_edge: string | null
  delta: number
  hamiltonian: { H: number, T: number, V: number, flat: boolean }
  trajectory: EdgeTrajectory[]
}
```

### EdgeTrajectory
```typescript
{
  edge: string              // e.g. "intent→requirements"
  status: "converged" | "iterating" | "pending" | "blocked"
  iteration: number
  delta: number
  started_at: string | null
  converged_at: string | null
}
```

### GapReport
```typescript
{
  project_id: string
  computed_at: string
  health_signal: "GREEN" | "AMBER" | "RED"
  layer_1: GapLayer
  layer_2: GapLayer
  layer_3: GapLayer   // advisory
}

interface GapLayer {
  gap_count: number
  coverage_pct: number
  gaps: GapItem[]
}

interface GapItem {
  req_key: string
  gap_type: "CODE_GAP" | "TEST_GAP" | "TELEMETRY_GAP" | "ORPHAN"
  files: string[]
  suggested_command: string | null
}
```

### QueueItem
```typescript
{
  type: "stuck" | "blocked" | "gap_cluster" | "human_gate" | "intent" | "in_progress"
  severity: "critical" | "high" | "medium" | "low"
  feature_id: string | null
  description: string
  command: string           // genesis command to run
  detail: QueueItemDetail
}
```

### RunSummary / RunTimeline — see ADR-007

---

## Backend Domain Model

```
WorkspaceScanner
  scan(root: Path) → list[ProjectSummary]
  _is_genesis_project(path: Path) → bool
  _derive_project_id(path: Path, root: Path) → str

EventReader
  read(workspace: Path) → list[Event]       # skips malformed lines

FeatureReader
  read_all(workspace: Path) → list[FeatureVector]  # skips malformed YAML

StateComputer
  project_state(features: list[FeatureVector]) → ProjectState
  hamiltonian(events: list[Event], feature_id: str) → HamiltonianValue

GapAnalyzer
  analyze(project: Path) → GapReport        # pure read, no writes
  _layer_1(spec_keys, code_keys, test_keys) → GapLayer
  _layer_2(spec_keys, test_keys) → GapLayer
  _layer_3(code_keys, telemetry_keys) → GapLayer

QueueBuilder
  build(features, gaps) → list[QueueItem]   # sorted by severity
  _command_for(item_type, feature_id, edge) → str
```

---

## CLI Entry Point (ADR-006)

```
genesis-nav [ROOT_DIR] [--port PORT] [--no-browser]
```

1. Validate ROOT_DIR exists (default: current directory)
2. Start FastAPI via uvicorn on PORT (default: 8765)
3. Open browser to `http://localhost:{PORT}` (unless `--no-browser`)
4. Block on uvicorn (Ctrl-C to stop)

Installed as a script in `pyproject.toml`:
```toml
[project.scripts]
genesis-nav = "genesis_nav.cli:main"
```

---

## Read-Only Enforcement

Per `REQ-NFR-ARCH-002`: no API handler may write to a workspace.

Enforcement strategy:
1. **Code review rule**: no `open(..., 'w')`, `open(..., 'a')`, `Path.write_text()`, `Path.mkdir()` in `routers/` or `analyzers/`
2. **Test assertion**: `conftest.py` fixture captures filesystem writes; each test asserts zero writes after API call
3. **ADR-008** records this as a hard invariant

---

## ADRs Index

| ADR | Decision |
|-----|---------|
| ADR-001 | React 19 + Vite 6 as frontend stack |
| ADR-002 | React Router v7 for client-side routing |
| ADR-003 | TanStack Query v5, staleTime: Infinity, manual refresh |
| ADR-004 | FastAPI + PyYAML backend, no ORM |
| ADR-005 | OpenAPI 3.1 as the binding contract |
| ADR-006 | Click CLI, uvicorn subprocess, browser auto-open |
| ADR-007 | Session history: scan `tests/e2e/runs/e2e_*/` + `.ai-workspace/runs/` |
| ADR-008 | Read-only invariant: enforced by test fixture, not runtime guard |
