# ADR-002: React Router v7 for Client-Side Routing

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-F-NAV-003

## Decision

Use React Router v7 with two routes: `/` (project list) and `/projects/:id` (project detail).

## Rationale

- React Router v7 supports data loaders — can pre-fetch project detail on navigation
- Two-route structure maps cleanly to the navigator's two views
- Deep-linking to `/projects/:id` is required (REQ-F-NAV-003 AC-4); React Router handles this with BrowserRouter
- No nested routing needed — the five views within project detail are tabs (client UI state), not routes

## Consequences

- The Vite dev server must be configured to serve `index.html` for all routes (history fallback)
- The `genesis-nav` CLI backend does not need to serve the frontend — Vite dev server handles it in dev; static files served by FastAPI in production
- Tab state (which of Status/Gaps/Queue/History is active) is local component state, not URL state (post-MVP: could add tab to URL)
