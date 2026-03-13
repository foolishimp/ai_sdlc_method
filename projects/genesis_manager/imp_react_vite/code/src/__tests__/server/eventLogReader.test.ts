// @vitest-environment node
// Validates: REQ-F-SUP-004, REQ-F-CTL-004, REQ-NFR-REL-001, REQ-F-SUP-002, REQ-F-OVR-003

import { describe, it, expect, vi, beforeEach } from 'vitest'

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
import { readAll, computeAutoMode, computeIsStuck } from '../../../server/readers/EventLogReader'
import type { WorkspaceEvent } from '../../../server/types'

const mockReadFile = vi.mocked(fs.readFile)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeEvent(overrides: Partial<WorkspaceEvent> & { event_type: string; timestamp: string }): WorkspaceEvent {
  return { ...overrides }
}

function iterCompleted(feature: string, edge: string, delta: unknown): WorkspaceEvent {
  return { event_type: 'iteration_completed', timestamp: '2026-01-01T00:00:00Z', feature, edge, delta }
}

// ---------------------------------------------------------------------------
// readAll
// ---------------------------------------------------------------------------

describe('readAll', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns empty events and warnings when file does not exist (ENOENT)', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)

    const result = await readAll('/some/path/events.jsonl')
    expect(result.events).toEqual([])
    expect(result.warnings).toEqual([])
  })

  it('rethrows errors that are not ENOENT', async () => {
    const err = Object.assign(new Error('Permission denied'), { code: 'EACCES' })
    mockReadFile.mockRejectedValueOnce(err)

    await expect(readAll('/some/path/events.jsonl')).rejects.toThrow('Permission denied')
  })

  it('parses valid JSONL lines into events', async () => {
    const line1 = JSON.stringify({ event_type: 'iteration_completed', timestamp: '2026-01-01T00:00:00Z', feature: 'F1' })
    const line2 = JSON.stringify({ event_type: 'auto_mode_set', timestamp: '2026-01-02T00:00:00Z' })
    mockReadFile.mockResolvedValueOnce(`${line1}\n${line2}`)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(2)
    expect(result.events[0].event_type).toBe('iteration_completed')
    expect(result.events[1].event_type).toBe('auto_mode_set')
    expect(result.warnings).toHaveLength(0)
  })

  it('skips blank lines without producing warnings', async () => {
    const line = JSON.stringify({ event_type: 'x', timestamp: 't' })
    mockReadFile.mockResolvedValueOnce(`\n${line}\n\n`)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(1)
    expect(result.warnings).toHaveLength(0)
  })

  it('produces a warning for malformed JSON lines and skips them', async () => {
    const valid = JSON.stringify({ event_type: 'x', timestamp: 't' })
    mockReadFile.mockResolvedValueOnce(`not-json\n${valid}`)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(1)
    expect(result.warnings).toHaveLength(1)
    expect(result.warnings[0]).toContain('invalid JSON')
  })

  it('produces a warning for JSON lines missing event_type', async () => {
    const bad = JSON.stringify({ timestamp: '2026-01-01T00:00:00Z', other: 'field' })
    mockReadFile.mockResolvedValueOnce(bad)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(0)
    expect(result.warnings).toHaveLength(1)
    expect(result.warnings[0]).toContain('missing required fields')
  })

  it('produces a warning for JSON lines missing timestamp', async () => {
    const bad = JSON.stringify({ event_type: 'x' })
    mockReadFile.mockResolvedValueOnce(bad)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(0)
    expect(result.warnings).toHaveLength(1)
    expect(result.warnings[0]).toContain('missing required fields')
  })

  it('produces a warning for null JSON values', async () => {
    mockReadFile.mockResolvedValueOnce('null')

    const result = await readAll('/path')
    expect(result.events).toHaveLength(0)
    expect(result.warnings).toHaveLength(1)
  })

  it('includes the 1-based line number in malformed JSON warnings', async () => {
    const valid = JSON.stringify({ event_type: 'x', timestamp: 't' })
    mockReadFile.mockResolvedValueOnce(`${valid}\nbad-json`)

    const result = await readAll('/path')
    expect(result.warnings[0]).toContain('2')
  })

  it('includes the 1-based line number in missing-field warnings', async () => {
    const bad = JSON.stringify({ no_type: true })
    const valid = JSON.stringify({ event_type: 'x', timestamp: 't' })
    mockReadFile.mockResolvedValueOnce(`${valid}\n${bad}`)

    const result = await readAll('/path')
    expect(result.warnings[0]).toContain('2')
  })

  it('returns all events when file has many valid lines', async () => {
    const lines = Array.from({ length: 50 }, (_, i) =>
      JSON.stringify({ event_type: `type_${i}`, timestamp: `2026-01-01T00:00:${String(i).padStart(2, '0')}Z` }),
    ).join('\n')
    mockReadFile.mockResolvedValueOnce(lines)

    const result = await readAll('/path')
    expect(result.events).toHaveLength(50)
    expect(result.warnings).toHaveLength(0)
  })

  it('handles Windows-style line endings (CRLF)', async () => {
    const line = JSON.stringify({ event_type: 'x', timestamp: 't' })
    mockReadFile.mockResolvedValueOnce(`${line}\r\n`)

    const result = await readAll('/path')
    // trim() in the implementation removes \r
    expect(result.events).toHaveLength(1)
  })

  it('preserves extra fields on valid events', async () => {
    const line = JSON.stringify({ event_type: 'x', timestamp: 't', feature: 'F1', edge: 'code', delta: 2 })
    mockReadFile.mockResolvedValueOnce(line)

    const result = await readAll('/path')
    expect((result.events[0] as WorkspaceEvent & { delta: number }).delta).toBe(2)
    expect(result.events[0].feature).toBe('F1')
  })
})

