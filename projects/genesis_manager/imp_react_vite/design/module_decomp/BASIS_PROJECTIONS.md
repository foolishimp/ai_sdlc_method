# Basis Projections — genesis_manager
# Implements: REQ-F-PROJ-001, REQ-F-NAV-001, REQ-F-UX-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001, REQ-F-CTL-001

**Version**: 0.1.0
**Date**: 2026-03-13
**Edge**: module_decomposition → basis_projections
**Tenant**: react_vite
**Source**: MODULE_DECOMPOSITION.md v0.1.0 + 7 MVP feature designs + ADR-GM-001..005

---

## 1. Projection Index

Each cell represents one (feature × module) projection. A tick means "this feature places work in this module." Empty cells mean the module is used as a dependency but has no feature-specific work there.

| Feature \ Module | api-client | routing | ux-shared | store | app-shell | feat-proj-nav | feat-overview | feat-supervision | feat-evidence | feat-control | server-core | server-workspace-reader | server-routes | server-write-handler |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **REQ-F-PROJ-001** Project Navigator | P-01-API | P-01-RTG | — | P-01-STO | — | P-01-FPN | — | — | — | — | P-01-SVC | P-01-SWR | P-01-SRR | — |
| **REQ-F-NAV-001** Navigation Infra | — | P-02-RTG | — | — | P-02-APP | — | — | — | — | — | — | — | P-02-SRR | — |
| **REQ-F-UX-001** UX Infrastructure | — | — | P-03-UXS | P-03-STO | P-03-APP | — | — | — | — | — | — | — | — | — |
| **REQ-F-OVR-001** Project Overview | P-04-API | — | — | P-04-STO | — | — | P-04-FOV | — | — | — | — | P-04-SWR | P-04-SRR | — |
| **REQ-F-SUP-001** Supervision Console | P-05-API | — | — | P-05-STO | — | — | — | P-05-FSU | — | — | — | P-05-SWR | P-05-SRR | P-05-SWH |
| **REQ-F-EVI-001** Evidence Browser | P-06-API | — | — | P-06-STO | — | — | — | — | P-06-FEV | — | — | P-06-SWR | P-06-SRR | — |
| **REQ-F-CTL-001** Control Surface | P-07-API | — | — | — | — | — | — | — | — | P-07-FCT | — | — | — | P-07-SWH |

**Total projections**: 30

---

## 2. Projections

---

### Projection P-01-API: REQ-F-PROJ-001 × api-client
**Feature**: Project Navigator
**Module**: `imp_react_vite/src/api/`

#### Scope in this module
- Define all shared TypeScript domain types: `WorkspaceSummary`, `RegisteredWorkspace`, `WorkspaceOverview`, `GateItem`, `FeatureVector`, `TraceabilityEntry`, `WorkspaceEvent`, `EventPayload`, `ApiError`
- Implement `WorkspaceApiClient` class with constructor accepting base URL from `import.meta.env.VITE_API_URL` (default `http://localhost:3001`)
- Implement `getWorkspaces(): Promise<WorkspaceSummary[]>` — GET `/api/workspaces`
- Implement `addWorkspace(path: string): Promise<WorkspaceSummary>` — POST `/api/workspaces` with body `{ path }`
- Implement `removeWorkspace(id: string): Promise<void>` — DELETE `/api/workspaces/:id`
- Implement `getWorkspaceSummary(id: string): Promise<WorkspaceSummary>` — GET `/api/workspaces/:id/summary`
- Shared error mapping: 4xx/5xx server responses → `ApiError`; network failure → `ApiError` with `status: 0`

#### Out of scope for this module
- `getOverview`, `getGates`, `getFeatures`, `getTraceability` — added in P-04-API, P-05-API, P-06-API
- `postEvent`, `rerunGapAnalysis`, `setAutoMode` — added in P-05-API, P-06-API, P-07-API
- State management (holding the fetched data) — owned by `store` (P-01-STO)
- Polling timer logic — owned by `app-shell` (P-03-APP)

#### Required interface from other modules
None. `api-client` is a leaf module. Uses browser `fetch` only.

#### Exposed interface (for other modules to depend on)

```typescript
// src/api/types.ts

export interface WorkspaceSummary {
  id: string                    // SHA-256 of path, first 12 hex chars
  path: string
  name: string                  // basename of path
  pendingGates: number
  stuckFeatures: number
  lastEventAt: string | null    // ISO 8601
}

export interface RegisteredWorkspace {
  id: string
  path: string
}

export interface WorkspaceOverview {
  workspaceId: string
  projectName: string
  features: FeatureVector[]
  recentEvents: WorkspaceEvent[]
  lastRefreshed: string         // ISO 8601
}

export interface GateItem {
  id: string                    // "{featureId}:{edge}"
  featureId: string
  featureTitle: string
  edge: string
  urgency: 'blocking' | 'high' | 'normal'
  raisedAt: string              // ISO 8601
  context: string               // human-readable gate context
}

export interface FeatureVector {
  id: string                    // REQ-F-* key
  title: string
  status: 'pending' | 'in_progress' | 'blocked' | 'stuck' | 'converged'
  currentEdge: string | null
  isStuck: boolean
  autoMode: boolean
  lastEventAt: string | null
}

export interface TraceabilityEntry {
  reqKey: string                // REQ-F-* key
  specFile: string | null
  codeFiles: string[]           // files with # Implements: tag
  testFiles: string[]           // files with # Validates: tag
  coverageStatus: 'full' | 'partial' | 'missing'
}

export interface WorkspaceEvent {
  index: number                 // 0-based line number in events.jsonl
  event_type: string
  timestamp: string             // ISO 8601
  feature?: string
  edge?: string
  actor?: string
  comment?: string
  data?: Record<string, unknown>
}

export interface EventPayload {
  event_type: string
  feature?: string
  edge?: string
  actor?: string
  comment?: string
  data?: Record<string, unknown>
}

export interface ApiError {
  status: number                // HTTP status, or 0 for network failure
  message: string
}

// src/api/WorkspaceApiClient.ts

export class WorkspaceApiClient {
  constructor(baseUrl?: string)
  getWorkspaces(): Promise<WorkspaceSummary[]>
  addWorkspace(path: string): Promise<WorkspaceSummary>
  removeWorkspace(id: string): Promise<void>
  getWorkspaceSummary(id: string): Promise<WorkspaceSummary>
}
```

#### Evaluator contract
- **success case**: `getWorkspaces()` returns `WorkspaceSummary[]` (may be empty array) when server returns 200
- **failure case**: any 4xx/5xx or network failure returns `Promise.reject(ApiError)` — never throws; caller handles via `.catch()` or `try/catch`
- **side effects**: none — pure HTTP; no state mutations, no events emitted

---

### Projection P-01-RTG: REQ-F-PROJ-001 × routing
**Feature**: Project Navigator
**Module**: `imp_react_vite/src/routing/`

#### Scope in this module
- Define `ROUTES` constant with all canonical path templates as `as const` object
- Define `NavHandle` discriminated union type (four variants: feature, run, req, event)
- Implement `buildNavPath(workspaceId: string, handle: NavHandle): string` helper
- Define router configuration array (for `createBrowserRouter` in app-shell) — includes the root `/` route pointing to `ProjectListPage`

#### Out of scope for this module
- All page components — owned by their respective feature modules
- React Router `<Routes>` / `<Outlet>` composition — owned by `app-shell` (P-02-APP)
- Navigation side effects (calling `navigate()`) — owned by feature modules

#### Required interface from other modules
None. `routing` is a leaf module. Uses React Router 6 types only.

#### Exposed interface (for other modules to depend on)

```typescript
// src/routing/routes.ts

export const ROUTES = {
  ROOT: '/',
  PROJECT: '/project/:workspaceId',
  OVERVIEW: '/project/:workspaceId/overview',
  SUPERVISION: '/project/:workspaceId/supervision',
  EVIDENCE: '/project/:workspaceId/evidence',
  FEATURE_DETAIL: '/project/:workspaceId/feature/:featureId',
  RUN_DETAIL: '/project/:workspaceId/run/:runId',
  REQ_DETAIL: '/project/:workspaceId/req/:reqKey',
  EVENT_DETAIL: '/project/:workspaceId/event/:eventIndex',
} as const

export type RoutePath = typeof ROUTES[keyof typeof ROUTES]

// src/routing/navHandle.ts

export type NavHandle =
  | { kind: 'feature'; featureId: string }
  | { kind: 'run'; runId: string }
  | { kind: 'req'; reqKey: string }
  | { kind: 'event'; eventIndex: number }

export function buildNavPath(workspaceId: string, handle: NavHandle): string

// src/routing/routerConfig.ts

import type { RouteObject } from 'react-router-dom'
export function buildRouterConfig(): RouteObject[]
// NOTE: buildRouterConfig() lazily imports feature page components to avoid circular deps
```

#### Evaluator contract
- **success case**: `buildNavPath('abc123', { kind: 'feature', featureId: 'REQ-F-AUTH-001' })` returns `'/project/abc123/feature/REQ-F-AUTH-001'`
- **failure case**: TypeScript compiler rejects any `NavHandle` that does not match the discriminated union — no runtime error path needed
- **side effects**: none

---

### Projection P-01-STO: REQ-F-PROJ-001 × store
**Feature**: Project Navigator
**Module**: `imp_react_vite/src/stores/`

