// Implements: REQ-F-CTL-003

import React, { useState } from 'react'
import { apiClient } from '../../api/WorkspaceApiClient'
import { ConfirmActionDialog } from '../../components/shared/ConfirmActionDialog'
import { CommandLabel } from '../../components/shared/CommandLabel'
import { CMD } from '../../components/shared/commandStrings'

type ChildVectorType = 'discovery' | 'spike' | 'poc' | 'hotfix'

interface SpawnFeaturePanelProps {
  workspaceId: string
  parentFeatureId: string
  onComplete: () => void
}

// SpawnFeaturePanel — form to spawn a new child feature vector.
// Reason field is required before confirm is enabled.
// Implements: REQ-F-CTL-003
export function SpawnFeaturePanel({ workspaceId, parentFeatureId, onComplete }: SpawnFeaturePanelProps): React.JSX.Element {
  const [childType, setChildType] = useState<ChildVectorType>('spike')
  const [reason, setReason] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)

  const command = CMD.spawnFeature(parentFeatureId, childType, reason)

  const handleConfirm = async () => {
    await apiClient.postEvent(workspaceId, {
      event_type: 'spawn_requested',
      parent_feature: parentFeatureId,
      child_type: childType,
      reason,
      actor: 'human',
    })
    setDialogOpen(false)
    setReason('')
    onComplete()
  }

  return (
    <div className="flex flex-col gap-3 p-3 border rounded-lg bg-background">
      <h4 className="text-xs font-semibold text-foreground/80 uppercase tracking-wide">Spawn Child Vector</h4>

      <div>
        <label className="block text-xs text-muted-foreground mb-1">Type</label>
        <select
          value={childType}
          onChange={(e) => setChildType(e.target.value as ChildVectorType)}
          className="w-full text-sm border border-border rounded px-2 py-1.5"
        >
          <option value="discovery">Discovery</option>
          <option value="spike">Spike</option>
          <option value="poc">PoC</option>
          <option value="hotfix">Hotfix</option>
        </select>
      </div>

      <div>
        <label className="block text-xs text-muted-foreground mb-1">
          Reason <span className="text-red-500">*</span>
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={2}
          placeholder="Why is this child vector needed?"
          className="w-full text-sm border border-border rounded px-2 py-1.5 resize-none"
        />
      </div>

      <CommandLabel command={command}>
        <button
          onClick={() => setDialogOpen(true)}
          disabled={!reason.trim()}
          className="w-full px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Spawn Child Vector
        </button>
      </CommandLabel>

      <ConfirmActionDialog
        open={dialogOpen}
        title="Spawn Child Vector"
        description={`Spawn a ${childType} child vector from ${parentFeatureId}?`}
        command={command}
        onConfirm={handleConfirm}
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  )
}
