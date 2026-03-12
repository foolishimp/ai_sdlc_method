// Implements: REQ-F-OVR-001, REQ-F-OVR-002, REQ-BR-SUPV-002

import React from 'react'
import type { FeatureStatusSummary } from '../../api/types'

interface FeatureStatusCountsProps {
  counts: FeatureStatusSummary
  onTileClick?: (status: string) => void
}

interface TileProps {
  label: string
  value: number
  accent?: boolean
  colorClass: string
  onClick?: () => void
}

function Tile({ label, value, accent, colorClass, onClick }: TileProps): React.JSX.Element {
  return (
    <button
      onClick={onClick}
      className={`flex-1 rounded-lg border p-3 text-left hover:opacity-80 transition-opacity ${colorClass}`}
    >
      <p className={`font-bold ${accent ? 'text-4xl' : 'text-3xl'}`}>{value}</p>
      <p className={`mt-0.5 ${accent ? 'text-sm font-semibold' : 'text-xs'}`}>{label}</p>
    </button>
  )
}

// FeatureStatusCounts — four status tiles with pending gates prominently shown.
// Implements: REQ-F-OVR-002, REQ-BR-SUPV-002 (gates visually prominent)
export function FeatureStatusCounts({ counts, onTileClick }: FeatureStatusCountsProps): React.JSX.Element {
  return (
    <div className="flex gap-3">
      <Tile
        label="Converged"
        value={counts.converged}
        colorClass="bg-green-50 border-green-200 text-emerald-400"
        onClick={() => onTileClick?.('converged')}
      />
      <Tile
        label="In Progress"
        value={counts.in_progress}
        colorClass="bg-blue-50 border-blue-200 text-blue-400"
        onClick={() => onTileClick?.('in_progress')}
      />
      <Tile
        label="Blocked"
        value={counts.blocked}
        colorClass="bg-red-950/20 border-red-200 text-red-400"
        onClick={() => onTileClick?.('blocked')}
      />
      <Tile
        label="Pending"
        value={counts.pending}
        colorClass="bg-background border-border text-foreground/80"
        onClick={() => onTileClick?.('pending')}
      />
      {/* Pending gates — visually prominent per REQ-BR-SUPV-002 */}
      <Tile
        label="Pending Gates"
        value={counts.pendingGates}
        accent
        colorClass={
          counts.pendingGates > 0
            ? 'bg-orange-950/30 border-orange-400 text-orange-900 ring-1 ring-orange-400'
            : 'bg-background border-border text-muted-foreground'
        }
        onClick={() => onTileClick?.('pending_gates')}
      />
    </div>
  )
}
