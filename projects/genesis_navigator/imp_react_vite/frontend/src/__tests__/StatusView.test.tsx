// Validates: REQ-F-STAT-001, REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusView } from '../components/StatusView'
import type { ProjectDetail } from '../api/types'

const mockProject: ProjectDetail = {
  project_id: 'proj-1',
  name: 'Test Project',
  root_path: '/workspace/test',
  state: 'ITERATING',
  features: [
    {
      feature_id: 'REQ-F-TEST-001',
      title: 'Test Feature',
      status: 'iterating',
      priority: 'high',
      satisfies: ['REQ-F-NAV-001'],
      trajectory: [
        { edge: 'design_code', status: 'converged', iteration: 1, delta: 0, started_at: null, converged_at: null },
        { edge: 'code_unit_tests', status: 'iterating', iteration: 2, delta: 3, started_at: null, converged_at: null },
      ],
      hamiltonian_t: 3,
      hamiltonian_v: 3,
      hamiltonian_h: 6,
    },
  ],
  last_event_at: '2026-03-12T10:00:00Z',
}

describe('StatusView', () => {
  it('renders project state', () => {
    render(<StatusView project={mockProject} />)
    expect(screen.getByTestId('status-view')).toBeInTheDocument()
    expect(screen.getByText('ITERATING')).toBeInTheDocument()
  })

  it('renders feature trajectory', () => {
    render(<StatusView project={mockProject} />)
    expect(screen.getByText('REQ-F-TEST-001')).toBeInTheDocument()
    expect(screen.getByText(/design_code/)).toBeInTheDocument()
    expect(screen.getByText(/code_unit_tests/)).toBeInTheDocument()
  })

  it('renders Hamiltonian values', () => {
    render(<StatusView project={mockProject} />)
    expect(screen.getByText(/H=6/)).toBeInTheDocument()
    expect(screen.getByText(/T=3/)).toBeInTheDocument()
    expect(screen.getByText(/V=3/)).toBeInTheDocument()
  })

  it('shows empty state when no features', () => {
    render(<StatusView project={{ ...mockProject, features: [] }} />)
    expect(screen.getByText('No feature vectors found.')).toBeInTheDocument()
  })
})
