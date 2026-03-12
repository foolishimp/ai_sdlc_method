# ADR-GM-004: Router — React Router 6
# Implements: REQ-F-NAV-005 (canonical bookmarkable URLs)

**Status**: Accepted | **Date**: 2026-03-13

## Context
REQ-F-NAV-005 requires stable, bookmarkable canonical URLs: `/feature/:id`, `/run/:run_id`, `/req/:req_key`, `/decision/:id`. The router must support these paths and allow direct URL navigation (no hash-based routing that breaks deep links). Chosen in Phase 1 so Phase 2 (NAV) can define the full ROUTES constant.

## Decision
**React Router 6** with `createBrowserRouter` (HTML5 history API — no hash).

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **React Router 6** | Industry standard; stable API; `createBrowserRouter` supports nested routes; loader pattern for data fetching; REQ-F-NAV-005 well-served | Slightly larger than TanStack Router; loaders add complexity if data fetching stays in Zustand |
| **TanStack Router** | Full TypeScript type-safety on route params; newer API | Less mature; smaller ecosystem; migration cost if standard changes |
| **Wouter** | Tiny (1.5kb) | No loader pattern; limited nested route support for canonical pages |

## Consequences
- `ROUTES` constant exported from `src/routes.ts`: typed map of all canonical URL patterns
- All navigation handle components import from `ROUTES` — no inline path strings
- Express server must be configured to return `index.html` for all non-`/api` paths (SPA fallback)
- **Connects to**: REQ-F-NAV-005 (canonical pages at stable URLs), all features that render navigation handles
