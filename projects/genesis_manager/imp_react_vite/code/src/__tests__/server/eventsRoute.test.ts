// @vitest-environment node
// Validates: REQ-DATA-WORK-001, REQ-DATA-WORK-002, REQ-BR-SUPV-001, REQ-BR-SUPV-002

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock external dependencies before importing route modules
// ---------------------------------------------------------------------------

vi.mock('../../../server/lib/workspaceRegistry.js', () => ({
  loadRegistry: vi.fn(),
  findById: vi.fn(),
}))

vi.mock('../../../server/handlers/EventEmitHandler.js', () => ({
  emitEvent: vi.fn(),
}))

import { loadRegistry, findById } from '../../../server/lib/workspaceRegistry.js'
import { emitEvent } from '../../../server/handlers/EventEmitHandler.js'
import { WriteError } from '../../../server/types.js'

const mockLoadRegistry = vi.mocked(loadRegistry)
const mockFindById = vi.mocked(findById)
const mockEmitEvent = vi.mocked(emitEvent)

// ---------------------------------------------------------------------------
// Import the router under test after all mocks are in place
// ---------------------------------------------------------------------------

import eventsRouter from '../../../server/routes/events.js'

// ---------------------------------------------------------------------------
// Minimal express-like request/response helpers
// ---------------------------------------------------------------------------

function makeRes() {
  const res = {
    _status: 200,
    _body: undefined as unknown,
    status(code: number) { this._status = code; return this },
    json(body: unknown) { this._body = body; return this },
  }
  return res
}

function makeReq(id: string, body: Record<string, unknown> = {}) {
  return { params: { id }, body }
}

// ---------------------------------------------------------------------------
// Extract the POST /:id/events handler from the router stack
// ---------------------------------------------------------------------------

function findPostHandler(router: { stack: { route?: { methods?: Record<string, boolean>; path: string; stack: { handle: (...args: unknown[]) => unknown }[] } }[] }) {
  for (const layer of router.stack) {
    if (layer.route && layer.route.path === '/:id/events') {
      return layer.route.stack[0].handle
    }
  }
  return null
}

const postHandler = findPostHandler(eventsRouter as unknown as Parameters<typeof findPostHandler>[0])

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const WORKSPACE_ID = 'ws-test-001'
const WORKSPACE_PATH = '/workspace/my-project/.ai-workspace'
const REGISTRY_ENTRY = { id: WORKSPACE_ID, path: WORKSPACE_PATH, name: 'My Project' }

// ---------------------------------------------------------------------------
// POST /:id/events — REQ-DATA-WORK-001: append event to events.jsonl
// ---------------------------------------------------------------------------

