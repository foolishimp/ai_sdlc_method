// Implements: REQ-F-EVI-004

import React from 'react'
import type { GapAnalysisData, GapLayer } from '../../api/types'
import { CommandLabel } from '../../components/shared/CommandLabel'
import { CMD } from '../../components/shared/commandStrings'

interface GapAnalysisPanelProps {
  data: GapAnalysisData | null
  loading: boolean
  onRerun: () => Promise<void>
}

function LayerSection({ label, layer }: { label: string; layer: GapLayer | null }): React.JSX.Element {
  if (!layer) return <></>
  const statusColor =
    layer.status === 'PASS'
      ? 'text-green-700 bg-green-50 border-green-200'
      : layer.status === 'ADVISORY'
      ? 'text-amber-700 bg-amber-50 border-amber-200'
      : 'text-red-700 bg-red-50 border-red-200'

  return (
    <div className="rounded border p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-700">{label}</span>
        <span className={`px-1.5 py-0.5 rounded text-xs font-bold border ${statusColor}`}>
          {layer.status}
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-2">
        {layer.coveredCount}/{layer.totalCount} covered
      </p>
      {layer.gaps.length > 0 && (
        <ul className="space-y-1">
          {layer.gaps.map((gap) => (
            <li key={gap.reqKey} className="text-xs text-gray-700">
              <span className="font-mono text-red-600">{gap.reqKey}</span>
              {gap.description && <span className="ml-1 text-gray-500">— {gap.description}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// GapAnalysisPanel — shows gap analysis layers + Re-run button with genesis command label.
// Implements: REQ-F-EVI-004, REQ-F-UX-002
export function GapAnalysisPanel({ data, loading, onRerun }: GapAnalysisPanelProps): React.JSX.Element {
  const [rerunning, setRerunning] = React.useState(false)
  const [rerunError, setRerunError] = React.useState<string | null>(null)

  const handleRerun = async () => {
    setRerunning(true)
    setRerunError(null)
    try {
      await onRerun()
    } catch (err) {
      setRerunError(err instanceof Error ? err.message : 'Rerun failed')
    } finally {
      setRerunning(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Gap Analysis</h3>
        <CommandLabel command={CMD.rerunGaps()}>
          <button
            onClick={() => void handleRerun()}
            disabled={rerunning}
            className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            {rerunning ? 'Running…' : 'Re-run'}
          </button>
        </CommandLabel>
      </div>

      {rerunError && (
        <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
          {rerunError}
        </div>
      )}

      {loading || !data ? (
        <p className="text-xs text-gray-400 italic">
          {loading ? 'Loading gap analysis…' : 'No gap analysis results yet. Click Re-run to generate.'}
        </p>
      ) : (
        <>
          {data.runAt && (
            <p className="text-xs text-gray-400">Last run: {new Date(data.runAt).toLocaleString()}</p>
          )}
          <LayerSection label="L1 — Code Coverage (Implements: tags)" layer={data.l1} />
          <LayerSection label="L2 — Spec Key Coverage" layer={data.l2} />
          <LayerSection label="L3 — Telemetry (Advisory)" layer={data.l3} />
        </>
      )}
    </div>
  )
}
