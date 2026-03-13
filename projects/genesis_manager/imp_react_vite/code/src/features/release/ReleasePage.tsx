// Implements: REQ-F-REL-001, REQ-F-REL-002, REQ-F-REL-003

import React, { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import { ConfirmActionDialog } from '../../components/shared/ConfirmActionDialog'
import type { ReleaseReadiness, ReleaseScopeItem, ReleaseResult } from '../../api/types'

// ---------------------------------------------------------------------------
// Readiness section
// ---------------------------------------------------------------------------

function ReadinessSection({
  readiness,
}: {
  readiness: ReleaseReadiness | null
}): React.JSX.Element {
  if (!readiness) {
    return (
      <div className="text-sm text-muted-foreground/60 italic">Loading readiness…</div>
    )
  }

  const isReady = readiness.verdict === 'ready'

  return (
    <div>
      {/* Verdict badge */}
      <div className="flex items-center gap-3 mb-4">
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${
            isReady
              ? 'bg-green-900/40 text-green-400 border border-green-700'
              : 'bg-red-900/40 text-red-400 border border-red-700'
          }`}
        >
          <span>{isReady ? '✓' : '✗'}</span>
          {isReady ? 'Ready to Release' : 'Not Ready'}
        </span>
      </div>

      {/* Conditions checklist */}
      <div className="space-y-2">
        {readiness.conditions.map((condition) => (
          <div
            key={condition.id}
            className="flex items-center gap-3 px-3 py-2 rounded bg-background/50 border border-border"
          >
            <span
              className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                condition.passed
                  ? 'bg-green-900/40 text-green-400'
                  : 'bg-red-900/40 text-red-400'
              }`}
            >
              {condition.passed ? '✓' : '✗'}
            </span>
            <span
              className={`text-sm flex-1 ${
                condition.passed ? 'text-foreground' : 'text-red-400'
              }`}
            >
              {condition.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Scope table
// ---------------------------------------------------------------------------

function ScopeTable({
  scope,
}: {
  scope: ReleaseScopeItem[] | null
}): React.JSX.Element {
  if (!scope) {
    return (
      <div className="text-sm text-muted-foreground/60 italic">Loading scope…</div>
    )
  }

  if (scope.length === 0) {
    return (
      <div className="text-sm text-muted-foreground/60 italic">No features found.</div>
    )
  }

  const converged = scope.filter((f) => f.status === 'converged')
  const inProgress = scope.filter((f) => f.status === 'in_progress')

  return (
    <div className="space-y-4">
      {converged.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-2">
            Converged — Eligible for Release ({converged.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Feature</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Title</th>
                  <th className="text-right py-2 px-3 text-muted-foreground font-medium">Coverage</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Converged Edges</th>
                </tr>
              </thead>
              <tbody>
                {converged.map((item) => (
                  <tr key={item.featureId} className="border-b border-border/40 hover:bg-muted/20">
                    <td className="py-2 px-3 font-mono text-foreground/80">{item.featureId}</td>
                    <td className="py-2 px-3 text-foreground">{item.title}</td>
                    <td className="py-2 px-3 text-right">
                      <span className="text-green-400 font-medium">{item.coveragePct}%</span>
                    </td>
                    <td className="py-2 px-3 text-muted-foreground">
                      {item.convergedEdges.length > 0
                        ? item.convergedEdges.join(', ')
                        : <span className="italic text-muted-foreground/40">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {inProgress.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-2">
            In Progress — Not Eligible ({inProgress.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Feature</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Title</th>
                  <th className="text-right py-2 px-3 text-muted-foreground font-medium">Progress</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Pending Edges</th>
                </tr>
              </thead>
              <tbody>
                {inProgress.map((item) => (
                  <tr key={item.featureId} className="border-b border-border/40 hover:bg-muted/20">
                    <td className="py-2 px-3 font-mono text-foreground/80">{item.featureId}</td>
                    <td className="py-2 px-3 text-foreground">{item.title}</td>
                    <td className="py-2 px-3 text-right">
                      <span className="text-orange-400 font-medium">{item.coveragePct}%</span>
                    </td>
                    <td className="py-2 px-3 text-muted-foreground">
                      {item.pendingEdges.length > 0
                        ? item.pendingEdges.join(', ')
                        : <span className="italic text-muted-foreground/40">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// ReleasePage
// ---------------------------------------------------------------------------

export function ReleasePage(): React.JSX.Element {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const id = workspaceId ?? ''

  const setActiveProject = useProjectStore((s) => s.setActiveProject)
  const overview = useWorkspaceStore((s) => s.overview)

  const [readiness, setReadiness] = useState<ReleaseReadiness | null>(null)
  const [scope, setScope] = useState<ReleaseScopeItem[] | null>(null)
  const [suggestedVersion, setSuggestedVersion] = useState<string>('1.0.0')
  const [loadError, setLoadError] = useState<string | null>(null)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [releaseResult, setReleaseResult] = useState<ReleaseResult | null>(null)

  const projectName = overview?.projectName ?? ''

  const loadData = useCallback(async () => {
    if (!id) return
    setLoadError(null)
    try {
      const [readinessData, scopeData, version] = await Promise.all([
        apiClient.getReleaseReadiness(id),
        apiClient.getReleaseScope(id),
        apiClient.suggestNextVersion(id),
      ])
      setReadiness(readinessData)
      setScope(scopeData)
      setSuggestedVersion(version)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load release data')
    }
  }, [id])

  useEffect(() => {
    if (id) {
      setActiveProject(id)
      void loadData()
    }
  }, [id, setActiveProject, loadData])

  const handleInitiateRelease = useCallback(async () => {
    const result = await apiClient.initiateRelease(id, suggestedVersion)
    setReleaseResult(result)
    setDialogOpen(false)
    // Reload readiness after release
    void loadData()
  }, [id, suggestedVersion, loadData])

  const isReady = readiness?.verdict === 'ready'
  const convergedCount = scope?.filter((f) => f.status === 'converged').length ?? 0

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      {/* Sidebar nav */}
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      {/* Main content column */}
      <div className="flex-1 overflow-y-auto flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-4 h-12 flex items-center justify-between">
          <span className="font-semibold text-foreground">Release Management</span>
          <button
            onClick={() => void loadData()}
            className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded hover:bg-muted/50 transition-colors"
          >
            Refresh
          </button>
        </header>

        {/* Body */}
        <div className="flex-1 p-6 space-y-6">
          {loadError && (
            <div className="rounded bg-red-950/20 border border-red-700 px-4 py-3 text-sm text-red-400">
              {loadError}
            </div>
          )}

          {/* Release result banner */}
          {releaseResult && (
            <div className="rounded bg-green-900/30 border border-green-700 px-4 py-3">
              <p className="text-sm font-semibold text-green-400">
                Release {releaseResult.version} created successfully
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {releaseResult.featuresIncluded} feature{releaseResult.featuresIncluded !== 1 ? 's' : ''} included
                &nbsp;·&nbsp;
                {new Date(releaseResult.timestamp).toLocaleString()}
              </p>
            </div>
          )}

          {/* Readiness section — REQ-F-REL-001 */}
          <section className="bg-secondary rounded-lg border border-border p-4">
            <h2 className="text-sm font-semibold text-foreground mb-4">
              Ship / No-Ship Readiness
            </h2>
            <ReadinessSection readiness={readiness} />

            {/* Initiate Release button — REQ-F-REL-003 */}
            <div className="mt-5 flex items-center gap-3">
              <button
                disabled={!isReady}
                onClick={() => setDialogOpen(true)}
                className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                  isReady
                    ? 'bg-green-700 text-white hover:bg-green-600'
                    : 'bg-muted text-muted-foreground cursor-not-allowed opacity-50'
                }`}
              >
                Initiate Release
              </button>
              {!isReady && (
                <span className="text-xs text-muted-foreground/60">
                  All readiness conditions must pass before initiating a release.
                </span>
              )}
              {isReady && (
                <span className="text-xs text-muted-foreground/60">
                  Will create release {suggestedVersion} with {convergedCount} converged feature{convergedCount !== 1 ? 's' : ''}.
                </span>
              )}
            </div>
          </section>

          {/* Release scope section — REQ-F-REL-002 */}
          <section className="bg-secondary rounded-lg border border-border p-4">
            <h2 className="text-sm font-semibold text-foreground mb-4">
              Release Scope
            </h2>
            <ScopeTable scope={scope} />
          </section>
        </div>
      </div>

      {/* Confirmation dialog — REQ-F-REL-003 */}
      <ConfirmActionDialog
        open={dialogOpen}
        title={`Initiate Release ${suggestedVersion}`}
        description={`This will append a release_created event to events.jsonl and mark version ${suggestedVersion} as released.`}
        command={`gen-release --version ${suggestedVersion}`}
        warningMessage={
          convergedCount > 0
            ? `${convergedCount} converged feature${convergedCount !== 1 ? 's' : ''} will be included in this release.`
            : undefined
        }
        onConfirm={handleInitiateRelease}
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  )
}
