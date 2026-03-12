// Implements: REQ-F-PROJ-001, REQ-F-PROJ-002

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore, selectSortedWorkspaces } from '../../stores/projectStore'
import { FreshnessIndicator } from '../../components/shared/FreshnessIndicator'
import { ProjectCard } from './ProjectCard'
import { WorkspaceConfigDrawer } from './WorkspaceConfigDrawer'
import { buildOverviewPath } from '../../routing/routes'

// ProjectListPage — root page listing all registered workspaces.
// Sorted: attention-required first, then most recently active.
// Implements: REQ-F-PROJ-001, REQ-F-PROJ-002
export function ProjectListPage(): React.JSX.Element {
  const navigate = useNavigate()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const workspaceSummaries = useProjectStore((s) => s.workspaceSummaries)
  const activeProjectId = useProjectStore((s) => s.activeProjectId)
  const setActiveProject = useProjectStore((s) => s.setActiveProject)
  const lastRefreshed = useProjectStore((s) => s.lastRefreshed)
  const pollingError = useProjectStore((s) => s.pollingError)
  const isRefreshing = useProjectStore((s) => s.isRefreshing)

  const sorted = selectSortedWorkspaces(workspaceSummaries)

  const handleSelect = (id: string) => {
    setActiveProject(id)
    navigate(buildOverviewPath(id))
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-secondary border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">Genesis Manager</h1>
          <p className="text-xs text-muted-foreground">Local workspace dashboard</p>
        </div>
        <div className="flex items-center gap-3">
          <FreshnessIndicator
            lastRefreshed={lastRefreshed}
            isRefreshing={isRefreshing}
            error={pollingError}
          />
          <button
            onClick={() => setDrawerOpen(true)}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + Add workspace
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-6 py-8">
        {sorted.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-muted-foreground/60 text-lg mb-2">No workspaces registered</p>
            <p className="text-muted-foreground/60 text-sm mb-6">
              Add a Genesis workspace to get started.
            </p>
            <button
              onClick={() => setDrawerOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Add workspace
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              {sorted.length} workspace{sorted.length !== 1 ? 's' : ''}
            </h2>
            {sorted.map((summary) => (
              <ProjectCard
                key={summary.workspaceId}
                summary={summary}
                isActive={summary.workspaceId === activeProjectId}
                onSelect={handleSelect}
              />
            ))}
          </div>
        )}
      </main>

      <WorkspaceConfigDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  )
}
