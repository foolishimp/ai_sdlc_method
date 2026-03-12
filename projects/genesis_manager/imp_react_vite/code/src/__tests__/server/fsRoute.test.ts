// @vitest-environment node
// Validates: REQ-F-FSNAV-001

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Request, Response } from 'express'

vi.mock('node:fs/promises', () => ({
  default: {
    stat: vi.fn(),
    readdir: vi.fn(),
    access: vi.fn(),
  },
}))

import fs from 'node:fs/promises'

// Import the handler after mocking — we'll extract the route handler by
// building a minimal Router wrapper that captures the registered handler.
// Strategy: re-import the module fresh per test by calling the handler directly
// through a thin express mock.

const mockStat = vi.mocked(fs.stat)
const mockReaddir = vi.mocked(fs.readdir)
const mockAccess = vi.mocked(fs.access)

// Minimal req/res mocks
function makeReq(query: Record<string, string> = {}): Partial<Request> {
  return { query } as Partial<Request>
}

function makeRes() {
  const res = {
    _status: 200,
    _body: null as unknown,
    status(code: number) { this._status = code; return this },
    json(body: unknown) { this._body = body; return this },
  }
  return res
}

// Helper: build a mock Dirent-like object
function makeDir(name: string) {
  return {
    name,
    isDirectory: () => true,
    isFile: () => false,
    isSymbolicLink: () => false,
  }
}

// We need to invoke the actual handler. Import the router and find the handler.
// The easiest approach: mount on a tiny express layer and call it.
// Since we can't use supertest, call router.handle() with fake req/res/next.
import express from 'express'
import fsRouter from '../../../server/routes/fs'

async function callBrowse(query: Record<string, string> = {}): Promise<{ status: number; body: unknown }> {
  return new Promise((resolve) => {
    const app = express()
    app.use('/', fsRouter)

    const req = Object.assign(
      { method: 'GET', url: `/browse?${new URLSearchParams(query)}`, path: '/browse', query },
      // minimal request fields express router needs
    )

    const res = {
      _status: 200,
      _body: null as unknown,
      status(code: number) { this._status = code; return this as unknown as Response },
      json(body: unknown) { this._body = body; resolve({ status: this._status, body }); return this as unknown as Response },
      headersSent: false,
      setHeader: vi.fn(),
      getHeader: vi.fn(),
      removeHeader: vi.fn(),
    }

    // Use router.handle directly
    ;(fsRouter as unknown as { handle: (req: unknown, res: unknown, next: () => void) => void })
      .handle(req, res, () => { resolve({ status: 404, body: { message: 'Not found' } }) })
  })
}

