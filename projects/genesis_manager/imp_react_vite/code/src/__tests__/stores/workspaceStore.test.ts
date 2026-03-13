// @vitest-environment jsdom
// Validates: REQ-F-UX-001, REQ-F-UX-002, REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock the API client before importing the store
// ---------------------------------------------------------------------------

vi.mock('../../api/WorkspaceApiClient', () => ({
  apiClient: {
    getOverview: vi.fn(),
    getGates: vi.fn(),
    getFeatures: vi.fn(),
    getTraceability: vi.fn(),
  },
}))

import { apiClient } from '../../api/WorkspaceApiClient'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import type { WorkspaceOverview, GateItem, FeatureVector, TraceabilityEntry } from '../../api/types'

const mockGetOverview = vi.mocked(apiClient.getOverview)
const mockGetGates = vi.mocked(apiClient.getGates)
const mockGetFeatures = vi.mocked(apiClient.getFeatures)
const mockGetTraceability = vi.mocked(apiClient.getTraceability)

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const WORKSPACE_ID = 'ws-test-001'

function makeOverview(): WorkspaceOverview {
  return {
    projectName: 'Test Project',
    methodVersion: 'v2.9',
    statusCounts: { converged: 1, in_progress: 2, blocked: 0, pending: 3, pendingGates: 1 },
    inProgressFeatures: [],
    recentActivities: [],
    featureLastEvents: {},
    pendingGateCount: 1,
    pendingGates: [],
    blockedFeatures: [],
  }
}

function makeGates(): GateItem[] {
  return [
    {
      id: 'REQ-F-001:code:human_approves_code',
      featureId: 'REQ-F-001',
      edge: 'code',
      gateName: 'human_approves_code',
      pendingSince: '2026-01-01T00:00:00Z',
      ageMs: 3600000,
    },
  ]
}

function makeFeatures(): FeatureVector[] {
  return [
    {
      featureId: 'REQ-F-001',
      title: 'Feature One',
      status: 'in_progress',
      currentEdge: 'code',
      currentDelta: 2,
      satisfies: ['REQ-F-001'],
      childVectors: [],
      autoModeEnabled: false,
    },
  ]
}

function makeTraceability(): TraceabilityEntry[] {
  return [
    {
      reqKey: 'REQ-F-001',
      taggedInCode: true,
      taggedInTests: false,
      codeFiles: ['src/foo.ts'],
      testFiles: [],
    },
  ]
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useWorkspaceStore — initial state', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Reset store to initial state
    useWorkspaceStore.setState({
      loadedWorkspaceId: null,
      overview: null,
      gates: [],
      features: [],
      traceability: [],
      isLoading: false,
      error: null,
    })
  })

  it('starts with no workspace loaded', () => {
    const state = useWorkspaceStore.getState()
    expect(state.loadedWorkspaceId).toBeNull()
    expect(state.overview).toBeNull()
  })

  it('starts with empty gates and features arrays', () => {
    const state = useWorkspaceStore.getState()
    expect(state.gates).toEqual([])
    expect(state.features).toEqual([])
    expect(state.traceability).toEqual([])
  })

  it('starts with isLoading=false and error=null', () => {
    const state = useWorkspaceStore.getState()
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })
})

