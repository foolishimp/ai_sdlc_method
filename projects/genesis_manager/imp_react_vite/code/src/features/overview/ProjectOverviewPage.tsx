// Implements: REQ-F-OVR-001, REQ-F-OVR-002, REQ-F-OVR-003, REQ-F-OVR-004

import React, { useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
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
import { buildSupervisionPath, buildEvidencePath, buildFeaturePath } from '../../routing/routes'

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
      <div className="flex items-center justify-center h-full text-gray-400">
        Loading workspace data…
      </div>
    )
  }

  const { statusCounts, inProgressFeatures, recentActivity, featureLastEvents, projectName, methodVersion } = overview

  return (
    // Fixed-height CSS grid — no page-level scroll (REQ-F-OVR-001 AC3)
    <div className="h-screen overflow-hidden flex flex-col bg-gray-50">
      {/* Row 1 — Header (~64px) */}
      <header className="flex-shrink-0 bg-white border-b px-6 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-gray-400 hover:text-gray-600 text-sm">← Projects</Link>
          <span className="text-gray-300">|</span>
          <h1 className="font-bold text-gray-900">{projectName}</h1>
          <span className="text-xs text-gray-400 font-mono">{methodVersion}</span>
        </div>
        <div className="flex items-center gap-3">
          <FreshnessIndicator
            lastRefreshed={lastRefreshed}
            isRefreshing={isRefreshing}
            error={pollingError}
          />
          <button
            onClick={dismissChanges}
            className="text-xs text-gray-500 hover:text-gray-700 border border-gray-200 rounded px-2 py-1"
          >
            Dismiss changes
          </button>
          <nav className="flex gap-2 text-sm">
            <button
              onClick={() => navigate(buildSupervisionPath(workspaceId))}
              className="px-3 py-1 rounded hover:bg-gray-100 text-gray-700"
            >
              Supervision
            </button>
            <button
              onClick={() => navigate(buildEvidencePath(workspaceId))}
              className="px-3 py-1 rounded hover:bg-gray-100 text-gray-700"
            >
              Evidence
            </button>
          </nav>
        </div>
      </header>

      {/* Row 2 — Status counts bar (~128px) */}
      <div className="flex-shrink-0 bg-white border-b px-6 py-4">
        <FeatureStatusCounts
          counts={statusCounts}
          onTileClick={(status) => navigate(buildSupervisionPath(workspaceId) + `?status=${status}`)}
        />
        <FeatureStatusBar counts={statusCounts} className="mt-3" />
      </div>

      {/* Row 3 — Body (remaining height) — 2 columns */}
      <div className="flex-1 overflow-hidden grid grid-cols-2 gap-0 divide-x divide-gray-200">
        {/* Left: In-progress features table */}
        <div className="flex flex-col overflow-hidden p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">In-Progress Features</h2>
          <div className="flex-1 overflow-y-auto">
            {inProgressFeatures.length === 0 ? (
              <p className="text-sm text-gray-400 italic">No features in progress.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 border-b">
                    <th className="pb-1 pr-3 font-medium">Feature</th>
                    <th className="pb-1 pr-3 font-medium">Edge</th>
                    <th className="pb-1 pr-3 font-medium text-right">Iter</th>
                    <th className="pb-1 pr-3 font-medium text-right">δ</th>
                    <th className="pb-1 font-medium">Changed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {inProgressFeatures.map((f) => {
                    const changed = isChanged(f.featureId, featureLastEvents[f.featureId])
                    return (
                      <tr
                        key={f.featureId}
                        className={`hover:bg-gray-50 ${changed ? 'border-l-2 border-blue-400' : ''}`}
                      >
                        <td className="py-1.5 pr-3">
                          <button
                            onClick={() => navigate(buildFeaturePath(workspaceId, f.featureId))}
                            className="font-mono text-xs text-blue-700 hover:underline text-left"
                          >
                            {f.featureId}
                          </button>
                        </td>
                        <td className="py-1.5 pr-3 text-xs text-gray-600">{f.currentEdge}</td>
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
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Activity</h2>
          {recentActivity ? (
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <button
                  onClick={() => navigate(buildFeaturePath(workspaceId, recentActivity.featureId))}
                  className="font-mono text-sm text-blue-700 hover:underline"
                >
                  {recentActivity.featureId}
                </button>
                <span className="text-gray-400">→</span>
                <span className="text-sm text-gray-700">{recentActivity.edge}</span>
                <span className="text-xs text-gray-400">#{recentActivity.iterationNumber}</span>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <div>δ = {recentActivity.delta}</div>
                <div>{new Date(recentActivity.timestamp).toLocaleString()}</div>
                {recentActivity.runId && (
                  <div className="font-mono text-gray-400 truncate">Run: {recentActivity.runId}</div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">No activity yet.</p>
          )}
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
