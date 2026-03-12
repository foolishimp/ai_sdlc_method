// Implements: REQ-F-OVR-002, REQ-F-OVR-003

import React from 'react'
import type { FeatureStatusSummary } from '../../api/types'

interface FeatureStatusBarProps {
  counts: FeatureStatusSummary
  className?: string
}

// FeatureStatusBar — horizontal proportional status bar showing feature distribution.
// Implements: REQ-F-OVR-002, REQ-F-OVR-003
export function FeatureStatusBar({ counts, className }: FeatureStatusBarProps): React.JSX.Element {
  const total = counts.converged + counts.in_progress + counts.blocked + counts.pending
  if (total === 0) {
    return (
      <div className={`h-3 rounded-full bg-gray-100 ${className ?? ''}`} />
    )
  }

  const pct = (n: number) => `${Math.round((n / total) * 100)}%`

  return (
    <div className={`flex h-3 rounded-full overflow-hidden gap-px ${className ?? ''}`}>
      {counts.converged > 0 && (
        <div
          style={{ width: pct(counts.converged) }}
          className="bg-green-500"
          title={`${counts.converged} converged`}
        />
      )}
      {counts.in_progress > 0 && (
        <div
          style={{ width: pct(counts.in_progress) }}
          className="bg-blue-500"
          title={`${counts.in_progress} in progress`}
        />
      )}
      {counts.blocked > 0 && (
        <div
          style={{ width: pct(counts.blocked) }}
          className="bg-red-400"
          title={`${counts.blocked} blocked`}
        />
      )}
      {counts.pending > 0 && (
        <div
          style={{ width: pct(counts.pending) }}
          className="bg-gray-300"
          title={`${counts.pending} pending`}
        />
      )}
    </div>
  )
}
