// Implements: REQ-F-PROJ-001, REQ-DATA-WORK-001, REQ-DATA-WORK-002
/// <reference types="vite/client" />

import type {
  WorkspaceSummary,
  WorkspaceOverview,
  GateItem,
  FeatureVector,
  TraceabilityEntry,
  WorkspaceEvent,
  EventPayload,
  GapAnalysisData,
  ApiError,
  FsBrowseResult,
} from './types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3001'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: res.statusText }))
    const err: ApiError = { status: res.status, message: body.message ?? res.statusText }
    throw err
  }
  return res.json() as Promise<T>
}

// Implements: REQ-F-PROJ-001, REQ-DATA-WORK-001
export class WorkspaceApiClient {
  private baseUrl: string

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl
  }

  // ─── Workspace registration ──────────────────────────────────────────────

  // Implements: REQ-F-PROJ-001
  async getWorkspaces(): Promise<WorkspaceSummary[]> {
    const res = await fetch(`${this.baseUrl}/api/workspaces`)
    return handleResponse<WorkspaceSummary[]>(res)
  }

  // Implements: REQ-F-PROJ-004
  async addWorkspace(path: string): Promise<WorkspaceSummary> {
    const res = await fetch(`${this.baseUrl}/api/workspaces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    })
    return handleResponse<WorkspaceSummary>(res)
  }

  // Implements: REQ-F-PROJ-004
  async removeWorkspace(id: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
    return handleResponse<void>(res)
  }

  // Implements: REQ-F-PROJ-001
  async getWorkspaceSummary(id: string): Promise<WorkspaceSummary> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/summary`)
    return handleResponse<WorkspaceSummary>(res)
  }

  // ─── Overview ────────────────────────────────────────────────────────────

  // Implements: REQ-F-OVR-001
  async getOverview(id: string): Promise<WorkspaceOverview> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/overview`)
    return handleResponse<WorkspaceOverview>(res)
  }

  // ─── Gates ───────────────────────────────────────────────────────────────

  // Implements: REQ-F-SUP-002
  async getGates(id: string): Promise<GateItem[]> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/gates`)
    return handleResponse<GateItem[]>(res)
  }

  // ─── Features ────────────────────────────────────────────────────────────

  // Implements: REQ-F-SUP-001
  async getFeatures(id: string): Promise<FeatureVector[]> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/features`)
    return handleResponse<FeatureVector[]>(res)
  }

  // ─── Events ──────────────────────────────────────────────────────────────

  // Implements: REQ-F-EVI-002
  async getEvents(id: string, featureId?: string): Promise<WorkspaceEvent[]> {
    const url = new URL(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/events`)
    if (featureId) url.searchParams.set('feature', featureId)
    const res = await fetch(url.toString())
    return handleResponse<WorkspaceEvent[]>(res)
  }

  // ─── Traceability ────────────────────────────────────────────────────────

  // Implements: REQ-F-EVI-001
  async getTraceability(id: string): Promise<TraceabilityEntry[]> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/traceability`)
    return handleResponse<TraceabilityEntry[]>(res)
  }

  // ─── Gap Analysis ────────────────────────────────────────────────────────

  // Implements: REQ-F-EVI-004
  async getGapAnalysis(id: string): Promise<GapAnalysisData> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/gap-analysis`)
    return handleResponse<GapAnalysisData>(res)
  }

  // Implements: REQ-F-EVI-004, REQ-DATA-WORK-002
  async rerunGapAnalysis(id: string): Promise<GapAnalysisData> {
    const res = await fetch(
      `${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/gap-analysis/rerun`,
      { method: 'POST' },
    )
    return handleResponse<GapAnalysisData>(res)
  }

  // ─── Filesystem Browse ───────────────────────────────────────────────────

  // Implements: REQ-F-FSNAV-001
  async browsePath(path?: string): Promise<FsBrowseResult> {
    const url = new URL(`${this.baseUrl}/api/fs/browse`)
    if (path) url.searchParams.set('path', path)
    const res = await fetch(url.toString())
    return handleResponse<FsBrowseResult>(res)
  }

  // ─── Write actions ───────────────────────────────────────────────────────

  // Implements: REQ-DATA-WORK-002, REQ-F-CTL-001
  async postEvent(id: string, event: EventPayload): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    })
    return handleResponse<void>(res)
  }

  // Implements: REQ-F-CTL-004, REQ-DATA-WORK-002
  async setAutoMode(id: string, featureId: string, enabled: boolean): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/workspaces/${encodeURIComponent(id)}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'auto_mode_set',
        feature: featureId,
        enabled,
        actor: 'human',
      } satisfies EventPayload),
    })
    return handleResponse<void>(res)
  }
}

// Singleton instance — used by all feature modules
export const apiClient = new WorkspaceApiClient()
