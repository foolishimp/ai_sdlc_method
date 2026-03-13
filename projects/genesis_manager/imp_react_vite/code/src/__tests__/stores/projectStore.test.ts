// @vitest-environment jsdom
// Validates: REQ-F-PROJ-001, REQ-F-PROJ-002, REQ-F-PROJ-003, REQ-F-PROJ-004, REQ-F-UX-001

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock the API client and zustand persist middleware before importing the store
// ---------------------------------------------------------------------------

vi.mock('../../api/WorkspaceApiClient', () => ({
  apiClient: {
    getWorkspaces: vi.fn(),
    addWorkspace: vi.fn(),
    removeWorkspace: vi.fn(),
    getWorkspaceSummary: vi.fn(),
  },
}))

// Mock zustand persist to avoid localStorage interactions in tests
vi.mock('zustand/middleware', async () => {
  const actual = await vi.importActual<typeof import('zustand/middleware')>('zustand/middleware')
  return {
    ...actual,
    // Override persist to be a passthrough — removes localStorage dependency in tests
    persist: (config: Parameters<typeof actual.persist>[0]) => config,
  }
})

import { apiClient } from '../../api/WorkspaceApiClient'
import { useProjectStore, selectSortedWorkspaces } from '../../stores/projectStore'
import type { WorkspaceSummary } from '../../api/types'

const mockGetWorkspaces = vi.mocked(apiClient.getWorkspaces)
const mockAddWorkspace = vi.mocked(apiClient.addWorkspace)

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeSummary(overrides: Partial<WorkspaceSummary> = {}): WorkspaceSummary {
  return {
    workspaceId: 'ws-001',
    projectName: 'Test Project',
    activeFeatureCount: 3,
    pendingGateCount: 0,
    stuckFeatureCount: 0,
    lastEventTimestamp: '2026-01-01T10:00:00Z',
    hasAttentionRequired: false,
    available: true,
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// selectSortedWorkspaces — REQ-F-PROJ-002
// ---------------------------------------------------------------------------

describe('selectSortedWorkspaces — REQ-F-PROJ-002', () => {
  it('returns empty array for empty summaries map', () => {
    expect(selectSortedWorkspaces({})).toEqual([])
  })

  it('places attention-required workspaces first', () => {
    const summaries = {
      'ws-001': makeSummary({ workspaceId: 'ws-001', hasAttentionRequired: false, lastEventTimestamp: '2026-01-01T10:00:00Z' }),
      'ws-002': makeSummary({ workspaceId: 'ws-002', hasAttentionRequired: true, lastEventTimestamp: '2026-01-01T09:00:00Z' }),
    }
    const sorted = selectSortedWorkspaces(summaries)
    expect(sorted[0].workspaceId).toBe('ws-002')
    expect(sorted[1].workspaceId).toBe('ws-001')
  })

  it('sorts by most recent lastEventTimestamp when attention status is equal', () => {
    const summaries = {
      'ws-older': makeSummary({ workspaceId: 'ws-older', lastEventTimestamp: '2026-01-01T08:00:00Z', hasAttentionRequired: false }),
      'ws-newer': makeSummary({ workspaceId: 'ws-newer', lastEventTimestamp: '2026-01-02T10:00:00Z', hasAttentionRequired: false }),
    }
    const sorted = selectSortedWorkspaces(summaries)
    expect(sorted[0].workspaceId).toBe('ws-newer')
    expect(sorted[1].workspaceId).toBe('ws-older')
  })

  it('handles null lastEventTimestamp (null sorts to end)', () => {
    const summaries = {
      'ws-null': makeSummary({ workspaceId: 'ws-null', lastEventTimestamp: null, hasAttentionRequired: false }),
      'ws-ts': makeSummary({ workspaceId: 'ws-ts', lastEventTimestamp: '2026-01-01T10:00:00Z', hasAttentionRequired: false }),
    }
    const sorted = selectSortedWorkspaces(summaries)
    // ws-ts has a real timestamp, should sort first
    expect(sorted[0].workspaceId).toBe('ws-ts')
  })

  it('attention-required beats more recent timestamp', () => {
    const summaries = {
      'ws-recent': makeSummary({ workspaceId: 'ws-recent', lastEventTimestamp: '2026-03-01T00:00:00Z', hasAttentionRequired: false }),
      'ws-attn': makeSummary({ workspaceId: 'ws-attn', lastEventTimestamp: '2026-01-01T00:00:00Z', hasAttentionRequired: true }),
    }
    const sorted = selectSortedWorkspaces(summaries)
    expect(sorted[0].workspaceId).toBe('ws-attn')
  })
})

// ---------------------------------------------------------------------------
// useProjectStore.setActiveProject — REQ-F-PROJ-003
// ---------------------------------------------------------------------------

describe('useProjectStore.setActiveProject — REQ-F-PROJ-003', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useProjectStore.setState({
      registeredPaths: [],
      activeProjectId: null,
      workspaceSummaries: {},
      lastRefreshed: null,
      pollingError: null,
      isRefreshing: false,
    })
  })

  it('sets the active project ID', () => {
    useProjectStore.getState().setActiveProject('ws-001')
    expect(useProjectStore.getState().activeProjectId).toBe('ws-001')
  })

  it('updates when called a second time', () => {
    useProjectStore.getState().setActiveProject('ws-001')
    useProjectStore.getState().setActiveProject('ws-002')
    expect(useProjectStore.getState().activeProjectId).toBe('ws-002')
  })
})

