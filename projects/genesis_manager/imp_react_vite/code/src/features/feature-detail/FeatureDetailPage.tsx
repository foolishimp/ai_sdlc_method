// Implements: REQ-F-NAV-003, REQ-F-VIS-001

import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import { buildOverviewPath } from '../../routing/routes'
import type {
  FeatureDetail,
  FeatureEdgeStatus,
  IterationSummary,
  ArtifactContent,
} from '../../api/types'

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }): React.JSX.Element {
  const colours: Record<string, string> = {
    converged:   'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
    in_progress: 'bg-blue-900/30 text-blue-400 border border-blue-800/40',
    iterating:   'bg-blue-900/30 text-blue-400 border border-blue-800/40',
    blocked:     'bg-red-900/30 text-red-400 border border-red-800/40',
    pending:     'bg-muted/40 text-muted-foreground border border-border',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colours[status] ?? 'bg-muted/40 text-muted-foreground border border-border'}`}>
      {status}
    </span>
  )
}

// ─── Artifact viewer ──────────────────────────────────────────────────────────

function ArtifactViewer({
  workspaceId,
  artifactPath,
  onClose,
}: {
  workspaceId: string
  artifactPath: string
  onClose: () => void
}): React.JSX.Element {
  const [artifact, setArtifact] = useState<ArtifactContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiClient
      .getArtifact(workspaceId, artifactPath)
      .then(setArtifact)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Failed to load artifact'))
      .finally(() => setLoading(false))
  }, [workspaceId, artifactPath])

  return (
    <div className="flex flex-col h-full">
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b bg-secondary">
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-foreground/80 truncate max-w-xs" title={artifactPath}>
            {artifactPath.split('/').pop()}
          </span>
          <span className="text-[10px] text-muted-foreground/60 truncate max-w-xs">{artifactPath}</span>
        </div>
        <button onClick={onClose} className="text-xs text-muted-foreground hover:text-foreground ml-4">✕</button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {loading && <p className="text-sm text-muted-foreground/60">Loading…</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {artifact && (
          <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap break-words leading-relaxed">
            {artifact.content}
          </pre>
        )}
      </div>
      {artifact && (
        <div className="flex-shrink-0 border-t px-4 py-1 text-[10px] text-muted-foreground/50">
          {artifact.extension.toUpperCase()} · {(artifact.sizeBytes / 1024).toFixed(1)} KB
        </div>
      )}
    </div>
  )
}

// ─── Iteration table ──────────────────────────────────────────────────────────

function IterationTable({ iterations }: { iterations: IterationSummary[] }): React.JSX.Element {
  if (iterations.length === 0) return <></>
  return (
    <table className="w-full text-xs mt-2">
      <thead>
        <tr className="text-left text-muted-foreground/60 border-b border-border/50">
          <th className="pb-1 pr-3 font-medium">#</th>
          <th className="pb-1 pr-3 font-medium text-right">δ</th>
          <th className="pb-1 pr-3 font-medium text-right">Pass</th>
          <th className="pb-1 pr-3 font-medium text-right">Fail</th>
          <th className="pb-1 pr-3 font-medium text-right">Skip</th>
          <th className="pb-1 font-medium">Time</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border/30">
        {iterations.map((it) => (
          <tr key={it.iteration} className={it.status === 'converged' ? 'text-emerald-400/80' : 'text-foreground/60'}>
            <td className="py-1 pr-3 font-mono">{it.iteration}</td>
            <td className={`py-1 pr-3 text-right font-mono font-semibold ${
              it.delta === 0 ? 'text-emerald-400' : it.delta != null ? 'text-amber-400' : ''
            }`}>
              {it.delta ?? '—'}
            </td>
            <td className="py-1 pr-3 text-right text-emerald-400">{it.evaluatorsPassed || '—'}</td>
            <td className={`py-1 pr-3 text-right ${it.evaluatorsFailed > 0 ? 'text-red-400' : 'text-muted-foreground/40'}`}>
              {it.evaluatorsFailed || '—'}
            </td>
            <td className="py-1 pr-3 text-right text-muted-foreground/50">{it.evaluatorsSkipped || '—'}</td>
            <td className="py-1 text-muted-foreground/50">{new Date(it.timestamp).toLocaleTimeString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ─── Edge card ────────────────────────────────────────────────────────────────

function EdgeCard({
  edge,
  onOpenArtifact,
}: {
  edge: FeatureEdgeStatus
  onOpenArtifact: (path: string) => void
}): React.JSX.Element {
  const [expanded, setExpanded] = useState(edge.status !== 'converged')

  const statusDot =
    edge.status === 'converged'
      ? 'bg-emerald-500'
      : edge.status === 'pending'
      ? 'bg-muted-foreground/30'
      : 'bg-blue-500 animate-pulse'

  return (
    <div className={`rounded-lg border ${
      edge.status === 'converged' ? 'border-emerald-800/30 bg-emerald-950/10'
      : edge.status === 'pending' ? 'border-border/40 bg-background/40 opacity-60'
      : 'border-blue-800/40 bg-blue-950/10'
    }`}>
      {/* Card header */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${statusDot}`} />
        <span className="font-mono text-sm font-medium text-foreground/90 flex-1">{edge.edge}</span>
        {edge.iterationCount > 0 && (
          <span className="text-xs text-muted-foreground/60">{edge.iterationCount} iter</span>
        )}
        {edge.delta != null && (
          <span className={`text-xs font-mono font-semibold ${edge.delta === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            δ={edge.delta}
          </span>
        )}
        <StatusBadge status={edge.status} />
        <span className="text-muted-foreground/40 ml-1">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 flex flex-col gap-3 border-t border-border/30 pt-3">
          {/* Meta row */}
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            {edge.convergedAt && (
              <span>Converged: <span className="text-foreground/70">{new Date(edge.convergedAt).toLocaleString()}</span></span>
            )}
          </div>

          {/* Produced asset */}
          {edge.producedAsset && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Asset:</span>
              <button
                onClick={() => onOpenArtifact(edge.producedAsset!)}
                className="font-mono text-xs text-primary hover:underline truncate max-w-md text-left"
                title={edge.producedAsset}
              >
                {edge.producedAsset}
              </button>
            </div>
          )}

          {/* Per-iteration breakdown */}
          {edge.iterations.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground/60 mb-1 uppercase tracking-wide font-medium">Iterations</p>
              <IterationTable iterations={edge.iterations} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function FeatureDetailPage(): React.JSX.Element {
  const { workspaceId, featureId } = useParams<{ workspaceId: string; featureId: string }>()
  const navigate = useNavigate()
  const setActiveProject = useProjectStore((s) => s.setActiveProject)

  const id = workspaceId ?? ''
  const fid = featureId ?? ''

  const [detail, setDetail] = useState<FeatureDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openArtifact, setOpenArtifact] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!id || !fid) return
    setActiveProject(id)
    setLoading(true)
    apiClient
      .getFeatureDetail(id, fid)
      .then((d) => { setDetail(d); setError(null) })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Failed to load feature'))
      .finally(() => setLoading(false))
  }, [id, fid, setActiveProject])

  useEffect(() => { load() }, [load])

  const projectName = detail?.featureId?.split('-')[0] ?? 'Project'

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-5 h-14 flex items-center gap-3">
          <button
            onClick={() => navigate(buildOverviewPath(id))}
            className="text-xs text-muted-foreground hover:text-foreground flex-shrink-0"
          >
            ← Overview
          </button>
          <span className="text-muted-foreground/40">/</span>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted-foreground/70">{fid}</span>
              {detail && <StatusBadge status={detail.status} />}
            </div>
            {detail?.title && (
              <span className="text-sm font-semibold text-foreground truncate">{detail.title}</span>
            )}
          </div>
        </header>

        {/* Body — left: trajectory, right: artifact viewer */}
        <div className="flex-1 overflow-hidden flex divide-x divide-border">

          {/* Left: description + edge trajectory */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {loading && <p className="text-sm text-muted-foreground/60">Loading feature…</p>}
            {error && (
              <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded p-3">{error}</div>
            )}

            {detail && (
              <>
                {/* Description */}
                {detail.description && (
                  <section className="bg-secondary/40 rounded-lg px-4 py-3 border border-border/40">
                    <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">{detail.description}</p>
                    <div className="flex flex-wrap gap-3 mt-2 text-xs text-muted-foreground">
                      {detail.intent && <span>Intent: <span className="font-mono">{detail.intent}</span></span>}
                      {detail.profile && <span>Profile: <span className="font-mono">{detail.profile}</span></span>}
                      {detail.vectorType && <span>Type: <span className="font-mono">{detail.vectorType}</span></span>}
                    </div>
                  </section>
                )}

                {/* Requirements covered */}
                {detail.satisfies.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {detail.satisfies.map((req) => (
                      <span key={req} className="font-mono text-xs bg-muted/50 text-foreground/70 px-2 py-0.5 rounded border border-border/50">
                        {req}
                      </span>
                    ))}
                  </div>
                )}

                {/* Active edge / delta */}
                {(detail.currentEdge || detail.currentDelta != null) && (
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    {detail.currentEdge && (
                      <span>Active: <span className="font-mono text-foreground/80">{detail.currentEdge}</span></span>
                    )}
                    {detail.currentDelta != null && (
                      <span>δ = <span className={`font-mono font-semibold ${detail.currentDelta === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>{detail.currentDelta}</span></span>
                    )}
                  </div>
                )}

                {/* Edge trajectory cards */}
                <section>
                  <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Edge trajectory</h2>
                  <div className="flex flex-col gap-2">
                    {detail.edges.map((e) => (
                      <EdgeCard key={e.edge} edge={e} onOpenArtifact={setOpenArtifact} />
                    ))}
                  </div>
                </section>

                {/* Child vectors */}
                {detail.childVectors.length > 0 && (
                  <section>
                    <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Child vectors</h2>
                    <div className="flex flex-col gap-1">
                      {detail.childVectors.map((child) => (
                        <span key={child} className="font-mono text-xs text-foreground/60">{child}</span>
                      ))}
                    </div>
                  </section>
                )}
              </>
            )}
          </div>

          {/* Right: artifact viewer */}
          <div className="w-80 flex-shrink-0 overflow-hidden flex flex-col">
            {openArtifact ? (
              <ArtifactViewer
                workspaceId={id}
                artifactPath={openArtifact}
                onClose={() => setOpenArtifact(null)}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <p className="text-xs text-muted-foreground/40 text-center px-4">Click an asset link<br/>to view its content</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
