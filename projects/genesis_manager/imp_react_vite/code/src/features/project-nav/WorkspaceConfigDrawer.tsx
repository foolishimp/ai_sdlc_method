// Implements: REQ-F-PROJ-004, REQ-F-FSNAV-003

import React, { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useProjectStore } from '../../stores/projectStore'
import { FolderBrowser } from './FolderBrowser'

interface WorkspaceConfigDrawerProps {
  open: boolean
  onClose: () => void
}

type InputMode = 'browse' | 'manual'

// WorkspaceConfigDrawer — add/remove workspace paths.
// Browse mode (default): FolderBrowser for point-and-click registration (REQ-F-FSNAV-003).
// Manual mode: existing text-input for power users.
// Implements: REQ-F-PROJ-004, REQ-F-FSNAV-003
export function WorkspaceConfigDrawer({ open, onClose }: WorkspaceConfigDrawerProps): React.JSX.Element {
  const [pathInput, setPathInput] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const [inputMode, setInputMode] = useState<InputMode>('browse')

  const workspaceSummaries = useProjectStore((s) => s.workspaceSummaries)
  const addWorkspace = useProjectStore((s) => s.addWorkspace)
  const removeWorkspace = useProjectStore((s) => s.removeWorkspace)

  const handleAdd = async () => {
    const path = pathInput.trim()
    if (!path) return
    setAdding(true)
    setAddError(null)
    try {
      await addWorkspace(path)
      setPathInput('')
    } catch (err) {
      const msg = err instanceof Error
        ? err.message
        : (err as { message?: string }).message ?? 'Failed to add workspace'
      setAddError(msg)
    } finally {
      setAdding(false)
    }
  }

  // AC-6: called by FolderBrowser when user clicks Add on a workspace dir.
  // The browser passes the project root; the server expects the .ai-workspace/ subdir.
  const handleSelectWorkspace = async (absolutePath: string) => {
    setAdding(true)
    setAddError(null)
    try {
      await addWorkspace(`${absolutePath}/.ai-workspace`)
    } catch (err) {
      const msg = err instanceof Error
        ? err.message
        : (err as { message?: string }).message ?? 'Failed to add workspace'
      setAddError(msg)
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = (id: string) => {
    removeWorkspace(id)
  }

  const workspaceList = Object.values(workspaceSummaries)

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed right-0 top-0 h-full w-full max-w-sm bg-background border-l border-border shadow-xl z-50 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <Dialog.Title className="text-base font-semibold">Manage Workspaces</Dialog.Title>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground text-xl leading-none"
            >
              ×
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            {/* Browse / Manual toggle (REQ-F-FSNAV-003) */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-2">
                Add workspace
              </label>

              <div className="flex gap-1 mb-3">
                <button
                  onClick={() => setInputMode('browse')}
                  className={`text-xs px-3 py-1 rounded transition-colors ${
                    inputMode === 'browse'
                      ? 'bg-primary text-primary-foreground'
                      : 'border border-border text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Browse
                </button>
                <button
                  onClick={() => setInputMode('manual')}
                  className={`text-xs px-3 py-1 rounded transition-colors ${
                    inputMode === 'manual'
                      ? 'bg-primary text-primary-foreground'
                      : 'border border-border text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Manual path
                </button>
              </div>

              {inputMode === 'browse' ? (
                <FolderBrowser
                  onSelectWorkspace={(p) => void handleSelectWorkspace(p)}
                />
              ) : (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={pathInput}
                    onChange={(e) => setPathInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') void handleAdd() }}
                    placeholder="/path/to/project"
                    className="flex-1 border border-input rounded px-2 py-1.5 text-sm font-mono bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <button
                    onClick={() => void handleAdd()}
                    disabled={adding || !pathInput.trim()}
                    className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {adding ? 'Adding…' : 'Add'}
                  </button>
                </div>
              )}

              {addError && (
                <p className="mt-1 text-xs text-destructive">{addError}</p>
              )}
              {adding && (
                <p className="mt-1 text-xs text-muted-foreground">Adding workspace…</p>
              )}
            </div>

            {/* Registered workspaces list */}
            <div>
              <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                Registered Workspaces ({workspaceList.length})
              </h3>
              {workspaceList.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No workspaces registered yet.</p>
              ) : (
                <ul className="divide-y divide-border">
                  {workspaceList.map((ws) => (
                    <li key={ws.workspaceId} className="flex items-center justify-between py-2 gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{ws.projectName}</p>
                        <p className="text-xs text-muted-foreground font-mono truncate">{ws.workspaceId}</p>
                        {!ws.available && (
                          <p className="text-xs text-destructive">Unavailable</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemove(ws.workspaceId)}
                        className="flex-shrink-0 text-xs text-destructive hover:opacity-80 border border-destructive/30 rounded px-2 py-0.5"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