// ---------------------------------------------------------------------------
// computeAutoMode
// ---------------------------------------------------------------------------

describe('computeAutoMode', () => {
  it('returns false when events array is empty', () => {
    expect(computeAutoMode([], 'F1')).toBe(false)
  })

  it('returns false when no auto_mode_set events exist for the feature', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'iteration_completed', timestamp: 't', feature: 'F1' }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })

  it('returns true when most recent auto_mode_set has enabled=true', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1', data: { enabled: true } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(true)
  })

  it('returns false when most recent auto_mode_set has enabled=false', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1', data: { enabled: false } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })

  it('uses the most recent auto_mode_set event — ignores older opposite value', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1', data: { enabled: true } }),
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't2', feature: 'F1', data: { enabled: false } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })

  it('uses the most recent auto_mode_set event when latest is true (overrides earlier false)', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1', data: { enabled: false } }),
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't2', feature: 'F1', data: { enabled: true } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(true)
  })

  it('does not confuse events for different features', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F2', data: { enabled: true } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })

  it('ignores auto_mode_set events with non-boolean enabled field', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1', data: { enabled: 'yes' } }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })

  it('ignores auto_mode_set events with no data field', () => {
    const events: WorkspaceEvent[] = [
      makeEvent({ event_type: 'auto_mode_set', timestamp: 't1', feature: 'F1' }),
    ]
    expect(computeAutoMode(events, 'F1')).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// computeIsStuck
// ---------------------------------------------------------------------------

describe('computeIsStuck', () => {
  it('returns false when no iteration_completed events exist', () => {
    expect(computeIsStuck([], 'F1', 'code')).toBe(false)
  })

  it('returns false with fewer than 3 matching events (1 event)', () => {
    const events = [iterCompleted('F1', 'code', 2)]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('returns false with fewer than 3 matching events (2 events)', () => {
    const events = [iterCompleted('F1', 'code', 2), iterCompleted('F1', 'code', 2)]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('returns true when last 3 events all have the same delta', () => {
    const events = [
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(true)
  })

  it('returns false when deltas differ (last differs by 1)', () => {
    const events = [
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 1),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('returns false when any of the last 3 deltas is null', () => {
    const events = [
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', null),
      iterCompleted('F1', 'code', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('returns false when any of the last 3 deltas is undefined', () => {
    const events = [
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', undefined),
      iterCompleted('F1', 'code', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('uses only the last 3 events — earlier different delta does not affect result', () => {
    const events = [
      iterCompleted('F1', 'code', 99), // older, different — should be ignored
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 2),
      iterCompleted('F1', 'code', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(true)
  })

  it('does not confuse events for a different feature', () => {
    const events = [
      iterCompleted('F2', 'code', 2),
      iterCompleted('F2', 'code', 2),
      iterCompleted('F2', 'code', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('does not confuse events for a different edge', () => {
    const events = [
      iterCompleted('F1', 'unit_tests', 2),
      iterCompleted('F1', 'unit_tests', 2),
      iterCompleted('F1', 'unit_tests', 2),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('returns true for string deltas that are all the same', () => {
    const events = [
      iterCompleted('F1', 'code', 'high'),
      iterCompleted('F1', 'code', 'high'),
      iterCompleted('F1', 'code', 'high'),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(true)
  })

  it('returns false for string deltas that differ', () => {
    const events = [
      iterCompleted('F1', 'code', 'high'),
      iterCompleted('F1', 'code', 'high'),
      iterCompleted('F1', 'code', 'low'),
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })

  it('ignores non-iteration_completed events when filtering', () => {
    const events: WorkspaceEvent[] = [
      iterCompleted('F1', 'code', 2),
      makeEvent({ event_type: 'review_requested', timestamp: 't', feature: 'F1', edge: 'code' }),
      iterCompleted('F1', 'code', 2),
      // Only 2 iteration_completed events → not stuck
    ]
    expect(computeIsStuck(events, 'F1', 'code')).toBe(false)
  })
})