#### Scope in this module
- Implement `projectStore` with Zustand `create()` + `persist` middleware (localStorage key: `genesis-manager-projects`)
- Store fields: `registeredPaths: string[]`, `activeProjectId: string | null`, `workspaceSummaries: Record<string, WorkspaceSummary>`, `pollingError: string | null`, `lastRefreshed: Date | null`
- Implement `addWorkspace(path: string): Promise<void>` — calls `WorkspaceApiClient.addWorkspace`, appends to `registeredPaths`, merges summary
- Implement `removeWorkspace(id: string): void` — removes from `registeredPaths` and `workspaceSummaries`; if active project matches, clears `activeProjectId`
- Implement `setActiveProject(id: string): void` — sets `activeProjectId`
- Implement `refreshAll(): Promise<void>` — calls `WorkspaceApiClient.getWorkspaces()` for each registered path, merges results into `workspaceSummaries`, updates `lastRefreshed`; on error sets `pollingError`

#### Out of scope for this module
- `workspaceStore` (overview, gates, features, traceability) — added in P-04-STO, P-05-STO, P-06-STO
- The polling timer itself — owned by `app-shell` hook (P-03-APP)
- Workspace detail loading — owned by `workspaceStore`

#### Required interface from other modules
```typescript
// from api-client (P-01-API)
WorkspaceApiClient.getWorkspaces(): Promise<WorkspaceSummary[]>
WorkspaceApiClient.addWorkspace(path: string): Promise<WorkspaceSummary>
WorkspaceApiClient.removeWorkspace(id: string): Promise<void>
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/stores/projectStore.ts

export interface ProjectState {
  registeredPaths: string[]
  activeProjectId: string | null
  workspaceSummaries: Record<string, WorkspaceSummary>
  pollingError: string | null
  lastRefreshed: Date | null
}

export interface ProjectActions {
  addWorkspace(path: string): Promise<void>
  removeWorkspace(id: string): void
  setActiveProject(id: string): void
  refreshAll(): Promise<void>
}

export type ProjectStore = ProjectState & ProjectActions

export const useProjectStore: UseBoundStore<StoreApi<ProjectStore>>
```

#### Evaluator contract
- **success case**: after `addWorkspace('/path/to/project')`, `registeredPaths` includes the path, `workspaceSummaries` has an entry for the returned summary id
- **failure case**: `addWorkspace` throws → `pollingError` is set with the `ApiError.message`; store state is unchanged (path not appended)
- **side effects**: localStorage updated on every state change via `persist` middleware

---

### Projection P-01-FPN: REQ-F-PROJ-001 × feature-project-nav
**Feature**: Project Navigator
**Module**: `imp_react_vite/src/features/project-nav/`

#### Scope in this module
- Implement `ProjectListPage.tsx` — root page at route `/`; renders list of `ProjectCard` for each entry in `workspaceSummaries`; renders empty state with "Add workspace" CTA when `registeredPaths` is empty
- Implement `ProjectCard.tsx` — renders one `WorkspaceSummary`; shows `name`, `path`, `pendingGates` attention badge (orange, hidden when 0), `stuckFeatures` badge (red, hidden when 0); clicking the card navigates to `/project/:id/overview`; remove button triggers `ConfirmActionDialog` (from ux-shared) then calls `store.removeWorkspace`
- Implement `WorkspaceConfigDrawer.tsx` — drawer (shadcn/ui Sheet) opened by "Add workspace" button on `ProjectListPage`; form field for filesystem path; submit calls `store.addWorkspace(path)`; shows `ApiError.message` inline on failure; closes on success

#### Out of scope for this module
- `FreshnessIndicator` — owned by `ux-shared` (P-03-UXS); import it, don't reimplement
- Polling — owned by `app-shell` (P-03-APP)
- Any sub-page routing — owned by other feature modules

#### Required interface from other modules
```typescript
// from store (P-01-STO)
useProjectStore(): ProjectStore  // registeredPaths, workspaceSummaries, addWorkspace, removeWorkspace, setActiveProject

// from api-client (types only — store handles the calls)
WorkspaceSummary  // type

// from routing (P-01-RTG)
ROUTES.OVERVIEW   // navigation target on card click
buildNavPath(workspaceId, { kind: 'feature', ... })  // not used here but must import ROUTES

// from ux-shared (P-03-UXS)
ConfirmActionDialog  // for remove workspace confirmation
CommandLabel         // shown in confirm dialog for cmd context
CMD.rerunGaps        // not used here; ConfirmActionDialog only
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/features/project-nav/ProjectListPage.tsx
export function ProjectListPage(): JSX.Element

// src/features/project-nav/ProjectCard.tsx
export interface ProjectCardProps {
  summary: WorkspaceSummary
  onRemove: () => void
  onClick: () => void
}
export function ProjectCard(props: ProjectCardProps): JSX.Element

// src/features/project-nav/WorkspaceConfigDrawer.tsx
export interface WorkspaceConfigDrawerProps {
  open: boolean
  onClose: () => void
}
export function WorkspaceConfigDrawer(props: WorkspaceConfigDrawerProps): JSX.Element
```

#### Evaluator contract
- **success case**: `ProjectListPage` renders one `ProjectCard` per `workspaceSummaries` entry; attention badge visible when `pendingGates > 0`; clicking card navigates to correct ROUTES.OVERVIEW path
- **failure case**: `addWorkspace` rejects → inline error message shown inside drawer; drawer stays open; no store mutation occurred
- **side effects**: `store.removeWorkspace(id)` mutates store → re-render removes card; `store.addWorkspace` mutates store → new card appears

---

### Projection P-01-SVC: REQ-F-PROJ-001 × server-core
**Feature**: Project Navigator
**Module**: `imp_react_vite/server/index.ts`

#### Scope in this module
- Bootstrap Express application on port specified by `PORT` env var (default `3001`)
- Mount `express.json()` body parser
- Mount CORS middleware — allow `http://localhost:5173` in development (`NODE_ENV !== 'production'`)
- Mount all routers from `server-routes`
- In production (`NODE_ENV === 'production'`): serve static SPA build from `../dist/` at root; all unmatched GET requests return `index.html` (SPA fallback)
- Export `startServer(port: number): http.Server` for test harness

#### Out of scope for this module
- Route handler logic — owned by `server-routes` (P-01-SRR)
- File reading — owned by `server-workspace-reader` (P-01-SWR)
- Write handling — owned by `server-write-handler` (P-05-SWH)

#### Required interface from other modules
```typescript
// from server-routes (P-01-SRR)
import { workspacesRouter } from './routes/workspaces'
import { workspaceRouter } from './routes/workspace'
import { eventsRouter } from './routes/events'
import { gapAnalysisRouter } from './routes/gapAnalysis'
import { navRouter } from './routes/nav'
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/index.ts
export function startServer(port: number): http.Server
export function createApp(): Express  // for test harness — creates app without listening
```

#### Evaluator contract
- **success case**: `createApp()` returns Express instance with all routes mounted; GET `/api/workspaces` returns 200 with JSON
- **failure case**: port already in use → process emits `EADDRINUSE` error; server does not start silently
- **side effects**: none beyond server binding

---

### Projection P-01-SWR: REQ-F-PROJ-001 × server-workspace-reader
**Feature**: Project Navigator
**Module**: `imp_react_vite/server/readers/`

#### Scope in this module
- Implement `WorkspaceReader` class for reading workspace metadata
- Implement `getWorkspaceSummary(workspacePath: string): Promise<WorkspaceSummary>` — reads `project_constraints.yml` for `projectName`; reads `events.jsonl` via `EventLogReader`; computes `pendingGates` and `stuckFeatures` counts; generates `id` as first 12 hex chars of SHA-256 of `workspacePath`
- Implement `EventLogReader` class — `readAll(eventsPath: string): Promise<WorkspaceEvent[]>`: reads file line-by-line, parses each JSONL line, assigns sequential `index`, skips malformed lines with a warning log; returns empty array if file does not exist

#### Out of scope for this module
- `getOverview`, `getGates`, `getFeatures` — added in P-04-SWR, P-05-SWR
- `TraceabilityScanner` — added in P-06-SWR
- `computeAutoMode`, `computeIsStuck` — added in P-05-SWR
- Write operations — owned by `server-write-handler` (P-05-SWH)

#### Required interface from other modules
None. `server-workspace-reader` is a leaf module — uses Node.js `fs/promises`, `yaml`, `crypto` only.

#### Exposed interface (for other modules to depend on)

```typescript
// server/readers/WorkspaceReader.ts
export class WorkspaceReader {
  getWorkspaceSummary(workspacePath: string): Promise<WorkspaceSummary>
}

// server/readers/EventLogReader.ts
export class EventLogReader {
  readAll(eventsPath: string): Promise<WorkspaceEvent[]>
}

// server/readers/types.ts — server-side domain types (mirror of src/api/types.ts)
export interface WorkspaceSummary { /* same shape as browser-side */ }
export interface WorkspaceEvent { /* same shape as browser-side */ }
```

#### Evaluator contract
- **success case**: `getWorkspaceSummary('/path/to/project')` returns a valid `WorkspaceSummary` with correct `pendingGates` count derived from unresolved `gate_raised` events in `events.jsonl`
- **failure case**: `workspacePath` does not exist → throws `ReadError { code: 'WORKSPACE_NOT_FOUND', path }`. `events.jsonl` missing → `pendingGates: 0`, `stuckFeatures: 0`, no error
- **side effects**: file reads only; no writes

