# Basis Projections — REQ-F-FSNAV-001: Filesystem Workspace Navigator
# Implements: REQ-F-FSNAV-001, REQ-F-FSNAV-002, REQ-F-FSNAV-003

**Version**: 0.1.0
**Date**: 2026-03-13
**Edge**: module_decomposition→basis_projections
**Tenant**: react_vite
**Source**: REQ-F-FSNAV-001-module-decomp.md

---

## Projection Index (addendum to BASIS_PROJECTIONS.md)

| # | Projection ID | File | Type | Module |
|---|---------------|------|------|--------|
| 1 | P-FSNAV-01 | `server/routes/fs.ts` | New | server-routes |
| 2 | P-FSNAV-02 | `server/index.ts` | Modified | server-core |
| 3 | P-FSNAV-03 | `src/api/types.ts` | Modified | api-client |
| 4 | P-FSNAV-04 | `src/api/WorkspaceApiClient.ts` | Modified | api-client |
| 5 | P-FSNAV-05 | `src/features/project-nav/FolderBrowser.tsx` | New | feature-project-nav |
| 6 | P-FSNAV-06 | `src/features/project-nav/WorkspaceConfigDrawer.tsx` | Modified | feature-project-nav |

---

## P-FSNAV-01 — `server/routes/fs.ts` (New)
**Implements**: REQ-F-FSNAV-001 (AC-1, AC-2, AC-3, AC-8)

**Full skeleton** (see `REQ-F-FSNAV-001-design.md` §Component 1 for the complete implementation):

```typescript
// server/routes/fs.ts
import { Router, Request, Response } from 'express'
import fs from 'node:fs/promises'
import path from 'node:path'

const router = Router()
const MAX_ENTRIES = 500

router.get('/browse', async (req: Request, res: Response): Promise<void> => {
  // 1. Resolve path (default: process.cwd()) — AC-2
  // 2. Validate it is a directory — 400 if not
  // 3. readdir with { withFileTypes: true }
  // 4. Filter: isDirectory() && !name.startsWith('.') — AC-8
  // 5. Parallel fs.access checks for .ai-workspace/events/events.jsonl — AC-1
  // 6. Sort: workspace dirs first, then alpha
  // 7. Cap at MAX_ENTRIES, set truncated flag
  // 8. Compute parent (null at root)
  // 9. res.json({ path, parent, entries, truncated })
})

export default router
```

**Exposed interface**:
```typescript
// GET /api/fs/browse?path=<string>
// Response: FsBrowseResult (defined in P-FSNAV-03)
```

**Internal dependencies**: `node:fs/promises`, `node:path` (built-in only)

---

## P-FSNAV-02 — `server/index.ts` (Modified)
**Implements**: REQ-F-FSNAV-001 mount point

**Delta** — 2 lines added after existing route mounts:
```typescript
import fsRouter from './routes/fs.js'
// ...
app.use('/api/fs', fsRouter)
```

**Position**: after `app.use('/api', navRouter)`, before the static serving block.

**No other changes** to this file.

---

## P-FSNAV-03 — `src/api/types.ts` (Modified)
**Implements**: REQ-F-FSNAV-001 (client-side types)

**Additions** (append to end of file):
```typescript
// ── Filesystem Browse (REQ-F-FSNAV-001) ─────────────────────────────────────

export interface FsEntry {
  name: string
  absolutePath: string
  isDir: true
  hasWorkspace: boolean
}

export interface FsBrowseResult {
  path: string
  parent: string | null
  entries: FsEntry[]
  truncated?: boolean
}
```

**No changes** to existing types.

---

## P-FSNAV-04 — `src/api/WorkspaceApiClient.ts` (Modified)
**Implements**: REQ-F-FSNAV-001

**Addition** — one method added to `WorkspaceApiClient` class:
```typescript
// Implements: REQ-F-FSNAV-001
async browsePath(path?: string): Promise<FsBrowseResult> {
  const url = new URL(`${this.baseUrl}/api/fs/browse`)
  if (path) url.searchParams.set('path', path)
  const res = await fetch(url.toString())
  return handleResponse<FsBrowseResult>(res)
}
```

**Import addition**: `FsBrowseResult` added to types import at top of file.

