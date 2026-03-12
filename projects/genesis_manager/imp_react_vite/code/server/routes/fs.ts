// Implements: REQ-F-FSNAV-001
// GET /api/fs/browse?path=<dir> — list subdirectories; detect Genesis workspaces.

import { Router, type Request, type Response } from 'express'
import fs from 'node:fs/promises'
import path from 'node:path'

const router = Router()
const MAX_ENTRIES = 500

interface FsEntry {
  name: string
  absolutePath: string
  isDir: true
  hasWorkspace: boolean
}

interface FsBrowseResult {
  path: string
  parent: string | null
  entries: FsEntry[]
  truncated: boolean
}

router.get('/browse', async (req: Request, res: Response): Promise<void> => {
  // AC-2: default to CWD when path param absent
  const rawPath =
    typeof req.query['path'] === 'string' ? req.query['path'] : process.cwd()

  // AC-3: path.resolve normalises ".." traversal
  const resolved = path.resolve(rawPath)

  // Validate resolved path is a directory
  try {
    const stat = await fs.stat(resolved)
    if (!stat.isDirectory()) {
      res.status(400).json({ message: 'path is not a directory' })
      return
    }
  } catch {
    res.status(400).json({ message: `path not found: ${resolved}` })
    return
  }

  let dirents
  try {
    dirents = await fs.readdir(resolved, { withFileTypes: true })
  } catch {
    res.status(500).json({ message: 'Failed to read directory' })
    return
  }

  // AC-8: exclude hidden entries; keep only directories
  const dirs = dirents
    .filter((d) => d.isDirectory() && !d.name.startsWith('.'))
    .sort((a, b) => a.name.localeCompare(b.name))

  const truncated = dirs.length > MAX_ENTRIES
  const limited = dirs.slice(0, MAX_ENTRIES)

  // AC-1: hasWorkspace check — parallel, non-throwing
  const entries: FsEntry[] = await Promise.all(
    limited.map(async (d) => {
      const absPath = path.join(resolved, d.name)
      const eventsFile = path.join(absPath, '.ai-workspace', 'events', 'events.jsonl')
      let hasWorkspace = false
      try {
        await fs.access(eventsFile)
        hasWorkspace = true
      } catch {
        // not a workspace
      }
      return { name: d.name, absolutePath: absPath, isDir: true as const, hasWorkspace }
    }),
  )

  // Workspace dirs first, then alpha within each group
  entries.sort((a, b) => {
    if (a.hasWorkspace !== b.hasWorkspace) return a.hasWorkspace ? -1 : 1
    return a.name.localeCompare(b.name)
  })

  // parent: null at filesystem root
  const parsed = path.parse(resolved)
  const parent: string | null = parsed.dir !== resolved ? parsed.dir : null

  const result: FsBrowseResult = { path: resolved, parent, entries, truncated }
  res.json(result)
})

export default router
