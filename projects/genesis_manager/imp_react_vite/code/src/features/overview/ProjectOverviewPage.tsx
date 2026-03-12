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

  const { statusCounts, inProgressFeatures, recentActivity, featureLastEvents, projectName, methodVersion } = overview

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
            {isChanged(recentActivity?.featureId ?? '', featureLastEvents[recentActivity?.featureId ?? '']) && (
              <button
                onClick={dismissChanges}
                className="text-xs text-muted-foreground hover:text-foreground/80 border border-border rounded px-2 py-1"
              >
                Dismiss changes
              </button>
            )}
          </div>
        </header>

        {/* Row 2 — Status counts bar */}
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
                    <th className="pb-1 pr-3 font-medium">Edge</th>
                    <th className="pb-1 pr-3 font-medium text-right">Iter</th>
                    <th className="pb-1 pr-3 font-medium text-right">δ</th>
                    <th className="pb-1 font-medium">Changed</th>
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
                        <td className="py-1.5 pr-3 text-xs text-muted-foreground">{f.currentEdge}</td>
                        <td className="py-1.5 pr-3 text-xs text-right">{f.iterationNumber}</td>
                        <td className="py-1.5 pr-3 text-xs text-right font-mono">{f.delta}</td>
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

        {/* Right: Recent activity */}
        <div className="p-4">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Recent Activity</h2>
          {recentActivity ? (
            <div className="rounded-lg border border-border bg-secondary p-4">
              <div className="flex items-center gap-2 mb-2">
                <button
                  onClick={() => navigate(buildFeaturePath(workspaceId, recentActivity.featureId))}
                  className="font-mono text-sm text-primary hover:underline"
                >
                  {recentActivity.featureId}
                </button>
                <span className="text-muted-foreground/60">→</span>
                <span className="text-sm text-foreground/80">{recentActivity.edge}</span>
                <span className="text-xs text-muted-foreground/60">#{recentActivity.iterationNumber}</span>
              </div>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>δ = {recentActivity.delta}</div>
                <div>{new Date(recentActivity.timestamp).toLocaleString()}</div>
                {recentActivity.runId && (
                  <div className="font-mono text-muted-foreground/60 truncate">Run: {recentActivity.runId}</div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground/60 italic">No activity yet.</p>
          )}
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