describe('GET /api/fs/browse', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  // AC-1: returns entries for subdirectories
  it('returns entries for subdirectories of the given path', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([makeDir('alpha'), makeDir('beta')] as never)
    mockAccess.mockRejectedValue(new Error('not found'))

    const { status, body } = await callBrowse({ path: '/tmp/test' })
    const b = body as Record<string, unknown>

    expect(status).toBe(200)
    const entries = b['entries'] as Array<Record<string, unknown>>
    expect(entries).toHaveLength(2)
    expect(entries[0]['name']).toBe('alpha')
    expect(entries[0]['isDir']).toBe(true)
    expect(entries[0]['hasWorkspace']).toBe(false)
    expect(b['truncated']).toBe(false)
  })

  // AC-1: hasWorkspace = true when events.jsonl accessible
  it('sets hasWorkspace=true when .ai-workspace/events/events.jsonl is accessible', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([makeDir('myproject')] as never)
    mockAccess.mockResolvedValueOnce(undefined)

    const { status, body } = await callBrowse({ path: '/some/dir' })
    const entries = (body as Record<string, unknown>)['entries'] as Array<Record<string, unknown>>

    expect(status).toBe(200)
    expect(entries[0]['hasWorkspace']).toBe(true)
  })

  // AC-2: defaults to CWD when no path param
  it('defaults to process.cwd() when path param is absent', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([] as never)

    const { status, body } = await callBrowse()

    expect(status).toBe(200)
    expect((body as Record<string, unknown>)['path']).toBe(process.cwd())
  })

  // AC-3: resolves ".." correctly
  it('resolves ".." traversal via path.resolve', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([] as never)

    const { body } = await callBrowse({ path: '/tmp/a/b/..' })

    expect((body as Record<string, unknown>)['path']).toBe('/tmp/a')
  })

  // AC-8: hidden directories excluded
  it('excludes hidden directories (name starts with ".")', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([
      makeDir('visible'),
      makeDir('.hidden'),
      makeDir('.git'),
    ] as never)
    mockAccess.mockRejectedValue(new Error())

    const { body } = await callBrowse({ path: '/tmp/test' })
    const entries = (body as Record<string, unknown>)['entries'] as Array<Record<string, unknown>>

    expect(entries).toHaveLength(1)
    expect(entries[0]['name']).toBe('visible')
  })

  // Workspace dirs sort first — route sorts alpha first, then applies workspace-first reorder
  it('sorts workspace dirs before non-workspace dirs', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    // readdir returns in this order; route sorts alpha first before workspace check
    mockReaddir.mockResolvedValue([makeDir('zorro'), makeDir('alpha')] as never)
    // After alphabetical sort: [alpha, zorro] — Promise.all fires in that order
    mockAccess
      .mockRejectedValueOnce(new Error()) // alpha → no workspace (comes first alphabetically)
      .mockResolvedValueOnce(undefined)   // zorro → has workspace

    const { body } = await callBrowse({ path: '/tmp/test' })
    const entries = (body as Record<string, unknown>)['entries'] as Array<Record<string, unknown>>

    // After workspace-first resort: zorro (workspace) before alpha (no workspace)
    expect(entries[0]['name']).toBe('zorro')
    expect(entries[0]['hasWorkspace']).toBe(true)
    expect(entries[1]['name']).toBe('alpha')
    expect(entries[1]['hasWorkspace']).toBe(false)
  })

  // truncated flag when > 500 entries
  it('sets truncated=true when entries exceed 500', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    const manyDirs = Array.from({ length: 501 }, (_, i) => makeDir(`dir${i}`))
    mockReaddir.mockResolvedValue(manyDirs as never)
    mockAccess.mockRejectedValue(new Error())

    const { body } = await callBrowse({ path: '/tmp/test' })
    const b = body as Record<string, unknown>

    expect(b['truncated']).toBe(true)
    expect((b['entries'] as unknown[]).length).toBe(500)
  })

  // parent null at root
  it('returns parent=null at the filesystem root', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([] as never)

    const { body } = await callBrowse({ path: '/' })

    expect((body as Record<string, unknown>)['parent']).toBeNull()
  })

  // parent path for non-root
  it('returns parent path for non-root directories', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([] as never)

    const { body } = await callBrowse({ path: '/tmp/a' })

    expect((body as Record<string, unknown>)['parent']).toBe('/tmp')
  })

  // 400 when path is not a directory
  it('returns 400 when path is not a directory', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => false } as never)

    const { status, body } = await callBrowse({ path: '/tmp/file.txt' })

    expect(status).toBe(400)
    expect((body as Record<string, string>)['message']).toMatch(/not a directory/)
  })

  // 400 when path does not exist
  it('returns 400 when path does not exist', async () => {
    mockStat.mockRejectedValue(new Error('ENOENT'))

    const { status, body } = await callBrowse({ path: '/nonexistent' })

    expect(status).toBe(400)
    expect((body as Record<string, string>)['message']).toMatch(/not found/)
  })

  // absolutePath on entries
  it('includes absolutePath on each entry', async () => {
    mockStat.mockResolvedValue({ isDirectory: () => true } as never)
    mockReaddir.mockResolvedValue([makeDir('mydir')] as never)
    mockAccess.mockRejectedValue(new Error())

    const { body } = await callBrowse({ path: '/tmp' })
    const entries = (body as Record<string, unknown>)['entries'] as Array<Record<string, unknown>>

    expect(entries[0]['absolutePath']).toBe('/tmp/mydir')
  })
})
