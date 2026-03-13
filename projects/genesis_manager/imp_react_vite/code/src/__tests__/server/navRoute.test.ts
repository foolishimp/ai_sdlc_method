// @vitest-environment node
// Validates: REQ-F-NAV-001, REQ-F-NAV-002, REQ-F-NAV-003, REQ-F-NAV-004, REQ-F-NAV-005

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock all external dependencies before importing the router
vi.mock('../../../server/lib/workspaceRegistry.js', () => ({
  loadRegistry: vi.fn(),
  findById: vi.fn(),
}))

vi.mock('../../../server/readers/WorkspaceReader.js', () => ({
  getFeatures: vi.fn(),
}))

vi.mock('../../../server/readers/EventLogReader.js', () => ({
  readAll: vi.fn(),
}))

vi.mock('../../../server/readers/TraceabilityScanner.js', () => ({
  scan: vi.fn(),
}))

import { loadRegistry, findById } from '../../../server/lib/workspaceRegistry.js'
import { getFeatures } from '../../../server/readers/WorkspaceReader.js'
import { readAll } from '../../../server/readers/EventLogReader.js'
import { scan } from '../../../server/readers/TraceabilityScanner.js'

const mockLoadRegistry = vi.mocked(loadRegistry)
const mockFindById = vi.mocked(findById)
const mockGetFeatures = vi.mocked(getFeatures)
const mockReadAll = vi.mocked(readAll)
const mockScan = vi.mocked(scan)

// ---------------------------------------------------------------------------
// Minimal express-like request/response mock helpers
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

function makeReq(params: Record<string, string> = {}, query: Record<string, string> = {}) {
  return { params, query }
}

// Import router after mocks are set up
import navRouter from '../../../server/routes/nav.js'

// ---------------------------------------------------------------------------
// Extract individual route handlers from the Express router stack
// ---------------------------------------------------------------------------

function findHandler(router: { stack: { route?: { path: string; stack: { handle: (...args: unknown[]) => unknown }[] } }[] }, path: string) {
  for (const layer of router.stack) {
    if (layer.route && layer.route.path === path) {
      return layer.route.stack[0].handle
    }
  }
  return null
}

const featureHandler = findHandler(navRouter as unknown as Parameters<typeof findHandler>[0], '/features/:featureId')
const reqHandler = findHandler(navRouter as unknown as Parameters<typeof findHandler>[0], '/req/:reqKey')
const eventHandler = findHandler(navRouter as unknown as Parameters<typeof findHandler>[0], '/events/:eventIndex')

// ---------------------------------------------------------------------------
// Shared fixtures
// ---------------------------------------------------------------------------

const WORKSPACE_ID = 'ws-001'
const WORKSPACE_PATH = '/workspace/test-project/.ai-workspace'
const REGISTRY = [{ id: WORKSPACE_ID, path: WORKSPACE_PATH, name: 'Test Project' }]

// ---------------------------------------------------------------------------
// GET /api/features/:featureId — REQ-F-NAV-001
// ---------------------------------------------------------------------------

