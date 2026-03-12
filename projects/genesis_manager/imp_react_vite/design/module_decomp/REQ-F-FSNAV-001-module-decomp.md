# Module Decomposition — REQ-F-FSNAV-001: Filesystem Workspace Navigator
# Implements: REQ-F-FSNAV-001, REQ-F-FSNAV-002, REQ-F-FSNAV-003

**Version**: 0.1.0
**Date**: 2026-03-13
**Edge**: design→module_decomposition
**Tenant**: react_vite
**Source**: REQ-F-FSNAV-001-design.md

---

## Module Delta (changes to existing decomposition)

REQ-F-FSNAV-001 touches 3 existing modules and adds 1 new server module:

| Module | Change |
|--------|--------|
| `server-routes` (`server/routes/`) | **Add** `fs.ts` — new browse route |
| `server-core` (`server/index.ts`) | **Modify** — mount `fsRouter` at `/api/fs` |
| `api-client` (`src/api/`) | **Extend** — `FsBrowseResult`, `FsEntry` types + `browsePath()` |
| `feature-project-nav` (`src/features/project-nav/`) | **Add** `FolderBrowser.tsx`; **Modify** `WorkspaceConfigDrawer.tsx` |

No new modules. No new npm dependencies.

---

## Module: server-routes (addendum)

### New file: `server/routes/fs.ts`
**Implements**: REQ-F-FSNAV-001 (AC-1, AC-2, AC-3, AC-8)

**Responsibilities**:
- `GET /api/fs/browse?path=<dir>` — list subdirectories of the given path
- Default to `process.cwd()` when `path` query param absent
- Detect Genesis workspaces: `hasWorkspace = ∃ .ai-workspace/events/events.jsonl`
- Exclude hidden entries (`name.startsWith('.')`)
- Cap at 500 entries; return `truncated: true` if over
- Sort: workspace dirs first, then alphabetical

**Interface exposed**:
```typescript
// GET /api/fs/browse?path=<string>
Response: FsBrowseResult {
  path:      string
  parent:    string | null
  entries:   FsEntry[]
  truncated: boolean
}
```

**Dependencies**: `node:fs/promises`, `node:path` (both built-in — no new packages)

---

## Module: server-core (addendum)

### Modified file: `server/index.ts`
**Change**: one new import + one `app.use` line

```typescript
import fsRouter from './routes/fs.js'
app.use('/api/fs', fsRouter)
```

**Why here**: consistent with how all other route modules are mounted (workspacesRouter, workspaceRouter, eventsRouter, gapAnalysisRouter, navRouter).

---

## Module: api-client (addendum)

### Modified file: `src/api/types.ts`
**Adds**:
```typescript
export interface FsBrowseResult {
  path: string
  parent: string | null
  entries: FsEntry[]
  truncated?: boolean
}

export interface FsEntry {
  name: string
  absolutePath: string
  isDir: true
  hasWorkspace: boolean
}
```

### Modified file: `src/api/WorkspaceApiClient.ts`
**Adds** method:
```typescript
// Implements: REQ-F-FSNAV-001
async browsePath(path?: string): Promise<FsBrowseResult> {
  const url = new URL(`${this.baseUrl}/api/fs/browse`)
  if (path) url.searchParams.set('path', path)
  const res = await fetch(url.toString())
  return handleResponse<FsBrowseResult>(res)
}
```

**No change** to singleton export `apiClient` — new method is available automatically.

---

## Module: feature-project-nav (addendum)

### New file: `src/features/project-nav/FolderBrowser.tsx`
**Implements**: REQ-F-FSNAV-002 (AC-4, AC-5, AC-6, AC-7)

**Responsibilities**:
- Fetch and display subdirectory listing via `apiClient.browsePath()`
- Render breadcrumb: split `currentPath` on `/`; each segment is a navigation button
- Render entry list: workspace dirs highlighted with badge; click → navigate or register
- Expose `onSelectWorkspace(absolutePath)` callback for parent to handle registration

**Props**:
```typescript
interface FolderBrowserProps {
  onSelectWorkspace: (absolutePath: string) => void
  initialPath?: string
}
```

**Local state only** — no Zustand. Navigation state is ephemeral to the drawer session.

**Dependencies**: `apiClient` (api-client module), `FsEntry`/`FsBrowseResult` types

### Modified file: `src/features/project-nav/WorkspaceConfigDrawer.tsx`
**Implements**: REQ-F-FSNAV-003 (AC-6)

**Changes**:
- Add `inputMode: 'browse' | 'manual'` local state (default: `'browse'`)
- Add Browse/Manual tab toggle buttons
- Render `<FolderBrowser>` when `inputMode === 'browse'`
- Existing text-input section shown when `inputMode === 'manual'` (unchanged)
- Add `handleSelectWorkspace(path)` that calls existing `addWorkspace()` store action

**No change to store** — `addWorkspace` action already exists in `useProjectStore`.

---

## Dependency graph (this feature only)

```
WorkspaceConfigDrawer  ──→  FolderBrowser
FolderBrowser          ──→  apiClient.browsePath()
apiClient              ──→  GET /api/fs/browse
server/routes/fs.ts    ──→  node:fs/promises, node:path
server/index.ts        ──→  server/routes/fs.ts (mount)
```

No circular dependencies introduced. All arrows point from consumer to provider.

---

## Build projections (6 files)

| # | File | Type | Module |
|---|------|------|--------|
| P-FSNAV-01 | `server/routes/fs.ts` | New | server-routes |
| P-FSNAV-02 | `server/index.ts` | Modified | server-core |
| P-FSNAV-03 | `src/api/types.ts` | Modified | api-client |
| P-FSNAV-04 | `src/api/WorkspaceApiClient.ts` | Modified | api-client |
| P-FSNAV-05 | `src/features/project-nav/FolderBrowser.tsx` | New | feature-project-nav |
| P-FSNAV-06 | `src/features/project-nav/WorkspaceConfigDrawer.tsx` | Modified | feature-project-nav |
