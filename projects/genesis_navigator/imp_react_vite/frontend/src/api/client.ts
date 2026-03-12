// Implements: REQ-F-API-001, REQ-F-API-002, REQ-F-API-003, REQ-F-API-004, REQ-F-FEATDETAIL-001, REQ-F-HIST-001, REQ-F-HIST-002, REQ-F-API-005
import type { ProjectSummary, ProjectDetail, FeatureDetail, GapReport, QueueItem, RunSummary, RunTimeline } from './types'

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  listProjects: (): Promise<ProjectSummary[]> =>
    fetchJson<ProjectSummary[]>('/api/projects'),

  getProject: (id: string): Promise<ProjectDetail> =>
    fetchJson<ProjectDetail>(`/api/projects/${encodeURIComponent(id)}`),

  getGaps: (id: string): Promise<GapReport> =>
    fetchJson<GapReport>(`/api/projects/${encodeURIComponent(id)}/gaps`),

  getQueue: (id: string): Promise<QueueItem[]> =>
    fetchJson<QueueItem[]>(`/api/projects/${encodeURIComponent(id)}/queue`),

  getFeature: (projectId: string, featureId: string): Promise<FeatureDetail> =>
    fetchJson<FeatureDetail>(
      `/api/projects/${encodeURIComponent(projectId)}/features/${encodeURIComponent(featureId)}`
    ),

  listRuns: (projectId: string): Promise<RunSummary[]> =>
    fetchJson<RunSummary[]>(`/api/projects/${encodeURIComponent(projectId)}/runs`),

  getRunTimeline: (projectId: string, runId: string): Promise<RunTimeline> =>
    fetchJson<RunTimeline>(
      `/api/projects/${encodeURIComponent(projectId)}/runs/${encodeURIComponent(runId)}`
    ),
}