// ---------------------------------------------------------------------------
// useProjectStore.addWorkspace — REQ-F-PROJ-004
// ---------------------------------------------------------------------------

describe('useProjectStore.addWorkspace — REQ-F-PROJ-004', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useProjectStore.setState({
      registeredPaths: [],
      activeProjectId: null,
      workspaceSummaries: {},
      lastRefreshed: null,
      pollingError: null,
      isRefreshing: false,
    })
  })

  it('adds the path to registeredPaths and the summary to workspaceSummaries', async () => {
    const summary = makeSummary({ workspaceId: 'ws-new' })
    mockAddWorkspace.mockResolvedValueOnce(summary)

    await useProjectStore.getState().addWorkspace('/some/project/.ai-workspace')

    const state = useProjectStore.getState()
    expect(state.registeredPaths).toContain('/some/project/.ai-workspace')
    expect(state.workspaceSummaries['ws-new']).toBeDefined()
    expect(state.workspaceSummaries['ws-new'].projectName).toBe('Test Project')
  })

  it('returns the summary from the API call', async () => {
    const summary = makeSummary({ workspaceId: 'ws-new' })
    mockAddWorkspace.mockResolvedValueOnce(summary)

    const result = await useProjectStore.getState().addWorkspace('/some/path')
    expect(result).toEqual(summary)
  })

  it('does not duplicate a path already in registeredPaths', async () => {
    useProjectStore.setState({ registeredPaths: ['/existing/path'] })
    const summary = makeSummary({ workspaceId: 'ws-dup' })
    mockAddWorkspace.mockResolvedValueOnce(summary)

    await useProjectStore.getState().addWorkspace('/existing/path')

    const state = useProjectStore.getState()
    const occurrences = state.registeredPaths.filter((p) => p === '/existing/path')
    expect(occurrences).toHaveLength(1)
  })
})

// ---------------------------------------------------------------------------
// useProjectStore.removeWorkspace — REQ-F-PROJ-004
// ---------------------------------------------------------------------------