---

### Projection P-01-SRR: REQ-F-PROJ-001 × server-routes
**Feature**: Project Navigator
**Module**: `imp_react_vite/server/routes/`

#### Scope in this module
- Implement `workspaces.ts` Express Router:
  - `GET /api/workspaces` — reads all registered workspace paths from `~/.genesis_manager/config.json`; calls `WorkspaceReader.getWorkspaceSummary` for each; returns `WorkspaceSummary[]`
  - `POST /api/workspaces` — validates body `{ path: string }`; validates path exists on disk (fs.access); appends to `~/.genesis_manager/config.json`; returns new `WorkspaceSummary`
  - `DELETE /api/workspaces/:id` — removes matching path from `~/.genesis_manager/config.json`; returns 204
  - `GET /api/workspaces/:id/summary` — resolves path from id; calls `WorkspaceReader.getWorkspaceSummary`; returns `WorkspaceSummary`
- Registry file: `~/.genesis_manager/config.json` — `{ workspaces: string[] }` — created on first write

#### Out of scope for this module
- `/overview`, `/gates`, `/features`, `/traceability` routes — added in P-04-SRR, P-05-SRR, P-06-SRR
- `/events` write route — added in P-05-SRR
- `/gap-analysis/rerun` route — added in P-06-SRR
- `/nav` routes — added in P-02-SRR

#### Required interface from other modules
```typescript
// from server-workspace-reader (P-01-SWR)
WorkspaceReader.getWorkspaceSummary(workspacePath: string): Promise<WorkspaceSummary>
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/routes/workspaces.ts
import { Router } from 'express'
export const workspacesRouter: Router

// Error responses follow convention:
// 400: { error: string }  — validation failure
// 404: { error: string }  — workspace id not found
// 500: { error: string }  — internal read failure
```

#### Evaluator contract
- **success case**: `POST /api/workspaces` with valid path → 201 with `WorkspaceSummary`; path appears in `~/.genesis_manager/config.json`
- **failure case**: `POST /api/workspaces` with non-existent path → 400 `{ error: 'Path does not exist on disk' }`; `~/.genesis_manager/config.json` not modified
- **side effects**: `~/.genesis_manager/config.json` written on POST and DELETE

---

### Projection P-02-RTG: REQ-F-NAV-001 × routing
**Feature**: Navigation Infrastructure
**Module**: `imp_react_vite/src/routing/`

#### Scope in this module
- Extend `buildRouterConfig()` (started in P-01-RTG) to include all workspace-scoped routes: `/project/:workspaceId/overview`, `/project/:workspaceId/supervision`, `/project/:workspaceId/evidence`
- Include nested detail routes: `/project/:workspaceId/feature/:featureId`, `/project/:workspaceId/event/:eventIndex`
- Provide `PlaceholderPage` component — renders route path and "Coming soon" for unimplemented routes (used as fallback during phased construction)
- `buildNavPath` covers all `NavHandle` variants

#### Out of scope for this module
- Actual page implementations — each owned by its feature module
- Layout wrapper / sidebar — owned by `app-shell` (P-02-APP)

#### Required interface from other modules
None.

#### Exposed interface (for other modules to depend on)

```typescript
// src/routing/PlaceholderPage.tsx
export function PlaceholderPage(): JSX.Element
// renders: current pathname + "This page is not yet implemented"

// buildRouterConfig() already exported from P-01-RTG — extended here, same export
```

#### Evaluator contract
- **success case**: navigating to `/project/abc123/supervision` renders `SupervisionConsolePage` (or `PlaceholderPage` if not yet implemented); no 404 or blank render
- **failure case**: unknown route beyond defined set renders `PlaceholderPage` with descriptive message rather than a blank screen
- **side effects**: none

---

### Projection P-02-APP: REQ-F-NAV-001 × app-shell
**Feature**: Navigation Infrastructure
**Module**: `imp_react_vite/src/`

#### Scope in this module
- Implement `main.tsx` — `ReactDOM.createRoot(document.getElementById('root')!).render(<App />)`
- Implement `App.tsx` — creates router with `createBrowserRouter(buildRouterConfig())`; wraps in `<RouterProvider>`; mounts `useWorkspacePoller` once at root
- Implement shared layout wrapper: left sidebar (`ProjectListSidebar`) showing project list for navigation; main content area renders `<Outlet>`
- `ProjectListSidebar` — minimal sidebar: list of registered project names; highlights active; links to `/project/:id/overview`; "Add workspace" link opens `WorkspaceConfigDrawer`

#### Out of scope for this module
- `useWorkspacePoller` hook — added in P-03-APP
- Full `ProjectListPage` — owned by `feature-project-nav` (P-01-FPN); sidebar is a reduced navigation aid only

#### Required interface from other modules
```typescript
// from routing (P-02-RTG)
buildRouterConfig(): RouteObject[]

// from store (P-01-STO)
useProjectStore(): ProjectStore  // registeredPaths, workspaceSummaries, activeProjectId
```

#### Exposed interface (for other modules to depend on)
None — `App.tsx` is the root; it is not imported by other modules.

#### Evaluator contract
- **success case**: app loads at `/` and renders `ProjectListPage`; navigating to `/project/:id/overview` renders `ProjectOverviewPage` with correct `workspaceId` param extracted from URL
- **failure case**: router receives an unknown path → `PlaceholderPage` renders without crashing
- **side effects**: `RouterProvider` manages browser history

---

### Projection P-02-SRR: REQ-F-NAV-001 × server-routes
**Feature**: Navigation Infrastructure
**Module**: `imp_react_vite/server/routes/`

#### Scope in this module
- Implement `nav.ts` Express Router:
  - `GET /api/workspaces/:id/events/:index` — resolves workspace from id; calls `EventLogReader.readAll`; returns event at position `index`; 404 if index out of bounds

#### Out of scope for this module
- Feature and run detail nav routes (low priority, not MVP-blocking) — deferred
- REQ detail routes — deferred (traceability lookup belongs to P-06-SRR)

#### Required interface from other modules
```typescript
// from server-workspace-reader (P-01-SWR)
EventLogReader.readAll(eventsPath: string): Promise<WorkspaceEvent[]>
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/routes/nav.ts
export const navRouter: Router
// GET /api/workspaces/:id/events/:index → WorkspaceEvent | 404
```

#### Evaluator contract
- **success case**: `GET /api/workspaces/abc123/events/5` returns the WorkspaceEvent at index 5 as JSON
- **failure case**: index 5 does not exist → 404 `{ error: 'Event index out of bounds' }`
- **side effects**: none

---

### Projection P-03-UXS: REQ-F-UX-001 × ux-shared
**Feature**: UX Infrastructure
**Module**: `imp_react_vite/src/components/shared/`

#### Scope in this module
- Implement `FreshnessIndicator.tsx` — 5-state visual component:
  - `loading`: spinner (no data yet)
  - `refreshing`: spinner + "Refreshing…" (data exists, poll in flight)
  - `error`: red icon + truncated error message
  - `stale`: amber icon + "Last refreshed N min ago" (lastRefreshed older than 60s)
  - `fresh`: green dot + "Updated just now" (within 60s)
- Implement `CommandLabel.tsx` — renders a `<code>` element styled as a terminal command string
- Implement `commandStrings.ts` — `CMD` object with genesis command equivalents for all user actions
- Implement `ConfirmActionDialog.tsx` — shadcn/ui `Dialog` wrapper: title, description, `CommandLabel` showing genesis equivalent, Cancel / Confirm buttons

#### Out of scope for this module
- Polling logic — owned by `app-shell` (P-03-APP)
- Any data fetching — components receive data as props only

#### Required interface from other modules
```typescript
// from routing (P-01-RTG) — NavHandle type used in CMD helper only for type safety
import type { NavHandle } from '../routing/navHandle'
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/components/shared/FreshnessIndicator.tsx
export interface FreshnessIndicatorProps {
  lastRefreshed: Date | null
  isRefreshing: boolean
  error: string | null
}
export function FreshnessIndicator(props: FreshnessIndicatorProps): JSX.Element

// src/components/shared/CommandLabel.tsx
export interface CommandLabelProps {
  command: string
}
export function CommandLabel(props: CommandLabelProps): JSX.Element

// src/components/shared/commandStrings.ts
export const CMD = {
  approveGate: (featureId: string, edge: string) => string,
  rejectGate: (featureId: string, edge: string) => string,
  spawnFeature: (vectorType: string) => string,
  setAutoMode: (featureId: string, enabled: boolean) => string,
  rerunGaps: (workspaceId: string) => string,
  addWorkspace: (path: string) => string,
  removeWorkspace: (path: string) => string,
} as const

// src/components/shared/ConfirmActionDialog.tsx
export interface ConfirmActionDialogProps {
  open: boolean
  title: string
  description: string
  command: string           // shown via <CommandLabel>
  onConfirm: () => void
  onCancel: () => void
  confirmLabel?: string     // default: "Confirm"
  destructive?: boolean     // default: false — red confirm button when true
}
export function ConfirmActionDialog(props: ConfirmActionDialogProps): JSX.Element
```

#### Evaluator contract
- **success case**: `FreshnessIndicator` with `lastRefreshed` 10s ago and `isRefreshing: false` renders green dot; same with `lastRefreshed` 2min ago renders amber icon
- **failure case**: `FreshnessIndicator` with `error: 'Network error'` renders red icon regardless of `lastRefreshed` value; error takes priority over freshness state
- **side effects**: none — all components are pure presentational; no state owned here

