// Validates: REQ-F-STAT-001, REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router'
import { StatusView } from '../components/StatusView'
import type { ProjectDetail } from '../api/types'

const mockProject: ProjectDetail = {
  project_id: 'proj-1',
  name: 'Test Project',
  state: 'ITERATING',
  features: [
    {
      feature_id: 'REQ-F-TEST-001',
      title: 'Test Feature',
      status: 'in_progress',
      current_edge: 'code_unit_tests',
      delta: 3,
      hamiltonian: { H: 6, T: 3, V: 3, flat: false },
      trajectory: [
        { edge: 'design_code', status: 'converged', iteration: 1, delta: 0, started_at: null, converged_at: null },
        { edge: 'code_unit_tests', status: 'in_progress', iteration: 2, delta: 3, started_at: null, converged_at: null },
      ],
      error: null,
    },
  ],
  total_edges: 10,
  converged_edges: 7,
}

describe('StatusView', () => {
  it('renders project state', () => {
    render(<MemoryRouter><StatusView project={mockProject} projectId="proj-1" /></MemoryRouter>)
    expect(screen.getByTestId('status-view')).toBeInTheDocument()
    expect(screen.getByText('ITERATING')).toBeInTheDocument()
  })

  it('renders feature trajectory', () => {
    render(<MemoryRouter><StatusView project={mockProject} projectId="proj-1" /></MemoryRouter>)
    expect(screen.getByRole('link', { name: 'REQ-F-TEST-001' })).toBeInTheDocument()
    expect(screen.getByText(/design_code/)).toBeInTheDocument()
    expect(screen.getByText(/code_unit_tests/)).toBeInTheDocument()
  })

  it('renders Hamiltonian values', () => {
    render(<MemoryRouter><StatusView project={mockProject} projectId="proj-1" /></MemoryRouter>)
    expect(screen.getByText(/H=6/)).toBeInTheDocument()
    expect(screen.getByText(/T=3/)).toBeInTheDocument()
    expect(screen.getByText(/V=3/)).toBeInTheDocument()
  })

  it('shows empty state when no features', () => {
    render(<MemoryRouter><StatusView project={{ ...mockProject, features: [] }} projectId="proj-1" /></MemoryRouter>)
    expect(screen.getByText('No feature vectors found.')).toBeInTheDocument()
  })

  it('renders feature_id as a link to the feature detail page', () => {
    render(<MemoryRouter><StatusView project={mockProject} projectId="proj-1" /></MemoryRouter>)
    const link = screen.getByRole('link', { name: 'REQ-F-TEST-001' })
    expect(link).toHaveAttribute('href', '/projects/proj-1/features/REQ-F-TEST-001')
  })
})
