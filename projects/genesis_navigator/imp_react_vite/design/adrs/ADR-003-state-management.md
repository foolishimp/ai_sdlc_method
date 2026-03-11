# ADR-003: TanStack Query v5, staleTime: Infinity, Manual Refresh

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-F-NAV-004, REQ-NFR-ARCH-001

## Decision

Use TanStack Query v5 for all server state. Set `staleTime: Infinity` on all queries.
Manual refresh triggers `queryClient.invalidateQueries()` on the relevant query keys.

## Rationale

- The navigator is explicitly a point-in-time reader (REQ-NFR-ARCH-001, INTENT.md "not a live monitor")
- `staleTime: Infinity` means data never refetches automatically — this is the correct semantic
- No global state store (Redux, Zustand) needed — all state is either server state (Query) or local UI state (useState/useReducer)
- TanStack Query v5 provides loading/error states, caching, and invalidation for free

## Cache key hierarchy

```
['projects']                           → GET /api/projects (project list)
['project', id]                        → GET /api/projects/{id} (project detail)
['gaps', id]                           → GET /api/projects/{id}/gaps
['queue', id]                          → GET /api/projects/{id}/queue
['history', id]                        → GET /api/projects/{id}/runs
['run', id, runId]                     → GET /api/projects/{id}/runs/{runId}
```

## Manual refresh behaviour

Refresh button on project detail invalidates `['project', id]`, `['gaps', id]`, `['queue', id]` simultaneously. History is refreshed separately (lower priority).

## Consequences

- No WebSocket, no SSE, no polling — data is fetched once per explicit user action
- The "last refresh" timestamp is derived from the TanStack Query `dataUpdatedAt` field
- Initial project list load fetches once on mount; subsequent navigations use cache
