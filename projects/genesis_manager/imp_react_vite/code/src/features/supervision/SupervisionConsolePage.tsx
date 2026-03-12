// Implements: REQ-F-SUP-001, REQ-F-VIS-001, REQ-BR-SUPV-002

import React, { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { FreshnessIndicator } from '../../components/shared/FreshnessIndicator'
import { HumanGateQueue } from './HumanGateQueue'
import { FeatureList } from './FeatureList'
import { ControlSurface } from '../control/ControlSurface'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import type { GateDecision, SupervisionFeature } from '../../api/types'

// SupervisionConsolePage — two-panel layout: sticky HumanGateQueue + scrollable FeatureList.
// Implements: REQ-F-SUP-001, REQ-BR-SUPV-002
export function SupervisionConsolePage(): React.JSX.Element {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const id = workspaceId ?? ''

  const loadWorkspace = useWorkspaceStore((s) => s.loadWorkspace)
  const gates = useWorkspaceStore((s) => s.gates)
  const features = useWorkspaceStore((s) => s.features)
  const overview = useWorkspaceStore((s) => s.overview)
  const setActiveProject = useProjectStore((s) => s.setActiveProject)
  const lastRefreshed = useProjectStore((s) => s.lastRefreshed)
  const pollingError = useProjectStore((s) => s.pollingError)
  const isRefreshing = useProjectStore((s) => s.isRefreshing)

  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null)
  // Optimistic gate removal
  const [removedGateIds, setRemovedGateIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (id) {
      setActiveProject(id)
      void loadWorkspace(id)
    }
  }, [id, loadWorkspace, setActiveProject])

  const refresh = useCallback(async () => {
    await loadWorkspace(id)
    setRemovedGateIds(new Set()) // clear optimistic removals after re-fetch
  }, [id, loadWorkspace])

  const handleApprove = useCallback(async (decision: GateDecision) => {
    // Optimistic removal
    const gate = gates.find(
      (g) => g.featureId === decision.featureId && g.edge === decision.edge && g.gateName === decision.gateName,
    )
    if (gate) setRemovedGateIds((prev) => new Set([...prev, gate.id]))

    await apiClient.postEvent(id, {
      event_type: 'review_approved',
      feature: decision.featureId,
      edge: decision.edge,
      gate_name: decision.gateName,
      decision: 'approved',
      comment: decision.comment,
      actor: 'human',
    })
    // Revalidate after a brief delay
    setTimeout(() => void refresh(), 2_000)
  }, [gates, id, refresh])

  const handleReject = useCallback(async (decision: GateDecision) => {
    const gate = gates.find(
      (g) => g.featureId === decision.featureId && g.edge === decision.edge && g.gateName === decision.gateName,
    )
    if (gate) setRemovedGateIds((prev) => new Set([...prev, gate.id]))

    await apiClient.postEvent(id, {
      event_type: 'review_approved',
      feature: decision.featureId,
      edge: decision.edge,
      gate_name: decision.gateName,
      decision: 'rejected',
      comment: decision.comment,
      actor: 'human',
    })
    setTimeout(() => void refresh(), 2_000)
  }, [gates, id, refresh])

  const visibleGates = gates.filter((g) => !removedGateIds.has(g.id))

  // Map FeatureVector[] → SupervisionFeature[].
  // Include all features — converged shown at bottom so auto-mode is always controllable.
  const supervisionFeatures: SupervisionFeature[] = features
    .map((f) => ({
      featureId: f.featureId,
      title: f.title,
      currentEdge: f.currentEdge ?? '',
      iterationNumber: 0,
      delta: f.currentDelta ?? 0,
      status: (f.status as SupervisionFeature['status']) ?? 'pending',
      autoModeEnabled: f.autoModeEnabled,
    }))

  const selectedFeature = selectedFeatureId
    ? supervisionFeatures.find((f) => f.featureId === selectedFeatureId) ?? null
    : null

  const projectName = overview?.projectName ?? ''

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      {/* Sidebar nav */}
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      {/* Main content column */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-4 h-12 flex items-center justify-between">
          <span className="font-semibold text-foreground">Supervision Console</span>
          <FreshnessIndicator
            lastRefreshed={lastRefreshed}
            isRefreshing={isRefreshing}
            error={pollingError}
          />
        </header>

        {/* Sticky gate queue — REQ-BR-SUPV-002 */}
        <div className="flex-shrink-0">
          <HumanGateQueue
            workspaceId={id}
            gates={visibleGates}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </div>

        {/* Body — two columns: feature list + control surface */}
        <div className="flex-1 overflow-hidden flex divide-x divide-border">
          {/* Left: feature list */}
          <div className="flex-1 overflow-y-auto">
            <FeatureList
              workspaceId={id}
              features={supervisionFeatures}
              onApprove={handleApprove}
              onReject={handleReject}
              onAutoModeChange={() => void refresh()}
            />
          </div>

          {/* Right: control surface (contextual) */}
          {selectedFeature && (
            <div className="w-80 flex-shrink-0 overflow-y-auto">
              <ControlSurface
                workspaceId={id}
                feature={selectedFeature}
                onActionComplete={() => void refresh()}
                onClose={() => setSelectedFeatureId(null)}
              />
            </div>
          )}
        </div>

        {/* Feature selector status bar */}
        <div className="flex-shrink-0 bg-secondary border-t px-4 py-2 text-xs text-muted-foreground/60">
          {selectedFeatureId
            ? `Selected: ${selectedFeatureId} — click again to deselect`
            : 'Click a feature to open the control surface'}
        </div>
      </div>
    </div>
  )
}
