// @vitest-environment node
// Validates: REQ-F-OVR-002, REQ-F-OVR-003, REQ-F-OVR-004

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock fs/promises and js-yaml (same pattern as workspaceReader.test.ts)
// ---------------------------------------------------------------------------

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

vi.mock('js-yaml', () => ({
  default: {
    load: vi.fn(),
  },
}))

import fs from 'node:fs/promises'
import yaml from 'js-yaml'
import { getOverview, getFeatures } from '../../../server/readers/WorkspaceReader'

const mockReadFile = vi.mocked(fs.readFile)
const mockReaddir = vi.mocked(fs.readdir)
const mockYamlLoad = vi.mocked(yaml.load)

const WORKSPACE = '/workspace/my-project/.ai-workspace'

// ---------------------------------------------------------------------------
// Helper: make an events.jsonl content string
// ---------------------------------------------------------------------------

function makeEventLine(overrides: Record<string, unknown>): string {
  return JSON.stringify({ event_type: 'noop', timestamp: '2026-01-01T00:00:00Z', ...overrides })
}

import type { Dirent } from 'node:fs'

function makeDirent(name: string): Dirent {
  return { name, isFile: () => true, isDirectory: () => false } as unknown as Dirent
}

// ---------------------------------------------------------------------------
// REQ-F-OVR-002 — statusCounts: converged / in_progress / blocked / pending
// ---------------------------------------------------------------------------

