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
        colorClass="bg-emerald-900/20 border-emerald-800/60 text-emerald-400"
        onClick={() => onTileClick?.('converged')}
      />
      <Tile
        label="In Progress"
        value={counts.in_progress}
        colorClass="bg-blue-900/20 border-blue-800/60 text-blue-400"
        onClick={() => onTileClick?.('in_progress')}
      />
      <Tile
        label="Blocked"
        value={counts.blocked}
        colorClass="bg-red-900/20 border-red-800/60 text-red-400"
        onClick={() => onTileClick?.('blocked')}
      />
      <Tile
        label="Pending"
        value={counts.pending}
        colorClass="bg-muted/40 border-border text-muted-foreground"
        onClick={() => onTileClick?.('pending')}
      />
    </div>
  )
}