describe('GET /features/:featureId', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockLoadRegistry.mockResolvedValue(REGISTRY)
    mockFindById.mockReturnValue(REGISTRY[0])
  })

  it('returns 400 when workspaceId query param is missing — REQ-F-NAV-001', async () => {
    const req = makeReq({ featureId: 'REQ-F-001' }, {})
    const res = makeRes()
    // findById should not be called if workspaceId missing
    mockFindById.mockReturnValue(undefined)
    await featureHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 404 when workspace is not found — REQ-F-NAV-001', async () => {
    mockFindById.mockReturnValue(undefined)
    const req = makeReq({ featureId: 'REQ-F-001' }, { workspaceId: 'unknown' })
    const res = makeRes()
    await featureHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
  })

  it('returns the feature vector when found — REQ-F-NAV-001', async () => {
    const feature = {
      feature: 'REQ-F-001',
      featureId: 'REQ-F-001',
      title: 'Test Feature',
      status: 'in_progress',
      trajectory: {},
      satisfies: [],
      childVectors: [],
      currentEdge: 'code',
      currentDelta: 2,
      autoModeEnabled: false,
    }
    mockGetFeatures.mockResolvedValue([feature])

    const req = makeReq({ featureId: 'REQ-F-001' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await featureHandler?.(req, res, () => {})

    expect(mockGetFeatures).toHaveBeenCalledWith(WORKSPACE_PATH)
    expect((res._body as typeof feature).feature).toBe('REQ-F-001')
  })

  it('returns 404 when feature ID is not in the workspace — REQ-F-NAV-001', async () => {
    mockGetFeatures.mockResolvedValue([])
    const req = makeReq({ featureId: 'REQ-F-UNKNOWN' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await featureHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
  })
})

// ---------------------------------------------------------------------------
// GET /api/req/:reqKey — REQ-F-NAV-002
// ---------------------------------------------------------------------------

describe('GET /req/:reqKey', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockLoadRegistry.mockResolvedValue(REGISTRY)
    mockFindById.mockReturnValue(REGISTRY[0])
    mockScan.mockResolvedValue([])
  })

  it('returns 400 when workspaceId query param is missing — REQ-F-NAV-002', async () => {
    const req = makeReq({ reqKey: 'REQ-F-001' }, {})
    const res = makeRes()
    mockFindById.mockReturnValue(undefined)
    await reqHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 404 when workspace is not found — REQ-F-NAV-002', async () => {
    mockFindById.mockReturnValue(undefined)
    const req = makeReq({ reqKey: 'REQ-F-001' }, { workspaceId: 'unknown' })
    const res = makeRes()
    await reqHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
  })

  it('returns matching events and traceability entries for a REQ key — REQ-F-NAV-002', async () => {
    const events = [
      { event_type: 'iteration_completed', timestamp: 't1', feature: 'REQ-F-001', edge: 'code' },
      { event_type: 'iteration_completed', timestamp: 't2', feature: 'REQ-F-002', edge: 'code' },
    ]
    mockReadAll.mockResolvedValue({ events: events as Parameters<typeof mockReadAll>[0] extends string ? Awaited<ReturnType<typeof mockReadAll>>['events'] : never, warnings: [] })

    const traceEntries = [
      { reqKey: 'REQ-F-001', kind: 'implements' as const, filePath: 'src/foo.ts', lineNumber: 10 },
    ]
    mockScan.mockResolvedValue(traceEntries)

    const req = makeReq({ reqKey: 'REQ-F-001' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await reqHandler?.(req, res, () => {})

    const body = res._body as { reqKey: string; events: unknown[]; traceability: unknown[] }
    expect(body.reqKey).toBe('REQ-F-001')
    // events that mention REQ-F-001 in their JSON
    expect(body.events.length).toBeGreaterThan(0)
    expect(body.traceability).toHaveLength(1)
  })

  it('filters events containing the REQ key anywhere in serialised form — REQ-F-NAV-002', async () => {
    const events = [
      { event_type: 'iteration_completed', timestamp: 't1', feature: 'REQ-F-002' },
    ]
    mockReadAll.mockResolvedValue({ events: events as unknown as Awaited<ReturnType<typeof readAll>>['events'], warnings: [] })
    mockScan.mockResolvedValue([])

    const req = makeReq({ reqKey: 'REQ-F-001' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await reqHandler?.(req, res, () => {})

    const body = res._body as { events: unknown[] }
    // REQ-F-001 does not appear in the event JSON, so 0 events
    expect(body.events).toHaveLength(0)
  })
})

// ---------------------------------------------------------------------------
// GET /api/events/:eventIndex — REQ-F-NAV-003, REQ-F-NAV-004
// ---------------------------------------------------------------------------

describe('GET /events/:eventIndex', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockLoadRegistry.mockResolvedValue(REGISTRY)
    mockFindById.mockReturnValue(REGISTRY[0])
  })

  it('returns 400 when eventIndex is not a number — REQ-F-NAV-003', async () => {
    const req = makeReq({ eventIndex: 'abc' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 400 when eventIndex is negative — REQ-F-NAV-003', async () => {
    const req = makeReq({ eventIndex: '-1' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 400 when workspaceId query param is missing — REQ-F-NAV-003', async () => {
    const req = makeReq({ eventIndex: '0' }, {})
    const res = makeRes()
    mockFindById.mockReturnValue(undefined)
    await eventHandler?.(req, res, () => {})
    expect(res._status).toBe(400)
  })

  it('returns 404 when workspace is not found — REQ-F-NAV-003', async () => {
    mockFindById.mockReturnValue(undefined)
    const req = makeReq({ eventIndex: '0' }, { workspaceId: 'unknown' })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
  })

  it('returns 404 when eventIndex is out of range — REQ-F-NAV-004', async () => {
    mockReadAll.mockResolvedValue({
      events: [{ event_type: 'x', timestamp: 't' }],
      warnings: [],
    })
    const req = makeReq({ eventIndex: '5' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})
    expect(res._status).toBe(404)
  })

  it('returns the event at the given 0-based index — REQ-F-NAV-004', async () => {
    const events = [
      { event_type: 'iteration_completed', timestamp: '2026-01-01T00:00:00Z', feature: 'F1' },
      { event_type: 'edge_converged', timestamp: '2026-01-02T00:00:00Z', feature: 'F1' },
    ]
    mockReadAll.mockResolvedValue({ events: events as unknown as Awaited<ReturnType<typeof readAll>>['events'], warnings: [] })

    const req = makeReq({ eventIndex: '1' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})

    const body = res._body as { eventIndex: number; event: typeof events[1] }
    expect(body.eventIndex).toBe(1)
    expect(body.event.event_type).toBe('edge_converged')
  })

  it('returns the event at index 0 — REQ-F-NAV-005 (stable bookmarkable URL)', async () => {
    const events = [
      { event_type: 'project_initialized', timestamp: '2026-01-01T00:00:00Z' },
    ]
    mockReadAll.mockResolvedValue({ events: events as unknown as Awaited<ReturnType<typeof readAll>>['events'], warnings: [] })

    const req = makeReq({ eventIndex: '0' }, { workspaceId: WORKSPACE_ID })
    const res = makeRes()
    await eventHandler?.(req, res, () => {})

    const body = res._body as { eventIndex: number; event: typeof events[0] }
    expect(body.eventIndex).toBe(0)
    expect(body.event.event_type).toBe('project_initialized')
  })
})
