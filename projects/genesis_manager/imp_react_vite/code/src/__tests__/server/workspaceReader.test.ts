// @vitest-environment node
// Validates: REQ-F-PROJ-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-NFR-REL-001

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Dirent } from 'node:fs'

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
import {
  getWorkspaceSummary,
  getGates,
  getFeatures,
  getOverview,
} from '../../../server/readers/WorkspaceReader'

const mockReadFile = vi.mocked(fs.readFile)
const mockReaddir = vi.mocked(fs.readdir)
const mockYamlLoad = vi.mocked(yaml.load)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDirent(name: string, isFile: boolean, isDirectory: boolean): Dirent {
  return { name, isFile: () => isFile, isDirectory: () => isDirectory } as unknown as Dirent
}

function makeEventLine(overrides: Record<string, unknown>): string {
  return JSON.stringify({ event_type: 'noop', timestamp: '2026-01-01T00:00:00Z', ...overrides })
}

const WORKSPACE = '/workspace/project'

// ---------------------------------------------------------------------------
// getWorkspaceSummary
// ---------------------------------------------------------------------------

describe('getWorkspaceSummary', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns 0 pendingGates and null lastEventAt when events file does not exist', async () => {
    // events.jsonl → ENOENT
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)
    // project_constraints.yml → also ENOENT
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.pendingGates).toBe(0)
    expect(summary.lastEventAt).toBeNull()
  })

  it('returns correct pendingGates count for unresolved review_requested', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events) // events.jsonl
    const constraintsErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(constraintsErr) // project_constraints.yml

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.pendingGates).toBe(1)
  })

  it('returns 0 pendingGates when review_approved follows review_requested for same triple', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1' }),
      makeEventLine({ event_type: 'review_approved', feature: 'F1', edge: 'code', gate_name: 'g1' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.pendingGates).toBe(0)
  })

  it('returns 0 pendingGates when review_rejected follows review_requested', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1' }),
      makeEventLine({ event_type: 'review_rejected', feature: 'F1', edge: 'code', gate_name: 'g1' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.pendingGates).toBe(0)
  })

  it('returns the timestamp of the last event as lastEventAt', async () => {
    const events = [
      makeEventLine({ event_type: 'x', timestamp: '2026-01-01T10:00:00Z' }),
      makeEventLine({ event_type: 'y', timestamp: '2026-01-02T12:00:00Z' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.lastEventAt).toBe('2026-01-02T12:00:00Z')
  })

  it('returns project name from project_constraints.yml project_name field', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err) // events.jsonl ENOENT
    mockReadFile.mockResolvedValueOnce('project_name: My Workspace') // constraints
    mockYamlLoad.mockReturnValueOnce({ project_name: 'My Workspace' })

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.name).toBe('My Workspace')
  })

  it('returns project name from name field when project_name is absent', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)
    mockReadFile.mockResolvedValueOnce('name: Fallback Name')
    mockYamlLoad.mockReturnValueOnce({ name: 'Fallback Name' })

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.name).toBe('Fallback Name')
  })

  it('returns "unknown" when project_constraints.yml is missing', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err) // events.jsonl
    mockReadFile.mockRejectedValueOnce(err) // constraints

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc123')
    expect(summary.name).toBe('unknown')
  })

  it('includes the workspaceId in the result', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'myid123')
    expect(summary.id).toBe('myid123')
    expect(summary.path).toBe(WORKSPACE)
  })

  it('counts stuckFeatures from iteration_completed events', async () => {
    // 3 identical-delta events for F1:code → stuck
    const events = [
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 2 }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 2 }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 2 }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const summary = await getWorkspaceSummary(WORKSPACE, 'abc')
    expect(summary.stuckFeatures).toBe(1)
  })
})

// ---------------------------------------------------------------------------
// getGates
// ---------------------------------------------------------------------------

describe('getGates', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns empty array when no events exist', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const gates = await getGates(WORKSPACE)
    expect(gates).toEqual([])
  })

  it('returns empty array when no review_requested events exist', async () => {
    const events = [makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code' })].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const gates = await getGates(WORKSPACE)
    expect(gates).toEqual([])
  })

  it('returns a gate for each unresolved review_requested', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1' }),
      makeEventLine({ event_type: 'review_requested', feature: 'F2', edge: 'unit_tests', gate_name: 'g2' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const gates = await getGates(WORKSPACE)
    expect(gates).toHaveLength(2)
  })

  it('returns gate with isStuck=true when feature+edge is stuck', async () => {
    const events = [
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 3 }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 3 }),
      makeEventLine({ event_type: 'iteration_completed', feature: 'F1', edge: 'code', delta: 3 }),
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'approve_arch' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const gates = await getGates(WORKSPACE)
    expect(gates).toHaveLength(1)
    expect(gates[0].isStuck).toBe(true)
  })

  it('returns gate with isStuck=false when not stuck', async () => {
    const events = [
      makeEventLine({ event_type: 'review_requested', feature: 'F1', edge: 'code', gate_name: 'g1' }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const gates = await getGates(WORKSPACE)
    expect(gates[0].isStuck).toBe(false)
  })

  it('includes feature, edge, and requestedAt on gate items', async () => {
    const events = [
      makeEventLine({
        event_type: 'review_requested',
        timestamp: '2026-03-01T08:00:00Z',
        feature: 'F1',
        edge: 'design',
        gate_name: 'human_approves_design',
      }),
    ].join('\n')
    mockReadFile.mockResolvedValueOnce(events)

    const gates = await getGates(WORKSPACE)
    expect(gates[0].feature).toBe('F1')
    expect(gates[0].edge).toBe('design')
    expect(gates[0].requestedAt).toBe('2026-03-01T08:00:00Z')
  })
})

