// Implements: REQ-F-PROJ-001, REQ-F-PROJ-002, REQ-F-PROJ-003

import React from 'react'
import type { WorkspaceSummary } from '../../api/types'

interface ProjectCardProps {
  summary: WorkspaceSummary
  isActive: boolean
  onSelect: (id: string) => void
}

// ProjectCard — renders a single workspace/project summary.
// Shows attention badge when pendingGateCount > 0 or stuckFeatureCount > 0.
// Implements: REQ-F-PROJ-001, REQ-F-PROJ-002, REQ-F-PROJ-003
export function ProjectCard({ summary, isActive, onSelect }: ProjectCardProps): React.JSX.Element {
  const {
    workspaceId,
    projectName,
    activeFeatureCount,
    pendingGateCount,
    stuckFeatureCount,
    hasAttentionRequired,
    available,
  } = summary

  const borderClass = isActive
    ? 'border-blue-500 shadow-md'
    : hasAttentionRequired
    ? 'border-orange-400'
    : 'border-border hover:border-border'

  return (
    <button
      onClick={() => onSelect(workspaceId)}
      className={`w-full text-left p-4 rounded-lg border-2 transition-colors bg-secondary ${borderClass} ${
        !available ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-foreground truncate">{projectName}</p>
          <p className="text-xs text-muted-foreground font-mono truncate">{workspaceId}</p>
        </div>

        {/* Attention badge — Implements: REQ-F-PROJ-002 */}
        {hasAttentionRequired && available && (
          <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-950/30 text-orange-400">
            Needs attention
          </span>
        )}

        {/* Unavailable badge — Implements: REQ-F-PROJ-004 */}
        {!available && (
          <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground">
            Unavailable
          </span>
        )}
      </div>

      {available && (
        <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
          <span>
            <span className="font-medium text-foreground">{activeFeatureCount}</span>{' '}
            active features
          </span>
          {pendingGateCount > 0 && (
            <span className="font-medium text-orange-700">
              {pendingGateCount} pending gate{pendingGateCount !== 1 ? 's' : ''}
            </span>
          )}
          {stuckFeatureCount > 0 && (
            <span className="font-medium text-amber-400">
              {stuckFeatureCount} stuck
            </span>
          )}
        </div>
      )}
    </button>
  )
}
