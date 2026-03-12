// Implements: REQ-F-EVI-002, REQ-F-EVI-003

import React from 'react'
import { useNavigate } from 'react-router-dom'
import type { WorkspaceEvent } from '../../api/types'
import { buildFeaturePath, buildRunPath } from '../../routing/routes'

interface EventDetailPanelProps {
  workspaceId: string
  event: WorkspaceEvent | null
  loading?: boolean
}

// EventDetailPanel — shows raw event JSON + human-readable summary.
// Each identifier in the event is a navigation handle.
// Implements: REQ-F-EVI-002, REQ-F-EVI-003
export function EventDetailPanel({ workspaceId, event, loading }: EventDetailPanelProps): React.JSX.Element {
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground/60 text-sm">
        Loading event…
      </div>
    )
  }

  if (!event) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground/60 text-sm italic">
        Select an event to view its details.
      </div>
    )
  }

  return (
    <div className="p-4 flex flex-col gap-4">
      {/* Human-readable summary */}
      <div className="rounded-lg bg-background border border-border p-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
          Event #{event.eventIndex}
        </p>
        <p className="text-sm font-medium text-foreground mb-1">{event.eventType}</p>
        <div className="text-xs text-muted-foreground space-y-0.5">
          {event.timestamp && <div>Time: {new Date(event.timestamp).toLocaleString()}</div>}
          {event.feature && (
            <div className="flex items-center gap-1">
              Feature:{' '}
              <button
                onClick={() => navigate(buildFeaturePath(workspaceId, event.feature!))}
                className="font-mono text-primary hover:underline"
              >
                {event.feature}
              </button>
            </div>
          )}
          {event.edge && <div>Edge: {event.edge}</div>}
          {event.iteration !== null && event.iteration !== undefined && (
            <div>Iteration: #{event.iteration}</div>
          )}
          {event.delta !== null && event.delta !== undefined && (
            <div>δ = {event.delta}</div>
          )}
          {event.runId && (
            <div className="flex items-center gap-1">
              Run:{' '}
              <button
                onClick={() => navigate(buildRunPath(workspaceId, event.runId!))}
                className="font-mono text-xs text-primary hover:underline truncate max-w-xs"
              >
                {event.runId}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Raw JSON */}
      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Raw JSON</p>
        <pre className="text-xs bg-gray-900 text-green-300 rounded p-3 overflow-x-auto">
          {JSON.stringify(event.raw, null, 2)}
        </pre>
      </div>
    </div>
  )
}
