// Validates: REQ-F-HIST-001
// Validates: REQ-F-HIST-002
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HistoryView } from '../components/HistoryView'
import type { RunSummary, RunTimeline } from '../api/types'

const mockRuns: RunSummary[] = [
  {
    run_id: 'current',
    timestamp: '2026-03-12T01:00:00Z',
    event_count: 42,
    edges_traversed: 3,
    final_state: 'ITERATING',
    is_current: true,
  },
  {
    run_id: 'e2e_20260310T120000',
    timestamp: '2026-03-10T12:00:00Z',
    event_count: 18,
    edges_traversed: 5,
    final_state: 'CONVERGED',
    is_current: false,
  },
]

const mockTimeline: RunTimeline = {
  run_id: 'current',
  event_count: 3,
  segments: [
    {
      feature: 'REQ-F-TEST-001',
      edge: 'design→code',
      events: [
        { event_type: 'edge_started', timestamp: '2026-03-12T00:00:00Z', feature: 'REQ-F-TEST-001', edge: 'design→code', data: {} },
        { event_type: 'edge_converged', timestamp: '2026-03-12T00:30:00Z', feature: 'REQ-F-TEST-001', edge: 'design→code', data: {} },
      ],
    },
    {
      feature: null,
      edge: null,
      events: [
        { event_type: 'project_initialized', timestamp: '2026-03-11T10:00:00Z', feature: null, edge: null, data: {} },
      ],
    },
  ],
}

vi.mock('../api/client', () => ({
  api: {
    listRuns: vi.fn(),
    getRunTimeline: vi.fn(),
  },
}))

import { api } from '../api/client'

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('HistoryView — run list', () => {
  beforeEach(() => {
    vi.mocked(api.listRuns).mockResolvedValue(mockRuns)
    vi.mocked(api.getRunTimeline).mockResolvedValue(mockTimeline)
  })

  it('renders the history-view container', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('history-view')).toBeInTheDocument())
  })

  it('shows current session run card first', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-current')).toBeInTheDocument())
    expect(screen.getByText(/Current Session/)).toBeInTheDocument()
  })

  it('shows archived run card', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-e2e_20260310T120000')).toBeInTheDocument())
  })

  it('current run is listed first', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getAllByTestId(/run-card-/).length).toBe(2))
    const cards = screen.getAllByTestId(/run-card-/)
    expect(cards[0]).toHaveAttribute('data-testid', 'run-card-current')
  })

  it('shows ITERATING badge on current run', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-current')).toBeInTheDocument())
    expect(screen.getByText('ITERATING')).toBeInTheDocument()
  })

  it('shows CONVERGED badge on archived run', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-e2e_20260310T120000')).toBeInTheDocument())
    expect(screen.getByText('CONVERGED')).toBeInTheDocument()
  })

  it('shows event count on run card', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-current')).toBeInTheDocument())
    expect(screen.getByText(/42 events/)).toBeInTheDocument()
  })

  it('shows empty state when no runs', async () => {
    vi.mocked(api.listRuns).mockResolvedValue([])
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByText('No runs found.')).toBeInTheDocument())
  })
})

describe('HistoryView — timeline', () => {
  beforeEach(() => {
    vi.mocked(api.listRuns).mockResolvedValue(mockRuns)
    vi.mocked(api.getRunTimeline).mockResolvedValue(mockTimeline)
  })

  it('auto-selects first run and shows timeline panel', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('timeline-panel')).toBeInTheDocument())
  })

  it('timeline shows segment header for feature+edge', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('timeline-panel')).toBeInTheDocument())
    expect(screen.getByText(/REQ-F-TEST-001/)).toBeInTheDocument()
    expect(screen.getByText(/design→code/)).toBeInTheDocument()
  })

  it('timeline shows event type badges', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('timeline-panel')).toBeInTheDocument())
    expect(screen.getByText('edge_started')).toBeInTheDocument()
    expect(screen.getByText('edge_converged')).toBeInTheDocument()
  })

  it('timeline shows project-level segment', async () => {
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('timeline-panel')).toBeInTheDocument())
    expect(screen.getByText(/\(project\)/)).toBeInTheDocument()
    expect(screen.getByText('project_initialized')).toBeInTheDocument()
  })

  it('clicking a different run loads its timeline', async () => {
    vi.mocked(api.getRunTimeline).mockImplementation((_, runId) => {
      if (runId === 'e2e_20260310T120000') {
        return Promise.resolve({
          run_id: 'e2e_20260310T120000',
          event_count: 1,
          segments: [{ feature: null, edge: null, events: [{ event_type: 'gaps_validated', timestamp: null, feature: null, edge: null, data: {} }] }],
        })
      }
      return Promise.resolve(mockTimeline)
    })

    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByTestId('run-card-e2e_20260310T120000')).toBeInTheDocument())
    fireEvent.click(screen.getByTestId('run-card-e2e_20260310T120000'))
    await waitFor(() => expect(screen.getByText('gaps_validated')).toBeInTheDocument())
  })

  it('shows empty segment message when timeline has no events', async () => {
    vi.mocked(api.getRunTimeline).mockResolvedValue({ run_id: 'current', event_count: 0, segments: [] })
    renderWithQuery(<HistoryView projectId="proj-1" />)
    await waitFor(() => expect(screen.getByText('No events in this run.')).toBeInTheDocument())
  })
})
