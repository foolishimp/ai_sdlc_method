// Implements: REQ-F-NAV-001, REQ-F-NAV-005

// ROUTES — single authoritative source of all canonical URL patterns.
// All NavHandle components and all page components reference this constant.
// Never use string literals for paths.

export const ROUTES = {
  // ─── Root ──────────────────────────────────────────────────────────────────
  ROOT: '/',

  // ─── Per-workspace work areas ─────────────────────────────────────────────
  PROJECT: '/project/:workspaceId',
  OVERVIEW: '/project/:workspaceId/overview',
  SUPERVISION: '/project/:workspaceId/supervision',
  EVIDENCE: '/project/:workspaceId/evidence',
  RELEASE: '/project/:workspaceId/release',

  // ─── Canonical detail pages ───────────────────────────────────────────────
  FEATURE_DETAIL: '/project/:workspaceId/feature/:featureId',
  RUN_DETAIL: '/project/:workspaceId/run/:runId',
  REQ_DETAIL: '/project/:workspaceId/req/:reqKey',
  EVENT_DETAIL: '/project/:workspaceId/event/:eventIndex',

  // ─── Catch-all ────────────────────────────────────────────────────────────
  NOT_FOUND: '*',
} as const

// ─── Path builder helpers ─────────────────────────────────────────────────────
// Implements: REQ-F-NAV-005

export function buildOverviewPath(workspaceId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/overview`
}

export function buildSupervisionPath(workspaceId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/supervision`
}

export function buildEvidencePath(workspaceId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/evidence`
}

export function buildFeaturePath(workspaceId: string, featureId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/feature/${encodeURIComponent(featureId)}`
}

export function buildRunPath(workspaceId: string, runId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/run/${encodeURIComponent(runId)}`
}

export function buildReqPath(workspaceId: string, reqKey: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/req/${encodeURIComponent(reqKey)}`
}

export function buildEventPath(workspaceId: string, eventIndex: number): string {
  return `/project/${encodeURIComponent(workspaceId)}/event/${eventIndex}`
}

export function buildReleasePath(workspaceId: string): string {
  return `/project/${encodeURIComponent(workspaceId)}/release`
}
