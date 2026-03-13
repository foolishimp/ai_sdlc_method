// Implements: REQ-F-PROJ-001, REQ-F-PROJ-002, REQ-F-PROJ-003, REQ-F-PROJ-004, REQ-F-UX-001, REQ-NFR-PERF-001

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '../api/WorkspaceApiClient'
import type { WorkspaceSummary } from '../api/types'

interface ProjectState {
  // ─── Persisted (localStorage) ──────────────────────────────────────────────
  // Implements: REQ-F-PROJ-004
  registeredPaths: string[]
  // Implements: REQ-F-PROJ-003
  activeProjectId: string | null

  // ─── Runtime ───────────────────────────────────────────────────────────────
  // Implements: REQ-F-PROJ-001
  workspaceSummaries: Record<string, WorkspaceSummary>
  // Implements: REQ-F-UX-001
  lastRefreshed: Date | null
  pollingError: string | null
  isRefreshing: boolean
}

interface ProjectActions {
  // Implements: REQ-F-PROJ-004
  addWorkspace: (path: string) => Promise<WorkspaceSummary>
  removeWorkspace: (id: string) => void
  // Implements: REQ-F-PROJ-003
  setActiveProject: (id: string) => void
  // Implements: REQ-F-UX-001
  refreshAll: () => Promise<void>
}

export type ProjectStore = ProjectState & ProjectActions

export const useProjectStore = create<ProjectStore>()(
  persist(
    (set, get) => ({
      // ─── Initial state ────────────────────────────────────────────────────
      registeredPaths: [],
      activeProjectId: null,
      workspaceSummaries: {},
      lastRefreshed: null,
      pollingError: null,
      isRefreshing: false,

      // ─── addWorkspace ─────────────────────────────────────────────────────
      // Implements: REQ-F-PROJ-004
      addWorkspace: async (path: string) => {
        const summary = await apiClient.addWorkspace(path)
        set((state) => ({
          registeredPaths: state.registeredPaths.includes(path)
            ? state.registeredPaths
            : [...state.registeredPaths, path],
          workspaceSummaries: {
            ...state.workspaceSummaries,
            [summary.workspaceId]: summary,
          },
        }))
        return summary
      },

      // ─── removeWorkspace ─────────────────────────────────────────────────
      // Implements: REQ-F-PROJ-004
      removeWorkspace: (id: string) => {
        set((state) => {
          const summary = state.workspaceSummaries[id]
          const newPaths = summary
            ? state.registeredPaths.filter((p) => p !== summary.workspaceId)
            : state.registeredPaths
          const { [id]: _removed, ...rest } = state.workspaceSummaries
          return {
            registeredPaths: newPaths,
            workspaceSummaries: rest,
            activeProjectId: state.activeProjectId === id ? null : state.activeProjectId,
          }
        })
      },

      // ─── setActiveProject ─────────────────────────────────────────────────
      // Implements: REQ-F-PROJ-003
      setActiveProject: (id: string) => {
        set({ activeProjectId: id })
      },

      // ─── refreshAll ──────────────────────────────────────────────────────
      // Implements: REQ-F-UX-001
      refreshAll: async () => {
        const { isRefreshing } = get()
        if (isRefreshing) return
        set({ isRefreshing: true })
        try {
          const summaries = await apiClient.getWorkspaces()
          const summaryMap: Record<string, WorkspaceSummary> = {}
          for (const s of summaries) {
            summaryMap[s.workspaceId] = s
          }
          set({
            workspaceSummaries: summaryMap,
            lastRefreshed: new Date(),
            pollingError: null,
            isRefreshing: false,
          })
        } catch (err) {
          set({
            pollingError:
              err instanceof Error ? err.message : 'Workspace unavailable',
            isRefreshing: false,
            // lastRefreshed intentionally NOT updated — stale timestamp signals the problem
          })
        }
      },
    }),
    {
      name: 'gm:project-store',
      // Only persist these fields; runtime state is re-derived on load
      partialize: (state) => ({
        registeredPaths: state.registeredPaths,
        activeProjectId: state.activeProjectId,
      }),
    },
  ),
)

// Selector: sorted workspace list — attention-required first
// Implements: REQ-F-PROJ-002
export function selectSortedWorkspaces(summaries: Record<string, WorkspaceSummary>): WorkspaceSummary[] {
  return Object.values(summaries).sort((a, b) => {
    const aAttn = a.hasAttentionRequired ? 1 : 0
    const bAttn = b.hasAttentionRequired ? 1 : 0
    if (bAttn !== aAttn) return bAttn - aAttn
    // Secondary: most recent event first
    const aTs = a.lastEventTimestamp ?? ''
    const bTs = b.lastEventTimestamp ?? ''
    return bTs.localeCompare(aTs)
  })
}
