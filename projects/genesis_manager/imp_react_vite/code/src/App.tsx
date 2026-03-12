// Implements: REQ-F-NAV-001, REQ-F-UX-001

import React from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { useWorkspacePoller } from './hooks/useWorkspacePoller'
import { ProjectListPage } from './features/project-nav/ProjectListPage'
import { ProjectOverviewPage } from './features/overview/ProjectOverviewPage'
import { SupervisionConsolePage } from './features/supervision/SupervisionConsolePage'
import { EvidenceBrowserPage } from './features/evidence/EvidenceBrowserPage'
import { ROUTES } from './routing/routes'

// Router configuration — all canonical routes
// Implements: REQ-F-NAV-005 (stable, bookmarkable URLs)
const router = createBrowserRouter([
  {
    path: ROUTES.ROOT,
    element: <ProjectListPage />,
  },
  {
    path: ROUTES.OVERVIEW,
    element: <ProjectOverviewPage />,
  },
  {
    path: ROUTES.SUPERVISION,
    element: <SupervisionConsolePage />,
  },
  {
    path: ROUTES.EVIDENCE,
    element: <EvidenceBrowserPage />,
  },
  {
    // /project/:workspaceId → redirect to overview
    path: ROUTES.PROJECT,
    element: <Navigate to="overview" replace />,
  },
  {
    path: ROUTES.NOT_FOUND,
    element: (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-2xl font-bold text-muted-foreground/60 mb-2">Page not found</p>
          <a href="/" className="text-blue-600 hover:underline text-sm">Return to projects</a>
        </div>
      </div>
    ),
  },
])

// Root component — polling mounted here so it runs on every page.
// Implements: REQ-F-UX-001 (single polling instance at app root)
function AppRoot(): React.JSX.Element {
  // Single useWorkspacePoller instance — drives all data freshness across all work areas
  useWorkspacePoller()
  return <RouterProvider router={router} />
}

export default AppRoot
