// Validates: REQ-F-API-001, REQ-F-API-002, REQ-F-API-003, REQ-F-API-004
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../api/client'

global.fetch = vi.fn()

describe('api client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('listProjects calls /api/projects', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response)
    const result = await api.listProjects()
    expect(fetch).toHaveBeenCalledWith('/api/projects')
    expect(result).toEqual([])
  })

  it('getProject calls /api/projects/:id', async () => {
    const mockProject = { project_id: 'p1', name: 'Test', state: 'CONVERGED' }
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProject,
    } as Response)
    const result = await api.getProject('p1')
    expect(fetch).toHaveBeenCalledWith('/api/projects/p1')
    expect(result).toEqual(mockProject)
  })

  it('getGaps calls /api/projects/:id/gaps', async () => {
    const mockReport = { project_id: 'p1', layers: [], total_req_keys: 0, covered_count: 0, gap_count: 0 }
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockReport,
    } as Response)
    await api.getGaps('p1')
    expect(fetch).toHaveBeenCalledWith('/api/projects/p1/gaps')
  })

  it('getQueue calls /api/projects/:id/queue', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response)
    await api.getQueue('p1')
    expect(fetch).toHaveBeenCalledWith('/api/projects/p1/queue')
  })

  it('throws on non-ok response', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    } as Response)
    await expect(api.getProject('missing')).rejects.toThrow('HTTP 404')
  })
})