describe('getOverview — statusCounts (REQ-F-OVR-002)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('counts converged features correctly', async () => {
    // events.jsonl: empty
    const evErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(evErr) // events.jsonl

    // features/active: one converged feature
    mockReaddir.mockResolvedValueOnce([makeDirent('F1.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' })) // completed dir

    mockReadFile.mockResolvedValueOnce('feature: F1')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F1', title: 'Feature 1', status: 'converged' })

    // project_constraints.yml
    mockReadFile.mockRejectedValueOnce(evErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.statusCounts.converged).toBe(1)
    expect(overview.statusCounts.in_progress).toBe(0)
  })

  it('counts in_progress features (status iterating maps to in_progress)', async () => {
    const evErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(evErr)

    mockReaddir.mockResolvedValueOnce([makeDirent('F2.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(evErr)

    mockReadFile.mockResolvedValueOnce('feature: F2')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F2', title: 'Feature 2', status: 'iterating' })

    mockReadFile.mockRejectedValueOnce(evErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.statusCounts.in_progress).toBeGreaterThan(0)
  })

  it('counts pending features (status pending)', async () => {
    const evErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(evErr)

    mockReaddir.mockResolvedValueOnce([makeDirent('F3.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(evErr)

    mockReadFile.mockResolvedValueOnce('feature: F3')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F3', title: 'Feature 3', status: 'pending' })

    mockReadFile.mockRejectedValueOnce(evErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.statusCounts.pending).toBe(1)
  })

  it('returns pendingGates count from unresolved review_requested events — REQ-F-OVR-002', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1', timestamp: '2026-01-01T01:00:00Z' }),
      makeEventLine({ event_type: 'review_requested', feature: 'F2', edge: 'design', gate_name: 'g2', timestamp: '2026-01-01T02:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const readdirErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValue(readdirErr)

    const constraintsErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(constraintsErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.statusCounts.pendingGates).toBe(2)
    expect(overview.pendingGateCount).toBe(2)
  })

  it('returns 0 pendingGates when all review_requested are resolved', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1', timestamp: '2026-01-01T01:00:00Z' }),
      makeEventLine({ event_type: 'review_approved', feature: 'F1', edge: 'code', gate_name: 'g1', timestamp: '2026-01-01T02:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const readdirErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValue(readdirErr)

    mockReadFile.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.pendingGateCount).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// REQ-F-OVR-003 — feature trajectory data: edge, iteration, delta fields
// ---------------------------------------------------------------------------

describe('getOverview — inProgressFeatures trajectory (REQ-F-OVR-003)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('includes iteration number from iteration_completed events', async () => {
    const events = [
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 3, iteration: 2, timestamp: '2026-01-01T01:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    mockReaddir.mockResolvedValueOnce([makeDirent('F1.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    mockReadFile.mockResolvedValueOnce('feature: F1')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F1', title: 'Feature 1', status: 'in_progress' })

    mockReadFile.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.inProgressFeatures.length).toBeGreaterThan(0)
    const f1 = overview.inProgressFeatures.find((f) => f.featureId === 'F1')
    expect(f1).toBeDefined()
    expect(f1?.iterationNumber).toBe(2)
    expect(f1?.delta).toBe(3)
    expect(f1?.currentEdge).toBe('code')
  })

  it('includes lastEventAt from most recent event for the feature', async () => {
    const events = [
      makeEventLine({ event_type: 'edge_started', feature: 'F1', edge: 'code', timestamp: '2026-01-01T00:00:00Z' }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 1, timestamp: '2026-01-01T01:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    mockReaddir.mockResolvedValueOnce([makeDirent('F1.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    mockReadFile.mockResolvedValueOnce('feature: F1')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F1', title: 'Feature 1', status: 'in_progress' })

    mockReadFile.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    const overview = await getOverview(WORKSPACE, 'ws-1')
    const f1 = overview.inProgressFeatures.find((f) => f.featureId === 'F1')
    expect(f1?.lastEventAt).toBe('2026-01-01T01:00:00Z')
  })

  it('includes recentActivities array in the overview', async () => {
    const evErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(evErr)
    mockReaddir.mockRejectedValue(evErr)
    mockReadFile.mockRejectedValueOnce(evErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(Array.isArray(overview.recentActivities)).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// REQ-F-OVR-004 — changeHighlights: features changed since last session
// Tested via getFeatures + featureLastEvents (overview.featureLastEvents)
// ---------------------------------------------------------------------------

describe('getOverview — featureLastEvents for change detection (REQ-F-OVR-004)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('featureLastEvents maps featureId to its most recent event timestamp', async () => {
    const events = [
      makeEventLine({ event_type: 'edge_started', feature: 'F1', timestamp: '2026-01-01T08:00:00Z' }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 2, timestamp: '2026-01-01T10:00:00Z' }),
      makeEventLine({ event_type: 'edge_started', feature: 'F2', timestamp: '2026-01-02T09:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    mockReaddir.mockRejectedValue(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    mockReadFile.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(overview.featureLastEvents['F1']).toBe('2026-01-01T10:00:00Z')
    expect(overview.featureLastEvents['F2']).toBe('2026-01-02T09:00:00Z')
  })

  it('featureLastEvents is empty when there are no events', async () => {
    const evErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(evErr)
    mockReaddir.mockRejectedValue(evErr)
    mockReadFile.mockRejectedValueOnce(evErr)

    const overview = await getOverview(WORKSPACE, 'ws-1')
    expect(Object.keys(overview.featureLastEvents)).toHaveLength(0)
  })
})

// ---------------------------------------------------------------------------
// getFeatures — FeatureVector satisfies field (REQ-F-OVR-002 via coverage)
// ---------------------------------------------------------------------------

describe('getFeatures — satisfies REQ keys present (REQ-F-OVR-002)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Default: events.jsonl not found (ENOENT) — handled gracefully by readAll
    mockReadFile.mockRejectedValue(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))
  })

  it('maps satisfies field from YAML to FeatureVector', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('F1.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    mockReadFile.mockResolvedValueOnce('yaml content')
    mockYamlLoad.mockReturnValueOnce({
      feature: 'REQ-F-AUTH-001',
      title: 'Auth feature',
      status: 'in_progress',
      satisfies: ['REQ-F-AUTH-001', 'REQ-F-AUTH-002'],
    })

    const features = await getFeatures(WORKSPACE)
    expect(features[0].satisfies).toEqual(['REQ-F-AUTH-001', 'REQ-F-AUTH-002'])
  })

  it('returns empty satisfies array when field is absent', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('F1.yml')] as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(Object.assign(new Error('ENOENT'), { code: 'ENOENT' }))

    mockReadFile.mockResolvedValueOnce('yaml content')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F1' })

    const features = await getFeatures(WORKSPACE)
    expect(features[0].satisfies).toEqual([])
  })
})
