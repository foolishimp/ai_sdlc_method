// Implements: REQ-F-PROJ-004

import React, { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useProjectStore } from '../../stores/projectStore'

interface WorkspaceConfigDrawerProps {
  open: boolean
  onClose: () => void
}

// WorkspaceConfigDrawer — add/remove workspace paths.
// Validates on submit: POST /api/workspaces (server validates path + events.jsonl)
// Implements: REQ-F-PROJ-004
export function WorkspaceConfigDrawer({ open, onClose }: WorkspaceConfigDrawerProps): React.JSX.Element {
  const [pathInput, setPathInput] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)

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
      setAddError(err instanceof Error ? err.message : 'Failed to add workspace')
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
        <Dialog.Overlay className="fixed inset-0 bg-black/30 z-40" />
        <Dialog.Content className="fixed right-0 top-0 h-full w-full max-w-sm bg-white shadow-xl z-50 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <Dialog.Title className="text-base font-semibold">Manage Workspaces</Dialog.Title>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            >
              ×
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            {/* Add workspace form */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Add workspace by absolute path
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={pathInput}
                  onChange={(e) => setPathInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleAdd() }}
                  placeholder="/path/to/project/.ai-workspace"
                  className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => void handleAdd()}
                  disabled={adding || !pathInput.trim()}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {adding ? 'Adding…' : 'Add'}
                </button>
              </div>
              {addError && (
                <p className="mt-1 text-xs text-red-600">{addError}</p>
              )}
            </div>

            {/* Registered workspaces list */}
            <div>
              <h3 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">
                Registered Workspaces ({workspaceList.length})
              </h3>
              {workspaceList.length === 0 ? (
                <p className="text-sm text-gray-400 italic">No workspaces registered yet.</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {workspaceList.map((ws) => (
                    <li key={ws.workspaceId} className="flex items-center justify-between py-2 gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{ws.projectName}</p>
                        <p className="text-xs text-gray-400 font-mono truncate">{ws.workspaceId}</p>
                        {!ws.available && (
                          <p className="text-xs text-red-500">Unavailable</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemove(ws.workspaceId)}
                        className="flex-shrink-0 text-xs text-red-500 hover:text-red-700 border border-red-200 rounded px-2 py-0.5"
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