describe('useProjectStore.removeWorkspace — REQ-F-PROJ-004', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useProjectStore.setState({
      registeredPaths: ['/project-a/.ai-workspace'],
      activeProjectId: 'ws-a',
      workspaceSummaries: {
        'ws-a': makeSummary({ workspaceId: 'ws-a' }),
      },
      lastRefreshed: null,
      pollingError: null,
      isRefreshing: false,
    })
  })

  it('removes the workspace from workspaceSummaries', () => {
    useProjectStore.getState().removeWorkspace('ws-a')
    expect(useProjectStore.getState().workspaceSummaries['ws-a']).toBeUndefined()
  })

  it('clears activeProjectId when the active project is removed', () => {
    useProjectStore.getState().removeWorkspace('ws-a')
    expect(useProjectStore.getState().activeProjectId).toBeNull()
  })

  it('keeps activeProjectId when a different project is removed', () => {
    useProjectStore.setState({
      workspaceSummaries: {
        'ws-a': makeSummary({ workspaceId: 'ws-a' }),
        'ws-b': makeSummary({ workspaceId: 'ws-b' }),
      },
      activeProjectId: 'ws-a',
    })
    useProjectStore.getState().removeWorkspace('ws-b')
    expect(useProjectStore.getState().activeProjectId).toBe('ws-a')
  })
})

// ---------------------------------------------------------------------------
// useProjectStore.refreshAll — REQ-F-UX-001, REQ-F-PROJ-001
// ---------------------------------------------------------------------------

describe('useProjectStore.refreshAll — REQ-F-UX-001, REQ-F-PROJ-001', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    useProjectStore.setState({
      registeredPaths: [],
      activeProjectId: null,
      workspaceSummaries: {},
      lastRefreshed: null,
      pollingError: null,
      isRefreshing: false,
    })
  })

  it('populates workspaceSummaries from API response', async () => {
    const summaries = [
      makeSummary({ workspaceId: 'ws-001' }),
      makeSummary({ workspaceId: 'ws-002', projectName: 'Second Project' }),
    ]
    mockGetWorkspaces.mockResolvedValueOnce(summaries)

    await useProjectStore.getState().refreshAll()

    const state = useProjectStore.getState()
    expect(state.workspaceSummaries['ws-001']).toBeDefined()
    expect(state.workspaceSummaries['ws-002']?.projectName).toBe('Second Project')
  })

  it('updates lastRefreshed timestamp on success', async () => {
    mockGetWorkspaces.mockResolvedValueOnce([])
    await useProjectStore.getState().refreshAll()
    expect(useProjectStore.getState().lastRefreshed).toBeInstanceOf(Date)
  })

  it('sets pollingError and does NOT update lastRefreshed when API fails', async () => {
    const before = new Date('2026-01-01T00:00:00Z')
    useProjectStore.setState({ lastRefreshed: before })
    mockGetWorkspaces.mockRejectedValueOnce(new Error('Workspace unavailable'))

    await useProjectStore.getState().refreshAll()

    const state = useProjectStore.getState()
    expect(state.pollingError).toBe('Workspace unavailable')
    // lastRefreshed unchanged — stale timestamp signals the problem
    expect(state.lastRefreshed).toBe(before)
  })

  it('does not start a second refresh when isRefreshing is true', async () => {
    useProjectStore.setState({ isRefreshing: true })
    mockGetWorkspaces.mockResolvedValueOnce([])

    await useProjectStore.getState().refreshAll()
    expect(mockGetWorkspaces).not.toHaveBeenCalled()
  })

  it('clears pollingError on successful refresh', async () => {
    useProjectStore.setState({ pollingError: 'old error' })
    mockGetWorkspaces.mockResolvedValueOnce([])

    await useProjectStore.getState().refreshAll()
    expect(useProjectStore.getState().pollingError).toBeNull()
  })

  it('sets isRefreshing=false after completion (success)', async () => {
    mockGetWorkspaces.mockResolvedValueOnce([])
    await useProjectStore.getState().refreshAll()
    expect(useProjectStore.getState().isRefreshing).toBe(false)
  })

  it('sets isRefreshing=false after completion (failure)', async () => {
    mockGetWorkspaces.mockRejectedValueOnce(new Error('fail'))
    await useProjectStore.getState().refreshAll()
    expect(useProjectStore.getState().isRefreshing).toBe(false)
  })
})
