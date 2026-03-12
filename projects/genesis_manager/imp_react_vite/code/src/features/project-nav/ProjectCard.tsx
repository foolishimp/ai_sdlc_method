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
    : 'border-gray-200 hover:border-gray-300'

  return (
    <button
      onClick={() => onSelect(workspaceId)}
      className={`w-full text-left p-4 rounded-lg border-2 transition-colors bg-white ${borderClass} ${
        !available ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 truncate">{projectName}</p>
          <p className="text-xs text-gray-500 font-mono truncate">{workspaceId}</p>
        </div>

        {/* Attention badge — Implements: REQ-F-PROJ-002 */}
        {hasAttentionRequired && available && (
          <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
            Needs attention
          </span>
        )}

        {/* Unavailable badge — Implements: REQ-F-PROJ-004 */}
        {!available && (
          <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
            Unavailable
          </span>
        )}
      </div>

      {available && (
        <div className="mt-3 flex gap-4 text-xs text-gray-600">
          <span>
            <span className="font-medium text-gray-900">{activeFeatureCount}</span>{' '}
            active features
          </span>
          {pendingGateCount > 0 && (
            <span className="font-medium text-orange-700">
              {pendingGateCount} pending gate{pendingGateCount !== 1 ? 's' : ''}
            </span>
          )}
          {stuckFeatureCount > 0 && (
            <span className="font-medium text-amber-700">
              {stuckFeatureCount} stuck
            </span>
          )}
        </div>
      )}
    </button>
  )
}
