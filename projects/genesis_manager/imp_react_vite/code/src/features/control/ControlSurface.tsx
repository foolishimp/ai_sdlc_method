// Implements: REQ-F-CTL-001, REQ-BR-SUPV-001

import React from 'react'
import type { SupervisionFeature, GateDecision } from '../../api/types'
import { GateActionPanel } from '../supervision/GateActionPanel'
import { AutoModeToggle } from '../supervision/AutoModeToggle'
import { SpawnFeaturePanel } from './SpawnFeaturePanel'
import { CommandLabel } from '../../components/shared/CommandLabel'
import { ConfirmActionDialog } from '../../components/shared/ConfirmActionDialog'
import { CMD } from '../../components/shared/commandStrings'
import { apiClient } from '../../api/WorkspaceApiClient'

interface ControlSurfaceProps {
  workspaceId: string
  feature: SupervisionFeature
  onActionComplete: () => void
  onClose: () => void
}

// ControlSurface — context panel showing available actions for a selected feature.
// All writes go through ConfirmActionDialog — no silent background writes.
// Implements: REQ-F-CTL-001, REQ-BR-SUPV-001
export function ControlSurface({ workspaceId, feature, onActionComplete, onClose }: ControlSurfaceProps): React.JSX.Element {
  const [startDialogOpen, setStartDialogOpen] = React.useState(false)
  const [selectedEdge, setSelectedEdge] = React.useState(feature.currentEdge ?? '')

  const iterationDisabled =
    feature.status === 'converged' ||
    (feature.status === 'blocked' && feature.blockReason !== 'human_gate') ||
    !selectedEdge

  const handleStartIteration = async () => {
    await apiClient.postEvent(workspaceId, {
      event_type: 'iteration_requested',
      feature: feature.featureId,
      edge: selectedEdge,
      actor: 'human',
    })
    setStartDialogOpen(false)
    onActionComplete()
  }

  const handleApprove = async (decision: GateDecision) => {
    await apiClient.postEvent(workspaceId, {
      event_type: 'review_approved',
      feature: decision.featureId,
      edge: decision.edge,
      gate_name: decision.gateName,
      decision: 'approved',
      comment: decision.comment,
      actor: 'human',
    })
    onActionComplete()
  }

  const handleReject = async (decision: GateDecision) => {
    await apiClient.postEvent(workspaceId, {
      event_type: 'review_approved',
      feature: decision.featureId,
      edge: decision.edge,
      gate_name: decision.gateName,
      decision: 'rejected',
      comment: decision.comment,
      actor: 'human',
    })
    onActionComplete()
  }

  return (
    <div className="flex flex-col gap-4 p-4 bg-secondary">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Control Surface</p>
          <p className="font-mono text-sm text-primary">{feature.featureId}</p>
        </div>
        <button onClick={onClose} className="text-muted-foreground/60 hover:text-muted-foreground text-lg leading-none">×</button>
      </div>

      {/* Start iteration */}
      <div className="border rounded-lg p-3">
        <h4 className="text-xs font-semibold text-foreground/80 uppercase tracking-wide mb-2">Start Iteration</h4>
        <input
          type="text"
          value={selectedEdge}
          onChange={(e) => setSelectedEdge(e.target.value)}
          placeholder="Edge (e.g. design)"
          className="w-full text-sm border border-border rounded px-2 py-1.5 mb-2"
        />
        <CommandLabel command={CMD.startIteration(feature.featureId, selectedEdge)}>
          <button
            onClick={() => setStartDialogOpen(true)}
            disabled={iterationDisabled}
            className="w-full px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              feature.status === 'converged'
                ? 'Feature is already converged'
                : iterationDisabled
                ? 'Feature is blocked or no edge selected'
                : undefined
            }
          >
            Start Iteration
          </button>
        </CommandLabel>
      </div>

      {/* Gate actions — if there's a pending gate */}
      {feature.blockingGate && (
        <GateActionPanel
          workspaceId={workspaceId}
          gate={feature.blockingGate}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}

      {/* Auto-mode */}
      <div className="border rounded-lg p-3 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-foreground/80">Auto Mode</p>
          <p className="text-xs text-muted-foreground/60">Continuously iterate until a gate</p>
        </div>
        <AutoModeToggle
          workspaceId={workspaceId}
          featureId={feature.featureId}
          currentlyEnabled={feature.autoModeEnabled}
          onComplete={onActionComplete}
        />
      </div>

      {/* Spawn child */}
      <SpawnFeaturePanel
        workspaceId={workspaceId}
        parentFeatureId={feature.featureId}
        onComplete={onActionComplete}
      />

      <ConfirmActionDialog
        open={startDialogOpen}
        title="Start Iteration"
        description={`Start iteration on feature ${feature.featureId}, edge "${selectedEdge}"?`}
        command={CMD.startIteration(feature.featureId, selectedEdge)}
        onConfirm={handleStartIteration}
        onCancel={() => setStartDialogOpen(false)}
      />
    </div>
  )
}
