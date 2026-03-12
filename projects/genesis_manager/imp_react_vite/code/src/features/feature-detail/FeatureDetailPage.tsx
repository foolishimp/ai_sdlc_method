// Implements: REQ-F-NAV-003, REQ-F-VIS-001

import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import { buildOverviewPath } from '../../routing/routes'
import type { FeatureDetail, FeatureEdgeStatus, FeatureEventSummary } from '../../api/types'

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }): React.JSX.Element {
  const colours: Record<string, string> = {
    converged: 'bg-emerald-900/30 text-emerald-400',
    in_progress: 'bg-blue-900/30 text-blue-400',
    iterating: 'bg-blue-900/30 text-blue-400',
    blocked: 'bg-red-900/30 text-red-400',
    pending: 'bg-muted text-muted-foreground',
  }
  const cls = colours[status] ?? 'bg-muted text-muted-foreground'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>
      {status}
    </span>
  )
}

// ─── Edge status icon ─────────────────────────────────────────────────────────

function EdgeIcon({ status }: { status: string }): React.JSX.Element {
  if (status === 'converged') return <span className="text-green-600 font-bold">✓</span>
  if (status === 'in_progress' || status === 'iterating') return <span className="text-blue-500">●</span>
  if (status === 'blocked') return <span className="text-red-500">✗</span>
  return <span className="text-muted-foreground/40">○</span>
}

// ─── Edge trajectory table ────────────────────────────────────────────────────

function EdgeTrajectoryTable({ edges }: { edges: FeatureEdgeStatus[] }): React.JSX.Element {
  if (edges.length === 0) {
    return <p className="text-sm text-muted-foreground/60 italic">No trajectory data.</p>
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-muted-foreground border-b">
          <th className="pb-1 pr-3 font-medium w-6"></th>
          <th className="pb-1 pr-3 font-medium">Edge</th>
          <th className="pb-1 pr-3 font-medium text-right">Iter</th>
          <th className="pb-1 pr-3 font-medium text-right">δ</th>
          <th className="pb-1 pr-3 font-medium">Converged</th>
          <th className="pb-1 font-medium">Asset</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border/50">
        {edges.map((e) => (
          <tr key={e.edge} className="hover:bg-muted/30">
            <td className="py-1.5 pr-3 text-center">
              <EdgeIcon status={e.status} />
            </td>
            <td className="py-1.5 pr-3 font-mono text-xs">{e.edge}</td>
            <td className="py-1.5 pr-3 text-xs text-right">{e.iterationCount}</td>
            <td className="py-1.5 pr-3 text-xs text-right font-mono">
              {e.delta !== null ? e.delta : '—'}
            </td>
            <td className="py-1.5 pr-3 text-xs text-muted-foreground">
              {e.convergedAt ? new Date(e.convergedAt).toLocaleString() : '—'}
            </td>
            <td className="py-1.5 text-xs text-muted-foreground truncate max-w-xs" title={e.producedAsset ?? ''}>
              {e.producedAsset ?? '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ─── Event list ───────────────────────────────────────────────────────────────

function EventList({ events }: { events: FeatureEventSummary[] }): React.JSX.Element {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground/60 italic">No events recorded.</p>
  }
  // Show newest first
  const sorted = [...events].reverse()
  return (
    <div className="space-y-1">
      {sorted.map((ev) => (
        <div key={ev.eventIndex} className="flex items-start gap-3 py-1.5 border-b border-border/50 text-xs">
          <span className="text-muted-foreground/50 font-mono w-8 flex-shrink-0 text-right">
            {ev.eventIndex}
          </span>
          <span className="text-muted-foreground flex-shrink-0 w-36">
            {new Date(ev.timestamp).toLocaleString()}
          </span>
          <span className="font-mono text-foreground/80 flex-shrink-0">{ev.eventType}</span>
          {ev.edge && (
            <span className="text-muted-foreground">· {ev.edge}</span>
          )}
          {ev.iteration !== null && (
            <span className="text-muted-foreground/60">#{ev.iteration}</span>
          )}
          {ev.delta !== null && (
            <span className="ml-auto text-muted-foreground font-mono">δ={ev.delta}</span>
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

// FeatureDetailPage — trajectory + event history for a single feature.
// Implements: REQ-F-NAV-003
export function FeatureDetailPage(): React.JSX.Element {
  const { workspaceId, featureId } = useParams<{ workspaceId: string; featureId: string }>()
  const navigate = useNavigate()
  const setActiveProject = useProjectStore((s) => s.setActiveProject)

  const id = workspaceId ?? ''
  const fid = featureId ?? ''

  const [detail, setDetail] = useState<FeatureDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id || !fid) return
    setActiveProject(id)
    setLoading(true)
    apiClient
      .getFeatureDetail(id, fid)
      .then((d) => {
        setDetail(d)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load feature')
      })
      .finally(() => setLoading(false))
  }, [id, fid, setActiveProject])

  const projectName = detail?.featureId?.split('-')[0] ?? 'Project'

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-5 h-12 flex items-center gap-3">
          <button
            onClick={() => navigate(buildOverviewPath(id))}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ← Overview
          </button>
          <span className="text-muted-foreground/40">/</span>
          <span className="font-mono text-sm text-foreground font-semibold">{fid}</span>
          {detail && <StatusBadge status={detail.status} />}
        </header>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {loading && (
            <div className="text-sm text-muted-foreground/60">Loading feature…</div>
          )}
          {error && (
            <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded p-3">
              {error}
            </div>
          )}
          {detail && (
            <>
              {/* Title + meta */}
              <section>
                <h1 className="text-base font-semibold text-foreground mb-1">{detail.title || fid}</h1>
                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                  {detail.currentEdge && (
                    <span>Current edge: <span className="font-mono text-foreground/80">{detail.currentEdge}</span></span>
                  )}
                  {detail.currentDelta !== null && (
                    <span>δ = <span className="font-mono">{detail.currentDelta}</span></span>
                  )}
                </div>
              </section>

              {/* Satisfies */}
              {detail.satisfies.length > 0 && (
                <section>
                  <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Satisfies
                  </h2>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.satisfies.map((req) => (
                      <span
                        key={req}
                        className="font-mono text-xs bg-muted text-foreground/80 px-2 py-0.5 rounded"
                      >
                        {req}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Children */}
              {detail.childVectors.length > 0 && (
                <section>
                  <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Child Vectors
                  </h2>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.childVectors.map((child) => (
                      <span
                        key={child}
                        className="font-mono text-xs bg-muted text-foreground/80 px-2 py-0.5 rounded"
                      >
                        {child}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Edge trajectory */}
              <section>
                <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Edge Trajectory
                </h2>
                <EdgeTrajectoryTable edges={detail.edges} />
              </section>

              {/* Events */}
              <section>
                <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Events ({detail.events.length})
                </h2>
                <EventList events={detail.events} />
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