---

### Projection P-03-STO: REQ-F-UX-001 × store
**Feature**: UX Infrastructure
**Module**: `imp_react_vite/src/stores/`

#### Scope in this module
- Implement `workspaceStore.ts` — Zustand store (no persistence) for active workspace detail data
- Fields: `overview: WorkspaceOverview | null`, `gates: GateItem[]`, `features: FeatureVector[]`, `traceability: TraceabilityEntry[]`, `isLoading: boolean`, `loadError: string | null`
- Implement `loadWorkspace(id: string): Promise<void>` — stub: sets `isLoading: true`; to be populated with actual fetches in P-04-STO, P-05-STO, P-06-STO
- Implement `clearWorkspace(): void` — resets all fields to null/empty; called on workspace switch

#### Out of scope for this module
- Data fetching implementations — extended in P-04-STO (overview), P-05-STO (gates/features), P-06-STO (traceability)
- `projectStore` — defined in P-01-STO

#### Required interface from other modules
```typescript
// from api-client (types only)
import type { WorkspaceOverview, GateItem, FeatureVector, TraceabilityEntry } from '../api/types'
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/stores/workspaceStore.ts
export interface WorkspaceState {
  overview: WorkspaceOverview | null
  gates: GateItem[]
  features: FeatureVector[]
  traceability: TraceabilityEntry[]
  isLoading: boolean
  loadError: string | null
}

export interface WorkspaceActions {
  loadWorkspace(id: string): Promise<void>
  clearWorkspace(): void
}

export type WorkspaceStore = WorkspaceState & WorkspaceActions

export const useWorkspaceStore: UseBoundStore<StoreApi<WorkspaceStore>>
```

#### Evaluator contract
- **success case**: `clearWorkspace()` resets all data fields to null/empty; `isLoading` becomes false; `loadError` becomes null
- **failure case**: not applicable at this projection — `loadWorkspace` is a stub; error handling added in downstream projections
- **side effects**: none (in-memory Zustand store, no persistence)

---

### Projection P-03-APP: REQ-F-UX-001 × app-shell
**Feature**: UX Infrastructure
**Module**: `imp_react_vite/src/`

#### Scope in this module
- Implement `hooks/useWorkspacePoller.ts`:
  - Fires `store.refreshAll()` immediately on mount
  - Sets up `setInterval` for 30s repeat
  - Clears interval on unmount
  - Propagates errors from `refreshAll()` to `projectStore.pollingError`
  - No return value — side-effect hook only
- Mount `useWorkspacePoller()` once inside `App.tsx` (not inside page components)

#### Out of scope for this module
- `refreshAll` implementation — owned by `store` (P-01-STO)
- Displaying freshness state — owned by feature modules using `FreshnessIndicator`

#### Required interface from other modules
```typescript
// from store (P-01-STO)
useProjectStore(): { refreshAll: () => Promise<void>, pollingError: string | null }
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/hooks/useWorkspacePoller.ts
export function useWorkspacePoller(): void
// No return value. Side effect only. Mount once at App root.
```

#### Evaluator contract
- **success case**: `useWorkspacePoller` fires `refreshAll()` immediately, then at 30s intervals; interval cleared when component unmounts (no memory leak)
- **failure case**: `refreshAll()` rejection is caught; `pollingError` updated in store; hook continues polling on next interval (does not crash or stop)
- **side effects**: `projectStore.refreshAll()` called periodically; `pollingError` set on store on failure

---

### Projection P-04-API: REQ-F-OVR-001 × api-client
**Feature**: Project Overview
**Module**: `imp_react_vite/src/api/`

#### Scope in this module
- Add `getOverview(id: string): Promise<WorkspaceOverview>` to `WorkspaceApiClient` — GET `/api/workspaces/:id/overview`

#### Out of scope for this module
- `WorkspaceOverview` type is already defined in P-01-API (no re-declaration needed)

#### Required interface from other modules
None.

#### Exposed interface (for other modules to depend on)

```typescript
// extends WorkspaceApiClient from P-01-API
getOverview(id: string): Promise<WorkspaceOverview>
```

#### Evaluator contract
- **success case**: returns `WorkspaceOverview` with populated `features` and `recentEvents` arrays
- **failure case**: 404 → `ApiError { status: 404, message: 'Workspace not found' }`
- **side effects**: none

---

### Projection P-04-STO: REQ-F-OVR-001 × store
**Feature**: Project Overview
**Module**: `imp_react_vite/src/stores/`

#### Scope in this module
- Extend `workspaceStore.loadWorkspace(id)` to call `WorkspaceApiClient.getOverview(id)` and populate `overview` field
- Clear `overview` to null before loading begins (`isLoading: true`)

#### Out of scope for this module
- `gates`, `features`, `traceability` fields — extended in P-05-STO, P-06-STO

#### Required interface from other modules
```typescript
// from api-client (P-04-API)
WorkspaceApiClient.getOverview(id: string): Promise<WorkspaceOverview>
```

#### Exposed interface (for other modules to depend on)
Already covered by `workspaceStore` interface from P-03-STO; `overview` field now populated.

#### Evaluator contract
- **success case**: after `loadWorkspace('abc123')`, `overview` is set with correct `projectName` and `features` count
- **failure case**: `getOverview` rejects → `loadError` set; `overview` remains null; `isLoading` becomes false
- **side effects**: workspace store state mutation

---

### Projection P-04-FOV: REQ-F-OVR-001 × feature-overview
**Feature**: Project Overview
**Module**: `imp_react_vite/src/features/overview/`

#### Scope in this module
- Implement `ProjectOverviewPage.tsx` — CSS Grid layout at `1440×900` without vertical scroll; two rows: top = `FeatureStatusBar` + `FeatureStatusCounts`; bottom = recent events timeline via `ChangeHighlighter`; mounts `useWorkspaceStore().loadWorkspace(workspaceId)` on route param change
- Implement `FeatureStatusBar.tsx` — horizontal bar divided proportionally by feature status; segments: converged (green), in_progress (blue), blocked (amber), stuck (red), pending (grey); each segment labelled with count
- Implement `FeatureStatusCounts.tsx` — prominent count card showing `pendingGates` count in large type; secondary counts for stuck features; links to Supervision Console
- Implement `ChangeHighlighter.tsx` — wrapper component; accepts `children` and `lastSessionStart: Date`; highlights child items that have events newer than `lastSessionStart` via a yellow left-border or background tint

#### Out of scope for this module
- Writing events — no write operations in overview
- Gate action handling — owned by `feature-supervision` (P-05-FSU)

#### Required interface from other modules
```typescript
// from store (P-04-STO)
useWorkspaceStore(): { overview: WorkspaceOverview | null, isLoading: boolean, loadError: string | null, loadWorkspace: (id: string) => Promise<void> }

// from routing (P-02-RTG)
ROUTES.SUPERVISION  // for "Go to Supervision" link in FeatureStatusCounts
useParams(): { workspaceId: string }

// from ux-shared (P-03-UXS)
FreshnessIndicator  // shown in page header
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/features/overview/ProjectOverviewPage.tsx
export function ProjectOverviewPage(): JSX.Element

// src/features/overview/FeatureStatusBar.tsx
export interface FeatureStatusBarProps {
  features: FeatureVector[]
}
export function FeatureStatusBar(props: FeatureStatusBarProps): JSX.Element

// src/features/overview/FeatureStatusCounts.tsx
export interface FeatureStatusCountsProps {
  pendingGates: number
  stuckFeatures: number
  workspaceId: string
}
export function FeatureStatusCounts(props: FeatureStatusCountsProps): JSX.Element

// src/features/overview/ChangeHighlighter.tsx
export interface ChangeHighlighterProps {
  lastSessionStart: Date
  eventTimestamp: string | null   // ISO string from event
  children: React.ReactNode
}
export function ChangeHighlighter(props: ChangeHighlighterProps): JSX.Element
```

#### Evaluator contract
- **success case**: `ProjectOverviewPage` at 1440×900 viewport has no vertical scrollbar; `FeatureStatusBar` segments sum to 100% width; `ChangeHighlighter` applies highlight class when `eventTimestamp` is after `lastSessionStart`
- **failure case**: `loadWorkspace` fails → error message displayed in place of data; layout does not break
- **side effects**: `loadWorkspace(workspaceId)` called on mount and on `workspaceId` param change

---

### Projection P-04-SWR: REQ-F-OVR-001 × server-workspace-reader
**Feature**: Project Overview
**Module**: `imp_react_vite/server/readers/`

#### Scope in this module
- Extend `WorkspaceReader` with `getOverview(workspacePath: string): Promise<WorkspaceOverview>`:
  - Reads all feature vector YAMLs from `.ai-workspace/features/` (active + completed subdirectories)
  - Reads last 20 events from `events.jsonl` via `EventLogReader.readAll`
  - Returns `WorkspaceOverview` with `features: FeatureVector[]` and `recentEvents: WorkspaceEvent[]`
- Implement feature YAML → `FeatureVector` mapping: parse `id`, `title`, `status`, `currentEdge`, `last_event_at` fields

#### Out of scope for this module
- Gate list computation — extended in P-05-SWR
- Traceability scanning — extended in P-06-SWR

#### Required interface from other modules
```typescript
// EventLogReader already defined in P-01-SWR
EventLogReader.readAll(eventsPath: string): Promise<WorkspaceEvent[]>
```

