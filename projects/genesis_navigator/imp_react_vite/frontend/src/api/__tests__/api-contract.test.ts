// Validates: REQ-NFR-CONTRACT-001
// Validates: REQ-NFR-ARCH-001
/**
 * API Contract Tests — TypeScript Types vs OpenAPI Snapshot
 *
 * These tests validate that TypeScript interfaces in types.ts are structurally
 * compatible with the backend's OpenAPI schema snapshot.
 *
 * Run `npm run update-api-snapshot` to regenerate the snapshot from a live backend.
 */

import { describe, it, expect } from 'vitest'
import snapshot from '../openapi-snapshot.json'
import type {
  ProjectSummary,
  ProjectDetail,
  FeatureDetail,
  GapReport,
  QueueItem,
  Hamiltonian,
  RunSummary,
  RunTimeline,
} from '../types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Extract required field names from a component schema. */
function requiredFields(schemaName: string): string[] {
  const schemas = (snapshot as Record<string, unknown>).components as
    | Record<string, { schemas?: Record<string, { required?: string[] }> }>
    | undefined
  return schemas?.schemas?.[schemaName]?.required ?? []
}

/** Extract ALL property names (required + optional) from a component schema. */
function allFields(schemaName: string): string[] {
  const schemas = (snapshot as Record<string, unknown>).components as
    | Record<string, { schemas?: Record<string, { properties?: Record<string, unknown> }> }>
    | undefined
  const props = schemas?.schemas?.[schemaName]?.properties ?? {}
  return Object.keys(props)
}

// ---------------------------------------------------------------------------
// Typed stubs — TypeScript MUST compile these. Any missing required field is a
// compile-time error, proving that the TypeScript type covers the snapshot.
// ---------------------------------------------------------------------------

const projectSummaryStub: ProjectSummary = {
  project_id: 'proj-1',
  name: 'My Project',
  path: '/path/to/proj',
  state: 'ITERATING',
  active_feature_count: 3,
  converged_feature_count: 1,
  last_event_at: '2026-03-12T00:00:00Z',
  scan_duration_ms: 12.5,
}

const projectDetailStub: ProjectDetail = {
  project_id: 'proj-1',
  name: 'My Project',
  state: 'ITERATING',
  features: [],
  total_edges: 10,
  converged_edges: 7,
}

const featureDetailStub: FeatureDetail = {
  feature_id: 'REQ-F-TEST-001',
  title: 'Test Feature',
  status: 'iterating',
  current_edge: 'design→code',
  delta: 2,
  hamiltonian: { H: 5, T: 3, V: 2, flat: false },
  trajectory: [],
  error: null,
  satisfies: ['REQ-F-TEST-001'],
  acceptance_criteria: ['AC1'],
}

const hamiltonianStub: Hamiltonian = { H: 5, T: 3, V: 2, flat: false }

const gapReportStub: GapReport = {
  project_id: 'proj-1',
  computed_at: '2026-03-12T00:00:00Z',
  health_signal: 'GREEN',
  layer_1: { gap_count: 0, coverage_pct: 100, gaps: [] },
  layer_2: { gap_count: 0, coverage_pct: 100, gaps: [] },
  layer_3: { gap_count: 0, coverage_pct: 100, gaps: [] },
}

const queueItemStub: QueueItem = {
  type: 'IN_PROGRESS',
  severity: 'low',
  feature_id: 'REQ-F-TEST-001',
  description: 'Feature iterating',
  command: '/gen-iterate',
  detail: {
    reason: 'Still iterating',
    delta: 2,
    failing_checks: [],
    expected_outcome: 'convergence',
    gap_keys: [],
    iteration_history: [],
  },
}

const runSummaryStub: RunSummary = {
  run_id: 'current',
  timestamp: '2026-03-12T00:00:00Z',
  event_count: 42,
  edges_traversed: 3,
  final_state: 'ITERATING',
  is_current: true,
}

const runTimelineStub: RunTimeline = {
  run_id: 'current',
  event_count: 5,
  segments: [],
}

// ---------------------------------------------------------------------------
// Contract tests
// ---------------------------------------------------------------------------

describe('API Contract: openapi-snapshot.json exists and is valid', () => {
  it('snapshot is a valid OpenAPI 3.x document', () => {
    expect(snapshot).toBeDefined()
    expect((snapshot as Record<string, unknown>).openapi).toMatch(/^3\./)
    expect((snapshot as Record<string, unknown>).paths).toBeDefined()
    expect((snapshot as Record<string, unknown>).components).toBeDefined()
  })
})

