// Implements: REQ-F-OVR-001, REQ-F-OVR-002, REQ-F-OVR-003, REQ-F-OVR-004

import React, { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { FreshnessIndicator } from '../../components/shared/FreshnessIndicator'
import { FeatureStatusCounts } from './FeatureStatusCounts'
import { FeatureStatusBar } from './FeatureStatusBar'
import {
  ChangeHighlighterProvider,
  useChangeHighlighter,
  ChangeBadge,
} from './ChangeHighlighter'
import { buildSupervisionPath, buildFeaturePath } from '../../routing/routes'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import type { PendingGateSummary, BlockedFeatureSummary } from '../../api/types'

// ─── Attention panel ─────────────────────────────────────────────────────────

function AttentionPanel({
  workspaceId,
  pendingGates,
  blockedFeatures,
}: {
  workspaceId: string
  pendingGates: PendingGateSummary[]
  blockedFeatures: BlockedFeatureSummary[]
}): React.JSX.Element {
  const navigate = useNavigate()
  const hasAnything = pendingGates.length > 0 || blockedFeatures.length > 0

  if (!hasAnything) {
    return (
      <p className="text-xs text-muted-foreground/40 italic mt-2">No pending gates or blocked features.</p>
    )
  }

  return (
    <div className="space-y-3">
      {pendingGates.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-2">
            ⚑ Pending Gates ({pendingGates.length})
          </h3>
          <div className="space-y-2">
            {pendingGates.map((g) => {
              const ageMs = Date.now() - new Date(g.requestedAt).getTime()
              const ageH = Math.floor(ageMs / 3_600_000)
              const ageLabel = ageH < 1 ? '<1h ago' : `${ageH}h ago`
              return (
                <div key={g.id} className="rounded border border-orange-800/40 bg-orange-900/10 px-3 py-2 text-xs">
                  <button
                    onClick={() => navigate(buildFeaturePath(workspaceId, g.feature))}
                    className="font-mono text-primary hover:underline block"
                  >
                    {g.feature}
                  </button>
                  <div className="text-muted-foreground mt-0.5">{g.edge} · {ageLabel}</div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {blockedFeatures.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">
            ⊘ Blocked ({blockedFeatures.length})
          </h3>
          <div className="space-y-2">
            {blockedFeatures.map((b) => (
              <div key={b.featureId} className="rounded border border-red-800/40 bg-red-900/10 px-3 py-2 text-xs">
                <button
                  onClick={() => navigate(buildFeaturePath(workspaceId, b.featureId))}
                  className="font-mono text-primary hover:underline block"
                >
                  {b.featureId}
                </button>
                <div className="text-muted-foreground mt-0.5 truncate">{b.title}</div>
                {b.reason && <div className="text-muted-foreground/60 mt-0.5 truncate">{b.reason}</div>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

// ─── Inner content (needs ChangeHighlighter context) ─────────────────────────

function OverviewContent({ workspaceId }: { workspaceId: string }): React.JSX.Element {
  const navigate = useNavigate()
  const overview = useWorkspaceStore((s) => s.overview)
  const { isChanged, dismissChanges } = useChangeHighlighter()
  const lastRefreshed = useProjectStore((s) => s.lastRefreshed)
  const pollingError = useProjectStore((s) => s.pollingError)
  const isRefreshing = useProjectStore((s) => s.isRefreshing)

  if (!overview) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground/60">
        Loading workspace data…
      </div>
    )
  }

  const {
    statusCounts,
    inProgressFeatures,
    recentActivities,
    featureLastEvents,
    projectName,
    methodVersion,
    pendingGates,
    blockedFeatures,
  } = overview

  // Dismiss is visible when ANY tracked feature has changed (REQ-F-OVR-004 fix)
  const anyChanged = Object.entries(featureLastEvents).some(([fid, ts]) => isChanged(fid, ts))

  return (
    // Fixed-height CSS grid — no page-level scroll (REQ-F-OVR-001 AC3)
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      {/* Sidebar nav */}
      <WorkspaceSidebar workspaceId={workspaceId} projectName={projectName} />

      {/* Main content column */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Row 1 — Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-5 h-12 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h1 className="font-semibold text-foreground">{projectName}</h1>
            <span className="text-xs text-muted-foreground/60 font-mono bg-muted px-1.5 py-0.5 rounded">{methodVersion}</span>
          </div>
          <div className="flex items-center gap-3">
            <FreshnessIndicator
              lastRefreshed={lastRefreshed}
              isRefreshing={isRefreshing}
              error={pollingError}
            />
            {anyChanged && (
              <button
                onClick={dismissChanges}
                className="text-xs text-muted-foreground hover:text-foreground/80 border border-border rounded px-2 py-1"
              >
                Dismiss changes
              </button>
            )}
          </div>
        </header>

        {/* Row 2 — Status counts bar (4 tiles only — converged/in_progress/blocked/pending) */}
        <div className="flex-shrink-0 bg-secondary border-b px-5 py-3">
          <FeatureStatusCounts
            counts={statusCounts}
            onTileClick={(status) => navigate(buildSupervisionPath(workspaceId) + `?status=${status}`)}
          />
          <FeatureStatusBar counts={statusCounts} className="mt-2" />
        </div>

        {/* Row 3 — Body (remaining height) — 2 columns */}
        <div className="flex-1 overflow-hidden grid grid-cols-2 gap-0 divide-x divide-border">

          {/* Left: In-progress features table */}
          <div className="flex flex-col overflow-hidden p-4">
            <h2 className="text-sm font-semibold text-foreground/80 mb-3">In-Progress Features</h2>
            <div className="flex-1 overflow-y-auto">
              {inProgressFeatures.length === 0 ? (
                <p className="text-sm text-muted-foreground/60 italic">No features in progress.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted-foreground border-b">
                      <th className="pb-1 pr-3 font-medium">Feature</th>
                      <th className="pb-1 pr-3 font-medium">Title</th>
                      <th className="pb-1 pr-3 font-medium">Edge</th>
                      <th className="pb-1 pr-3 font-medium text-right">Iter</th>
                      <th className="pb-1 pr-3 font-medium text-right">δ</th>
                      <th className="pb-1 font-medium">●</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {inProgressFeatures.map((f) => {
                      const changed = isChanged(f.featureId, featureLastEvents[f.featureId])
                      return (
                        <tr
                          key={f.featureId}
                          className={`hover:bg-background ${changed ? 'border-l-2 border-blue-400' : ''}`}
                        >
                          <td className="py-1.5 pr-3">
                            <button
                              onClick={() => navigate(buildFeaturePath(workspaceId, f.featureId))}
                              className="font-mono text-xs text-primary hover:underline text-left"
                            >
                              {f.featureId}
                            </button>
                          </td>
                          <td className="py-1.5 pr-3 text-xs text-foreground/70 max-w-[14rem] truncate">{f.title}</td>
                          <td className="py-1.5 pr-3 text-xs text-muted-foreground">{f.currentEdge}</td>
                          <td className="py-1.5 pr-3 text-xs text-right">{f.iterationNumber}</td>
                          <td className={`py-1.5 pr-3 text-xs text-right font-mono ${f.delta === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {f.delta}
                          </td>
                          <td className="py-1.5">
                            {changed && <ChangeBadge />}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Right column: Attention panel + Recent Activity */}
          <div className="flex flex-col overflow-hidden divide-y divide-border">

            {/* Attention panel */}
            <div className="flex-1 overflow-y-auto p-4">
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Attention
                {(pendingGates.length > 0 || blockedFeatures.length > 0) && (
                  <span className="ml-2 text-orange-400 font-bold">
                    {pendingGates.length + blockedFeatures.length}
                  </span>
                )}
              </h2>
              <AttentionPanel
                workspaceId={workspaceId}
                pendingGates={pendingGates ?? []}
                blockedFeatures={blockedFeatures ?? []}
              />
            </div>

            {/* Recent activity list — last 5 */}
            <div className="flex-shrink-0 p-4 max-h-56 overflow-y-auto">
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Recent Activity</h2>
              {recentActivities.length === 0 ? (
                <p className="text-xs text-muted-foreground/60 italic">No activity yet.</p>
              ) : (
                <div className="space-y-1.5">
                  {recentActivities.map((a, i) => (
                    <div key={i} className="rounded border border-border bg-secondary px-3 py-2 text-xs">
                      <div className="flex items-baseline gap-2 mb-0.5">
                        <button
                          onClick={() => navigate(buildFeaturePath(workspaceId, a.featureId))}
                          className="font-mono text-primary hover:underline flex-shrink-0"
                        >
                          {a.featureId}
                        </button>
                        {a.title && (
                          <span className="text-foreground/70 truncate">{a.title}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span className="text-foreground/80">{a.edge}</span>
                        <span className="text-muted-foreground/60">#{a.iterationNumber}</span>
                        <span className={a.delta === 0 ? 'text-emerald-400' : 'text-amber-400'}>δ={a.delta}</span>
                        <span className="ml-auto text-muted-foreground/50">{new Date(a.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

// ProjectOverviewPage — fixed-height layout, no vertical scroll.
// Implements: REQ-F-OVR-001, REQ-F-OVR-004
export function ProjectOverviewPage(): React.JSX.Element {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const loadWorkspace = useWorkspaceStore((s) => s.loadWorkspace)
  const setActiveProject = useProjectStore((s) => s.setActiveProject)

  const id = workspaceId ?? ''

  useEffect(() => {
    if (id) {
      setActiveProject(id)
      void loadWorkspace(id)
    }
  }, [id, loadWorkspace, setActiveProject])

  return (
    <ChangeHighlighterProvider>
      <OverviewContent workspaceId={id} />
    </ChangeHighlighterProvider>
  )
}