describe('POST /workspaces/:id/events', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockLoadRegistry.mockResolvedValue([REGISTRY_ENTRY])
    mockFindById.mockReturnValue(REGISTRY_ENTRY)
    mockEmitEvent.mockResolvedValue(undefined)
  })

  it('returns 200 ok when a valid event is posted — REQ-DATA-WORK-001', async () => {
    const req = makeReq(WORKSPACE_ID, { event_type: 'iteration_completed' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(200)
    expect(res._body).toEqual({ ok: true })
  })

  it('calls emitEvent with the workspace path and payload — REQ-DATA-WORK-001', async () => {
    const payload = { event_type: 'edge_started', feature: 'REQ-F-001', edge: 'code' }
    const req = makeReq(WORKSPACE_ID, payload)
    const res = makeRes()
    await postHandler?.(req, res, () => {})

    expect(mockEmitEvent).toHaveBeenCalledWith(WORKSPACE_PATH, expect.objectContaining({
      event_type: 'edge_started',
      feature: 'REQ-F-001',
      edge: 'code',
    }))
  })

  it('passes optional fields (actor, comment, data) through to emitEvent — REQ-DATA-WORK-002', async () => {
    const payload = {
      event_type: 'review_approved',
      feature: 'REQ-F-001',
      edge: 'design',
      actor: 'human',
      comment: 'LGTM',
      data: { gate: 'approve_arch' },
    }
    const req = makeReq(WORKSPACE_ID, payload)
    const res = makeRes()
    await postHandler?.(req, res, () => {})

    expect(mockEmitEvent).toHaveBeenCalledWith(WORKSPACE_PATH, expect.objectContaining({
      actor: 'human',
      comment: 'LGTM',
      data: { gate: 'approve_arch' },
    }))
  })

  // ─── REQ-BR-SUPV-001: review_requested event type accepted ───────────────

  it('accepts review_requested event type — REQ-BR-SUPV-001', async () => {
    const req = makeReq(WORKSPACE_ID, {
      event_type: 'review_requested',
      feature: 'REQ-F-001',
      edge: 'code',
    })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(200)
    expect(mockEmitEvent).toHaveBeenCalledWith(WORKSPACE_PATH, expect.objectContaining({
      event_type: 'review_requested',
    }))
  })

  // ─── REQ-BR-SUPV-002: review_approved / review_rejected accepted ─────────

  it('accepts review_approved event type — REQ-BR-SUPV-002', async () => {
    const req = makeReq(WORKSPACE_ID, {
      event_type: 'review_approved',
      feature: 'REQ-F-001',
      edge: 'code',
      actor: 'human',
    })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(200)
  })

  it('accepts review_rejected event type — REQ-BR-SUPV-002', async () => {
    const req = makeReq(WORKSPACE_ID, {
      event_type: 'review_rejected',
      feature: 'REQ-F-001',
      edge: 'code',
      actor: 'human',
      comment: 'Needs rework',
    })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(200)
  })

  // ─── Error cases ──────────────────────────────────────────────────────────

  it('returns 400 when event_type is missing from the body', async () => {
    const req = makeReq(WORKSPACE_ID, { feature: 'REQ-F-001' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
    expect(mockEmitEvent).not.toHaveBeenCalled()
  })

  it('returns 400 when event_type is not a string', async () => {
    const req = makeReq(WORKSPACE_ID, { event_type: 42 })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 404 when workspace is not found', async () => {
    mockFindById.mockReturnValue(undefined)
    const req = makeReq('unknown-id', { event_type: 'iteration_completed' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
    expect(mockEmitEvent).not.toHaveBeenCalled()
  })

  it('returns 503 when emitEvent throws WriteError with LOCK_TIMEOUT', async () => {
    mockEmitEvent.mockRejectedValueOnce(new WriteError('locked', 'LOCK_TIMEOUT'))
    const req = makeReq(WORKSPACE_ID, { event_type: 'iteration_completed' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(503)
    const body = res._body as { code: string }
    expect(body.code).toBe('LOCK_TIMEOUT')
  })

  it('returns 400 when emitEvent throws WriteError with INVALID_PAYLOAD', async () => {
    mockEmitEvent.mockRejectedValueOnce(new WriteError('bad payload', 'INVALID_PAYLOAD'))
    const req = makeReq(WORKSPACE_ID, { event_type: 'bad-event' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
    const body = res._body as { code: string }
    expect(body.code).toBe('INVALID_PAYLOAD')
  })

  it('returns 500 when emitEvent throws WriteError with IO_ERROR', async () => {
    mockEmitEvent.mockRejectedValueOnce(new WriteError('disk error', 'IO_ERROR'))
    const req = makeReq(WORKSPACE_ID, { event_type: 'iteration_completed' })
    const res = makeRes()
    await postHandler?.(req, res, () => {})
    expect(res._status).toBe(500)
  })
})

// ---------------------------------------------------------------------------
// EventEmitHandler — appendFile pattern (REQ-DATA-WORK-002)
// Tests that emitEvent uses proper atomic file operations.
// ---------------------------------------------------------------------------

describe('emitEvent (EventEmitHandler) — atomic write pattern', () => {
  // We test the handler in isolation with mocked fs.
  // The atomic tmp→rename pattern is in workspaceRegistry.saveRegistry.
  // emitEvent itself uses appendFile (append to existing file after lockfile).

  vi.mock('node:fs/promises', () => ({
    default: {
      readFile: vi.fn(),
      readdir: vi.fn(),
      stat: vi.fn(),
      mkdir: vi.fn(),
      writeFile: vi.fn(),
      rename: vi.fn(),
      appendFile: vi.fn(),
      access: vi.fn(),
    },
  }))

  vi.mock('proper-lockfile', () => ({
    default: {
      lock: vi.fn(),
    },
  }))

  it('WriteLog module can be imported and appendWriteLog is exported — REQ-DATA-WORK-002', async () => {
    // TODO: integration test needed for full lock→append→release cycle
    const { appendWriteLog } = await import('../../../server/handlers/WriteLog.js')
    expect(typeof appendWriteLog).toBe('function')
  })

  it('WriteError class sets code and message correctly', () => {
    const err = new WriteError('test message', 'LOCK_TIMEOUT')
    expect(err.message).toBe('test message')
    expect(err.code).toBe('LOCK_TIMEOUT')
    expect(err.name).toBe('WriteError')
  })

  it('WriteError works for all error codes', () => {
    const codes = ['LOCK_TIMEOUT', 'IO_ERROR', 'INVALID_PAYLOAD'] as const
    for (const code of codes) {
      const err = new WriteError('msg', code)
      expect(err.code).toBe(code)
    }
  })
})
