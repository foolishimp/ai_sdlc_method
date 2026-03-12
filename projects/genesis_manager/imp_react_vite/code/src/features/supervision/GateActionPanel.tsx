// Implements: REQ-F-CTL-001, REQ-F-CTL-002, REQ-F-SUP-002

import React, { useState } from 'react'
import type { GateItem, GateDecision } from '../../api/types'
import { ConfirmActionDialog } from '../../components/shared/ConfirmActionDialog'
import { CommandLabel } from '../../components/shared/CommandLabel'
import { CMD } from '../../components/shared/commandStrings'

interface GateActionPanelProps {
  workspaceId: string
  gate: GateItem
  onApprove: (decision: GateDecision) => Promise<void>
  onReject: (decision: GateDecision) => Promise<void>
}

type DialogMode = 'approve' | 'reject' | null

// GateActionPanel — approve/reject form for a pending human gate.
// Comment is required for rejection (REQ-F-CTL-002 AC3).
// Implements: REQ-F-CTL-001, REQ-F-CTL-002, REQ-F-SUP-002
export function GateActionPanel({ workspaceId: _workspaceId, gate, onApprove, onReject }: GateActionPanelProps): React.JSX.Element {
  const [dialogMode, setDialogMode] = useState<DialogMode>(null)
  const [comment, setComment] = useState('')

  const handleConfirm = async () => {
    const decision: GateDecision = {
      featureId: gate.featureId,
      edge: gate.edge,
      gateName: gate.gateName,
      decision: dialogMode === 'approve' ? 'approved' : 'rejected',
      comment: comment || undefined,
    }
    if (dialogMode === 'approve') {
      await onApprove(decision)
    } else if (dialogMode === 'reject') {
      await onReject(decision)
    }
    setDialogMode(null)
    setComment('')
  }

  const approveCmd = CMD.approveGate(gate.featureId, gate.edge, gate.gateName)
  const rejectCmd = CMD.rejectGate(gate.featureId, gate.edge, comment, gate.gateName)

  return (
    <div className="border border-orange-200 rounded-lg p-3 bg-orange-50">
      <div className="mb-2">
        <span className="text-xs font-semibold text-orange-800 uppercase tracking-wide">
          Gate: {gate.gateName}
        </span>
        <span className="ml-2 text-xs text-muted-foreground">{gate.edge}</span>
      </div>

      <CommandLabel command={approveCmd}>
        <div className="flex gap-2">
          <button
            onClick={() => setDialogMode('approve')}
            className="flex-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Approve
          </button>
          <button
            onClick={() => { setDialogMode('reject'); setComment('') }}
            className="flex-1 px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            Reject
          </button>
        </div>
      </CommandLabel>

      <ConfirmActionDialog
        open={dialogMode !== null}
        title={dialogMode === 'approve' ? 'Approve Gate' : 'Reject Gate'}
        description={
          dialogMode === 'approve'
            ? `Approve gate "${gate.gateName}" for feature ${gate.featureId} on edge ${gate.edge}?`
            : `Reject gate "${gate.gateName}" for feature ${gate.featureId}? A comment is required.`
        }
        command={dialogMode === 'approve' ? approveCmd : rejectCmd}
        requireComment={dialogMode === 'reject'}
        comment={comment}
        onCommentChange={setComment}
        onConfirm={handleConfirm}
        onCancel={() => { setDialogMode(null); setComment('') }}
      />
    </div>
  )
}
