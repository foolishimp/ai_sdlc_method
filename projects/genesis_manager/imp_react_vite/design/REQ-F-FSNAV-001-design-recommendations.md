# Design Recommendations — REQ-F-FSNAV-001: Filesystem Workspace Navigator

**Feature**: REQ-F-FSNAV-001
**Edge**: feature_decomposition→design_recommendations
**Iteration**: 1
**Date**: 2026-03-13

---

## Summary

Replace the current manual absolute-path input in `WorkspaceConfigDrawer` with a filesystem browser that lets users navigate folders and one-click register Genesis workspaces. The browser must run on the server (filesystem access) and stream entries to the client (no filesystem API in browsers).

---

## Recommendation 1 — Server: `/api/fs/browse` route (AC-1, AC-2, AC-3)

Add a new route file `server/routes/fs.ts` following the existing `routes/workspaces.ts` pattern.

**Endpoint**: `GET /api/fs/browse?path=<absolute-dir>`

```
Response: {
  path:    string          // resolved absolute path returned
  parent:  string | null   // parent dir (null at filesystem root)
  entries: FsEntry[]
}

FsEntry: {
  name:         string   // directory name only
  absolutePath: string   // full path (used for navigation + registration)
  isDir:        true     // only directories returned
  hasWorkspace: boolean  // .ai-workspace/events/events.jsonl accessible
}
```

**Implementation notes**:
- Default path = `process.cwd()` when query param absent (AC-2)
- Resolve `path.resolve(rawParam)` to normalise `..` traversal (AC-3)
- `readdir` with `withFileTypes: true`, filter `isDirectory()` only
- Hidden entries (name starts with `.`) excluded from results (AC-8)
- `hasWorkspace` check: `fs.access(join(entry, '.ai-workspace', 'events', 'events.jsonl'))` — no-throw, boolean
- Sort: workspace dirs first, then alphabetically within each group
- Cap at 500 entries; return `truncated: true` if over (AC-1 tolerance)
- No path traversal restriction beyond `path.resolve` normalisation — server already runs with user's filesystem permissions

Mount in `server/index.ts`:
```ts
import fsRouter from './routes/fs.js'
app.use('/api/fs', fsRouter)
```

---

## Recommendation 2 — Client: `FolderBrowser` component (AC-4–AC-7)

New component: `src/features/project-nav/FolderBrowser.tsx`

**UI structure** (no external deps beyond what's already in the project):
```
┌─────────────────────────────────────────────┐
│ / Users / jim / src / apps              [↑] │  ← breadcrumb (AC-7)
├─────────────────────────────────────────────┤
│ 📁 ai_sdlc_method          [Genesis ✓]  [+] │  ← workspace badge + add button (AC-6)
│ 📁 c4h                                      │  ← regular dir (AC-5)
│ 📁 c4h_editor                               │
│   ...                                       │
└─────────────────────────────────────────────┘
```

**State** (local — no Zustand store needed):
```ts
interface BrowserState {
  currentPath: string
  entries: FsEntry[]
  loading: boolean
  error: string | null
}
```

**Behaviour**:
- On mount: fetch `/api/fs/browse` (defaults to CWD)
- Click regular dir → fetch `/api/fs/browse?path={entry.absolutePath}` (AC-5)
- Click workspace dir → call `onSelectWorkspace(entry.absolutePath)` (AC-6)
- Breadcrumb segments: split `currentPath` on `/`, each segment clickable, builds path by joining from root (AC-7)

**FsEntry API type** added to `src/api/types.ts`:
```ts
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

New method on `WorkspaceApiClient`:
```ts
async browsePath(path?: string): Promise<FsBrowseResult> {
  const url = new URL(`${this.baseUrl}/api/fs/browse`)
  if (path) url.searchParams.set('path', path)
  const res = await fetch(url.toString())
  return handleResponse<FsBrowseResult>(res)
}
```

---

## Recommendation 3 — Integration: WorkspaceConfigDrawer replacement (AC-6)

Replace the text-input section in `WorkspaceConfigDrawer` with the `FolderBrowser`. Keep the text-input as a fallback toggle ("Enter path manually") for power users.

```
┌── Manage Workspaces ─────────────────────── × ┐
│                                               │
│  [Browse]  [Manual path]  ← tab toggle        │
│                                               │
│  [FolderBrowser component]                   │
│    or                                        │
│  [existing text input + Add button]          │
│                                               │
│  ─── Registered workspaces ───────────────   │
│   genesis_manager  /…/.ai-workspace    [×]   │
└───────────────────────────────────────────────┘
```

**On workspace selection** (`onSelectWorkspace`):
1. Call `addWorkspace(absolutePath)` (existing store action — already calls `POST /api/workspaces`)
2. On success: close drawer, navigate to the new workspace overview

No new Zustand stores needed. FolderBrowser is a controlled component driven by local state + the existing `addWorkspace` action.

---

## Recommendation 4 — CORS allowlist (already resolved)

Port 5174 has been added to the CORS allowlist in `server/index.ts`. No further action needed.

---

## Non-recommendations (explicit exclusions)

- **No symlink traversal** — `readdir` returns `isDirectory()` only; symlinks to directories will appear but are fine as-is.
- **No file display** — entries are directories only; files are irrelevant to workspace discovery.
- **No persistence of last-browsed path** — CWD default is sufficient; localStorage would add complexity for no gain.
- **No debounce on navigation** — each click is a discrete user action; no rapid-fire concern.

---

## Evaluator checklist (self-assessed)

| Check | Result |
|-------|--------|
| AC-1 browse API spec is complete | ✓ |
| AC-2 default-to-CWD covered | ✓ |
| AC-3 `..` traversal via `path.resolve` | ✓ |
| AC-4 FolderBrowser renders breadcrumb + list + badge | ✓ |
| AC-5 click-to-navigate behaviour specified | ✓ |
| AC-6 click-workspace triggers registration | ✓ |
| AC-7 breadcrumb clickable | ✓ |
| AC-8 hidden dirs excluded | ✓ |
| Fits existing route pattern (routes/*.ts) | ✓ |
| Fits existing component pattern (features/project-nav/) | ✓ |
| No new dependencies required | ✓ |
| Text-input fallback preserved | ✓ |
