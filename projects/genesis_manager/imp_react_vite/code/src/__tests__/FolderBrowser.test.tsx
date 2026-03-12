// Validates: REQ-F-FSNAV-002
// @vitest-environment jsdom

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { FolderBrowser } from '../features/project-nav/FolderBrowser'
import type { FsBrowseResult } from '../api/types'

vi.mock('../api/WorkspaceApiClient', () => ({
  apiClient: {
    browsePath: vi.fn(),
  },
}))

import { apiClient } from '../api/WorkspaceApiClient'

const mockBrowsePath = vi.mocked(apiClient.browsePath)

const makeBrowseResult = (overrides?: Partial<FsBrowseResult>): FsBrowseResult => ({
  path: '/Users/jim/src',
  parent: '/Users/jim',
  entries: [],
  truncated: false,
  ...overrides,
})

describe('FolderBrowser', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  // AC-4: renders breadcrumb, list, and badge
  it('renders breadcrumb from the current path', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult({ path: '/Users/jim/src' }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Loading…')).not.toBeInTheDocument()
    })

    // Breadcrumb segments: Users, jim, src
    expect(screen.getByRole('button', { name: 'Users' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'jim' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'src' })).toBeInTheDocument()
  })

  // AC-4: renders entry list
  it('renders directory entries in the list', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult({
      entries: [
        { name: 'alpha', absolutePath: '/Users/jim/src/alpha', isDir: true, hasWorkspace: false },
        { name: 'beta', absolutePath: '/Users/jim/src/beta', isDir: true, hasWorkspace: false },
      ],
    }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    expect(screen.getByText('alpha')).toBeInTheDocument()
    expect(screen.getByText('beta')).toBeInTheDocument()
  })

  // AC-4: workspace badge shown for Genesis dirs
  it('shows Genesis badge on workspace directories', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult({
      entries: [
        { name: 'my_project', absolutePath: '/Users/jim/src/my_project', isDir: true, hasWorkspace: true },
      ],
    }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    expect(screen.getByText('Genesis')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add' })).toBeInTheDocument()
  })

  // AC-5: clicking a directory navigates into it
  it('navigates into a directory on click (AC-5)', async () => {
    mockBrowsePath
      .mockResolvedValueOnce(makeBrowseResult({
        path: '/Users/jim/src',
        entries: [
          { name: 'apps', absolutePath: '/Users/jim/src/apps', isDir: true, hasWorkspace: false },
        ],
      }))
      .mockResolvedValueOnce(makeBrowseResult({ path: '/Users/jim/src/apps', entries: [] }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    fireEvent.click(screen.getByText('apps'))

    await waitFor(() => {
      expect(mockBrowsePath).toHaveBeenCalledWith('/Users/jim/src/apps')
    })
  })

  // AC-6: clicking Add on a workspace dir calls onSelectWorkspace
  it('calls onSelectWorkspace when Add is clicked on a workspace dir (AC-6)', async () => {
    const onSelect = vi.fn()
    mockBrowsePath.mockResolvedValue(makeBrowseResult({
      entries: [
        { name: 'genesis_manager', absolutePath: '/Users/jim/src/genesis_manager', isDir: true, hasWorkspace: true },
      ],
    }))

    render(<FolderBrowser onSelectWorkspace={onSelect} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: 'Add' }))

    expect(onSelect).toHaveBeenCalledWith('/Users/jim/src/genesis_manager')
  })

  // AC-7: breadcrumb segment click navigates to that ancestor
  it('navigates to ancestor path when breadcrumb segment is clicked (AC-7)', async () => {
    mockBrowsePath
      .mockResolvedValueOnce(makeBrowseResult({
        path: '/Users/jim/src/apps',
        parent: '/Users/jim/src',
        entries: [],
      }))
      .mockResolvedValueOnce(makeBrowseResult({ path: '/Users/jim', entries: [] }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    // Click 'jim' breadcrumb segment → should navigate to /Users/jim
    fireEvent.click(screen.getByRole('button', { name: 'jim' }))

    await waitFor(() => {
      expect(mockBrowsePath).toHaveBeenCalledWith('/Users/jim')
    })
  })

  // AC-7: Up button navigates to parent
  it('navigates to parent when Up button is clicked (AC-7)', async () => {
    mockBrowsePath
      .mockResolvedValueOnce(makeBrowseResult({
        path: '/Users/jim/src',
        parent: '/Users/jim',
        entries: [],
      }))
      .mockResolvedValueOnce(makeBrowseResult({ path: '/Users/jim', entries: [] }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: '↑ Up' }))

    await waitFor(() => {
      expect(mockBrowsePath).toHaveBeenCalledWith('/Users/jim')
    })
  })

  // Up button hidden at root (parent = null)
  it('does not show Up button when parent is null', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult({ path: '/', parent: null, entries: [] }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    expect(screen.queryByRole('button', { name: '↑ Up' })).not.toBeInTheDocument()
  })

  // Loading state shown initially
  it('shows loading indicator while fetching', () => {
    mockBrowsePath.mockReturnValue(new Promise(() => {})) // never resolves

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  // Error state
  it('shows error message on browse failure', async () => {
    mockBrowsePath.mockRejectedValue(new Error('Network error'))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  // Truncation notice
  it('shows truncation notice when result is truncated', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult({ truncated: true, entries: [] }))

    render(<FolderBrowser onSelectWorkspace={vi.fn()} />)

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())

    expect(screen.getByText(/500 entries shown/)).toBeInTheDocument()
  })

  // initialPath passed to first browse call
  it('calls browsePath with initialPath on mount', async () => {
    mockBrowsePath.mockResolvedValue(makeBrowseResult())

    render(<FolderBrowser onSelectWorkspace={vi.fn()} initialPath="/custom/path" />)

    await waitFor(() => {
      expect(mockBrowsePath).toHaveBeenCalledWith('/custom/path')
    })
  })
})
