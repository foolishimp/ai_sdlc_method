// Implements: REQ-F-API-001, REQ-F-API-002, REQ-F-API-003, REQ-F-API-004
import type { ProjectSummary, ProjectDetail, GapReport, QueueItem } from './types'

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
}