// ---------------------------------------------------------------------------
// getFeatures
// ---------------------------------------------------------------------------

describe('getFeatures', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns empty array when active/ and completed/ dirs do not exist', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValue(err)

    const features = await getFeatures(WORKSPACE)
    expect(features).toEqual([])
  })

  it('maps raw YAML to FeatureVector with defaults for missing fields', async () => {
    const activeDirent = [makeDirent('REQ-F-001.yml', true, false)]
    const completedErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })

    mockReaddir.mockResolvedValueOnce(activeDirent as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(completedErr)

    mockReadFile.mockResolvedValueOnce('feature: REQ-F-001')
    mockYamlLoad.mockReturnValueOnce({ feature: 'REQ-F-001' })

    const features = await getFeatures(WORKSPACE)
    expect(features).toHaveLength(1)
    expect(features[0].feature).toBe('REQ-F-001')
    expect(features[0].title).toBe('')     // default
    expect(features[0].status).toBe('pending') // default
    expect(features[0].trajectory).toEqual({}) // default
  })

  it('maps trajectory correctly when present', async () => {
    const activeDirent = [makeDirent('F1.yml', true, false)]
    const completedErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })

    mockReaddir.mockResolvedValueOnce(activeDirent as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(completedErr)

    mockReadFile.mockResolvedValueOnce('yaml content')
    mockYamlLoad.mockReturnValueOnce({
      feature: 'F1',
      title: 'Feature One',
      status: 'in_progress',
      trajectory: { code: { status: 'converged', iteration: 3 } },
    })

    const features = await getFeatures(WORKSPACE)
    expect(features[0].trajectory['code']).toEqual({ status: 'converged', iteration: 3 })
  })

  it('skips non-yml files in active/ directory', async () => {
    const dirents = [
      makeDirent('README.md', true, false),
      makeDirent('feature.yml', true, false),
    ]
    const completedErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })

    mockReaddir.mockResolvedValueOnce(dirents as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(completedErr)

    mockReadFile.mockResolvedValueOnce('feature: X')
    mockYamlLoad.mockReturnValueOnce({ feature: 'X' })

    const features = await getFeatures(WORKSPACE)
    expect(features).toHaveLength(1) // only the .yml
  })

  it('reads features from both active/ and completed/ directories', async () => {
    const activeDirents = [makeDirent('active.yml', true, false)]
    const completedDirents = [makeDirent('completed.yml', true, false)]

    mockReaddir.mockResolvedValueOnce(activeDirents as unknown as Dirent[])
    mockReaddir.mockResolvedValueOnce(completedDirents as unknown as Dirent[])

    mockReadFile.mockResolvedValueOnce('feature: A')
    mockYamlLoad.mockReturnValueOnce({ feature: 'A' })
    mockReadFile.mockResolvedValueOnce('feature: B')
    mockYamlLoad.mockReturnValueOnce({ feature: 'B' })

    const features = await getFeatures(WORKSPACE)
    expect(features).toHaveLength(2)
  })
})

// ---------------------------------------------------------------------------
// getOverview
// ---------------------------------------------------------------------------

describe('getOverview', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns an overview with lastRefreshed as ISO timestamp', async () => {
    const eventsErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(eventsErr) // events.jsonl
    const readdirErr = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValue(readdirErr) // features dirs
    mockReadFile.mockRejectedValueOnce(eventsErr) // project_constraints.yml

    const before = new Date().toISOString()
    const overview = await getOverview(WORKSPACE, 'ws1')
    const after = new Date().toISOString()

    expect(overview.lastRefreshed).toBeDefined()
    expect(overview.lastRefreshed >= before).toBe(true)
    expect(overview.lastRefreshed <= after).toBe(true)
  })

  it('returns the workspaceId in the overview', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)
    mockReaddir.mockRejectedValue(err)
    mockReadFile.mockRejectedValueOnce(err)

    const overview = await getOverview(WORKSPACE, 'ws-abc-123')
    expect(overview.workspaceId).toBe('ws-abc-123')
  })

  it('returns recentEvents from the last 20 events', async () => {
    const lines = Array.from({ length: 25 }, (_, i) =>
      makeEventLine({ event_type: 'x', timestamp: `2026-01-${String(i + 1).padStart(2, '0')}T00:00:00Z` }),
    ).join('\n')
    mockReadFile.mockResolvedValueOnce(lines) // events.jsonl
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValue(err)
    mockReadFile.mockRejectedValueOnce(err) // constraints

    const overview = await getOverview(WORKSPACE, 'ws1')
    expect(overview.recentEvents).toHaveLength(20)
  })

  it('includes features in the overview', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err) // events.jsonl
    const activeDirents = [makeDirent('F1.yml', true, false)]
    mockReaddir.mockResolvedValueOnce(activeDirents as unknown as Dirent[])
    mockReaddir.mockRejectedValueOnce(err)
    mockReadFile.mockResolvedValueOnce('feature: F1')
    mockYamlLoad.mockReturnValueOnce({ feature: 'F1' })
    mockReadFile.mockRejectedValueOnce(err) // constraints

    const overview = await getOverview(WORKSPACE, 'ws1')
    expect(overview.features).toHaveLength(1)
    expect(overview.features[0].feature).toBe('F1')
  })
})