#### Exposed interface (for other modules to depend on)

```typescript
// extends WorkspaceReader from P-01-SWR
getOverview(workspacePath: string): Promise<WorkspaceOverview>
```

#### Evaluator contract
- **success case**: returns `WorkspaceOverview` with correct `features` count derived from `.ai-workspace/features/active/` YAML files
- **failure case**: `.ai-workspace/` directory missing → returns `WorkspaceOverview` with empty `features` and `recentEvents` arrays (workspace exists but is uninitialised)
- **side effects**: file reads only

---

### Projection P-04-SRR: REQ-F-OVR-001 × server-routes
**Feature**: Project Overview
**Module**: `imp_react_vite/server/routes/`

#### Scope in this module
- Implement `workspace.ts` Express Router:
  - `GET /api/workspaces/:id/overview` — resolves workspace path from id; calls `WorkspaceReader.getOverview`; returns `WorkspaceOverview`

#### Out of scope for this module
- `/gates`, `/features`, `/traceability` endpoints — added in P-05-SRR, P-06-SRR

#### Required interface from other modules
```typescript
// from server-workspace-reader (P-04-SWR)
WorkspaceReader.getOverview(workspacePath: string): Promise<WorkspaceOverview>
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/routes/workspace.ts
export const workspaceRouter: Router
// GET /api/workspaces/:id/overview → WorkspaceOverview | 404
```

#### Evaluator contract
- **success case**: returns 200 with `WorkspaceOverview` JSON
- **failure case**: unknown workspace id → 404; reader error → 500 with `{ error: string }`
- **side effects**: none

---

### Projection P-05-API: REQ-F-SUP-001 × api-client
**Feature**: Supervision Console
**Module**: `imp_react_vite/src/api/`

#### Scope in this module
- Add `getGates(id: string): Promise<GateItem[]>` — GET `/api/workspaces/:id/gates`
- Add `getFeatures(id: string): Promise<FeatureVector[]>` — GET `/api/workspaces/:id/features`
- Add `postEvent(id: string, event: EventPayload): Promise<void>` — POST `/api/workspaces/:id/events`
- Add `setAutoMode(id: string, featureId: string, enabled: boolean): Promise<void>` — POST `/api/workspaces/:id/events` with `{ event_type: 'auto_mode_set', feature: featureId, data: { enabled } }`

#### Out of scope for this module
- `rerunGapAnalysis` — added in P-06-API
- All types already defined in P-01-API

#### Required interface from other modules
None.

#### Exposed interface (for other modules to depend on)

```typescript
// extends WorkspaceApiClient
getGates(id: string): Promise<GateItem[]>
getFeatures(id: string): Promise<FeatureVector[]>
postEvent(id: string, event: EventPayload): Promise<void>
setAutoMode(id: string, featureId: string, enabled: boolean): Promise<void>
```

#### Evaluator contract
- **success case**: `postEvent` with valid payload returns `Promise<void>` (resolved); server has appended event to `events.jsonl`
- **failure case**: server returns 503 (lock contention) → `ApiError { status: 503, message: 'Write lock unavailable, retry in a moment' }`
- **side effects**: `postEvent` triggers a server-side write to `events.jsonl`

---

### Projection P-05-STO: REQ-F-SUP-001 × store
**Feature**: Supervision Console
**Module**: `imp_react_vite/src/stores/`

#### Scope in this module
- Extend `workspaceStore.loadWorkspace(id)` to also call `getGates(id)` and `getFeatures(id)` in parallel with `getOverview` (via `Promise.all`)
- Populate `gates: GateItem[]` and `features: FeatureVector[]` fields

#### Out of scope for this module
- `traceability` — extended in P-06-STO

#### Required interface from other modules
```typescript
// from api-client (P-05-API)
WorkspaceApiClient.getGates(id: string): Promise<GateItem[]>
WorkspaceApiClient.getFeatures(id: string): Promise<FeatureVector[]>
```

#### Exposed interface (for other modules to depend on)
`gates` and `features` fields now populated in `workspaceStore`.

#### Evaluator contract
- **success case**: after `loadWorkspace`, `gates` contains all pending `GateItem`s sorted by urgency
- **failure case**: any of the three parallel fetches fails → `loadError` set; all three data fields set to null/empty arrays
- **side effects**: store state mutation

---

### Projection P-05-FSU: REQ-F-SUP-001 × feature-supervision
**Feature**: Supervision Console
**Module**: `imp_react_vite/src/features/supervision/`

#### Scope in this module
- Implement `SupervisionConsolePage.tsx` — two-panel layout: top sticky `HumanGateQueue`; scrollable main area with `FeatureList`; right panel `ControlSurface` (imported from `feature-control` — forward reference stub acceptable here)
- Implement `HumanGateQueue.tsx` — renders sorted `GateItem[]` by urgency (blocking first); collapses to a count badge when queue empty; each item shows feature title, edge name, time raised, approve/reject buttons that open `GateActionPanel`
- Implement `FeatureList.tsx` — renders `FeatureVector[]` sorted: stuck → blocked → in_progress → pending → converged; each row shows status indicator, feature id, title, `isStuck` badge, `autoMode` badge; clicking navigates to `ROUTES.FEATURE_DETAIL`
- Implement `GateActionPanel.tsx` — approve/reject form; approve: optional comment field + `ConfirmActionDialog`; reject: required comment field (form validates non-empty) + `ConfirmActionDialog`; both call `postEvent` on confirm
- Implement `AutoModeToggle.tsx` — reads `enabled` from props (derived from `FeatureVector.autoMode`); toggle switch; on change calls `setAutoMode` via `api-client`; shows `CommandLabel` for the equivalent genesis command

#### Out of scope for this module
- `ControlSurface` — owned by `feature-control` (P-07-FCT); `SupervisionConsolePage` imports it
- Traceability and event detail — owned by `feature-evidence` (P-06-FEV)

#### Required interface from other modules
```typescript
// from store (P-05-STO)
useWorkspaceStore(): { gates: GateItem[], features: FeatureVector[], loadWorkspace: (id: string) => Promise<void> }

// from api-client (P-05-API)
WorkspaceApiClient.postEvent(id: string, event: EventPayload): Promise<void>
WorkspaceApiClient.setAutoMode(id: string, featureId: string, enabled: boolean): Promise<void>

// from ux-shared (P-03-UXS)
ConfirmActionDialog
CommandLabel
CMD.approveGate, CMD.rejectGate, CMD.setAutoMode
FreshnessIndicator

// from routing (P-02-RTG)
ROUTES.FEATURE_DETAIL
buildNavPath
useParams(): { workspaceId: string }
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/features/supervision/SupervisionConsolePage.tsx
export function SupervisionConsolePage(): JSX.Element

// src/features/supervision/GateActionPanel.tsx
export interface GateActionPanelProps {
  gate: GateItem
  workspaceId: string
  onApprove: (comment: string) => Promise<void>
  onReject: (comment: string) => Promise<void>   // comment required — validated non-empty
  onDismiss: () => void
}
export function GateActionPanel(props: GateActionPanelProps): JSX.Element

// src/features/supervision/AutoModeToggle.tsx
export interface AutoModeToggleProps {
  featureId: string
  workspaceId: string
  enabled: boolean
  onToggle: (enabled: boolean) => Promise<void>
}
export function AutoModeToggle(props: AutoModeToggleProps): JSX.Element

// src/features/supervision/FeatureList.tsx
export interface FeatureListProps {
  features: FeatureVector[]
  workspaceId: string
  onFeatureClick: (featureId: string) => void
}
export function FeatureList(props: FeatureListProps): JSX.Element

// src/features/supervision/HumanGateQueue.tsx
export interface HumanGateQueueProps {
  gates: GateItem[]
  workspaceId: string
  onGateAction: (gate: GateItem, approved: boolean, comment: string) => Promise<void>
}
export function HumanGateQueue(props: HumanGateQueueProps): JSX.Element
```

#### Evaluator contract
- **success case**: `GateActionPanel` reject path: submit button disabled until comment field non-empty; on confirm, `postEvent` called with `event_type: 'review_rejected'`, `comment` field set; `ConfirmActionDialog` shows `CMD.rejectGate(featureId, edge)` command
- **failure case**: `postEvent` rejects → error toast shown; gate stays in queue (no optimistic removal)
- **side effects**: `postEvent` appends event to server-side `events.jsonl`; store refresh triggered after successful action

---

### Projection P-05-SWR: REQ-F-SUP-001 × server-workspace-reader
**Feature**: Supervision Console
**Module**: `imp_react_vite/server/readers/`

#### Scope in this module
- Extend `WorkspaceReader` with `getGates(workspacePath: string): Promise<GateItem[]>`:
  - Calls `EventLogReader.readAll` to get full event log
  - Extracts all `gate_raised` events
  - For each `gate_raised`, checks if a `review_approved` or `review_rejected` event exists for the same `feature` + `edge` combination with a later timestamp
  - Returns only unresolved gates as `GateItem[]`, sorted by urgency (blocking first, then by `raisedAt` ascending)
- Extend `WorkspaceReader` with `getFeatures(workspacePath: string): Promise<FeatureVector[]>`:
  - Reads feature YAML files from `.ai-workspace/features/`
  - Enriches each with computed `isStuck` and `autoMode` from event log