**No changes** to existing methods or the singleton export.

---

## P-FSNAV-05 — `src/features/project-nav/FolderBrowser.tsx` (New)
**Implements**: REQ-F-FSNAV-002 (AC-4, AC-5, AC-6, AC-7)

**Full skeleton** (see `REQ-F-FSNAV-001-design.md` §Component 2 for the complete implementation):

```typescript
// src/features/project-nav/FolderBrowser.tsx
import React, { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../../api/WorkspaceApiClient'
import type { FsEntry } from '../../api/types'

interface FolderBrowserProps {
  onSelectWorkspace: (absolutePath: string) => void
  initialPath?: string
}

export function FolderBrowser({ onSelectWorkspace, initialPath }: FolderBrowserProps) {
  // State: currentPath, parent, entries, truncated, loading, error
  // navigate(targetPath?) — fetches apiClient.browsePath(), updates state
  // useEffect → navigate(initialPath) on mount
  // breadcrumbSegments = currentPath.split('/').filter(Boolean)
  // Render:
  //   - Breadcrumb: / + segments + ↑ Up button (AC-7)
  //   - Entry list with 🟢/📁 icon, Genesis badge, Add button (AC-4, AC-5, AC-6)
  //   - Truncation notice if truncated (AC-1 tolerance)
  //   - Loading/error states
}
```

**Props contract**:
- `onSelectWorkspace(absolutePath)` — called when user clicks Add on a workspace dir
- `initialPath?` — undefined means server uses CWD

**Local state only** — no Zustand interactions.

---

## P-FSNAV-06 — `src/features/project-nav/WorkspaceConfigDrawer.tsx` (Modified)
**Implements**: REQ-F-FSNAV-003 (AC-6)

**Additions to existing component**:

1. New import:
   ```typescript
   import { FolderBrowser } from './FolderBrowser'
   ```

2. New local state:
   ```typescript
   type InputMode = 'browse' | 'manual'
   const [inputMode, setInputMode] = useState<InputMode>('browse')
   ```

3. New handler:
   ```typescript
   const handleSelectWorkspace = async (absolutePath: string) => {
     setAdding(true)
     setAddError(null)
     try {
       await addWorkspace(absolutePath)
     } catch (err) {
       setAddError(err instanceof Error ? err.message : 'Failed to add workspace')
     } finally {
       setAdding(false)
     }
   }
   ```

4. JSX additions in the "add workspace" section:
   - Browse/Manual toggle tab buttons above the input area
   - `{inputMode === 'browse' ? <FolderBrowser onSelectWorkspace={...} /> : <>{existing text input}</> }`

**No changes** to: workspace list rendering, remove button, store interactions, drawer open/close logic.

---

## AC Coverage

| AC | Covered by |
|----|-----------|
| AC-1 | P-FSNAV-01 hasWorkspace parallel check, 500 cap, truncated flag |
| AC-2 | P-FSNAV-01 `process.cwd()` default |
| AC-3 | P-FSNAV-01 `path.resolve(rawPath)` normalises `..` |
| AC-4 | P-FSNAV-05 breadcrumb + list + badge render |
| AC-5 | P-FSNAV-05 navigate(entry.absolutePath) on dir click |
| AC-6 | P-FSNAV-05 onSelectWorkspace → P-FSNAV-06 handleSelectWorkspace → addWorkspace() |
| AC-7 | P-FSNAV-05 breadcrumb segment buttons + ↑ Up button |
| AC-8 | P-FSNAV-01 `!d.name.startsWith('.')` filter |

---

## Build Order

Dependencies flow: P-FSNAV-01 → P-FSNAV-02 → (server complete) → P-FSNAV-03 → P-FSNAV-04 → P-FSNAV-05 → P-FSNAV-06

Recommended build sequence:
1. P-FSNAV-03 (types — no deps)
2. P-FSNAV-01 (server route — no client deps)
3. P-FSNAV-02 (mount — requires P-FSNAV-01)
4. P-FSNAV-04 (api client method — requires P-FSNAV-03)
5. P-FSNAV-05 (FolderBrowser — requires P-FSNAV-03, P-FSNAV-04)
6. P-FSNAV-06 (drawer update — requires P-FSNAV-05)
