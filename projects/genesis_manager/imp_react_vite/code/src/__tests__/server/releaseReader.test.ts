// @vitest-environment node
// Validates: REQ-F-REL-001, REQ-F-REL-002, REQ-F-REL-003

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

import fs from 'node:fs/promises'
import {
  computeReadiness,
  getReleaseScopeFormatted,
  initiateRelease,
  suggestNextVersion,
} from '../../../server/readers/ReleaseReader'

const mockReadFile = vi.mocked(fs.readFile)
const mockReaddir = vi.mocked(fs.readdir)
const mockAppendFile = vi.mocked(fs.appendFile)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDirent(name: string): Dirent {
  return { name, isFile: () => true, isDirectory: () => false } as unknown as Dirent
}

function makeEvent(eventType: string, extra?: Record<string, unknown>): string {
  return JSON.stringify({ event_type: eventType, timestamp: '2026-01-01T00:00:00Z', ...extra })
}

// ---------------------------------------------------------------------------
// computeReadiness
// ---------------------------------------------------------------------------

describe('computeReadiness', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns ready when active dir is empty, no pending gates, and gaps_validated passes', async () => {
    // events.jsonl — no pending gates, has gaps_validated passing
    mockReadFile.mockResolvedValueOnce(
      [
        makeEvent('gaps_validated', { data: { layer_results: { layer_1: 'pass', layer_2: 'pass' } } }),
      ].join('\n'),
    )
    // features/active/ — empty
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.verdict).toBe('ready')
    expect(result.conditions.every((c) => c.passed)).toBe(true)
  })

  it('returns not-ready when active features exist with non-converged status', async () => {
    mockReadFile.mockResolvedValueOnce(
      [
        makeEvent('gaps_validated', { data: { layer_results: { layer_1: 'pass', layer_2: 'pass' } } }),
      ].join('\n'),
    )
    // features/active/ has one in-progress feature
    mockReaddir.mockResolvedValueOnce([makeDirent('REQ-F-FOO-001.yml')])
    mockReadFile.mockResolvedValueOnce(
      'feature: REQ-F-FOO-001\ntitle: Foo\nstatus: in_progress\nsatisfies:\n  - REQ-F-FOO-001\n',
    )

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.verdict).toBe('not-ready')
    const condition = result.conditions.find((c) => c.id === 'all_features_converged')
    expect(condition?.passed).toBe(false)
  })

  it('returns not-ready when pending human gates exist', async () => {
    // review_requested without a matching review_approved
    mockReadFile.mockResolvedValueOnce(
      [
        makeEvent('review_requested', { feature: 'REQ-F-FOO-001', edge: 'code', gate_name: 'human_approves' }),
        makeEvent('gaps_validated', { data: { layer_results: { layer_1: 'pass', layer_2: 'pass' } } }),
      ].join('\n'),
    )
    // active dir empty
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.verdict).toBe('not-ready')
    const condition = result.conditions.find((c) => c.id === 'no_pending_gates')
    expect(condition?.passed).toBe(false)
  })

  it('returns not-ready when no gaps_validated event exists', async () => {
    // No gaps_validated event
    mockReadFile.mockResolvedValueOnce(
      makeEvent('iteration_completed', { feature: 'F1', edge: 'code', delta: 0 }),
    )
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.verdict).toBe('not-ready')
    const condition = result.conditions.find((c) => c.id === 'gaps_validated')
    expect(condition?.passed).toBe(false)
  })

  it('returns not-ready when gaps_validated has layer_1 fail', async () => {
    mockReadFile.mockResolvedValueOnce(
      makeEvent('gaps_validated', { data: { layer_results: { layer_1: 'fail', layer_2: 'pass' } } }),
    )
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.verdict).toBe('not-ready')
    const condition = result.conditions.find((c) => c.id === 'gaps_validated')
    expect(condition?.passed).toBe(false)
  })

  it('treats resolved review_requested (with review_approved) as no pending gates', async () => {
    mockReadFile.mockResolvedValueOnce(
      [
        makeEvent('review_requested', { feature: 'F1', edge: 'code', gate_name: 'g' }),
        makeEvent('review_approved', { feature: 'F1', edge: 'code', gate_name: 'g' }),
        makeEvent('gaps_validated', { data: { layer_results: { layer_1: 'pass', layer_2: 'pass' } } }),
      ].join('\n'),
    )
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    const condition = result.conditions.find((c) => c.id === 'no_pending_gates')
    expect(condition?.passed).toBe(true)
  })

  it('returns all three conditions in the response', async () => {
    mockReadFile.mockResolvedValueOnce('')
    mockReaddir.mockResolvedValueOnce([])

    const result = await computeReadiness('/workspace', '/workspace/events/events.jsonl')
    expect(result.conditions).toHaveLength(3)
    const ids = result.conditions.map((c) => c.id)
    expect(ids).toContain('all_features_converged')
    expect(ids).toContain('no_pending_gates')
    expect(ids).toContain('gaps_validated')
  })
})

// ---------------------------------------------------------------------------
// getReleaseScopeFormatted
// ---------------------------------------------------------------------------

