// Implements: REQ-F-VIS-001, REQ-F-NAV-001
// Persistent sidebar navigation for workspace-level pages.
// Shows workspace name, active-section indicator, and nav links.

import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { buildOverviewPath, buildSupervisionPath, buildEvidencePath } from '../../routing/routes'

interface WorkspaceSidebarProps {
  workspaceId: string
  projectName: string
}

function NavItem({
  to,
  label,
  icon,
  active,
}: {
  to: string
  label: string
  icon: React.ReactNode
  active: boolean
}): React.JSX.Element {
  return (
    <Link
      to={to}
      className={`flex flex-col items-center gap-1 px-2 py-3 rounded-lg text-xs transition-colors ${
        active
          ? 'bg-primary/15 text-primary'
          : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
      }`}
    >
      <span className="text-base leading-none">{icon}</span>
      <span className="leading-none">{label}</span>
    </Link>
  )
}

export function WorkspaceSidebar({ workspaceId, projectName }: WorkspaceSidebarProps): React.JSX.Element {
  const { pathname } = useLocation()

  const isOverview = pathname.includes('/overview')
  const isSupervision = pathname.includes('/supervision')
  const isEvidence = pathname.includes('/evidence')

  return (
    <aside className="flex-shrink-0 w-16 bg-secondary border-r border-border flex flex-col items-center py-3 gap-1">
      {/* Back to projects */}
      <Link
        to="/"
        className="flex flex-col items-center gap-1 px-2 py-2 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors mb-2"
        title="All projects"
      >
        <span className="text-base leading-none">⌂</span>
        <span className="leading-none">Home</span>
      </Link>

      <div className="w-8 h-px bg-border mb-1" />

      {/* Workspace badge — links to project overview (project home) */}
      <Link
        to={buildOverviewPath(workspaceId)}
        title={`${projectName} — Overview`}
        className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold mb-1 transition-colors ${
          isOverview
            ? 'bg-primary text-primary-foreground ring-2 ring-primary/50'
            : 'bg-primary/20 text-primary hover:bg-primary/30'
        }`}
      >
        {projectName.slice(0, 2).toUpperCase()}
      </Link>
      {/* Project name label under badge */}
      <span className="text-[10px] text-muted-foreground/60 leading-none max-w-[56px] truncate text-center mb-2">
        {projectName}
      </span>

      <NavItem
        to={buildSupervisionPath(workspaceId)}
        label="Supervise"
        icon="⊙"
        active={isSupervision}
      />
      <NavItem
        to={buildEvidencePath(workspaceId)}
        label="Evidence"
        icon="≡"
        active={isEvidence}
      />
    </aside>
  )
}
