// Implements: REQ-F-SUP-003, REQ-F-SUP-004

import React from 'react'
import { useNavigate } from 'react-router-dom'
import type { SupervisionFeature, GateItem, GateDecision } from '../../api/types'
import { AutoModeToggle } from './AutoModeToggle'
import { GateActionPanel } from './GateActionPanel'
import { buildFeaturePath } from '../../routing/routes'

interface FeatureListProps {
  workspaceId: string
  features: SupervisionFeature[]
  onApprove: (decision: GateDecision) => Promise<void>
  onReject: (decision: GateDecision) => Promise<void>
  onAutoModeChange: () => void
}

function statusBadge(status: SupervisionFeature['status']): React.JSX.Element {
  const map: Record<string, string> = {
    converged: 'bg-emerald-900/30 text-emerald-400',
    stuck: 'bg-amber-950/30 text-amber-400',
    blocked: 'bg-red-950/30 text-red-400',
    in_progress: 'bg-blue-950/30 text-blue-400',
    pending: 'bg-muted text-muted-foreground',
  }
  return (
    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${map[status] ?? 'bg-muted text-muted-foreground'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}

function blockReasonLabel(feature: SupervisionFeature): string {
  if (!feature.blockReason) return ''
  if (feature.blockReason === 'human_gate') return 'Waiting on gate'
  if (feature.blockReason === 'spawn_dependency') {
    return `Waiting for child: ${feature.blockingChildFeatureId ?? '?'}`
  }
  return 'Blocked'
}

const STATUS_ORDER: SupervisionFeature['status'][] = ['stuck', 'blocked', 'in_progress', 'pending', 'converged']

// FeatureList — all features sorted: stuck > blocked > in_progress > pending.
// Implements: REQ-F-SUP-001 AC2, REQ-F-SUP-003, REQ-F-SUP-004
export function FeatureList({
  workspaceId,
  features,
  onApprove,
  onReject,
  onAutoModeChange,
}: FeatureListProps): React.JSX.Element {
  const navigate = useNavigate()

  const sorted = [...features].sort((a, b) => {
    return STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  })

  if (sorted.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground/60 text-sm italic">
        No features in workspace.
      </div>
    )
  }

  let lastSection = ''

  return (
    <div className="flex flex-col divide-y divide-border/50">
      {sorted.map((feature) => {
        const section = feature.status
        const showHeader = section !== lastSection
        lastSection = section

        return (
          <React.Fragment key={feature.featureId}>
            {showHeader && (
              <div className="px-4 py-1 bg-background text-xs font-semibold text-muted-foreground uppercase tracking-wide sticky top-0">
                {section === 'stuck' && 'Stuck'}
                {section === 'blocked' && 'Blocked'}
                {section === 'in_progress' && 'In Progress'}
                {section === 'pending' && 'Pending'}
                {section === 'converged' && 'Converged'}
              </div>
            )}

            <div
              className={`px-4 py-3 flex flex-col gap-2 ${
                feature.status === 'stuck'
                  ? 'bg-amber-950/20'
                  : feature.status === 'blocked'
                  ? 'bg-red-950/20'
                  : feature.status === 'converged'
                  ? 'opacity-50'
                  : 'bg-secondary'
              }`}
            >
              <div className="flex items-center gap-3">
                <button
                  onClick={() => navigate(buildFeaturePath(workspaceId, feature.featureId))}
                  className="font-mono text-sm text-primary hover:underline"
                >
                  {feature.featureId}
                </button>
                {statusBadge(feature.status)}
                <span className="text-xs text-muted-foreground">{feature.currentEdge}</span>
                <span className="text-xs text-muted-foreground/60 ml-auto">δ = {feature.delta}</span>

                {/* Auto-mode toggle visible in every row — REQ-BR-SUPV-001 */}
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-muted-foreground/60">Auto</span>
                  <AutoModeToggle
                    workspaceId={workspaceId}
                    featureId={feature.featureId}
                    currentlyEnabled={feature.autoModeEnabled}
                    onComplete={onAutoModeChange}
                  />
                </div>
              </div>

              {/* Stuck detail — Implements: REQ-F-SUP-004 */}
              {feature.status === 'stuck' && feature.consecutiveStuckIterations !== undefined && (
                <p className="text-xs text-amber-400">
                  δ unchanged for {feature.consecutiveStuckIterations} consecutive iterations on {feature.currentEdge}
                </p>
              )}

              {/* Blocked detail — Implements: REQ-F-SUP-003 */}
              {feature.status === 'blocked' && (
                <p className="text-xs text-red-400">{blockReasonLabel(feature)}</p>
              )}

              {/* Inline gate actions for blocked-by-gate features */}
              {feature.blockingGate && (
                <GateActionPanel
                  workspaceId={workspaceId}
                  gate={feature.blockingGate as GateItem}
                  onApprove={onApprove}
                  onReject={onReject}
                />
              )}
            </div>
          </React.Fragment>
        )
      })}
    </div>
  )
}