- Extend `EventLogReader` with:
  - `computeAutoMode(events: WorkspaceEvent[], featureId: string): boolean` — returns `enabled` from last `auto_mode_set` event for `featureId`; default `false`
  - `computeIsStuck(events: WorkspaceEvent[], featureId: string, edge: string): boolean` — returns `true` if `iteration_abandoned` event exists for this feature+edge with no subsequent `edge_started` event

#### Out of scope for this module
- Writing events — owned by `server-write-handler` (P-05-SWH)

#### Required interface from other modules
None beyond what is already defined in P-01-SWR.

#### Exposed interface (for other modules to depend on)

```typescript
// extends WorkspaceReader
getGates(workspacePath: string): Promise<GateItem[]>
getFeatures(workspacePath: string): Promise<FeatureVector[]>

// extends EventLogReader
computeAutoMode(events: WorkspaceEvent[], featureId: string): boolean
computeIsStuck(events: WorkspaceEvent[], featureId: string, edge: string): boolean
```

#### Evaluator contract
- **success case**: `getGates` returns only gates where no `review_approved`/`review_rejected` event exists at a later timestamp; resolved gates are excluded
- **failure case**: corrupt JSONL line in `events.jsonl` → skipped with warning log; remaining lines processed normally
- **side effects**: file reads only

---

### Projection P-05-SRR: REQ-F-SUP-001 × server-routes
**Feature**: Supervision Console
**Module**: `imp_react_vite/server/routes/`

#### Scope in this module
- Extend `workspace.ts` router:
  - `GET /api/workspaces/:id/gates` — calls `WorkspaceReader.getGates`; returns `GateItem[]`
  - `GET /api/workspaces/:id/features` — calls `WorkspaceReader.getFeatures`; returns `FeatureVector[]`
- Implement `events.ts` Express Router:
  - `POST /api/workspaces/:id/events` — validates body has `event_type: string`; resolves workspace path; calls `emitEvent(path, body)`; returns 204 on success; 503 on `WriteError`

#### Out of scope for this module
- `/traceability` — added in P-06-SRR
- `/gap-analysis/rerun` — added in P-06-SRR

#### Required interface from other modules
```typescript
// from server-workspace-reader (P-05-SWR)
WorkspaceReader.getGates(workspacePath: string): Promise<GateItem[]>
WorkspaceReader.getFeatures(workspacePath: string): Promise<FeatureVector[]>

// from server-write-handler (P-05-SWH)
emitEvent(workspacePath: string, payload: EventPayload): Promise<void>
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/routes/events.ts
export const eventsRouter: Router
// POST /api/workspaces/:id/events → 204 | 400 | 503

// workspace.ts now also handles /gates and /features
```

#### Evaluator contract
- **success case**: `POST /api/workspaces/:id/events` with valid body returns 204; event appears in `events.jsonl`
- **failure case**: lock contention → `WriteError` thrown by `emitEvent` → 503 response; client retries
- **side effects**: appends to `events.jsonl` via `emitEvent`

---

### Projection P-05-SWH: REQ-F-SUP-001 × server-write-handler
**Feature**: Supervision Console
**Module**: `imp_react_vite/server/handlers/`

#### Scope in this module
- Implement `EventEmitHandler.ts` — `emitEvent` function:
  - Acquires `proper-lockfile` lock on `events.jsonl` (lock file: `events.jsonl.lock`, retries: 3, stale: 10s)
  - Constructs full event JSON: merges payload with `{ timestamp: new Date().toISOString(), project: <projectName from project_constraints.yml> }`
  - Appends single JSONL line (JSON + `\n`) to `events.jsonl`
  - Releases lock
  - On lock failure: throws `WriteError { code: 'LOCK_FAILED', message: string }`
- Implement `WriteLog.ts` — after successful write, appends an entry to `~/.genesis_manager/write_log.jsonl`: `{ timestamp, workspacePath, event_type, actor }` on one line

#### Out of scope for this module
- Read operations — owned by `server-workspace-reader`
- Route handling — owned by `server-routes`

#### Required interface from other modules
None. Leaf module — uses `fs/promises` and `proper-lockfile` only.

#### Exposed interface (for other modules to depend on)

```typescript
// server/handlers/EventEmitHandler.ts
export interface WriteError {
  code: 'LOCK_FAILED' | 'WRITE_FAILED'
  message: string
}

export async function emitEvent(
  workspacePath: string,
  payload: EventPayload
): Promise<void>
// throws WriteError on lock failure or write failure
```

#### Evaluator contract
- **success case**: `emitEvent` appends exactly one JSONL line to `events.jsonl`; lock acquired and released in the same call; write log entry appended to `~/.genesis_manager/write_log.jsonl`
- **failure case**: lock acquisition fails after 3 retries → throws `WriteError { code: 'LOCK_FAILED' }`; `events.jsonl` is not modified
- **side effects**: `events.jsonl` appended (1 line); `~/.genesis_manager/write_log.jsonl` appended (1 line)

---

### Projection P-06-API: REQ-F-EVI-001 × api-client
**Feature**: Evidence Browser
**Module**: `imp_react_vite/src/api/`

#### Scope in this module
- Add `getTraceability(id: string): Promise<TraceabilityEntry[]>` — GET `/api/workspaces/:id/traceability`
- Add `rerunGapAnalysis(id: string): Promise<void>` — POST `/api/workspaces/:id/gap-analysis/rerun`

#### Out of scope for this module
- All types already defined in P-01-API

#### Required interface from other modules
None.

#### Exposed interface (for other modules to depend on)

```typescript
// extends WorkspaceApiClient
getTraceability(id: string): Promise<TraceabilityEntry[]>
rerunGapAnalysis(id: string): Promise<void>
```

#### Evaluator contract
- **success case**: `rerunGapAnalysis` returns `Promise<void>` when server accepts the request (202 Accepted); gen-gaps subprocess started async server-side
- **failure case**: server cannot find `gen-gaps` binary → 500 `ApiError`
- **side effects**: `rerunGapAnalysis` triggers server-side child process spawn

---

### Projection P-06-STO: REQ-F-EVI-001 × store
**Feature**: Evidence Browser
**Module**: `imp_react_vite/src/stores/`

#### Scope in this module
- Extend `workspaceStore.loadWorkspace(id)` to also call `getTraceability(id)` in parallel with other fetches
- Populate `traceability: TraceabilityEntry[]` field

#### Required interface from other modules
```typescript
// from api-client (P-06-API)
WorkspaceApiClient.getTraceability(id: string): Promise<TraceabilityEntry[]>
```

#### Exposed interface (for other modules to depend on)
`traceability` field now populated in `workspaceStore`.

#### Evaluator contract
- **success case**: after `loadWorkspace`, `traceability` contains one entry per REQ-* key found in spec
- **failure case**: traceability scan fails (source files not accessible) → `loadError` set; `traceability` is empty array
- **side effects**: store state mutation

---

### Projection P-06-FEV: REQ-F-EVI-001 × feature-evidence
**Feature**: Evidence Browser
**Module**: `imp_react_vite/src/features/evidence/`

#### Scope in this module
- Implement `EvidenceBrowserPage.tsx` — two-column layout: left (60%) `TraceabilityTable`; right (40%) `EventDetailPanel`; top strip `GapAnalysisPanel`; mounts `loadWorkspace` on route param change
- Implement `TraceabilityTable.tsx` — sortable table; columns: REQ Key, Spec, Code Files (count), Test Files (count), Coverage Status; clicking a row selects it and shows event detail in `EventDetailPanel`; coverage status renders coloured badge (full=green, partial=amber, missing=red)
- Implement `EventDetailPanel.tsx` — shows full JSON of selected `WorkspaceEvent`; formatted as syntax-highlighted JSONL; displays event type, timestamp, feature, edge, actor, comment prominently; "No event selected" placeholder when nothing selected
- Implement `GapAnalysisPanel.tsx` — collapsible panel at top; shows last gap analysis run timestamp from events; "Re-run gen-gaps" button triggers `rerunGapAnalysis` API call + `ConfirmActionDialog`; shows last gap counts if available in events

#### Out of scope for this module
- Writing gate approval events — owned by `feature-supervision`
- Control surface — owned by `feature-control`

#### Required interface from other modules
```typescript
// from store (P-06-STO)
useWorkspaceStore(): { traceability: TraceabilityEntry[], features: FeatureVector[], loadWorkspace: (id: string) => Promise<void> }

// from api-client (P-06-API)
WorkspaceApiClient.rerunGapAnalysis(id: string): Promise<void>

// from ux-shared (P-03-UXS)
FreshnessIndicator
ConfirmActionDialog
CMD.rerunGaps

// from routing (P-02-RTG)
useParams(): { workspaceId: string }
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/features/evidence/EvidenceBrowserPage.tsx
export function EvidenceBrowserPage(): JSX.Element

// src/features/evidence/TraceabilityTable.tsx
export interface TraceabilityTableProps {
  entries: TraceabilityEntry[]
  onRowSelect: (entry: TraceabilityEntry | null) => void
  selectedReqKey: string | null
}
export function TraceabilityTable(props: TraceabilityTableProps): JSX.Element

// src/features/evidence/EventDetailPanel.tsx
export interface EventDetailPanelProps {
  event: WorkspaceEvent | null
}
export function EventDetailPanel(props: EventDetailPanelProps): JSX.Element

// src/features/evidence/GapAnalysisPanel.tsx
export interface GapAnalysisPanelProps {
  workspaceId: string
  lastRunAt: string | null    // ISO string from events, null if never run
  onRerun: () => Promise<void>
}
export function GapAnalysisPanel(props: GapAnalysisPanelProps): JSX.Element
```

