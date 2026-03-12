// Implements: REQ-F-SUP-001, REQ-F-SUP-002, REQ-BR-SUPV-002

import React from 'react'
import type { GateItem, GateDecision } from '../../api/types'
import { GateActionPanel } from './GateActionPanel'

interface HumanGateQueueProps {
  workspaceId: string
  gates: GateItem[]
  onApprove: (decision: GateDecision) => Promise<void>
  onReject: (decision: GateDecision) => Promise<void>
}

function formatAge(ageMs: number): string {
  const minutes = Math.floor(ageMs / 60_000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// HumanGateQueue — sticky top pending gates list.
// Empty state shows green "all clear" indicator.
// Implements: REQ-F-SUP-002, REQ-BR-SUPV-002 (appears above all other content)
export function HumanGateQueue({ workspaceId, gates, onApprove, onReject }: HumanGateQueueProps): React.JSX.Element {
  if (gates.length === 0) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-emerald-900/20 border-b border-emerald-800/40">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        <span className="text-sm text-emerald-400 font-medium">No pending gates</span>
      </div>
    )
  }

  return (
    <div className="border-b border-orange-800/40 bg-orange-900/20">
      <div className="px-4 py-2 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
        <span className="text-sm font-semibold text-orange-300">
          {gates.length} pending gate{gates.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="px-4 pb-3 flex flex-col gap-2">
        {gates.map((gate) => (
          <div key={gate.id} className="flex items-start gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs text-blue-700">{gate.featureId}</span>
                <span className="text-xs text-muted-foreground">·</span>
                <span className="text-xs text-muted-foreground">{gate.edge}</span>
                <span className="text-xs text-muted-foreground ml-auto">{formatAge(gate.ageMs)}</span>
              </div>
              <GateActionPanel
                workspaceId={workspaceId}
                gate={gate}
                onApprove={onApprove}
                onReject={onReject}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