describe('getReleaseScopeFormatted', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns converged features from completed/ dir', async () => {
    // completed/ dir has one feature
    mockReaddir.mockResolvedValueOnce([makeDirent('REQ-F-FOO-001.yml')])
    mockReadFile.mockResolvedValueOnce(
      'feature: REQ-F-FOO-001\ntitle: Foo Feature\nstatus: converged\nsatisfies:\n  - REQ-F-FOO-001\ntrajectory:\n  code:\n    status: converged\n    iteration: 3\n',
    )
    // active/ dir — empty
    mockReaddir.mockResolvedValueOnce([])

    const result = await getReleaseScopeFormatted('/workspace')
    expect(result).toHaveLength(1)
    expect(result[0].featureId).toBe('REQ-F-FOO-001')
    expect(result[0].title).toBe('Foo Feature')
    expect(result[0].status).toBe('converged')
    expect(result[0].coveragePct).toBe(100)
    expect(result[0].convergedEdges).toContain('code')
  })

  it('returns in_progress features from active/ dir', async () => {
    // completed/ dir — empty
    mockReaddir.mockResolvedValueOnce([])
    // active/ dir has one in-progress feature
    mockReaddir.mockResolvedValueOnce([makeDirent('REQ-F-BAR-001.yml')])
    mockReadFile.mockResolvedValueOnce(
      'feature: REQ-F-BAR-001\ntitle: Bar Feature\nstatus: in_progress\nsatisfies:\n  - REQ-F-BAR-001\ntrajectory:\n  code:\n    status: converged\n    iteration: 1\n  unit_tests:\n    status: pending\n    iteration: 0\n',
    )

    const result = await getReleaseScopeFormatted('/workspace')
    expect(result).toHaveLength(1)
    expect(result[0].status).toBe('in_progress')
    expect(result[0].convergedEdges).toContain('code')
    expect(result[0].pendingEdges).toContain('unit_tests')
  })

  it('returns empty array when both dirs are empty', async () => {
    mockReaddir.mockResolvedValueOnce([])
    mockReaddir.mockResolvedValueOnce([])

    const result = await getReleaseScopeFormatted('/workspace')
    expect(result).toEqual([])
  })

  it('returns empty array when dirs do not exist', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValueOnce(err)
    mockReaddir.mockRejectedValueOnce(err)

    const result = await getReleaseScopeFormatted('/workspace')
    expect(result).toEqual([])
  })
})

// ---------------------------------------------------------------------------
// initiateRelease
// ---------------------------------------------------------------------------

describe('initiateRelease', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('appends release_created event with correct fields', async () => {
    // completed/ dir has 2 features
    mockReaddir.mockResolvedValueOnce([
      makeDirent('REQ-F-FOO-001.yml'),
      makeDirent('REQ-F-BAR-001.yml'),
    ])
    mockReadFile.mockResolvedValueOnce('feature: REQ-F-FOO-001\ntitle: Foo\nstatus: converged\n')
    mockReadFile.mockResolvedValueOnce('feature: REQ-F-BAR-001\ntitle: Bar\nstatus: converged\n')
    mockAppendFile.mockResolvedValueOnce(undefined)

    const result = await initiateRelease('/workspace', '/workspace/events/events.jsonl', '3.0.8')

    expect(mockAppendFile).toHaveBeenCalledOnce()
    const [, appendedContent] = mockAppendFile.mock.calls[0] as [string, string]
    const parsed = JSON.parse(appendedContent.trim())
    expect(parsed.event_type).toBe('release_created')
    expect(parsed.version).toBe('3.0.8')
    expect(typeof parsed.timestamp).toBe('string')
    expect(result.version).toBe('3.0.8')
    expect(result.featuresIncluded).toBe(2)
  })

  it('returns featuresIncluded = 0 when completed dir is empty', async () => {
    mockReaddir.mockResolvedValueOnce([])
    mockAppendFile.mockResolvedValueOnce(undefined)

    const result = await initiateRelease('/workspace', '/workspace/events/events.jsonl', '1.0.0')
    expect(result.featuresIncluded).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// suggestNextVersion
// ---------------------------------------------------------------------------

describe('suggestNextVersion', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns 1.0.0 when no events file exists', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const version = await suggestNextVersion('/workspace/events/events.jsonl')
    expect(version).toBe('1.0.0')
  })

  it('returns 1.0.0 when no release_created event exists', async () => {
    mockReadFile.mockResolvedValueOnce(
      makeEvent('iteration_completed', { feature: 'F1', edge: 'code' }),
    )

    const version = await suggestNextVersion('/workspace/events/events.jsonl')
    expect(version).toBe('1.0.0')
  })

  it('bumps patch from last release_created event version field', async () => {
    mockReadFile.mockResolvedValueOnce(
      makeEvent('release_created', { version: '3.0.7' }),
    )

    const version = await suggestNextVersion('/workspace/events/events.jsonl')
    expect(version).toBe('3.0.8')
  })

  it('uses the last release_created event (not the first)', async () => {
    mockReadFile.mockResolvedValueOnce(
      [
        makeEvent('release_created', { version: '2.0.0' }),
        makeEvent('release_created', { version: '3.0.7' }),
      ].join('\n'),
    )

    const version = await suggestNextVersion('/workspace/events/events.jsonl')
    expect(version).toBe('3.0.8')
  })
})
