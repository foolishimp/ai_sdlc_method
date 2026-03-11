// Validates: REQ-F-SHELL-001, REQ-F-SHELL-002, REQ-F-NAV-002
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { App } from '../App'

// Mock the api module
vi.mock('../api/client', () => ({
  api: {
    listProjects: vi.fn().mockResolvedValue([]),
    getProject: vi.fn().mockResolvedValue({
      project_id: 'test-proj',
      name: 'Test Project',
      root_path: '/tmp/test',
      state: 'ITERATING',
      features: [],
      last_event_at: null,
    }),
    getGaps: vi.fn().mockResolvedValue({
      project_id: 'test-proj',
      layers: [],
      total_req_keys: 0,
      covered_count: 0,
      gap_count: 0,
    }),
    getQueue: vi.fn().mockResolvedValue([]),
  },
}))

function makeWrapper(initialPath = '/') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('App routing', () => {
  it('renders project list at /', async () => {
    render(<App />, { wrapper: makeWrapper('/') })
    expect(await screen.findByText('Genesis Navigator')).toBeInTheDocument()
  })

  it('renders project detail at /projects/:id', async () => {
    render(<App />, { wrapper: makeWrapper('/projects/test-proj') })
    expect(await screen.findByText('Test Project')).toBeInTheDocument()
  })
})

describe('ProjectDetailPage tabs', () => {
  it('shows status tab by default', async () => {
    render(<App />, { wrapper: makeWrapper('/projects/test-proj') })
    await screen.findByText('Test Project')
    expect(screen.getByTestId('tab-status')).toBeInTheDocument()
    expect(screen.getByTestId('tab-gaps')).toBeInTheDocument()
    expect(screen.getByTestId('tab-queue')).toBeInTheDocument()
    expect(screen.getByTestId('status-view')).toBeInTheDocument()
  })

  it('switches to gaps tab on click', async () => {
    const user = userEvent.setup()
    render(<App />, { wrapper: makeWrapper('/projects/test-proj') })
    await screen.findByText('Test Project')
    await user.click(screen.getByTestId('tab-gaps'))
    expect(screen.getByTestId('gap-view')).toBeInTheDocument()
  })

  it('switches to queue tab on click', async () => {
    const user = userEvent.setup()
    render(<App />, { wrapper: makeWrapper('/projects/test-proj') })
    await screen.findByText('Test Project')
    await user.click(screen.getByTestId('tab-queue'))
    expect(screen.getByTestId('queue-view')).toBeInTheDocument()
  })
})
