// Implements: REQ-F-NAV-001, REQ-F-NAV-002, REQ-F-NAV-003, REQ-F-NAV-004

import {
  buildFeaturePath,
  buildRunPath,
  buildReqPath,
  buildEventPath,
} from './routes'

// NavHandle discriminated union — every navigable entity in genesis_manager
// is representable as one of these four variants.
export type NavHandle =
  | { kind: 'feature'; featureId: string }
  | { kind: 'run'; runId: string }
  | { kind: 'req'; reqKey: string }
  | { kind: 'event'; eventIndex: number }

// buildNavPath — resolves a NavHandle + workspace context to a stable URL.
// Implements: REQ-F-NAV-005 (stable, bookmarkable URLs)
export function buildNavPath(workspaceId: string, handle: NavHandle): string {
  switch (handle.kind) {
    case 'feature':
      return buildFeaturePath(workspaceId, handle.featureId)
    case 'run':
      return buildRunPath(workspaceId, handle.runId)
    case 'req':
      return buildReqPath(workspaceId, handle.reqKey)
    case 'event':
      return buildEventPath(workspaceId, handle.eventIndex)
  }
}

// Convenience constructors
export const navHandle = {
  feature: (featureId: string): NavHandle => ({ kind: 'feature', featureId }),
  run: (runId: string): NavHandle => ({ kind: 'run', runId }),
  req: (reqKey: string): NavHandle => ({ kind: 'req', reqKey }),
  event: (eventIndex: number): NavHandle => ({ kind: 'event', eventIndex }),
} as const