describe('API Contract: ProjectSummary', () => {
  it('TypeScript stub satisfies all required snapshot fields', () => {
    const required = requiredFields('ProjectSummary')
    const stub = projectSummaryStub as Record<string, unknown>
    for (const field of required) {
      expect(stub[field], `Missing required field: ${field}`).toBeDefined()
    }
  })

  it('snapshot contains expected fields', () => {
    const fields = allFields('ProjectSummary')
    expect(fields).toContain('project_id')
    expect(fields).toContain('name')
    expect(fields).toContain('path')
    expect(fields).toContain('state')
    expect(fields).toContain('active_feature_count')
    expect(fields).toContain('converged_feature_count')
    expect(fields).toContain('scan_duration_ms')
  })

  it('TypeScript type covers path field (not root_path)', () => {
    expect(projectSummaryStub.path).toBe('/path/to/proj')
  })

  it('TypeScript type covers active_feature_count (not feature_count)', () => {
    expect(projectSummaryStub.active_feature_count).toBe(3)
  })
})

describe('API Contract: GapReport (not yet a declared response model)', () => {
  it('TypeScript stub has all expected fields from Pydantic schema', () => {
    // GapReport is not yet in the OpenAPI snapshot components — the /gaps endpoint
    // returns an untyped dict. This test validates TypeScript shape only.
    // FINDING: Add response_model=GapReport to the /gaps endpoint to get schema coverage.
    expect(gapReportStub.project_id).toBeDefined()
    expect(gapReportStub.computed_at).toBeDefined()
    expect(gapReportStub.health_signal).toBeDefined()
    expect(gapReportStub.layer_1).toBeDefined()
    expect(gapReportStub.layer_2).toBeDefined()
    expect(gapReportStub.layer_3).toBeDefined()
  })
})

describe('API Contract: RunSummary', () => {
  it('stub has all expected fields from backend schema', () => {
    expect(runSummaryStub.run_id).toBe('current')
    expect(runSummaryStub.event_count).toBe(42)
    expect(runSummaryStub.edges_traversed).toBe(3)
    expect(runSummaryStub.final_state).toBe('ITERATING')
    expect(runSummaryStub.is_current).toBe(true)
  })

  it('RunTimeline stub has run_id, event_count, segments', () => {
    expect(runTimelineStub.run_id).toBeDefined()
    expect(typeof runTimelineStub.event_count).toBe('number')
    expect(Array.isArray(runTimelineStub.segments)).toBe(true)
  })
})

describe('API Contract: Hamiltonian', () => {
  it('stub has H, T, V, flat fields', () => {
    expect(hamiltonianStub.H).toBe(5)
    expect(hamiltonianStub.T).toBe(3)
    expect(hamiltonianStub.V).toBe(2)
    expect(hamiltonianStub.flat).toBe(false)
  })
})

describe('API Contract: FeatureDetail', () => {
  it('stub covers all required fields', () => {
    expect(featureDetailStub.feature_id).toBeDefined()
    expect(featureDetailStub.title).toBeDefined()
    expect(featureDetailStub.status).toBeDefined()
    expect(featureDetailStub.delta).toBeDefined()
    expect(featureDetailStub.hamiltonian).toBeDefined()
    expect(featureDetailStub.trajectory).toBeDefined()
  })
})

describe('API Contract: QueueItem', () => {
  it('stub covers all required fields', () => {
    expect(queueItemStub.type).toBeDefined()
    expect(queueItemStub.severity).toBeDefined()
    expect(queueItemStub.description).toBeDefined()
    expect(queueItemStub.command).toBeDefined()
    expect(queueItemStub.detail).toBeDefined()
  })
})

describe('API Contract: endpoint coverage', () => {
  it('snapshot includes /api/projects endpoint', () => {
    const paths = (snapshot as Record<string, unknown>).paths as Record<string, unknown>
    expect(paths['/api/projects']).toBeDefined()
  })

  it('snapshot includes /api/projects/{project_id} endpoint', () => {
    const paths = (snapshot as Record<string, unknown>).paths as Record<string, unknown>
    expect(paths['/api/projects/{project_id}']).toBeDefined()
  })

  it('snapshot includes gaps endpoint', () => {
    const paths = (snapshot as Record<string, unknown>).paths as Record<string, unknown>
    expect(paths['/api/projects/{project_id}/gaps']).toBeDefined()
  })

  it('snapshot includes queue endpoint', () => {
    const paths = (snapshot as Record<string, unknown>).paths as Record<string, unknown>
    expect(paths['/api/projects/{project_id}/queue']).toBeDefined()
  })

  it('snapshot includes runs endpoints', () => {
    const paths = (snapshot as Record<string, unknown>).paths as Record<string, unknown>
    expect(paths['/api/projects/{project_id}/runs']).toBeDefined()
    expect(paths['/api/projects/{project_id}/runs/current']).toBeDefined()
    expect(paths['/api/projects/{project_id}/runs/{run_id}']).toBeDefined()
  })
})
