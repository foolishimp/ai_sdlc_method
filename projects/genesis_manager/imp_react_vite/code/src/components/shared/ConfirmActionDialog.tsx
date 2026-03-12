// Implements: REQ-F-UX-002, REQ-F-CTL-001, REQ-DATA-WORK-002

import React, { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { CommandLabel } from './CommandLabel'

interface ConfirmActionDialogProps {
  open: boolean
  title: string
  description: string
  command: string // shown as CommandLabel beneath description
  requireComment?: boolean // true for gate rejection
  comment?: string
  onCommentChange?: (value: string) => void
  warningMessage?: string // e.g. auto-mode warning
  onConfirm: () => Promise<void>
  onCancel: () => void
}

// ConfirmActionDialog — shared confirmation wrapper for all write actions.
// Every write in genesis_manager goes through this dialog.
// Implements: REQ-F-CTL-001, REQ-DATA-WORK-002
export function ConfirmActionDialog({
  open,
  title,
  description,
  command,
  requireComment = false,
  comment = '',
  onCommentChange,
  warningMessage,
  onConfirm,
  onCancel,
}: ConfirmActionDialogProps): React.JSX.Element {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const confirmDisabled = loading || (requireComment && comment.trim() === '')

  const handleConfirm = async () => {
    setLoading(true)
    setError(null)
    try {
      await onConfirm()
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
      setLoading(false)
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onCancel() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-secondary rounded-lg shadow-xl p-6 w-full max-w-md">
          <Dialog.Title className="text-base font-semibold text-foreground mb-1">
            {title}
          </Dialog.Title>
          <Dialog.Description className="text-sm text-muted-foreground mb-3">
            {description}
          </Dialog.Description>

          {warningMessage && (
            <div className="mb-3 rounded bg-amber-950/20 border border-amber-200 px-3 py-2 text-sm text-amber-400">
              {warningMessage}
            </div>
          )}

          {requireComment && (
            <div className="mb-3">
              <label className="block text-xs font-medium text-foreground/80 mb-1">
                Comment <span className="text-red-500">*</span>
              </label>
              <textarea
                className="w-full border border-border rounded px-2 py-1.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                value={comment}
                onChange={(e) => onCommentChange?.(e.target.value)}
                placeholder="Required for rejection…"
              />
            </div>
          )}

          <div className="mb-4">
            <CommandLabel command={command} />
          </div>

          {error && (
            <div className="mb-3 rounded bg-red-950/20 border border-red-200 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              onClick={onCancel}
              disabled={loading}
              className="px-3 py-1.5 text-sm border border-border rounded hover:bg-background disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={() => void handleConfirm()}
              disabled={confirmDisabled}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Working…' : 'Confirm'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