describe('useWorkspaceStore.loadWorkspace — REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useWorkspaceStore.setState({
      loadedWorkspaceId: null,
      overview: null,
      gates: [],
      features: [],
      traceability: [],
      isLoading: false,
      error: null,
    })
  })

  it('sets loadedWorkspaceId and populates all data on success — REQ-F-OVR-001', async () => {
    mockGetOverview.mockResolvedValueOnce(makeOverview())
    mockGetGates.mockResolvedValueOnce(makeGates())
    mockGetFeatures.mockResolvedValueOnce(makeFeatures())
    mockGetTraceability.mockResolvedValueOnce(makeTraceability())

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)

    const state = useWorkspaceStore.getState()
    expect(state.loadedWorkspaceId).toBe(WORKSPACE_ID)
    expect(state.overview?.projectName).toBe('Test Project')
    expect(state.gates).toHaveLength(1)
    expect(state.features).toHaveLength(1)
    expect(state.traceability).toHaveLength(1)
  })

  it('sets isLoading=true during fetch, false after completion — REQ-F-UX-001', async () => {
    const loadingStates: boolean[] = []

    mockGetOverview.mockImplementation(() => {
      loadingStates.push(useWorkspaceStore.getState().isLoading)
      return Promise.resolve(makeOverview())
    })
    mockGetGates.mockResolvedValueOnce([])
    mockGetFeatures.mockResolvedValueOnce([])
    mockGetTraceability.mockResolvedValueOnce([])

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)

    expect(loadingStates[0]).toBe(true)
    expect(useWorkspaceStore.getState().isLoading).toBe(false)
  })

  it('captures error message when API call fails', async () => {
    mockGetOverview.mockRejectedValueOnce(new Error('Network error'))
    mockGetGates.mockResolvedValueOnce([])
    mockGetFeatures.mockResolvedValueOnce([])
    mockGetTraceability.mockResolvedValueOnce([])

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)

    const state = useWorkspaceStore.getState()
    expect(state.error).toBe('Network error')
    expect(state.isLoading).toBe(false)
  })

  it('sets a fallback error message for non-Error rejections', async () => {
    mockGetOverview.mockRejectedValueOnce('string error')
    mockGetGates.mockResolvedValueOnce([])
    mockGetFeatures.mockResolvedValueOnce([])
    mockGetTraceability.mockResolvedValueOnce([])

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)

    const state = useWorkspaceStore.getState()
    expect(state.error).toBe('Failed to load workspace')
  })

  it('does not re-fetch when the same workspace is already loaded', async () => {
    mockGetOverview.mockResolvedValue(makeOverview())
    mockGetGates.mockResolvedValue([])
    mockGetFeatures.mockResolvedValue([])
    mockGetTraceability.mockResolvedValue([])

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)
    const callCountAfterFirst = mockGetOverview.mock.calls.length

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)
    expect(mockGetOverview.mock.calls.length).toBe(callCountAfterFirst)
  })
})

describe('useWorkspaceStore.clearWorkspace', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('resets all state to initial values', async () => {
    mockGetOverview.mockResolvedValueOnce(makeOverview())
    mockGetGates.mockResolvedValueOnce(makeGates())
    mockGetFeatures.mockResolvedValueOnce(makeFeatures())
    mockGetTraceability.mockResolvedValueOnce(makeTraceability())

    await useWorkspaceStore.getState().loadWorkspace(WORKSPACE_ID)
    useWorkspaceStore.getState().clearWorkspace()

    const state = useWorkspaceStore.getState()
    expect(state.loadedWorkspaceId).toBeNull()
    expect(state.overview).toBeNull()
    expect(state.gates).toEqual([])
    expect(state.features).toEqual([])
  })
})

describe('useWorkspaceStore.refreshOverview — REQ-F-UX-001', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useWorkspaceStore.setState({ overview: null, isLoading: false, error: null })
  })

  it('updates overview when refresh succeeds', async () => {
    const updated = { ...makeOverview(), projectName: 'Updated Name' }
    mockGetOverview.mockResolvedValueOnce(updated)

    await useWorkspaceStore.getState().refreshOverview(WORKSPACE_ID)

    expect(useWorkspaceStore.getState().overview?.projectName).toBe('Updated Name')
  })

  it('silently ignores errors on refresh (polling resilience) — REQ-F-UX-001', async () => {
    mockGetOverview.mockRejectedValueOnce(new Error('Server unavailable'))

    await expect(useWorkspaceStore.getState().refreshOverview(WORKSPACE_ID)).resolves.not.toThrow()
  })
})

describe('useWorkspaceStore.refreshGates — REQ-F-SUP-002', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useWorkspaceStore.setState({ gates: [] })
  })

  it('updates gates list on success', async () => {
    mockGetGates.mockResolvedValueOnce(makeGates())
    await useWorkspaceStore.getState().refreshGates(WORKSPACE_ID)
    expect(useWorkspaceStore.getState().gates).toHaveLength(1)
  })

  it('silently ignores errors on gate refresh', async () => {
    mockGetGates.mockRejectedValueOnce(new Error('fail'))
    await expect(useWorkspaceStore.getState().refreshGates(WORKSPACE_ID)).resolves.not.toThrow()
  })
})

describe('useWorkspaceStore.refreshFeatures — REQ-F-SUP-001', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useWorkspaceStore.setState({ features: [] })
  })

  it('updates features list on success', async () => {
    mockGetFeatures.mockResolvedValueOnce(makeFeatures())
    await useWorkspaceStore.getState().refreshFeatures(WORKSPACE_ID)
    expect(useWorkspaceStore.getState().features).toHaveLength(1)
  })

  it('silently ignores errors on features refresh', async () => {
    mockGetFeatures.mockRejectedValueOnce(new Error('fail'))
    await expect(useWorkspaceStore.getState().refreshFeatures(WORKSPACE_ID)).resolves.not.toThrow()
  })
})
