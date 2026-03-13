// Implements: REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001, REQ-NFR-PERF-001

import { create } from 'zustand'
import { apiClient } from '../api/WorkspaceApiClient'
import type {
  WorkspaceOverview,
  GateItem,
  FeatureVector,
  TraceabilityEntry,
} from '../api/types'

interface WorkspaceState {
  // Loaded workspace ID (null = no workspace loaded)
  loadedWorkspaceId: string | null

  // Implements: REQ-F-OVR-001
  overview: WorkspaceOverview | null

  // Implements: REQ-F-SUP-001, REQ-F-SUP-002
  gates: GateItem[]

  // Implements: REQ-F-SUP-001
  features: FeatureVector[]

  // Implements: REQ-F-EVI-001
  traceability: TraceabilityEntry[]

  // Loading / error states
  isLoading: boolean
  error: string | null
}

interface WorkspaceActions {
  loadWorkspace: (id: string) => Promise<void>
  clearWorkspace: () => void
  refreshOverview: (id: string) => Promise<void>
  refreshGates: (id: string) => Promise<void>
  refreshFeatures: (id: string) => Promise<void>
}

export type WorkspaceStore = WorkspaceState & WorkspaceActions

const initialState: WorkspaceState = {
  loadedWorkspaceId: null,
  overview: null,
  gates: [],
  features: [],
  traceability: [],
  isLoading: false,
  error: null,
}

export const useWorkspaceStore = create<WorkspaceStore>()((set, get) => ({
  ...initialState,

  // Implements: REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001
  loadWorkspace: async (id: string) => {
    if (get().loadedWorkspaceId === id && get().overview !== null) return
    set({ isLoading: true, error: null })
    try {
      const [overview, gates, features, traceability] = await Promise.all([
        apiClient.getOverview(id),
        apiClient.getGates(id),
        apiClient.getFeatures(id),
        apiClient.getTraceability(id),
      ])
      set({
        loadedWorkspaceId: id,
        overview,
        gates,
        features,
        traceability,
        isLoading: false,
        error: null,
      })
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load workspace',
      })
    }
  },

  clearWorkspace: () => {
    set(initialState)
  },

  // Implements: REQ-F-OVR-001, REQ-F-UX-001 (partial refresh on poll)
  refreshOverview: async (id: string) => {
    try {
      const overview = await apiClient.getOverview(id)
      set({ overview })
    } catch {
      // Silently skip; pollingError handled by projectStore
    }
  },

  // Implements: REQ-F-SUP-002
  refreshGates: async (id: string) => {
    try {
      const gates = await apiClient.getGates(id)
      set({ gates })
    } catch {
      // Silently skip
    }
  },

  // Implements: REQ-F-SUP-001
  refreshFeatures: async (id: string) => {
    try {
      const features = await apiClient.getFeatures(id)
      set({ features })
    } catch {
      // Silently skip
    }
  },
}))