#### Evaluator contract
- **success case**: selecting a `TraceabilityEntry` row with `coverageStatus: 'missing'` shows red badge; `EventDetailPanel` renders the selected event JSON with correct field labels
- **failure case**: `rerunGapAnalysis` rejects → error shown inline in `GapAnalysisPanel`; "Re-run" button re-enabled
- **side effects**: `rerunGapAnalysis` triggers server-side gen-gaps child process

---

### Projection P-06-SWR: REQ-F-EVI-001 × server-workspace-reader
**Feature**: Evidence Browser
**Module**: `imp_react_vite/server/readers/`

#### Scope in this module
- Implement `TraceabilityScanner` class:
  - `scan(projectRoot: string): Promise<TraceabilityEntry[]>`
  - Walks source tree (respects `.gitignore` patterns; skips `node_modules`, `.git`, `dist`)
  - For each file: extracts `# Implements: REQ-*` tags (code files) and `# Validates: REQ-*` tags (test files) via regex
  - Builds map: REQ key → `{ codeFiles: string[], testFiles: string[] }`
  - Reads spec directory to enumerate all defined REQ-* keys (from `.ai-workspace/spec/` YAML or `AISDLC_IMPLEMENTATION_REQUIREMENTS.md`)
  - Computes `coverageStatus`: `full` if both codeFiles and testFiles non-empty; `partial` if only one; `missing` if neither
  - Result is mtime-cached: re-scan only if any watched file newer than last scan timestamp

#### Out of scope for this module
- Serving the results — owned by `server-routes` (P-06-SRR)
- Gap analysis subprocess — owned by `server-routes` (P-06-SRR)

#### Required interface from other modules
None beyond Node.js `fs/promises` and `path`.

#### Exposed interface (for other modules to depend on)

```typescript
// server/readers/TraceabilityScanner.ts
export class TraceabilityScanner {
  scan(projectRoot: string): Promise<TraceabilityEntry[]>
}
```

#### Evaluator contract
- **success case**: `scan()` returns one `TraceabilityEntry` per REQ-* key; files tagged `# Implements: REQ-F-AUTH-001` appear in `codeFiles` for that entry
- **failure case**: projectRoot does not exist → returns empty array with warning log (does not throw)
- **side effects**: mtime cache updated in memory; no writes to disk

---

### Projection P-06-SRR: REQ-F-EVI-001 × server-routes
**Feature**: Evidence Browser
**Module**: `imp_react_vite/server/routes/`

#### Scope in this module
- Extend `workspace.ts` router:
  - `GET /api/workspaces/:id/traceability` — calls `TraceabilityScanner.scan(projectRoot)`; returns `TraceabilityEntry[]`
- Implement `gapAnalysis.ts` Express Router:
  - `POST /api/workspaces/:id/gap-analysis/rerun` — spawns `gen-gaps` as child process with `workspacePath` as argument; returns 202 immediately; child process output is logged but not returned

#### Out of scope for this module
- The gen-gaps implementation — that is the genesis CLI, external to this project

#### Required interface from other modules
```typescript
// from server-workspace-reader (P-06-SWR)
TraceabilityScanner.scan(projectRoot: string): Promise<TraceabilityEntry[]>

// Node.js child_process.spawn — for gen-gaps
```

#### Exposed interface (for other modules to depend on)

```typescript
// server/routes/gapAnalysis.ts
export const gapAnalysisRouter: Router
// POST /api/workspaces/:id/gap-analysis/rerun → 202 | 500
```

#### Evaluator contract
- **success case**: `POST` returns 202 immediately; `gen-gaps` subprocess is running in background; stdout/stderr logged to server console
- **failure case**: `gen-gaps` binary not found on PATH → 500 `{ error: 'gen-gaps command not found' }`; 202 not returned
- **side effects**: child process spawned; gen-gaps may write to workspace files

---

### Projection P-07-API: REQ-F-CTL-001 × api-client
**Feature**: Control Surface
**Module**: `imp_react_vite/src/api/`

#### Scope in this module
- `postEvent` already added in P-05-API — reused for spawn event emission
- No new methods needed: `ControlSurface` posts events via the existing `postEvent` method with `event_type: 'spawn_created'`

#### Out of scope for this module
- All methods already defined; no additions needed for REQ-F-CTL-001

#### Required interface from other modules
None.

#### Exposed interface (for other modules to depend on)

```typescript
// SpawnFeaturePanel uses:
postEvent(id: string, event: EventPayload): Promise<void>
// with payload: { event_type: 'spawn_created', data: { vectorType, title, satisfies } }
```

#### Evaluator contract
- **success case**: `postEvent` with `event_type: 'spawn_created'` resolves; event in `events.jsonl`
- **failure case**: network or server error → `ApiError`; UI shows error; no optimistic state mutation
- **side effects**: server-side `events.jsonl` append

---

### Projection P-07-FCT: REQ-F-CTL-001 × feature-control
**Feature**: Control Surface
**Module**: `imp_react_vite/src/features/control/`

#### Scope in this module
- Implement `ControlSurface.tsx` — panel component rendered within `SupervisionConsolePage`; sections: (1) Gate Actions (renders `GateActionPanel` for selected gate), (2) Spawn Feature (renders `SpawnFeaturePanel`), (3) Auto Mode (renders `AutoModeToggle` for selected feature)
- Implement `SpawnFeaturePanel.tsx` — form with fields: `vectorType` (select: feature / spike / poc / hotfix), `title` (text input), `satisfies` (REQ key, text input with validation pattern `REQ-F-[A-Z]+-\d+`); submit calls `postEvent` with `event_type: 'spawn_created'`; `ConfirmActionDialog` shows `CMD.spawnFeature(vectorType)` equivalent command

#### Out of scope for this module
- `GateActionPanel` — owned by `feature-supervision` (P-05-FSU); imported here
- `AutoModeToggle` — owned by `feature-supervision` (P-05-FSU); imported here
- Event log writes beyond `spawn_created` — owned by `feature-supervision`

#### Required interface from other modules
```typescript
// from feature-supervision (P-05-FSU)
import { GateActionPanel, GateActionPanelProps } from '../supervision/GateActionPanel'
import { AutoModeToggle, AutoModeToggleProps } from '../supervision/AutoModeToggle'

// from api-client (P-07-API)
WorkspaceApiClient.postEvent(id: string, event: EventPayload): Promise<void>

// from ux-shared (P-03-UXS)
ConfirmActionDialog
CMD.spawnFeature
```

#### Exposed interface (for other modules to depend on)

```typescript
// src/features/control/ControlSurface.tsx
export interface ControlSurfaceProps {
  workspaceId: string
  selectedGate: GateItem | null
  selectedFeature: FeatureVector | null
  onGateAction: (gate: GateItem, approved: boolean, comment: string) => Promise<void>
  onAutoModeToggle: (featureId: string, enabled: boolean) => Promise<void>
}
export function ControlSurface(props: ControlSurfaceProps): JSX.Element

// src/features/control/SpawnFeaturePanel.tsx
export type VectorType = 'feature' | 'spike' | 'poc' | 'hotfix'

export interface SpawnPayload {
  vectorType: VectorType
  title: string
  satisfies: string           // REQ-F-* key
}

export interface SpawnFeaturePanelProps {
  workspaceId: string
  onSpawn: (payload: SpawnPayload) => Promise<void>
}
export function SpawnFeaturePanel(props: SpawnFeaturePanelProps): JSX.Element
```

#### Evaluator contract
- **success case**: `SpawnFeaturePanel` submit with valid `satisfies` pattern emits `spawn_created` event; `ConfirmActionDialog` closes; form resets; success toast shown
- **failure case**: `satisfies` field does not match `REQ-F-[A-Z]+-\d+` → inline validation error; submit button disabled; `postEvent` not called
- **side effects**: `postEvent` appends `spawn_created` event to `events.jsonl`

---

### Projection P-07-SWH: REQ-F-CTL-001 × server-write-handler
**Feature**: Control Surface
**Module**: `imp_react_vite/server/handlers/`

#### Scope in this module
- `emitEvent` already implemented in P-05-SWH; no new server-side handler needed
- `spawn_created` events go through the same `POST /api/workspaces/:id/events` path
- No feature-specific server-side spawn logic — genesis CLI handles spawning based on events; the server is write-only

#### Out of scope for this module
- Genesis CLI integration — external to genesis_manager

#### Required interface from other modules
None beyond P-05-SWH.

#### Exposed interface (for other modules to depend on)
Same `emitEvent` function from P-05-SWH — no additions.

#### Evaluator contract
- **success case**: `spawn_created` event appended to `events.jsonl` identically to any other event type
- **failure case**: lock contention → `WriteError` propagated to route → 503 response
- **side effects**: same as P-05-SWH

---

## 3. Feature Coverage Check

### REQ-F-PROJ-001 — Project Navigator

| Projection | Module | Covers |
|---|---|---|
| P-01-API | api-client | All domain types + getWorkspaces, addWorkspace, removeWorkspace, getWorkspaceSummary |
| P-01-RTG | routing | ROUTES, NavHandle, buildNavPath, root route config |
| P-01-STO | store | projectStore — registeredPaths, summaries, addWorkspace, removeWorkspace, setActiveProject, refreshAll |
| P-01-FPN | feature-project-nav | ProjectListPage, ProjectCard, WorkspaceConfigDrawer |
| P-01-SVC | server-core | Express bootstrap, middleware, route mounting, production SPA serve |
| P-01-SWR | server-workspace-reader | WorkspaceReader.getWorkspaceSummary, EventLogReader.readAll |
| P-01-SRR | server-routes | GET/POST/DELETE /api/workspaces, GET /api/workspaces/:id/summary |

