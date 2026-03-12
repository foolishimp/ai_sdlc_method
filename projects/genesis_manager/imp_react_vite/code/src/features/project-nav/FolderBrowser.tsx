// Implements: REQ-F-FSNAV-002, REQ-F-FSNAV-003
// FolderBrowser — browse the local filesystem and discover Genesis workspaces.

import React, { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../../api/WorkspaceApiClient'
import type { FsEntry } from '../../api/types'

export interface FolderBrowserProps {
  onSelectWorkspace: (absolutePath: string) => void
  initialPath?: string
}

// Implements: REQ-F-FSNAV-002 (AC-4, AC-5, AC-6, AC-7)
export function FolderBrowser({ onSelectWorkspace, initialPath }: FolderBrowserProps): React.JSX.Element {
  const [currentPath, setCurrentPath] = useState<string>('')
  const [parent, setParent] = useState<string | null>(null)
  const [entries, setEntries] = useState<FsEntry[]>([])
  const [truncated, setTruncated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const navigate = useCallback(async (targetPath?: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.browsePath(targetPath)
      setCurrentPath(result.path)
      setParent(result.parent)
      setEntries(result.entries)
      setTruncated(result.truncated ?? false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to browse')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void navigate(initialPath)
  }, [initialPath, navigate])

  // AC-7: breadcrumb segments — each is clickable
  const breadcrumbSegments = currentPath.split('/').filter(Boolean)

  return (
    <div className="flex flex-col gap-2 text-sm">
      {/* Breadcrumb (AC-7) */}
      <div className="flex items-center gap-1 text-xs font-mono flex-wrap min-h-[1.5rem]">
        <button
          onClick={() => void navigate('/')}
          className="hover:underline text-muted-foreground hover:text-foreground"
        >
          /
        </button>
        {breadcrumbSegments.map((seg, i) => {
          const segPath = '/' + breadcrumbSegments.slice(0, i + 1).join('/')
          return (
            <React.Fragment key={segPath}>
              <span className="text-muted-foreground">/</span>
              <button
                onClick={() => void navigate(segPath)}
                className="hover:underline text-muted-foreground hover:text-foreground"
              >
                {seg}
              </button>
            </React.Fragment>
          )
        })}
        {parent && (
          <button
            onClick={() => void navigate(parent)}
            className="ml-auto text-xs text-muted-foreground hover:text-foreground border border-border rounded px-1.5 py-0.5"
          >
            ↑ Up
          </button>
        )}
      </div>

      {/* Entry list */}
      {loading && (
        <p className="text-muted-foreground italic text-xs">Loading…</p>
      )}
      {error && (
        <p className="text-destructive text-xs">{error}</p>
      )}
      {!loading && !error && (
        <ul className="divide-y divide-border max-h-64 overflow-y-auto rounded border border-border">
          {entries.length === 0 && (
            <li className="px-3 py-2 text-xs text-muted-foreground italic">
              No subdirectories found
            </li>
          )}
          {entries.map((entry) => (
            <li
              key={entry.absolutePath}
              className="flex items-center justify-between px-3 py-2 hover:bg-accent"
            >
              {/* AC-5: click non-workspace dir → navigate; AC-6: click workspace dir → navigate (add button registers) */}
              <button
                onClick={() => void navigate(entry.absolutePath)}
                className="flex items-center gap-2 min-w-0 text-left flex-1"
              >
                <span>{entry.hasWorkspace ? '🟢' : '📁'}</span>
                <span className="truncate">{entry.name}</span>
                {entry.hasWorkspace && (
                  <span className="text-xs text-primary font-medium shrink-0 ml-1">
                    Genesis
                  </span>
                )}
              </button>
              {/* AC-6: Add button triggers registration */}
              {entry.hasWorkspace && (
                <button
                  onClick={() => onSelectWorkspace(entry.absolutePath)}
                  className="shrink-0 ml-2 text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded hover:opacity-90"
                >
                  Add
                </button>
              )}
            </li>
          ))}
          {truncated && (
            <li className="px-3 py-2 text-xs text-muted-foreground italic">
              ⚠ 500 entries shown — navigate into a subfolder to see more
            </li>
          )}
        </ul>
      )}
    </div>
  )
}