**Coverage verdict**: Full. All ACs covered — workspace registration (P-01-STO + P-01-FPN), server CRUD (P-01-SVC + P-01-SRR), type safety (P-01-API), navigation (P-01-RTG).

---

### REQ-F-NAV-001 — Navigation Infrastructure

| Projection | Module | Covers |
|---|---|---|
| P-02-RTG | routing | All workspace-scoped routes, PlaceholderPage, complete buildNavPath |
| P-02-APP | app-shell | App.tsx router creation, layout wrapper, ProjectListSidebar |
| P-02-SRR | server-routes | nav.ts — event detail by index |

**Coverage verdict**: Full. Router configured (P-02-RTG), app mounted with layout (P-02-APP), nav API endpoint (P-02-SRR). All canonical pages routable.

---

### REQ-F-UX-001 — UX Infrastructure

| Projection | Module | Covers |
|---|---|---|
| P-03-UXS | ux-shared | FreshnessIndicator (5 states), CommandLabel, CMD strings, ConfirmActionDialog |
| P-03-STO | store | workspaceStore scaffold — overview/gates/features/traceability/isLoading/loadError |
| P-03-APP | app-shell | useWorkspacePoller — 30s polling, immediate first fire, error propagation |

**Coverage verdict**: Full. Freshness display (P-03-UXS), polling engine (P-03-APP), store scaffold for downstream features (P-03-STO).

---

### REQ-F-OVR-001 — Project Overview

| Projection | Module | Covers |
|---|---|---|
| P-04-API | api-client | getOverview |
| P-04-STO | store | workspaceStore.loadWorkspace → overview field |
| P-04-FOV | feature-overview | ProjectOverviewPage (no-scroll grid), FeatureStatusBar, FeatureStatusCounts, ChangeHighlighter |
| P-04-SWR | server-workspace-reader | WorkspaceReader.getOverview — YAML parsing + event log summary |
| P-04-SRR | server-routes | GET /api/workspaces/:id/overview |

**Coverage verdict**: Full. Fixed-height grid (P-04-FOV), status bar (P-04-FOV), change highlighting (P-04-FOV), server read path (P-04-SWR + P-04-SRR).

---

### REQ-F-SUP-001 — Supervision Console

| Projection | Module | Covers |
|---|---|---|
| P-05-API | api-client | getGates, getFeatures, postEvent, setAutoMode |
| P-05-STO | store | workspaceStore.loadWorkspace → gates, features fields |
| P-05-FSU | feature-supervision | SupervisionConsolePage, HumanGateQueue, FeatureList, GateActionPanel, AutoModeToggle |
| P-05-SWR | server-workspace-reader | getGates (unresolved gate computation), getFeatures (with isStuck/autoMode), computeAutoMode, computeIsStuck |
| P-05-SRR | server-routes | GET /gates, GET /features, POST /events |
| P-05-SWH | server-write-handler | emitEvent with proper-lockfile, WriteLog |

**Coverage verdict**: Full. Gate queue UI (P-05-FSU), approve/reject with required comment (P-05-FSU), isStuck derived from events (P-05-SWR), auto-mode toggle (P-05-FSU), write path with locking (P-05-SWH).

---

### REQ-F-EVI-001 — Evidence Browser

| Projection | Module | Covers |
|---|---|---|
| P-06-API | api-client | getTraceability, rerunGapAnalysis |
| P-06-STO | store | workspaceStore.loadWorkspace → traceability field |
| P-06-FEV | feature-evidence | EvidenceBrowserPage, TraceabilityTable, EventDetailPanel, GapAnalysisPanel |
| P-06-SWR | server-workspace-reader | TraceabilityScanner (# Implements / # Validates tags, mtime cache) |
| P-06-SRR | server-routes | GET /traceability, POST /gap-analysis/rerun |

**Coverage verdict**: Full. REQ key coverage display (P-06-FEV + P-06-SWR), event detail panel (P-06-FEV), gen-gaps rerun (P-06-SRR + P-06-FEV), mtime-cached scan (P-06-SWR).

---

### REQ-F-CTL-001 — Control Surface

| Projection | Module | Covers |
|---|---|---|
| P-07-API | api-client | spawn_created event via postEvent (no new methods needed) |
| P-07-FCT | feature-control | ControlSurface panel, SpawnFeaturePanel |
| P-07-SWH | server-write-handler | spawn_created goes through existing emitEvent (no additions) |

**Coverage verdict**: Full. ControlSurface panel with gate actions + spawn + auto-mode (P-07-FCT), SpawnFeaturePanel with vectorType/title/satisfies form (P-07-FCT), event write path shared from REQ-F-SUP-001 projections.

---

## 4. Construction Order

Construction can proceed in four waves. Agents within the same wave have no interdependencies and can build in parallel.

### Wave 1 — Leaf modules (no browser or server dependencies)

All four can be constructed simultaneously by independent agents.

| Agent | Projection(s) | What to build |
|---|---|---|
| Agent A | P-01-API | All shared TypeScript types + WorkspaceApiClient (getWorkspaces, addWorkspace, removeWorkspace, getWorkspaceSummary) |
| Agent B | P-01-RTG + P-02-RTG | ROUTES, NavHandle, buildNavPath, PlaceholderPage, full buildRouterConfig() |
| Agent C | P-01-SWR + P-04-SWR + P-05-SWR + P-06-SWR | WorkspaceReader (all methods), EventLogReader (readAll + computeAutoMode + computeIsStuck), TraceabilityScanner |
| Agent D | P-05-SWH + P-07-SWH | EventEmitHandler (emitEvent with proper-lockfile), WriteLog |

**Gate**: All Wave 1 modules have Vitest unit tests passing against their exposed interfaces using stub data (no running server required).

---

### Wave 2 — Second-order modules (depend on Wave 1 only)

| Agent | Projection(s) | What to build | Depends on |
|---|---|---|---|
| Agent E | P-03-UXS | FreshnessIndicator, CommandLabel, CMD, ConfirmActionDialog | P-01-RTG (NavHandle type) |
| Agent F | P-01-STO + P-03-STO + P-04-STO + P-05-STO + P-06-STO | projectStore + full workspaceStore (all loadWorkspace extensions, refreshAll, clearWorkspace) | P-01-API (all methods) |
| Agent G | P-01-SRR + P-02-SRR + P-04-SRR + P-05-SRR + P-06-SRR + P-01-SVC | All server routes + Express bootstrap | P-01-SWR, P-05-SWH |

**Gate**: Server-side: integration test calling `createApp()` with filesystem fixtures; each route returns correct shape. Browser-side: store tests with mocked `WorkspaceApiClient`.

---

### Wave 3 — Feature modules (depend on Wave 1 + Wave 2)

All five feature modules can be constructed simultaneously.

| Agent | Projection(s) | What to build | Depends on |
|---|---|---|---|
| Agent H | P-02-APP + P-03-APP | App.tsx, main.tsx, sidebar layout, useWorkspacePoller | P-01-STO (projectStore), P-02-RTG |
| Agent I | P-01-FPN | ProjectListPage, ProjectCard, WorkspaceConfigDrawer | P-01-STO, P-03-UXS, P-01-RTG |
| Agent J | P-04-FOV | ProjectOverviewPage, FeatureStatusBar, FeatureStatusCounts, ChangeHighlighter | P-04-STO, P-03-UXS, P-02-RTG |
| Agent K | P-05-FSU | SupervisionConsolePage, HumanGateQueue, FeatureList, GateActionPanel, AutoModeToggle | P-05-STO, P-05-API, P-03-UXS, P-02-RTG |
| Agent L | P-06-FEV | EvidenceBrowserPage, TraceabilityTable, EventDetailPanel, GapAnalysisPanel | P-06-STO, P-06-API, P-03-UXS, P-02-RTG |

**Gate**: Component tests using Vitest + React Testing Library with mocked stores and API; key interactions tested (approve gate, reject gate validation, add workspace, re-run gaps).

---

### Wave 4 — Cross-feature dependent module

| Agent | Projection(s) | What to build | Depends on |
|---|---|---|---|
| Agent M | P-07-FCT | ControlSurface, SpawnFeaturePanel | P-05-FSU (GateActionPanel, AutoModeToggle), P-07-API (postEvent), P-03-UXS |

**Gate**: ControlSurface renders correctly within SupervisionConsolePage; SpawnFeaturePanel form validation blocks submit on invalid REQ key; spawn event emitted on confirm.

---

### Integration Gate (all waves complete)

- Full E2E: browser at `http://localhost:5173`; add workspace pointing to a real genesis workspace directory; overview page loads feature data; supervision shows gates; evidence shows traceability; approve a gate → event in `events.jsonl`; gen-gaps rerun button triggers subprocess; FreshnessIndicator cycles through states on poll.

---

*30 projections covering 7 features × 14 modules. DAG acyclic. Maximum parallel agents: 4 (Wave 1), 3 (Wave 2), 5 (Wave 3), 1 (Wave 4). All projections self-contained — each can be implemented independently with only type stubs from other modules.*
